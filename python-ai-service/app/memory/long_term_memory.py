"""
长期记忆管理器
复用 consult_history 集合，按 user_id 过滤做跨会话语义检索
"""
import json
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.config import get_settings
from app.repositories.milvus_client import search_by_text
from app.memory.privacy_manager import PrivacyManager

logger = logging.getLogger(__name__)

MEMORY_PROMPT_HEADER = "【历史记忆】"
MAX_MEMORY_TOKENS = 200


class LongTermMemory:
    """长期记忆管理器：基于 consult_history 集合的跨会话语义检索"""

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.MEMORY_LONG_TERM_ENABLED
        self.collection_name = settings.MILVUS_COLLECTION_HISTORY
        self.min_score = settings.MEMORY_LONG_TERM_MIN_SCORE
        self.top_k = settings.MEMORY_LONG_TERM_TOP_K
        self.privacy = PrivacyManager()

    def recall(self, user_id: Optional[int], current_question: str,
               short_term_summary: Optional[dict] = None) -> str:
        """
        从长期记忆中召回相关历史。

        仅在短期记忆缺失时调用，避免每次请求都查 Milvus。

        Args:
            user_id: 当前用户 ID（游客为 None）
            current_question: 当前问题
            short_term_summary: 短期记忆摘要（可选，用于增强查询）

        Returns:
            记忆提示块字符串，无命中时返回空字符串
        """
        if not self.enabled or user_id is None:
            return ""

        try:
            # 构造查询文本：当前问题 + 短期记忆核心诉求
            query_parts = [current_question]
            if short_term_summary:
                core_demand = short_term_summary.get("核心诉求", "")
                if core_demand:
                    query_parts.append(core_demand)
            query_text = " ".join(query_parts)

            # Milvus 语义检索，按 user_id 过滤
            filter_expr = f"user_id == {user_id}"
            results = search_by_text(
                collection_name=self.collection_name,
                query_text=query_text,
                top_k=self.top_k,
                filter_expr=filter_expr,
                output_fields=["source_id", "question", "answer", "session_id", "content_json"],
                min_score=self.min_score,
            )

            if not results:
                logger.info(f"[long_term] 未命中历史记忆: user_id={user_id}")
                return ""

            # 构建记忆提示块
            memory_block = self._build_memory_prompt(results)
            logger.info(f"[long_term] 命中 {len(results)} 条历史记忆: user_id={user_id}")
            return memory_block

        except Exception as e:
            logger.error(f"[long_term] 长期记忆检索失败: {e}")
            return ""

    def _build_memory_prompt(self, results: List[Dict[str, Any]]) -> str:
        """构建记忆提示块，控制在 MAX_MEMORY_TOKENS 以内"""
        lines = [MEMORY_PROMPT_HEADER]

        for i, result in enumerate(results, 1):
            content_json = result.get("content_json", "{}")
            if isinstance(content_json, str):
                try:
                    content_json = json.loads(content_json)
                except (json.JSONDecodeError, TypeError):
                    content_json = {}

            question = content_json.get("question", "")
            answer = content_json.get("answer", "")
            score = result.get("score", 0.0)

            # 截断过长的回答
            if len(answer) > 150:
                answer = answer[:150] + "..."

            lines.append(f"{i}. 用户曾咨询：{question}")
            lines.append(f"   结论：{answer}（相关度：{score:.2f}）")

        memory_text = "\n".join(lines)

        # Token 硬上限控制（中文约 1.5 字/token）
        max_chars = MAX_MEMORY_TOKENS * 1.5
        if len(memory_text) > max_chars:
            memory_text = memory_text[:int(max_chars)] + "..."

        return memory_text
