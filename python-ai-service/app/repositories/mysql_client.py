import aiomysql
import logging
from functools import lru_cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 连接池单例
_pool: aiomysql.Pool | None = None


async def get_mysql_pool() -> aiomysql.Pool:
    """获取 MySQL 连接池单例"""
    global _pool
    if _pool is not None and not _pool._closed:
        return _pool

    settings = get_settings()
    _pool = await aiomysql.create_pool(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        db=settings.MYSQL_DATABASE,
        user=settings.MYSQL_USERNAME,
        password=settings.MYSQL_PASSWORD,
        charset=settings.MYSQL_CHARSET,
        minsize=settings.MYSQL_MIN_SIZE,
        maxsize=settings.MYSQL_MAX_SIZE,
        autocommit=True,
    )
    logger.info(f"[mysql] 连接池创建成功: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    return _pool


async def close_mysql_pool():
    """关闭 MySQL 连接池"""
    global _pool
    if _pool is not None and not _pool._closed:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("[mysql] 连接池已关闭")


async def execute(sql: str, args=None) -> int:
    """执行 SQL（INSERT/UPDATE/DELETE），返回影响行数"""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, args)
            return cur.rowcount


async def fetchone(sql: str, args=None) -> dict | None:
    """查询单条记录，返回字典或 None"""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchone()


async def fetchall(sql: str, args=None) -> list[dict]:
    """查询多条记录，返回字典列表"""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchall()

async def test1():
    row = await fetchall("SELECT * FROM user")
    logger.info(f"连接测试: {row}")
    await close_mysql_pool()
    return row

if __name__ == '__main__':
    import asyncio
    asyncio.run(test1())
    logger.info("测试完成")
