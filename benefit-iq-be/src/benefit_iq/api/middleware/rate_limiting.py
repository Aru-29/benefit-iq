"""Redis Sliding Window Rate Limiting Middleware."""

import time

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from benefit_iq.infrastructure.cache.redis.redis_cache import RedisCache


# pylint: disable=too-few-public-methods
class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Redis Sliding Window Rate Limiting Middleware."""

    def __init__(
        self,
        app,
        redis_cache: RedisCache,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter settings."""
        super().__init__(app)
        self.redis_cache = redis_cache
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        """Sliding window rate limit dispatch handler."""
        client = self.redis_cache.client

        # Bypass rate limiting if redis is not connected or available
        if not client:
            return await call_next(request)

        # Use client IP as key (in production use X-Forwarded-For if behind proxy)
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"rate_limit:{client_ip}"
        now = time.time()

        try:
            # We use a pipeline for atomicity
            async with client.pipeline(transaction=True) as pipe:
                # Remove timestamps older than the window
                pipe.zremrangebyscore(key, 0, now - self.window_seconds)
                # Count the number of requests in the window
                pipe.zcard(key)
                # Add the current request timestamp
                pipe.zadd(key, {str(now): now})
                # Expire the key after the window to save memory
                pipe.expire(key, self.window_seconds)

                results = await pipe.execute()

            request_count = results[1]

            if request_count >= self.max_requests:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": "Too many requests. Please try again later.",
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )

        except Exception:  # pylint: disable=broad-exception-caught
            # Fail open if Redis is down to preserve application availability
            pass

        return await call_next(request)
