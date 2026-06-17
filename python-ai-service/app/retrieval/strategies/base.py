"""检索策略抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseRetrievalStrategy(ABC):
    """检索策略接口 — 所有策略实现此接口"""

    @abstractmethod
    def retrieve(self, query: str, collection_name: str,
                 top_k: int = 20, min_score: float = 0.5) -> List[Dict]:
        ...
