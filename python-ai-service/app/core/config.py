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
    DEEPSEEK_API_KEY: str
    DEEPSEEK_MODEL:str
    DEEPSEEK_API_BASE_URL:str

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

    # 检索优化开关
    RERANK_ENABLED: bool = True  #重排是否需要开启
    MULTI_QUERY_ENABLED: bool = True  #问题多路改写是否需要开启
    HYBRID_SEARCH_ENABLED: bool = True  #混合检索（向量+BM25）是否开启

    # Java API 配置（管理端 Agent 调用 law-law-service）
    JAVA_API_BASE_URL: str = "http://localhost:8082"
    JAVA_API_TIMEOUT: int = 30
    JAVA_API_RETRY_COUNT: int = 3

    # MCP 配置(管理端 Agent 经 MCP 调 law-ai-service 工具面)
    MCP_LAW_AI_URL: str = "http://localhost:8083/mcp"

    # AI 配置获取地址（RAG config_manager 调用 law-ai-service 的 /internal/ai-config）
    AI_CONFIG_URL: str = "http://localhost:8083"

    # 对话记忆管理配置
    MEMORY_WORKING_MAX_TURNS: int = 3          # 工作记忆保留轮数
    MEMORY_WORKING_MAX_TOKENS: int = 2500       # 工作记忆 token 硬上限
    MEMORY_SHORT_TERM_TTL_HOURS: int = 12       # 短期记忆 TTL（小时）
    MEMORY_SHORT_TERM_MAX_TOKENS: int = 800     # 短期记忆摘要 token 上限
    MEMORY_COMPRESS_THRESHOLD: int = 5          # 累积 N 轮触发压缩
    MEMORY_DESENSITIZE_ENABLED: bool = True     # 隐私脱敏开关

    # 长期记忆配置
    MEMORY_LONG_TERM_ENABLED: bool = True       # 长期记忆开关
    MEMORY_LONG_TERM_MIN_SCORE: float = 0.6     # 语义检索最低分数阈值
    MEMORY_LONG_TERM_TOP_K: int = 3             # 语义检索返回数量

    # 语义缓存配置
    SEMANTIC_CACHE_ENABLED: bool = True
    SEMANTIC_CACHE_COLLECTION: str = "semantic_cache"
    SEMANTIC_CACHE_THRESHOLD: float = 0.95     # 高于此阈值直接返回缓存
    SEMANTIC_CACHE_REFRESH_THRESHOLD: float = 0.85  # 介于此值和阈值之间，返回缓存并标记刷新
    SEMANTIC_CACHE_TTL_DAYS: int = 7
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
