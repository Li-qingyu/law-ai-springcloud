from functools import lru_cache

from app.core.ai_config.config_manager import ConfigManager


@lru_cache()
def get_ai_config_manager() -> ConfigManager:
    return ConfigManager()


__all__ = ["get_ai_config_manager", "ConfigManager"]
