from pydantic_settings import BaseSettings,SettingsConfigDict
import os
from functools import lru_cache

class Settings(BaseSettings):
    """
        优先级：
            系统环境变量>.env>默认值
    """
    DEBUG: bool = True

    # 服务配置
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000

    #配置ai
    DASHSCOPE_API_KEY: str
    OPENAI_MODEL: str="qwen3.5-plus"
    EMBEDDING_MODEL:str="text-embedding-v3"
    EMBEDDING_DIMENSION:int= 1024

    #配置Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_DATABASE_NAME: str
    MILVUS_COLLECTION_ARTICLES: str
    MILVUS_COLLECTION_CASES: str
    MILVUS_COLLECTION_HISTORY: str
    MILVUS_METRIC_TYPE: str   # 度量类型COSINE（余弦相似度

    #redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str | None = None
    REDIS_EXPIRE_TIME: int = 86400

    #agent配置
    AGENT_MAX_ITERATIONS: int = 10      # 最大迭代次数
    TOOL_SCORE_THRESHOLD: float = 0.7
    TOP_K_RESULTS: int = 5
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),  # 指向项目根目录的 .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

if __name__ == '__main__':
    settings=get_settings()
    print(settings.DEBUG)
    print(settings.MILVUS_HOST)
