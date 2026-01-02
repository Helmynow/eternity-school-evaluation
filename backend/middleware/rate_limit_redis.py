"""
Redis-based distributed rate limiting middleware
For production use with multiple server instances
"""

import os
import time
from typing import Optional, Tuple

import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting using Redis"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window = 60  # 1 minute window

        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except Exception as e:
            print(f"Redis not available, falling back to in-memory rate limiting: {e}")
            self.redis_client = None
            self.redis_available = False
            # Fallback to in-memory storage
            from collections import defaultdict

            self.memory_store = defaultdict(lambda: (0, time.time()))

    def _get_key(self, client_ip: str, path: str) -> str:
        """Generate Redis key for rate limiting"""
        # Use path-specific keys for better granularity
        minute = int(time.time() // 60)
        return f"ratelimit:{client_ip}:{path}:{minute}"

    def _check_rate_limit_redis(self, client_ip: str, path: str) -> Tuple[bool, int, int]:
        """Check rate limit using Redis"""
        key = self._get_key(client_ip, path)

        try:
            # Increment counter
            count = self.redis_client.incr(key)

            # Set expiration if this is the first request in this window
            if count == 1:
                self.redis_client.expire(key, self.window)

            # Check if limit exceeded
            remaining = max(0, self.requests_per_minute - count)
            reset_time = int(time.time() // 60) * 60 + self.window

            return count <= self.requests_per_minute, remaining, reset_time

        except Exception as e:
            # If Redis fails, allow request (fail open)
            print(f"Redis rate limit check failed: {e}")
            return True, self.requests_per_minute, int(time.time() + self.window)

    def _check_rate_limit_memory(self, client_ip: str, path: str) -> Tuple[bool, int, int]:
        """Fallback in-memory rate limiting"""
        current_time = time.time()
        count, window_start = self.memory_store[f"{client_ip}:{path}"]

        # Reset if window expired
        if current_time - window_start > self.window:
            count = 0
            window_start = current_time

        # Check rate limit
        if count >= self.requests_per_minute:
            remaining = 0
        else:
            remaining = self.requests_per_minute - count - 1

        # Update counter
        self.memory_store[f"{client_ip}:{path}"] = (count + 1, window_start)
        reset_time = int(window_start + self.window)

        return count < self.requests_per_minute, remaining, reset_time

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/api/v2/health", "/health"]:
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Check rate limit
        if self.redis_available:
            allowed, remaining, reset_time = self._check_rate_limit_redis(client_ip, path)
        else:
            allowed, remaining, reset_time = self._check_rate_limit_memory(client_ip, path)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": reset_time - int(time.time()),
                },
                headers={
                    "Retry-After": str(reset_time - int(time.time())),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
