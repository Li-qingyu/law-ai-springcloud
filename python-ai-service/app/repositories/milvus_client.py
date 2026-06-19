from app.utils.embedding import get_embedding_model, embed_text, embed_texts
from pymilvus import connections, Collection, AnnSearchRequest, RRFRanker
from app.core.config import get_settings
import logging
from typing import List

def init_milvus():
    settings = get_settings()
    connections.connect(
        alias="law-ai", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT,
        db_name=settings.MILVUS_DATABASE_NAME
    )
    logging.info(f"成功连接到milvus:{settings.MILVUS_HOST},{settings.MILVUS_PORT},{settings.MILVUS_DATABASE_NAME}")


def search_by_text(
        collection_name:str,query_text:str,
        top_k:int=None,filter_expr:str=None,
        output_fields:List[str]=None,
        min_score:float=None
)->List[dict]:
    """
        通过文本搜索相似数据

        Args:
            collection_name: 集合名称
            query_text: 查询文本
            top_k: 返回结果数量
            filter_expr: 过滤表达式
            output_fields: 输出字段列表
            min_score: 最低分数阈值，默认从配置读取 TOOL_SCORE_THRESHOLD

        Returns:
            过滤后的搜索结果列表
    """
    query_vector = embed_text(query_text)
    settings=get_settings()

    if top_k is None:
        top_k=settings.TOP_K_RESULTS
    if output_fields is None:
        output_fields=["source_id","content_json"]
    if min_score is None:
        min_score = settings.TOOL_SCORE_THRESHOLD
    collection=Collection(name=collection_name,using="law-ai")
    collection.load()
    result=collection.search(
        data=[query_vector],
        anns_field="vector",
        limit=top_k,
        param={"metric_type": settings.MILVUS_METRIC_TYPE, "params": {"nprobe": 16}},
        expr=filter_expr,
        output_fields=output_fields
    )
    search_result=[]
    for hits in result:
        for hit in hits:
            if hit.score >= min_score:
                search_result.append({
                    "id":hit.id,
                    "score":hit.score,
                    "type":collection_name,
                    "source_id":hit.entity.get("source_id"),
                    "content_json":hit.entity.get("content_json"),
                })
    logging.info(f"搜索结果数量:{len(search_result)}")
    return search_result


def hybrid_search(
        collection_name: str, query_text: str,
        top_k: int = None, min_score: float = None,
) -> List[dict]:
    """
    混合检索：Dense Vector + BM25 Sparse Vector，RRF 融合

    前提：集合已通过 migrate_hybrid_search.py 迁移，包含 bm25_text + sparse_vector 字段和 BM25 Function。
    BM25 Function 会自动从 bm25_text 字段生成 sparse_vector（jieba 中文分词），检索时只需传
    query_text 的稠密向量和原始文本，Milvus 内部完成 BM25 tokenize 和稀疏向量检索。

    Args:
        collection_name: 集合名称
        query_text: 查询文本
        top_k: 返回结果数量
        min_score: 最低分数阈值

    Returns:
        搜索结果列表
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.TOP_K_RESULTS
    if min_score is None:
        min_score = 0  # RRF 分数远小于余弦相似度，不应用高阈值

    # 生成稠密向量（语义检索用）
    dense_vector = embed_text(query_text)

    collection = Collection(name=collection_name, using="law-ai")
    collection.load()

    # Milvus hybrid_search API
    # Dense 路：向量相似度检索
    # Sparse 路：BM25 全文检索（sparse_vector 由 BM25 Function 从 content 自动生成）
    # 检索时 dense 传向量，sparse 传原始文本（Milvus 内部 tokenize）
    results = collection.hybrid_search(
        reqs=[
            AnnSearchRequest(
                data=[dense_vector],
                anns_field="vector",
                param={"metric_type": settings.MILVUS_METRIC_TYPE, "params": {"nprobe": 16}},
                limit=top_k,
            ),
            AnnSearchRequest(
                data=[query_text],          # BM25 Function 接收原始文本，内部自动 tokenize
                anns_field="sparse_vector",
                param={"metric_type": "BM25"},
                limit=top_k,
            ),
        ],
        rerank=RRFRanker(k=60),             # RRF 融合，k=60 为标准参数
        limit=top_k,
        output_fields=["source_id", "content_json"],
    )

    search_result = []
    for hits in results:
        for hit in hits:
            if hit.score >= min_score:
                search_result.append({
                    "id": hit.id,
                    "score": hit.score,
                    "type": collection_name,
                    "source_id": hit.entity.get("source_id"),
                    "content_json": hit.entity.get("content_json"),
                })
    logging.info(f"混合检索结果数量:{len(search_result)}")
    return search_result


if __name__ == '__main__':
    # 测试代码
    init_milvus()

    settings=get_settings()
    # 向量搜索测试
    text = "劳动合同"
    results = search_by_text(settings.MILVUS_COLLECTION_CASES , text, top_k=3)
    results1 =hybrid_search(settings.MILVUS_COLLECTION_CASES , text)
    print(f"\n查询: {text}")
    print(f"找到 {len(results)} 条结果:\n")
    for result in results:
        print(f"   分类: {result}")
        print(f"   相似度分数: {result['score']:.4f}")
        print()
