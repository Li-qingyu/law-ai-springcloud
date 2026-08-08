import asyncio
import json
import logging
import time

import httpx

from app.core.ai_config.exceptions import AiConfigNotFoundError
from app.core.ai_config.models import AiConfig
from app.core.config import get_settings
from app.repositories.async_redis_client import get_async_redis

logger = logging.getLogger(__name__)

REDIS_KEY_DEFAULT = "ai:config:default"
REDIS_TTL_REFRESH = 7 * 24 * 60 * 60

CACHE_TTL_SECONDS = 30


class ConfigManager:

    def __init__(self):
        self._cache: dict | None = None
        self._cache_time: float = 0.0

    async def get_current_config(self) -> AiConfig:
        if self._cache and (time.time() - self._cache_time) < CACHE_TTL_SECONDS:
            return self._cache

        config = await self._from_redis(REDIS_KEY_DEFAULT)
        if config:
            self._set_cache(config)
            return config

        config = await self._from_http()
        if config:
            self._set_cache(config)
            return config

        config = self._from_env()
        if config:
            self._set_cache(config)
            return config

        raise AiConfigNotFoundError("所有配置源均不可用")

    async def get_config(self, provider: str) -> AiConfig:
        config = await self._from_redis_by_provider(provider)
        if config:
            return config

        config = await self._from_http(provider)
        if config:
            return config

        config = self._from_env()
        if config:
            return config

        raise AiConfigNotFoundError(f"未找到配置: {provider}")

    async def get_api_key(self) -> str:
        config = await self.get_current_config()
        return config.api_key

    async def create_llm(self, provider: str | None = None, **overrides):
        from langchain.chat_models import init_chat_model

        if provider:
            config = await self.get_config(provider)
        else:
            config = await self.get_current_config()

        override_model = overrides.pop("model", None)
        model_name = override_model or config.model_name

        return init_chat_model(
            f"openai:{model_name}",
            base_url=config.api_base_url,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            **overrides,
        )

    def invalidate_cache(self):
        self._cache = None
        self._cache_time = 0.0

    async def _from_redis(self, key: str) -> AiConfig | None:
        try:
            r = await get_async_redis()
            raw = await r.get(key)
            if not raw:
                return None
            await r.expire(key, REDIS_TTL_REFRESH)
            data = json.loads(raw)
            logger.debug(f"[ai_config] Redis 命中: key={key}")
            return AiConfig.from_json(data)
        except Exception as e:
            logger.warning(f"[ai_config] Redis 读取失败: {e}")
            return None

    async def _from_redis_by_provider(self, provider: str) -> AiConfig | None:
        """按 provider 查找 Redis，key 格式为 ai:config:{provider}:{modelName}"""
        try:
            r = await get_async_redis()
            cursor = 0
            pattern = f"ai:config:{provider}:*"
            while True:
                cursor, keys = await r.scan(cursor=cursor, match=pattern, count=20)
                for key in keys:
                    raw = await r.get(key)
                    if raw:
                        await r.expire(key, REDIS_TTL_REFRESH)
                        data = json.loads(raw)
                        logger.debug(f"[ai_config] Redis 按 provider 命中: key={key}")
                        return AiConfig.from_json(data)
                if cursor == 0:
                    break
            return None
        except Exception as e:
            logger.warning(f"[ai_config] Redis 按 provider 查询失败: {e}")
            return None

    async def _from_http(self, provider: str | None = None) -> AiConfig | None:
        settings = get_settings()
        url = f"{settings.AI_CONFIG_URL}/internal/ai-config/current"
        params = {"provider": provider} if provider else {}
        timeout = httpx.Timeout(connect=3.0, read=5.0)

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        body = resp.json()
                        if body.get("code") == 200 and body.get("data"):
                            logger.debug(f"[ai_config] HTTP 降级命中: {url}")
                            return AiConfig.from_json(body["data"])
                logger.warning(f"[ai_config] HTTP 返回异常: status={resp.status_code}")
            except Exception as e:
                logger.warning(f"[ai_config] HTTP 请求失败(attempt {attempt+1}): {e}")
                if attempt == 0:
                    await asyncio.sleep(0.5)
        return None

    def _from_env(self) -> AiConfig | None:
        try:
            settings = get_settings()
            config = AiConfig(
                provider="qwen",
                model_name=settings.OPENAI_MODEL,
                api_key=settings.DASHSCOPE_API_KEY,
                api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                max_tokens=4096,
                temperature=0.7,
            )
            logger.info("[ai_config] 使用 .env 兜底配置")
            return config
        except Exception as e:
            logger.error(f"[ai_config] .env 读取失败: {e}")
            return None

    def _set_cache(self, config: AiConfig):
        self._cache = config
        self._cache_time = time.time()
