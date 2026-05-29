from fastapi import  FastAPI
from app.api.v1 import ai
from app.core.config import get_settings
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

# 根路径测试
@app.get("/")
async def root():
    return {"message": "Python AI Service is running"}

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.SERVICE_HOST, port=settings.SERVICE_PORT)