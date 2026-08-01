import logging

from functools import lru_cache
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_async_redis() -> Redis:
    settings = get_settings()
    client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )
    logger.info(f"[async_redis] 连接已创建: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
    return client
