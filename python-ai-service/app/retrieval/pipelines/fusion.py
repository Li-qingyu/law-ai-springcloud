"""RRF 融合器 — 合并多路检索结果（用于 Python 侧手动融合场景）"""
from typing import List, Dict


def reciprocal_rank_fusion(
    result_lists: List[List[Dict]],
    k: int = 60
) -> List[Dict]:
    """
    Reciprocal Rank Fusion (RRF)
    score = Σ 1/(k + rank_i)，rank 从 0 开始

    Args:
        result_lists: 多路检索结果列表，如 [vector_results, bm25_results]
        k: 平滑常数，默认 60
    Returns:
        按 RRF 分数降序排列的融合结果
    """
    scores: Dict[str, float] = {}
    id_to_item: Dict[str, Dict] = {}

    for results in result_lists:
        for rank, item in enumerate(results):
            item_id = item.get("id")
            if item_id is None:
                continue
            scores[item_id] = scores.get(item_id, 0) + 1.0 / (k + rank)
            id_to_item[item_id] = item

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    fused = []
    for item_id in sorted_ids:
        item = id_to_item[item_id].copy()
        item["rrf_score"] = scores[item_id]
        fused.append(item)

    return fused
