"""动态检索参数决策器 — 根据意图选择参数，与检索逻辑解耦"""
from dataclasses import dataclass


@dataclass
class RetrievalParams:
    recall_k: int = 20            # 召回数量
    final_k: int = 5              # 精排后返回数量
    min_score: float = 0.5        # 最低分数阈值
    use_multi_query: bool = False  # 是否启用多路改写
    use_hybrid: bool = False      # 是否启用混合检索（向量+BM25）


# 意图 → 参数映射表（可外部配置化）
INTENT_PARAMS = {
    "simple_query": RetrievalParams(recall_k=10, final_k=3, min_score=0.75, use_multi_query=False, use_hybrid=False),
    "consultation": RetrievalParams(recall_k=20, final_k=5, min_score=0.55, use_multi_query=True,  use_hybrid=True),
    "follow_up":    RetrievalParams(recall_k=15, final_k=5, min_score=0.65, use_multi_query=False, use_hybrid=False),
}


def get_params(intent: str) -> RetrievalParams:
    """根据意图获取检索参数，未知意图使用默认参数"""
    return INTENT_PARAMS.get(intent, RetrievalParams())
