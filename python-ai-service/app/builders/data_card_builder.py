"""
数据卡片构建器
将Milvus搜索结果转换为前端数据卡片格式
"""
from typing import List, Dict, Any, Optional
import json
import logging


from app.models.response import (
    DataCard,
    LawArticleDataCard,
    LawCaseDataCard,
    ConsultHistoryDataCard
)

logger = logging.getLogger(__name__)

class DataCardBuilder:
    """
    将Milvus搜索结果转换为数据卡片
    """

    @staticmethod
    def build_law_article_data_card(result: Dict[str, Any]) -> Optional[DataCard]:
        """
        将Milvus搜索结果转换为法律条文数据卡片
        """
        try:
            content_json =result.get("content_json","{}")
            if isinstance(content_json, str):
                content_json = json.loads(content_json)
            return LawArticleDataCard(
                type="law_article",
                id=result.get("source_id",0),
                book_id=content_json.get("book_id"),
                article_title=content_json.get("article_title"),
                content=content_json.get("content"),
                relevance=min(max(result.get("score", 0.0), 0.0), 1.0),
                detail_url=None
            )
        except Exception as e:
            logger.error(f"构建法律条文卡片失败: {e}")
            return None

    @staticmethod
    def build_law_case_data_card(result: Dict[str, Any]) -> Optional[DataCard]:
        """
        将Milvus搜索结果转换为法律案例数据卡片
        """
        try:
            content_json =result.get("content_json","{}")
            if isinstance(content_json, str):
                content_json = json.loads(content_json)
            return LawCaseDataCard(
                type="law_case",
                id=result.get("source_id", 0),
                title=content_json.get("title", ""),
                type_id=content_json.get("type_id"),
                tags=content_json.get("tags"),
                content=content_json.get("summary", content_json.get("content", ""))[:200],
                judgment=content_json.get("judgment"),
                cover=content_json.get("cover"),
                relevance=min(max(result.get("score", 0.0), 0.0), 1.0),
                detail_url=None
            )
        except Exception as e:
            logger.error(f"构建法律案例卡片失败: {e}")
            return None

    @staticmethod
    def build_consult_history_data_card(result: Dict[str, Any]) -> Optional[DataCard]:
        """
        将Milvus搜索结果转换为咨询历史数据卡片
        """
        try:
            content_json =result.get("content_json","{}")
            if isinstance(content_json, str):
                content_json = json.loads(content_json)
            return ConsultHistoryDataCard(
                type="consult_history",
                id=result.get("source_id", 0),
                user_id=content_json.get("user_id"),
                session_id=content_json.get("session_id"),
                question=content_json.get("question", ""),
                answer=content_json.get("answer", "")[:300],
                relevance=min(max(result.get("score", 0.0), 0.0), 1.0),
                detail_url=None
            )
        except Exception as e:
            logger.error(f"构建咨询历史卡片失败: {e}")
            return None

    @classmethod
    def from_milvus_result(cls, results: List[Dict[str, Any]],card_type: str) -> List[DataCard]:
        """
        将Milvus搜索结果转换为数据卡片列表
        """
        cards=[]
        builder_map = {
            "law_articles": cls.build_law_article_data_card,
            "law_cases": cls.build_law_case_data_card,
            "consult_history": cls.build_consult_history_data_card
        }
        builder = builder_map.get(card_type)
        if not builder:
            logger.error(f"不支持的卡片类型: {card_type}")
            return []
        for result in results:
            card = builder(result)
            if card:
                cards.append(card)
        logger.info(f"转换完成，共找到 {len(cards)} 条数据卡片")
        return cards
