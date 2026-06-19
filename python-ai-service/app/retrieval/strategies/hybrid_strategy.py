"""混合检索策略 — 向量检索 + BM25，Milvus RRF 原生融合"""
from typing import List, Dict
from app.retrieval.strategies.base import BaseRetrievalStrategy
from app.repositories.milvus_client import hybrid_search


class HybridStrategy(BaseRetrievalStrategy):
    """混合检索策略：Milvus Hybrid Search（Dense + BM25 Sparse）

    BM25 Function 从 bm25_text 自动生成 sparse_vector，
    Milvus RRFRerank 在服务端完成融合排序，Python 侧无需手动 RRF。
    """

    def retrieve(self, query: str, collection_name: str,
                 top_k: int = 20, min_score: float = 0.5) -> List[Dict]:
        # RRF 分数范围远小于余弦相似度，不应用 min_score 过滤
        # 质量过滤由下游管道（reranker）处理
        return hybrid_search(
            collection_name=collection_name,
            query_text=query,
            top_k=top_k,
            min_score=0,
        )
