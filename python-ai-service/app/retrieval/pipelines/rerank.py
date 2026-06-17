"""Rerank 精排处理器 — 独立组件，可插入任意检索流程"""
from abc import ABC, abstractmethod
from typing import List, Dict
import json
import logging

from app.retrieval.pipelines.base import PipelineStep

logger = logging.getLogger(__name__)


def extract_text_from_content_json(content_json: dict) -> str:
    """
    从 content_json 中提取纯文本内容。
    支持三种数据格式：
    - 条文：article_title + content
    - 案例：title + content
    - AI对话：question + answer

    Args:
        content_json: JSON 字符串或纯文本

    Returns:
        提取的纯文本内容
    """
    if not content_json:
        return ""
    data = content_json.get("content_json")
    try:
        if not isinstance(data, dict):
            return ""

        if content_json.get("type") == "consult_history":
            question = data.get("question", "")
            answer = data.get("answer", "")
            return f"问题：{question} 回答：{answer}".strip()
        elif content_json.get("type") == "law_cases":
            title = data.get("title", "")
            content = data.get("content", "")
            return f"标题：{title}内容： {content}".strip()
        elif content_json.get("type") == "law_article":
            article_title=data.get("article_title", "")
            content = data.get("content", "")
            return f"条文标题： {article_title} 条文内容 {content}".strip()
        else :
            # 兜底：尝试提取常见文本字段
            return data.get("content", "") or data.get("text", "") or json.dumps(data, ensure_ascii=False)

    except (json.JSONDecodeError, TypeError):
        return str(data)


class BaseReranker(ABC):
    """精排器抽象基类"""

    @abstractmethod
    def rerank(self, query: str, candidates: List[Dict], top_n: int) -> List[Dict]:
        ...


class DashScopeReranker(BaseReranker):
    """DashScope gte-rerank-v2 精排实现"""

    def __init__(self, api_key: str, model: str = "gte-rerank-v2"):
        self.api_key = api_key
        self.model = model

    def rerank(self, query: str, candidates: List[Dict], top_n: int = 5) -> List[Dict]:
        if len(candidates) <= top_n:
            return candidates

        try:
            import dashscope
            # 提取纯文本内容，而非 JSON 字符串
            documents = [extract_text_from_content_json(c) for c in candidates]
            response = dashscope.TextReRank.call(
                model=self.model,
                query=query,
                documents=documents,
                top_n=top_n,
                return_documents=True,
            )
            return [candidates[r.index] for r in response.output.results]
        except Exception as e:
            logger.warning(f"[DashScopeReranker] Rerank 失败，降级返回前 {top_n} 条: {e}")
            return candidates[:top_n]


class NoopReranker(BaseReranker):
    """空精排（降级/关闭时使用）"""

    def rerank(self, query: str, candidates: List[Dict], top_n: int = 5) -> List[Dict]:
        return candidates[:top_n]


class RerankStep(PipelineStep):
    """将 Reranker 包装为管道步骤"""

    def __init__(self, reranker: BaseReranker, top_n: int = 5):
        self.reranker = reranker
        self.top_n = top_n

    def process(self, query: str, results: List[Dict]) -> List[Dict]:
        return self.reranker.rerank(query, results, top_n=self.top_n)

