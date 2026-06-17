"""多路 Query 改写策略"""
from typing import List, Dict
import logging
from app.retrieval.strategies.base import BaseRetrievalStrategy
from app.retrieval.strategies.vector_strategy import VectorStrategy

logger = logging.getLogger(__name__)

QUERY_REWRITE_PROMPT = """你是一个法律检索查询改写助手。
请将用户的问题改写为 3 个不同角度的法律检索查询词，要求：
1. 使用标准法律术语
2. 每个查询侧重不同的法律关系
3. 简洁明了，适合向量检索

用户问题：{question}

请直接输出 3 个查询词，每行一个，不要编号和解释。"""


class MultiQueryStrategy(BaseRetrievalStrategy):
    """多路 Query 改写策略：LLM 改写 + 并行检索 + 合并"""

    def __init__(self, llm, inner_strategy: BaseRetrievalStrategy = None):
        self.llm = llm
        self.inner = inner_strategy or VectorStrategy()

    def _rewrite(self, query: str) -> List[str]:
        """LLM 改写为多个查询"""
        try:
            prompt = QUERY_REWRITE_PROMPT.format(question=query)
            result = self.llm.invoke(prompt)
            queries = [q.strip() for q in result.content.strip().split("\n") if q.strip()]
            logger.info(f"[MultiQueryStrategy] 改写为 {len(queries)} 个查询: {queries}")
            return queries
        except Exception as e:
            logger.warning(f"[MultiQueryStrategy] 改写失败，使用原始查询: {e}")
            return []

    def retrieve(self, query: str, collection_name: str,
                 top_k: int = 20, min_score: float = 0.5) -> List[Dict]:
        # 原始查询 + 改写查询
        rewritten = self._rewrite(query)
        queries = [query] + rewritten

        all_results = []
        per_query_k = max(top_k // len(queries), 5)
        for q in queries:
            results = self.inner.retrieve(q, collection_name, top_k=per_query_k, min_score=min_score)
            all_results.extend(results)
            logger.info(f"[MultiQueryStrategy] 查询 '{q[:30]}...' 返回 {len(results)} 条")

        logger.info(f"[MultiQueryStrategy] 合并后共 {len(all_results)} 条候选")
        return all_results
