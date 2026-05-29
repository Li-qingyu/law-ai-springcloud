from app.utils.embedding import get_embedding_model, embed_text, embed_texts
from pymilvus import connections, Collection
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


if __name__ == '__main__':
    # 测试代码
    init_milvus()

    settings=get_settings()
    # 向量搜索测试
    text = "劳动合同"
    results = search_by_text(settings.MILVUS_COLLECTION_CASES , text, top_k=3)

    print(f"\n查询: {text}")
    print(f"找到 {len(results)} 条结果:\n")
    for result in results:
        print(f"   分类: {result}")
        print(f"   相似度分数: {result['score']:.4f}")
        print()
