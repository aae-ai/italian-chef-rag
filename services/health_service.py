import time
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check for all ChefBot components"""

    def __init__(self, components: Dict[str, Any]):
        """
        Initialize with component references.

        Args:
            components: Dict with keys:
                - llm: ChatGroq instance
                - vector_db: VectorDB instance
                - session_manager: SessionManager instance
                - redis: Redis client (optional)
                - cache: RedisQueryCache (optional)
                - metrics: METRICS instance (optional)
        """
        self.llm = components.get('llm')
        self.vector_db = components.get('vector_db')
        self.session_manager = components.get('session_manager')
        self.redis = components.get('redis')
        self.cache = components.get('cache')
        self.metrics = components.get('metrics')
        self.start_time = components.get('start_time', time.time())

    def check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check.

        Returns:
            Health status dictionary
        """
        status = {
            "status": "healthy",
            "components": {},
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "timestamp": datetime.now().isoformat()
        }

        # Check LLM
        try:
            if self.llm:
                self.llm.invoke("ping")
                status["components"]["llm"] = "healthy"
        except Exception as e:
            status["components"]["llm"] = f"error: {str(e)}"
            status["status"] = "degraded"
            logger.error(f"LLM health check failed: {e}")

        # Check Vector DB
        try:
            if self.vector_db:
                self.vector_db.get_store()
                status["components"]["vector_db"] = "healthy"
        except Exception as e:
            status["components"]["vector_db"] = f"error: {str(e)}"
            status["status"] = "degraded"
            logger.error(f"Vector DB health check failed: {e}")

        # Check MongoDB (via SessionManager)
        try:
            if self.session_manager:
                if self.session_manager.health_check():
                    status["components"]["mongodb"] = "healthy"
                else:
                    status["components"]["mongodb"] = "error: connection failed"
                    status["status"] = "degraded"
        except Exception as e:
            status["components"]["mongodb"] = f"error: {str(e)}"
            status["status"] = "degraded"
            logger.error(f"MongoDB health check failed: {e}")

        # Check Redis
        try:
            if self.redis:
                self.redis.ping()
                status["components"]["redis"] = "healthy"
        except Exception as e:
            status["components"]["redis"] = f"error: {str(e)}"
            status["status"] = "degraded"
            logger.error(f"Redis health check failed: {e}")

        # Cache stats
        if self.cache:
            try:
                status["cache"] = self.cache.get_stats()
            except Exception:
                status["cache"] = {"error": "unavailable"}

        # Metrics stats
        if self.metrics:
            try:
                status["metrics"] = self.metrics.get_stats()
            except Exception:
                status["metrics"] = {"error": "unavailable"}

        return status
