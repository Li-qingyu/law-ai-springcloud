"""
检索模块
提供策略模式 + 管道模式的检索架构
"""
from app.retrieval.retriever import Retriever
from app.retrieval.params import RetrievalParams, get_params

__all__ = ["Retriever", "RetrievalParams", "get_params"]
