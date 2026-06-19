"""
短期记忆管理器
负责：滚动窗口压缩、结构化摘要生成、Redis 存储（Python 端独立 Key）
Java 端继续用 ai:session:{id} 存原始历史，Python 端用 ai:memory:{id}:short_term 存摘要。
"""
import json
import logging
import time
from datetime import datetime
from typing import Optional, List

from app.core.config import get_settings
from app.memory.redis_client import get_redis

logger = logging.getLogger(__name__)

# Redis Key 前缀（Python 端独立，不与 Java 冲突）
MEMORY_KEY_PREFIX = "ai:memory:"
MEMORY_KEY_SUFFIX = ":short_term"

# 摘要压缩 Prompt
SUMMARY_PROMPT = """请将以下法律对话片段压缩为结构化摘要，严格保留法律精确性：

对话内容：
{conversation_text}

请输出 JSON：
{{
  "核心诉求": "一句话",
  "已确认事实": [
    {{"事实": "...", "依据": "用户陈述/用户提供的文件/模型推断", "状态": "已确认/待核实"}}
  ],
  "已讨论法律要点": [
    {{"法条或原则": "...", "适用结论": "...", "是否存疑": true/false}}
  ],
  "待跟进事项": ["..."],
  "当事人特殊表述": "当事人使用的特定法律术语或特别强调的表述，原样保留"
}}

要求：
- 法律条文引用必须包含全称及条号，不得省略；
- 金额、日期、人名（可用化名）、地点等关键信息原样保留，不得改写；
- 如果某项无内容，返回空数组或空字符串。
只输出 JSON，无其他内容。"""


