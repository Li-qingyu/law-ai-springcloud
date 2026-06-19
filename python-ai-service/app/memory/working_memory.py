"""
工作记忆管理器
负责：窗口管理（保留最近 2-3 轮）、会话元信息摘要头、引用锚点
"""
import re
import logging
from typing import List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WorkingMemory:
    """工作记忆：保留最近 N 轮完整对话，token 硬上限控制"""

    def __init__(self, max_turns: int = None, max_tokens: int = None):
        settings = get_settings()
        self.max_turns = max_turns or settings.MEMORY_WORKING_MAX_TURNS
        self.max_tokens = max_tokens or settings.MEMORY_WORKING_MAX_TOKENS
        self.current_turn_tokens = 1500  # 当前轮保护上限

    def build_context(self, conversation_history: list) -> str:
        """
        构建工作记忆上下文文本。
        conversation_history: List[ConversationHistoryMessage] (role, content, timestamp)
        """
        if not conversation_history:
            return ""

        # 1. 当前轮保护：最近 2 条消息（一轮问答）必须完整保留
        protected = conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history

        # 2. 更早的轮次，按 token 预算截断
        earlier = conversation_history[:-2] if len(conversation_history) > 2 else []
        # 只保留最近 max_turns-1 轮（因为当前轮已保护）
        max_earlier_msgs = (self.max_turns - 1) * 2
        if len(earlier) > max_earlier_msgs:
            earlier = earlier[-max_earlier_msgs:]

        # 3. Token 硬上限控制：从旧到新累加
        context_parts = []
        total_tokens = 0

        for msg in earlier:
            msg_tokens = _estimate_tokens(msg.content)
            if total_tokens + msg_tokens > self.max_tokens - self.current_turn_tokens:
                logger.info(f"[working_memory] token 上限，截断早期消息")
                break
            context_parts.append(_format_message(msg))
            total_tokens += msg_tokens

        # 4. 当前轮完整保护
        for msg in protected:
            context_parts.append(_format_message(msg))

        return "\n".join(context_parts)

    def get_working_turns_for_history(self, conversation_history: list) -> list:
        """
        返回应注入 LLM 的工作记忆消息列表（用于 LangChain Message 转换）。
        与 build_context 逻辑一致，但返回原始消息对象。
        """
        if not conversation_history:
            return []

        protected = conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history
        earlier = conversation_history[:-2] if len(conversation_history) > 2 else []
        max_earlier_msgs = (self.max_turns - 1) * 2
        if len(earlier) > max_earlier_msgs:
            earlier = earlier[-max_earlier_msgs:]

        result = []
        total_tokens = 0

        for msg in earlier:
            msg_tokens = _estimate_tokens(msg.content)
            if total_tokens + msg_tokens > self.max_tokens - self.current_turn_tokens:
                break
            result.append(msg)
            total_tokens += msg_tokens

        result.extend(protected)
        return result


def _estimate_tokens(text: str) -> int:
    """估算 token 数（中文约 1.5 字/token）"""
    return max(1, int(len(text) / 1.5))


def _format_message(msg) -> str:
    """格式化单条消息为可读文本"""
    role = "用户" if msg.role == "user" else "助手"
    return f"{role}：{msg.content}"


def build_memory_header(short_term_summary: dict, round_count: int) -> str:
    """
    构建会话元信息摘要头，注入系统 prompt 前端。
    即使工作记忆只保留最近两轮，模型也能掌握整体脉络。
    """
    if not short_term_summary:
        return ""

    core_demand = short_term_summary.get("核心诉求", "未知")
    confirmed_facts = short_term_summary.get("已确认事实", [])
    cited_laws = short_term_summary.get("已讨论法律要点", [])

    facts_str = "、".join(
        [f["事实"] for f in confirmed_facts[:3]]
    ) if confirmed_facts else "无"
    laws_str = "、".join(
        [l["法条或原则"] for l in cited_laws[:2]]
    ) if cited_laws else "无"

    return (
        f"【本次咨询已进行 {round_count} 轮，核心诉求：{core_demand}；"
        f"已确认事实：{facts_str}；已引用法条：{laws_str}】"
    )


def extract_reference_anchor(conversation_history: list) -> str:
    """
    提取引用锚点：从对话历史中找到最后一条法条引用，防止事实漂移。
    当工作记忆丢弃旧轮时，保留最后一条对关键事实的引用摘要（1-2 句）。
    """
    if not conversation_history or len(conversation_history) < 4:
        return ""

    # 从后往前查找助手回复中的法条引用
    for msg in reversed(conversation_history):
        if msg.role == "assistant":
            law_refs = re.findall(r'[一-鿿]+法(?:[典律则])?[^一-鿿]*第?\d+条', msg.content)
            if law_refs:
                # 清理匹配结果中的书名号等非CJK字符
                cleaned = [re.sub(r'[》）)》\s]', '', ref) for ref in law_refs]
                unique_refs = list(dict.fromkeys(cleaned))[:2]
                return f"（前述已引用：{'、'.join(unique_refs)}）"

    return ""
