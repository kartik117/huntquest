from functools import lru_cache

from redis import Redis

from huntquest.config import settings


@lru_cache
def get_redis() -> Redis:
    return Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=False)
