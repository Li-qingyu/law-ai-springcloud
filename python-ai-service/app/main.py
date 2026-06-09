from fastapi import  FastAPI
from app.api.v1 import ai
from app.core.config import get_settings
from app.services.semantic_cache import init_cache_collection
import logging
import sys
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # 输出到控制台
    ]
)

#创建应用实例
app = FastAPI(
    title="Python AI Service",
    description="法律咨询AI服务"
)

#注册路由
app.include_router(ai.router)


@app.on_event("startup")
async def startup_event():
    """服务启动时初始化资源"""
    try:
        init_cache_collection()
    except Exception as e:
        logging.warning(f"语义缓存集合初始化跳过: {e}")

# 根路径测试
@app.get("/")
async def root():
    return {"message": "Python AI Service is running"}

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.SERVICE_HOST, port=settings.SERVICE_PORT)