import redis
import logging
from functools import lru_cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_redis() -> redis.Redis:
    """获取 Redis 客户端单例"""
    settings = get_settings()
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )
    try:
        client.ping()
        logger.info("[redis] 连接成功")
        print("redis连接成功")
    except redis.ConnectionError as e:
        logger.error(f"[redis] 连接失败: {e}")
        raise
    return client


if __name__ == '__main__':
    redis = get_redis()
