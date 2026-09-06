import logging
import time
import uuid
from typing import Callable
from fastapi import Request
from app.core.redis import get_redis
from app.core.error_codes import APIException, ErrorCode

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, requests_per_window: int, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds

    async def check(self, request: Request, route_name: str) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{route_name}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            r = await get_redis()
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            member = f"{now}:{uuid.uuid4().hex[:8]}"
            pipe.zadd(key, {member: now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()
            request_count = results[2]

            if request_count > self.requests_per_window:
                retry_after = int(self.window_seconds - (now - window_start))
                raise APIException(
                    code=ErrorCode.RATE_LIMITED,
                    message=f"Too many requests. Please wait {retry_after} seconds.",
                    status_code=429,
                    headers={"Retry-After": str(max(1, retry_after))},
                )
        except APIException:
            raise
        except Exception as exc:
            # Fallback gracefully if Redis is unavailable (ADR-011)
            logger.warning(
                "Redis rate limiter unavailable for key '%s'; failing open for availability. Error: %s",
                key,
                exc,
            )


quotes_limiter = RateLimiter(requests_per_window=20, window_seconds=60)
checkout_limiter = RateLimiter(requests_per_window=5, window_seconds=60)
products_limiter = RateLimiter(requests_per_window=120, window_seconds=60)
eligibility_limiter = RateLimiter(requests_per_window=10, window_seconds=60)
