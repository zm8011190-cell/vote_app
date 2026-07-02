import os
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import HTTPException, Request
from redis.asyncio import Redis, from_url
from redis.exceptions import ConnectionError, RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

redis_client: Redis | None = None
redis_available = False


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    global redis_client, redis_available
    redis_client = from_url(REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        redis_available = True
    except (ConnectionError, RedisError, OSError):
        redis_available = False
        if redis_client is not None:
            await redis_client.close()
            redis_client = None
    try:
        yield
    finally:
        if redis_client is not None:
            await redis_client.close()
            redis_client = None
            redis_available = False


def get_redis_client() -> Redis | None:
    return redis_client


async def rate_limiter(request: Request) -> None:
    if not redis_available or redis_client is None:
        return

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    window = int(time.time() // WINDOW_SECONDS)
    key = f"rate_limit:{client_ip}:{window}"

    try:
        current_count = await redis_client.incr(key)
        if current_count == 1:
            await redis_client.expire(key, WINDOW_SECONDS)
        if current_count > RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    except (ConnectionError, RedisError, OSError):
        return
