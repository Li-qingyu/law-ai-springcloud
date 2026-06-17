"""管道基类 — 支持链式组合"""
from abc import ABC, abstractmethod
from typing import List, Dict


class PipelineStep(ABC):
    """管道步骤抽象基类"""

    @abstractmethod
    def process(self, query: str, results: List[Dict]) -> List[Dict]:
        ...


class RetrievalPipeline:
    """可组合的检索管道"""

    def __init__(self, steps: List[PipelineStep] = None):
        self.steps = steps or []

    def add_step(self, step: PipelineStep) -> "RetrievalPipeline":
        self.steps.append(step)
        return self

    def execute(self, query: str, results: List[Dict]) -> List[Dict]:
        for step in self.steps:
            results = step.process(query, results)
        return results
