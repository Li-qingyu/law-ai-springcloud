"""
全链路测试：向量检索 vs 混合检索效果对比

测试场景：
1. 精确法条查询（如"劳动合同法第47条"）— 混合检索应优于向量
2. 语义模糊查询（如"公司辞退要赔钱吗"）— 两者应接近
3. 多关键词查询（如"租赁合同押金返还 承租人保管义务"）— 混合检索应更精准

使用方式:
    cd python-ai-service
    python scripts/test_hybrid_vs_vector.py
"""

import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymilvus import connections
from app.core.config import get_settings
from app.repositories.milvus_client import search_by_text, hybrid_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TEST_QUERIES = [
    # (查询, 集合, 说明)
    ("劳动合同法第47条", "law_articles", "精确法条编号查询"),
    ("租赁合同押金返还 承租人保管义务", "law_articles", "多关键词精确查询"),
    ("公司辞退要赔钱吗", "law_articles", "口语化语义查询"),
    ("交通事故对方全责赔偿项目", "law_cases", "案例关键词查询"),
    ("借钱不还怎么办", "law_articles", "口语化简短查询"),
    ("买卖不破租赁", "law_articles", "法律术语精确查询"),
]


def run_comparison():
    settings = get_settings()
    collections = [
        settings.MILVUS_COLLECTION_ARTICLES,
        settings.MILVUS_COLLECTION_CASES,
        settings.MILVUS_COLLECTION_HISTORY,
    ]

    print("=" * 80)
    print("向量检索 vs 混合检索 效果对比测试")
    print("=" * 80)

    for query, collection, desc in TEST_QUERIES:
        print(f"\n{'─' * 80}")
        print(f"查询: {query}")
        print(f"说明: {desc}")
        print(f"集合: {collection}")
        print(f"{'─' * 80}")

        # 向量检索
        t1 = time.time()
        vector_results = search_by_text(collection, query, top_k=5, min_score=0.3)
        vector_time = int((time.time() - t1) * 1000)

        # 混合检索（RRF 分数范围不同于余弦相似度，min_score=0 展示全部结果）
        t2 = time.time()
        hybrid_results = hybrid_search(collection, query, top_k=5, min_score=0)
        hybrid_time = int((time.time() - t2) * 1000)

        print(f"\n  [向量检索] 耗时 {vector_time}ms, 返回 {len(vector_results)} 条:")
        for i, r in enumerate(vector_results):
            score = r.get("score", 0)
            sid = r.get("source_id", "N/A")
            content = str(r.get("content_json") or "")[:80]
            print(f"    {i+1}. score={score:.4f}  source_id={sid}  {content}...")

        print(f"\n  [混合检索] 耗时 {hybrid_time}ms, 返回 {len(hybrid_results)} 条:")
        for i, r in enumerate(hybrid_results):
            score = r.get("score", 0)
            sid = r.get("source_id", "N/A")
            content = str(r.get("content_json") or "")[:80]
            print(f"    {i+1}. score={score:.4f}  source_id={sid}  {content}...")

        # 对比分析
        vector_ids = {r.get("source_id") for r in vector_results}
        hybrid_ids = {r.get("source_id") for r in hybrid_results}
        common = vector_ids & hybrid_ids
        only_vector = vector_ids - hybrid_ids
        only_hybrid = hybrid_ids - vector_ids

        print(f"\n  [对比] 共同: {len(common)}条, 仅向量: {len(only_vector)}条, 仅混合: {len(only_hybrid)}条")
        if only_hybrid:
            print(f"    混合独有 source_id: {only_hybrid}")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    connections.connect(
        alias="law-ai",
        host=settings.MILVUS_HOST if (settings := get_settings()) else "localhost",
        port=settings.MILVUS_PORT,
        db_name=settings.MILVUS_DATABASE_NAME,
    )
    logger.info(f"已连接 Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    run_comparison()
