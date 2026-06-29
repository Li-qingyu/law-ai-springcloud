from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import ai
from app.api.v1 import admin
from app.core.config import get_settings
from app.services.semantic_cache import init_cache_collection, SemanticCache
import logging
import sys
import uvicorn
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # 输出到控制台
    ]
)


async def _cache_cleanup_loop(stop_event: asyncio.Event):
    """每 24 小时清理一次过期语义缓存，收到停止信号后等当前清理完成再退出"""
    CLEANUP_INTERVAL = 24 * 3600  # 24 小时

    while not stop_event.is_set():
        try:
            # 超时 → 到达清理时间，执行清理
            # event 被 set → 收到停止信号，退出循环
            await asyncio.wait_for(stop_event.wait(), timeout=CLEANUP_INTERVAL)
            break  # event 被 set，退出
        except asyncio.TimeoutError:
            pass  # 超时，继续执行清理

        try:
            cache = SemanticCache()
            deleted = cache.cleanup_expired()
            logging.info(f"[cache_cleanup] 定时清理过期缓存 {deleted} 条")
        except Exception as e:
            logging.error(f"[cache_cleanup] 定时清理失败: {e}")

    logging.info("[cache_cleanup] 定时任务已退出")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    try:
        init_cache_collection()
    except Exception as e:
        logging.warning(f"语义缓存集合初始化跳过: {e}")

    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(_cache_cleanup_loop(stop_event))
    logging.info("语义缓存定时清理任务已注册")

    yield

    # 关闭时：通知停止，等待当前清理完成
    stop_event.set()
    try:
        await asyncio.wait_for(cleanup_task, timeout=30)
    except asyncio.TimeoutError:
        logging.warning("[cache_cleanup] 清理任务超时，强制退出")
    logging.info("语义缓存定时清理任务已停止")


#创建应用实例
app = FastAPI(
    title="Python AI Service",
    description="法律咨询AI服务",
    lifespan=lifespan,
)

#注册路由
app.include_router(ai.router)
app.include_router(admin.router)


# 根路径测试
@app.get("/")
async def root():
    return {"message": "Python AI Service is running"}

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.SERVICE_HOST, port=settings.SERVICE_PORT)