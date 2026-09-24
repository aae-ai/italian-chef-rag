"""
ChefBot RAG Engine
==================
Italian Chef Bot - RAG-powered recipe assistant
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from langchain_classic.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# LangChain
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_groq import ChatGroq

# Core
from core.config import Config
from core.prompts import get_contextualize_prompt, get_qa_prompt

# Models & Services
from models.schemas import ChefBotResponse, SourceDocument
from services.cache_service import RedisQueryCache
from services.health_service import HealthChecker
from services.metrics_service import METRICS, ChefBotCallbackHandler
from services.rate_limiter import RateLimiter
from services.session_service import SessionManager
from services.vector_store import VectorDB

logger = logging.getLogger(__name__)


class ChefBot:
    def __init__(
        self, cache_enabled: bool = True, rate_limit: int = 60, rate_window: int = 60
    ):
        logger.info("Initializing ChefBot...")

        self.cache_enabled = cache_enabled
        self.start_time = time.time()

        # Initialize core components
        self.session_manager = SessionManager()
        self.vector_db = VectorDB()
        self.vector_db.ingest_if_empty()

        # Initialize Redis components
        import redis

        self.redis = redis.from_url(Config.REDIS_URL, decode_responses=True)

        self.cache = (
            RedisQueryCache(Config.REDIS_URL, Config.CACHE_TTL)
            if cache_enabled
            else None
        )
        self.rate_limiter = RateLimiter(Config.REDIS_URL, rate_limit, rate_window)

        # Initialize RAG
        self._init_rag()

        # Initialize health checker
        self.health_checker = HealthChecker(
            {
                "llm": self.llm,
                "vector_db": self.vector_db,
                "session_manager": self.session_manager,
                "redis": self.redis,
                "cache": self.cache,
                "metrics": METRICS,
                "start_time": self.start_time,
            }
        )

        logger.info("ChefBot initialized successfully!")

    def _init_rag(self):
        """Initialize core RAG components"""
        self.retriever = self.vector_db.get_store().as_retriever(search_kwargs={"k": 4})

        callback_handler = ChefBotCallbackHandler()
        self.llm = ChatGroq(
            model=Config.LLM_MODEL,
            temperature=0.2,
            api_key=Config.GROQ_API_KEY,
            callbacks=[callback_handler],
        )

        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, get_contextualize_prompt()
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, get_qa_prompt())

        rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

        # FIXED: restored output_messages_key="answer" so history is saved
        self.chain = RunnableWithMessageHistory(
            rag_chain,
            self.session_manager.get_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

    def _validate_query(self, query: str) -> None:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query) > 10000:
            raise ValueError("Query too long (max 10000 characters)")

    def _extract_sources(self, response: Dict[str, Any]) -> List[SourceDocument]:
        sources = []

        # Try multiple possible keys (LangChain sometimes returns different ones)
        docs = (
            response.get("source_documents")
            or response.get("context")
            or response.get("docs")
            or []
        )

        for doc in docs:
            if hasattr(doc, "page_content"):  # LangChain Document object
                content = doc.page_content[:500]

                # Smart source name detection
                metadata = doc.metadata or {}
                source_name = (
                    metadata.get("source")
                    or metadata.get("filename")
                    or metadata.get("title")
                    or metadata.get("recipe_name")
                    or metadata.get("url")
                    or metadata.get("id")
                    or "Recipe Document"
                )

                sources.append(
                    SourceDocument(
                        content=content,
                        source=source_name,
                        score=metadata.get("score", 0.0),
                    )
                )
            elif isinstance(doc, dict):
                content = doc.get("page_content", "")[:500]
                metadata = doc.get("metadata", {})
                source_name = (
                    metadata.get("source")
                    or metadata.get("filename")
                    or metadata.get("title")
                    or metadata.get("recipe_name")
                    or "Recipe Document"
                )
                sources.append(
                    SourceDocument(content=content, source=source_name, score=0.0)
                )

        return sources

    def ask(self, query: str, session_id: str = None) -> ChefBotResponse:
        """
        Main RAG Execution Pipeline (The 'Caching Dance'):
        1. VALIDATE: Ensure query integrity.
        2. RATE LIMIT: Prevent abuse via Redis sorted sets.
        3. CACHE LOOKUP: Check Redis for pre-existing answers (Speed/Cost optimization).
        4. HISTORY SYNC: If cached, manually update MongoDB history to maintain context.
        5. RAG CHAIN: If cache miss, execute full retrieval and LLM generation.
        6. PERSIST: Save fresh LLM results back to Redis with TTL.
        """
        start_time = time.time()
        self._validate_query(query)

        if not session_id:
            session_id = str(uuid.uuid4())

        # Rate limit check
        if not self.rate_limiter.is_allowed(session_id):
            METRICS.record_request("ask", "rate_limited")
            return ChefBotResponse(
                answer="Too many requests. Please wait before trying again.",
                sources=[],
                session_id=session_id,
                cached=False,
                latency_ms=0,
            )

        METRICS.requests_in_flight.inc()

        try:
            # Cache check
            if self.cache_enabled and self.cache:
                cached_response = self.cache.get(query, session_id)
                if cached_response:
                    METRICS.record_request("ask", "cache_hit")
                    
                    # Manually update history for cached responses
                    try:
                        history = self.session_manager.get_history(session_id)
                        history.add_user_message(query)
                        history.add_ai_message(cached_response.answer)
                    except Exception as e:
                        logger.warning(f"Failed to update history for cached response: {e}")

                    METRICS.requests_in_flight.dec()
                    return cached_response

            METRICS.record_request("ask", "processing")

            response = self.chain.invoke(
                {"input": query}, config={"configurable": {"session_id": session_id}}
            )

            answer = response.get("answer", "No response.")
            sources = self._extract_sources(response)
            latency_ms = (time.time() - start_time) * 1000

            METRICS.record_latency("ask", latency_ms / 1000)

            result = ChefBotResponse(
                answer=answer,
                sources=sources,
                session_id=session_id,
                cached=False,
                latency_ms=latency_ms,
            )

            # Cache response
            if self.cache_enabled and self.cache and answer != "No response.":
                self.cache.set(query, result, session_id)

            METRICS.requests_in_flight.dec()
            return result

        except Exception as e:
            METRICS.requests_in_flight.dec()
            METRICS.record_error(type(e).__name__)
            METRICS.record_request("ask", "error")
            logger.error(f"RAG chain failed: {e}", exc_info=True)
            return ChefBotResponse(
                answer="I encountered an error. Please try again.",
                sources=[],
                session_id=session_id,
                cached=False,
                latency_ms=(time.time() - start_time) * 1000,
            )

    # Simplified pass-throughs or removal (depending on router usage)
    def health_check(self) -> Dict[str, Any]:
        return self.health_checker.check()

    def metrics(self) -> bytes:
        return METRICS.metrics()

    def get_stats(self) -> Dict[str, Any]:
        return METRICS.get_stats()

    def get_cache_stats(self) -> Dict[str, Any]:
        return self.cache.get_stats() if self.cache else {"error": "Cache disabled"}

    def invalidate_cache(self, session_id: str = None):
        if self.cache:
            self.cache.invalidate(session_id or "*")
