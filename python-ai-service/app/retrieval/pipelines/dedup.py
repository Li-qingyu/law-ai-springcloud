"""去重处理器"""
from typing import List, Dict
from app.retrieval.pipelines.base import PipelineStep


class DedupStep(PipelineStep):
    """基于 id 去重，保留分数更高的条目"""

    def process(self, query: str, results: List[Dict]) -> List[Dict]:
        seen = {}
        for item in results:
            item_id = item.get("id")
            if item_id not in seen or item.get("score", 0) > seen[item_id].get("score", 0):
                seen[item_id] = item
        return list(seen.values())
