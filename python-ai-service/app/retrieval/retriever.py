"""统一检索入口 — 组装策略和管道，对外暴露简单接口"""
import logging
from typing import Dict, List
from app.retrieval.strategies.base import BaseRetrievalStrategy
from app.retrieval.pipelines.base import RetrievalPipeline

logger = logging.getLogger(__name__)


class Retriever:
    """
    统一检索器 — 组装层
    - 策略决定"怎么召回"
    - 管道决定"怎么处理召回结果"
    - 两者通过接口解耦，可独立替换
    """

    def __init__(self, strategy: BaseRetrievalStrategy, pipeline: RetrievalPipeline = None):
        self.strategy = strategy
        self.pipeline = pipeline

    def retrieve(self, query: str, collection_name: str,
                 recall_k: int = 20, final_k: int = 5, min_score: float = 0.5) -> List[Dict]:
        # 1. 策略召回
        candidates = self.strategy.retrieve(query, collection_name, top_k=recall_k, min_score=min_score)
        logger.info(f"[Retriever] 召回 {len(candidates)} 条候选")

        # 2. 管道处理（去重 + 精排）
        if self.pipeline:
            candidates = self.pipeline.execute(query, candidates)

        result = candidates[:final_k]
        logger.info(f"[Retriever] 精排后返回 {len(result)} 条")
        return result
