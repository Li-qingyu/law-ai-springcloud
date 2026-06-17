"""
并行检索模块
使用 asyncio 并行检索多个 Milvus 集合，减少工具调用延迟
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

from app.core.config import get_settings
from app.repositories.milvus_client import search_by_text

logger = logging.getLogger(__name__)


async def _async_search(collection_name: str, query_text: str,
                        top_k: int = None, min_score: float = None,
                        retriever=None) -> List[Dict[str, Any]]:
    """将同步的检索放入线程池执行"""
    loop = asyncio.get_event_loop()
    if retriever:
        return await loop.run_in_executor(
            None,
            lambda: retriever.retrieve(
                query_text, collection_name,
                recall_k=top_k * 4 if top_k else 20,
                final_k=top_k or 5,
            )
        )
    return await loop.run_in_executor(
        None,
        lambda: search_by_text(
            collection_name=collection_name,
            query_text=query_text,
            top_k=top_k,
            min_score=min_score,
        )
    )


async def parallel_search_all(query_text: str, top_k: int = 5,
                               retriever=None) -> Dict[str, List[Dict]]:
    """
    并行检索所有 Milvus 集合（法条、案例、历史）。

    Args:
        query_text: 查询文本
        top_k: 每个集合返回结果数
        retriever: 可选的 Retriever 实例

    Returns:
        {"law_articles": [...], "law_cases": [...], "consult_history": [...]}
    """
    settings = get_settings()
    collections = {
        "law_articles": settings.MILVUS_COLLECTION_ARTICLES,
        "law_cases": settings.MILVUS_COLLECTION_CASES,
        "consult_history": settings.MILVUS_COLLECTION_HISTORY,
    }

    tasks = {
        name: _async_search(col, query_text, top_k=top_k, retriever=retriever)
        for name, col in collections.items()
    }

    results = {}
    gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for (name, _), result in zip(tasks.items(), gathered):
        if isinstance(result, Exception):
            logger.error(f"[parallel_search] {name} 检索失败: {result}")
            results[name] = []
        else:
            results[name] = result
            logger.info(f"[parallel_search] {name} 返回 {len(result)} 条结果")

    return results


def parallel_search_all_sync(query_text: str, top_k: int = 5,
                              retriever=None) -> Dict[str, List[Dict]]:
    """
    同步版本的并行检索（用于非 async 上下文）。
    使用 ThreadPoolExecutor 并行执行。

    Args:
        query_text: 查询文本
        top_k: 每个集合返回结果数
        retriever: 可选的 Retriever 实例
    """
    from concurrent.futures import ThreadPoolExecutor

    settings = get_settings()
    collections = {
        "law_articles": settings.MILVUS_COLLECTION_ARTICLES,
        "law_cases": settings.MILVUS_COLLECTION_CASES,
        "consult_history": settings.MILVUS_COLLECTION_HISTORY,
    }

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        if retriever:
            futures = {
                name: executor.submit(
                    retriever.retrieve,
                    query_text, col,
                    top_k * 4, top_k,
                )
                for name, col in collections.items()
            }
        else:
            futures = {
                name: executor.submit(search_by_text, col, query_text, top_k)
                for name, col in collections.items()
            }
        for name, future in futures.items():
            try:
                results[name] = future.result()
                logger.info(f"[parallel_search] {name} 返回 {len(results[name])} 条结果")
            except Exception as e:
                logger.error(f"[parallel_search] {name} 检索失败: {e}")
                results[name] = []

    return results


def build_tool_context_from_results(results: Dict[str, List[Dict]]) -> str:
    """将并行检索结果构建为工具上下文文本，供流式生成使用"""
    context_parts = []
    tool_name_map = {
        "law_articles": "法律条文检索",
        "law_cases": "法律案例检索",
        "consult_history": "历史咨询检索",
    }

    for tool_name, items in results.items():
        if not items:
            continue
        display_name = tool_name_map.get(tool_name, tool_name)
        for i, item in enumerate(items):
            score = item.get("score", 0)
            content = item.get("content_json", "")
            context_parts.append(
                f"### {display_name} 结果 {i+1} [相关度: {score:.2f}]\n{content}"
            )

    return "\n\n".join(context_parts) if context_parts else "无工具检索结果"
