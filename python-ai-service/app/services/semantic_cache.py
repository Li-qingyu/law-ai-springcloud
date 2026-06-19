"""
语义缓存模块
对高频法律问题建立语义缓存，相似问题直接返回缓存结果
"""
import json
import logging
import time
from typing import Optional, Dict, Any, List

from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections, utility

from app.core.config import get_settings
from app.utils.embedding import embed_text

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 天


def init_cache_collection():
    """初始化语义缓存集合（如果不存在）。调用前需确保 Milvus 连接已建立。"""
    settings = get_settings()
    collection_name = settings.SEMANTIC_CACHE_COLLECTION
    alias = "law-ai"

    # 检查连接是否已建立
    try:
        connections.get_connection(alias)
    except Exception:
        from app.repositories.milvus_client import init_milvus
        init_milvus()

    # 检查集合是否已存在
    if utility.has_collection(collection_name, using=alias):
        logger.info(f"[semantic_cache] 集合 {collection_name} 已存在")
        return

    # 创建集合
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
        FieldSchema(name="content_json", dtype=DataType.JSON, max_length=8192),
        FieldSchema(name="created_at", dtype=DataType.INT64),
        FieldSchema(name="hit_count", dtype=DataType.INT64),
    ]
    schema = CollectionSchema(fields, description="语义缓存集合")
    collection = Collection(name=collection_name, schema=schema, using=alias)

    # 创建向量索引
    index_params = {
        "metric_type": settings.MILVUS_METRIC_TYPE,
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="vector", index_params=index_params)
    logger.info(f"[semantic_cache] 集合 {collection_name} 创建成功")


def _serialize_content(question: str, answer: str, data_cards: list) -> str:
    """将问答对序列化为 JSON 字符串"""
    return json.dumps({
        "question": question,
        "answer": answer,
        "data_cards": data_cards,
    }, ensure_ascii=False)


def _deserialize_content(content_json) -> dict:
    """将 JSON 字符串或 dict 反序列化为 dict"""
    if isinstance(content_json, dict):
        return content_json
    try:
        return json.loads(content_json)
    except (json.JSONDecodeError, TypeError):
        return {"question": "", "answer": "", "data_cards": []}


class SemanticCache:
    """语义缓存管理器"""

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.SEMANTIC_CACHE_ENABLED
        self.collection_name = settings.SEMANTIC_CACHE_COLLECTION
        self.threshold = settings.SEMANTIC_CACHE_THRESHOLD
        self.refresh_threshold = settings.SEMANTIC_CACHE_REFRESH_THRESHOLD

    def get(self, question: str) -> Optional[Dict[str, Any]]:
        """
        查询语义缓存。

        Returns:
            None: 未命中
            {"answer": str, "data_cards": list, "score": float, "need_refresh": bool}: 命中
        """
        if not self.enabled:
            return None

        try:
            query_vector = embed_text(question)
            collection = Collection(name=self.collection_name, using="law-ai")
            collection.load()

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                limit=1,
                param={"metric_type": "COSINE", "params": {"nprobe": 16}},
                output_fields=["content_json", "created_at", "hit_count"],
            )

            if not results or not results[0]:
                return None

            hit = results[0][0]
            score = hit.score

            if score < self.refresh_threshold:
                logger.info(f"[semantic_cache] 未命中 (score={score:.4f})")
                return None

            # 检查 TTL
            created_at = hit.entity.get("created_at", 0)
            if created_at and (time.time() - created_at) > CACHE_TTL_SECONDS:
                logger.info(f"[semantic_cache] 缓存已过期")
                return None

            # 解析 JSON 内容
            content = _deserialize_content(hit.entity.get("content_json", "{}"))

            # 更新命中次数（Milvus 不支持 update，用 delete + reinsert）
            try:
                old_hit_count = hit.entity.get("hit_count", 0)
                self._reinsert_with_hit_count(
                    hit_id=hit.id,
                    vector=query_vector,
                    content_json=hit.entity.get("content_json", "{}"),
                    created_at=created_at,
                    hit_count=old_hit_count + 1,
                )
            except Exception as e:
                logger.warning(f"[semantic_cache] 更新命中次数失败: {e}")

            need_refresh = score < self.threshold
            logger.info(f"[semantic_cache] 命中 (score={score:.4f}, need_refresh={need_refresh})")

            return {
                "answer": content.get("answer", ""),
                "data_cards": content.get("data_cards", []),
                "score": score,
                "need_refresh": need_refresh,
            }

        except Exception as e:
            logger.error(f"[semantic_cache] 查询失败: {e}")
            return None

    def set(self, question: str, answer: str, data_cards: list):
        """写入语义缓存"""
        if not self.enabled:
            return

        try:
            query_vector = embed_text(question)
            content_json = _serialize_content(question, answer, data_cards)

            collection = Collection(name=self.collection_name, using="law-ai")
            # 使用字典插入，字段名明确对应
            collection.insert([{
                "vector": query_vector,
                "content_json": content_json,
                "created_at": int(time.time()),
                "hit_count": 0,
            }])
            collection.flush()
            logger.info(f"[semantic_cache] 缓存写入成功: {question[:50]}")

        except Exception as e:
            logger.error(f"[semantic_cache] 写入失败: {e}")

    def _reinsert_with_hit_count(self, hit_id: int, vector: list,
                                  content_json: str, created_at: int, hit_count: int):
        """删除旧记录并以更新后的 hit_count 重新插入"""
        collection = Collection(name=self.collection_name, using="law-ai")
        collection.delete(f"id == {hit_id}")
        collection.insert([{
            "vector": vector,
            "content_json": content_json,
            "created_at": created_at,
            "hit_count": hit_count,
        }])

    def invalidate_by_ids(self, ids: list):
        """根据 ID 批量失效缓存"""
        if not ids:
            return
        try:
            collection = Collection(name=self.collection_name, using="law-ai")
            id_str = ", ".join(str(i) for i in ids)
            collection.delete(f"id in [{id_str}]")
            logger.info(f"[semantic_cache] 失效 {len(ids)} 条缓存")
        except Exception as e:
            logger.error(f"[semantic_cache] 失效失败: {e}")