class ShortTermMemory:
    """短期记忆管理器"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key = f"{MEMORY_KEY_PREFIX}{session_id}{MEMORY_KEY_SUFFIX}"
        settings = get_settings()
        self.ttl_seconds = settings.MEMORY_SHORT_TERM_TTL_HOURS * 3600
        self.compress_threshold = settings.MEMORY_COMPRESS_THRESHOLD
        self._data: Optional[dict] = None

    def _load(self) -> dict:
        """从 Redis 加载短期记忆"""
        if self._data is not None:
            return self._data
        try:
            r = get_redis()
            raw = r.get(self.key)
            if raw:
                self._data = json.loads(raw)
            else:
                self._data = {
                    "summary": {},
                    "pending_rounds": [],
                    "round_count": 0,
                    "updated_at": None,
                }
        except Exception as e:
            logger.warning(f"[short_term] 加载失败: {e}")
            self._data = {
                "summary": {},
                "pending_rounds": [],
                "round_count": 0,
                "updated_at": None,
            }
        return self._data

    def _save(self):
        """保存短期记忆到 Redis"""
        try:
            r = get_redis()
            self._data["updated_at"] = datetime.now().isoformat()
            r.set(self.key, json.dumps(self._data, ensure_ascii=False))
            r.expire(self.key, self.ttl_seconds)
            logger.debug(f"[short_term] 保存成功: {self.key}")
        except Exception as e:
            logger.warning(f"[short_term] 保存失败: {e}")

    def get_summary(self) -> dict:
        """获取当前摘要"""
        return self._load().get("summary", {})

    def get_round_count(self) -> int:
        """获取总轮次"""
        return self._load().get("round_count", 0)

    def get_pending_rounds(self) -> list:
        """获取尚未压缩的原始轮次"""
        return self._data.get("pending_rounds", [])

    def add_round(self, question: str, answer: str):
        """
        添加一轮对话到短期记忆。
        不立即压缩，先缓存到 pending_rounds，累积到阈值时批量压缩。
        """
        data = self._load()
        data["pending_rounds"].append({"q": question, "a": answer})
        data["round_count"] = data.get("round_count", 0) + 1
        self._save()

        pending_count = len(data["pending_rounds"])
        logger.info(
            f"[short_term] 添加轮次: session={self.session_id}, "
            f"total={data['round_count']}, pending={pending_count}"
        )

        return pending_count >= self.compress_threshold

    async def compress_pending(self, llm=None) -> dict:
        """
        压缩 pending_rounds 为结构化摘要。
        调用方应在 add_round 返回 True 时调用此方法。
        """
        data = self._load()
        pending = data.get("pending_rounds", [])
        if not pending:
            return data.get("summary", {})

        # 格式化待压缩轮次
        conversation_text = _format_rounds_for_summary(pending)

        # 调用 LLM 生成摘要
        new_summary_chunk = await _call_llm_summary(conversation_text, llm)

        # 与现有摘要合并
        existing_summary = data.get("summary", {})
        merged = _merge_summaries(existing_summary, new_summary_chunk)

        # 更新状态
        data["summary"] = merged
        data["pending_rounds"] = []
        self._save()

        logger.info(
            f"[short_term] 压缩完成: session={self.session_id}, "
            f"compressed_rounds={len(pending)}"
        )
        return merged


def _format_rounds_for_summary(rounds: list) -> str:
    """将轮次列表格式化为摘要 Prompt 的输入"""
    lines = []
    for i, r in enumerate(rounds, 1):
        lines.append(f"【第{i}轮】")
        lines.append(f"用户：{r['q']}")
        # 截断过长回答，避免 LLM 输入过大
        answer = r['a'][:1000] + "..." if len(r['a']) > 1000 else r['a']
        lines.append(f"助手：{answer}")
    return "\n".join(lines)


async def _call_llm_summary(conversation_text: str, llm=None) -> dict:
    """调用 LLM 生成结构化摘要"""
    from langchain_community.chat_models import ChatTongyi
    from app.core.config import get_settings

    settings = get_settings()

    # 使用小模型降低延迟和费用
    if llm is None:
        llm = ChatTongyi(
            api_key=settings.DASHSCOPE_API_KEY,
            model="qwen-turbo",
        )

    prompt = SUMMARY_PROMPT.format(conversation_text=conversation_text)

    try:
        import asyncio
        result = await asyncio.to_thread(llm.invoke, prompt)
        content = result.content.strip()

        # 提取 JSON（处理可能的 markdown 包裹）
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content)
    except Exception as e:
        logger.error(f"[short_term] LLM 摘要生成失败: {e}")
        return {
            "核心诉求": "",
            "已确认事实": [],
            "已讨论法律要点": [],
            "待跟进事项": [],
            "当事人特殊表述": "",
        }


def _merge_summaries(existing: dict, new_chunk: dict) -> dict:
    """
    增量合并摘要：将新压缩结果合并到现有摘要。
    控制总大小不超过 MEMORY_SHORT_TERM_MAX_TOKENS。
    """
    if not existing:
        return new_chunk

    merged = {
        "核心诉求": new_chunk.get("核心诉求") or existing.get("核心诉求", ""),
        "已确认事实": _merge_facts(
            existing.get("已确认事实", []),
            new_chunk.get("已确认事实", [])
        ),
        "已讨论法律要点": _merge_law_points(
            existing.get("已讨论法律要点", []),
            new_chunk.get("已讨论法律要点", [])
        ),
        "待跟进事项": _deduplicate_list(
            existing.get("待跟进事项", []) + new_chunk.get("待跟进事项", [])
        ),
        "当事人特殊表述": _merge_special_terms(
            existing.get("当事人特殊表述", ""),
            new_chunk.get("当事人特殊表述", "")
        ),
    }

    # 大小控制：限制事实和法律要点数量
    if len(merged["已确认事实"]) > 5:
        merged["已确认事实"] = merged["已确认事实"][-5:]
    if len(merged["已讨论法律要点"]) > 4:
        merged["已讨论法律要点"] = merged["已讨论法律要点"][-4:]
    if len(merged["待跟进事项"]) > 3:
        merged["待跟进事项"] = merged["待跟进事项"][-3:]

    return merged


def _normalize_key(text: str) -> str:
    """标准化文本用于去重：去除标点、空白，统一大小写"""
    import re
    text = re.sub(r'[，。、；：“”‘’（）《》\s.,;:!?\-\(\)\[\]\{\}]', '', text)
    return text.lower()


def _merge_facts(old_facts: list, new_facts: list) -> list:
    """合并事实列表，去重（基于标准化后的全文）"""
    seen = set()
    merged = []

    for fact in new_facts + old_facts:
        key = _normalize_key(fact.get("事实", ""))
        if key and key not in seen:
            seen.add(key)
            merged.append(fact)

    return merged


def _merge_law_points(old_points: list, new_points: list) -> list:
    """合并法律要点，去重（基于标准化后的法条名称）"""
    seen = set()
    merged = []

    for point in new_points + old_points:
        key = _normalize_key(point.get("法条或原则", ""))
        if key and key not in seen:
            seen.add(key)
            merged.append(point)

    return merged


def _deduplicate_list(items: list) -> list:
    """简单列表去重，保持顺序"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _merge_special_terms(old: str, new: str) -> str:
    """合并当事人特殊表述"""
    if not old:
        return new
    if not new:
        return old
    if new in old:
        return old
    return f"{old}；{new}"
