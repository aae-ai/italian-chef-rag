"""
Rate Limiter Module
===================
Sliding window rate limiter using Redis
"""

import time
import logging
import redis

from services.metrics_service import METRICS

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window rate limiter using Redis.
    Prevents abuse by limiting requests per session.
    """

    def __init__(
        self,
        redis_url: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ):
        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = "chefbot:ratelimit:"
        logger.info(f"Rate limiter initialized: {max_requests} req/{window_seconds}s")

    def is_allowed(self, session_id: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            session_id: Session identifier

        Returns:
            True if allowed, False if rate limited
        """
        key = f"{self.key_prefix}{session_id}"
        current_time = time.time()
        window_start = current_time - self.window_seconds

        try:
            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request timestamp
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiry on the key
            pipe.expire(key, self.window_seconds)

            results = pipe.execute()
            request_count = results[1]

            if request_count >= self.max_requests:
                # Remove the request we just added
                self.redis.zrem(key, str(current_time))
                METRICS.record_error("rate_limit_exceeded")
                logger.warning(f"Rate limit exceeded for session: {session_id}")
                return False

            return True

        except redis.RedisError as e:
            logger.warning(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True

    def get_remaining(self, session_id: str) -> int:
        """
        Get remaining requests for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of remaining requests
        """
        key = f"{self.key_prefix}{session_id}"
        current_time = time.time()
        window_start = current_time - self.window_seconds

        try:
            # Clean old entries
            self.redis.zremrangebyscore(key, 0, window_start)

            # Count current
            count = self.redis.zcard(key)
            return max(0, self.max_requests - count)

        except redis.RedisError:
            return self.max_requests
