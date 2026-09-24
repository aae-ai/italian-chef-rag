import time
import json
import logging
import hashlib
import redis
from typing import Optional, List, Dict, Any
from models.schemas import ChefBotResponse, SourceDocument
from services.metrics_service import METRICS

logger = logging.getLogger(__name__)

class RedisQueryCache:
    """
    Redis-based query cache for reducing LLM API calls.
    
    Intent:
    - Provides a persistent L2 cache layer shared across app instances.
    - Uses SHA-256 hashing to create deterministic keys from queries.
    - Employs 'SETEX' (Set with Expiration) to ensure the cache is self-cleaning.
    """

    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int = 3600,
        max_cache_size: int = 10000
    ):
        self.ttl = ttl_seconds
        self.max_cache_size = max_cache_size

        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        self.cache_key_prefix = "chefbot:cache:"
        logger.info(f"Redis cache initialized (TTL: {ttl_seconds}s)")

    def _hash_query(self, query: str, session_id: str = None) -> str:
        """Create consistent hash for query"""
        key_data = f"{query}:{session_id or 'global'}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _make_key(self, query_hash: str) -> str:
        """Make full Redis key"""
        return f"{self.cache_key_prefix}{query_hash}"

    def get(self, query: str, session_id: str = None) -> Optional[ChefBotResponse]:
        """Get cached response if available"""
        query_hash = self._hash_query(query, session_id)
        key = self._make_key(query_hash)

        try:
            cached_data = self.redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                if time.time() - data['timestamp'] < self.ttl:
                    METRICS.record_cache_hit()
                    sources = [SourceDocument(**s) for s in data.get('sources', [])]
                    return ChefBotResponse(
                        answer=data['answer'],
                        sources=sources,
                        session_id=session_id or "",
                        cached=True
                    )
                self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")

        METRICS.record_cache_miss()
        return None

    def set(self, query: str, response: ChefBotResponse, session_id: str = None) -> bool:
        """Cache a response"""
        query_hash = self._hash_query(query, session_id)
        key = self._make_key(query_hash)

        try:
            cache_entry = {
                'answer': response.answer,
                'sources': [
                    {"content": s.content, "source": s.source, "score": s.score}
                    for s in response.sources
                ],
                'timestamp': time.time()
            }
            self.redis.setex(key, self.ttl, json.dumps(cache_entry))
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    def invalidate(self, pattern: str = "*"):
        """Invalidate cache entries matching pattern"""
        try:
            keys = self.redis.keys(f"{self.cache_key_prefix}{pattern}")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            keys = self.redis.keys(f"{self.cache_key_prefix}*")
            return {"entries": len(keys), "ttl_seconds": self.ttl}
        except Exception:
            return {"error": "Redis connection failed"}
