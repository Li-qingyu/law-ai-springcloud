"""
隐私脱敏模块
对敏感信息（手机号、身份证、姓名）进行正则替换
"""
import re
import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 敏感信息正则模式
SENSITIVE_PATTERNS = {
    "id_card": re.compile(r"\d{17}[\dXx]"),
    "phone": re.compile(r"1[3-9]\d{9}"),
    "name": re.compile(r"[一-龥]{2,4}(?=先生|女士|小姐)"),
}


class PrivacyManager:
    """隐私管理器"""

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.MEMORY_DESENSITIZE_ENABLED

    def desensitize(self, text: str) -> str:
        """对文本进行脱敏处理"""
        if not self.enabled or not text:
            return text

        result = text
        for field_name, pattern in SENSITIVE_PATTERNS.items():
            result = pattern.sub(f"[{field_name}]", result)

        if result != text:
            logger.debug("[privacy] 文本脱敏完成")

        return result

    def desensitize_for_llm(self, text: str) -> str:
        """发送 LLM 前脱敏（与 desensitize 相同，语义区分用）"""
        return self.desensitize(text)

    def desensitize_for_storage(self, text: str) -> str:
        """长期记忆存储前脱敏（与 desensitize 相同，语义区分用）"""
        return self.desensitize(text)
