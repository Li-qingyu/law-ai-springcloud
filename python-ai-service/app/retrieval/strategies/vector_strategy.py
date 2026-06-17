"""纯向量检索策略 — 从现有 milvus_client.search_by_text 抽离"""
from typing import List, Dict
from app.retrieval.strategies.base import BaseRetrievalStrategy
from app.repositories.milvus_client import search_by_text


class VectorStrategy(BaseRetrievalStrategy):
    """纯向量检索策略，复用现有的 search_by_text"""

    def retrieve(self, query: str, collection_name: str,
                 top_k: int = 20, min_score: float = 0.5) -> List[Dict]:
        return search_by_text(
            collection_name, query,
            top_k=top_k, min_score=min_score,
        )
