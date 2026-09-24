import time
import logging
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest,
    CONTENT_TYPE_LATEST, REGISTRY
)
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from core.config import Config

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and manages Prometheus metrics for ChefBot"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if MetricsCollector._initialized:
            return
        
        # Request metrics
        self.requests_total = Counter(
            'chefbot_requests_total',
            'Total number of requests',
            ['status', 'endpoint']
        )
        self.requests_in_flight = Gauge(
            'chefbot_requests_in_flight',
            'Number of requests currently being processed'
        )
        # Latency metrics
        self.request_latency = Histogram(
            'chefbot_request_latency_seconds',
            'Request latency in seconds',
            ['endpoint'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        self.llm_latency = Histogram(
            'chefbot_llm_latency_seconds',
            'LLM call latency in seconds',
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
        )
        self.vector_search_latency = Histogram(
            'chefbot_vector_search_latency_seconds',
            'Vector search latency in seconds',
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
        )
        # Token metrics
        self.tokens_used = Counter(
            'chefbot_tokens_used_total',
            'Total tokens used',
            ['model', 'type']
        )
        # Cache metrics
        self.cache_hits = Counter('chefbot_cache_hits_total', 'Total number of cache hits')
        self.cache_misses = Counter('chefbot_cache_misses_total', 'Total number of cache misses')
        self.cache_hit_ratio = Gauge('chefbot_cache_hit_ratio', 'Cache hit ratio')
        # Error metrics
        self.errors_total = Counter(
            'chefbot_errors_total',
            'Total number of errors',
            ['error_type']
        )
        # Internal counters
        self._cache_hits = 0
        self._cache_misses = 0
        MetricsCollector._initialized = True

    def record_request(self, endpoint: str, status: str = "success"):
        self.requests_total.labels(endpoint=endpoint, status=status).inc()

    def record_latency(self, endpoint: str, latency: float):
        self.request_latency.labels(endpoint=endpoint).observe(latency)

    def record_llm_latency(self, latency: float):
        self.llm_latency.observe(latency)

    def record_vector_latency(self, latency: float):
        self.vector_search_latency.observe(latency)

    def record_tokens(self, model: str, prompt_tokens: int, completion_tokens: int):
        self.tokens_used.labels(model=model, type='prompt').inc(prompt_tokens)
        self.tokens_used.labels(model=model, type='completion').inc(completion_tokens)

    def record_cache_hit(self):
        self._cache_hits += 1
        self.cache_hits.inc()
        self._update_hit_ratio()

    def record_cache_miss(self):
        self._cache_misses += 1
        self.cache_misses.inc()
        self._update_hit_ratio()

    def _update_hit_ratio(self):
        total = self._cache_hits + self._cache_misses
        if total > 0:
            ratio = self._cache_hits / total
            self.cache_hit_ratio.set(ratio)

    def record_error(self, error_type: str):
        self.errors_total.labels(error_type=error_type).inc()

    def get_stats(self) -> dict:
        """Get current metrics summary"""
        total_requests = self._cache_hits + self._cache_misses
        hit_ratio = self._cache_hits / total_requests if total_requests > 0 else 0
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_ratio": round(hit_ratio, 3),
        }

    def metrics(self) -> bytes:
        """Get Prometheus metrics in exposition format"""
        return generate_latest(REGISTRY)

# Singleton instance
METRICS = MetricsCollector()

class ChefBotCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LangChain metrics"""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.llm_start_time = time.time()

    def on_llm_end(self, response, **kwargs):
        if hasattr(self, 'llm_start_time'):
            latency = time.time() - self.llm_start_time
            METRICS.record_llm_latency(latency)

            if isinstance(response, LLMResult) and response.llm_output:
                token_usage = response.llm_output.get('token_usage', {})
                if token_usage:
                    METRICS.record_tokens(
                        Config.LLM_MODEL,
                        token_usage.get('prompt_tokens', 0),
                        token_usage.get('completion_tokens', 0)
                    )

    def on_retriever_start(self, query, **kwargs):
        self.retriever_start_time = time.time()

    def on_retriever_end(self, documents, **kwargs):
        if hasattr(self, 'retriever_start_time'):
            latency = time.time() - self.retriever_start_time
            METRICS.record_vector_latency(latency)

    def on_chain_error(self, error, **kwargs):
        METRICS.record_error(type(error).__name__)
