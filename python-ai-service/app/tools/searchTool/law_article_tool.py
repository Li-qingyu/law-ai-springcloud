"""法律条文搜索工具"""

from app.tools.searchTool.base_search_tool import BaseSearchTool
from app.core.config import get_settings
from typing import Any


class LawArticleSearchTool(BaseSearchTool):
    """法律条文搜索工具"""

    name: str = "search_law_articles"
    description: str = (
         "搜索国家法律法规、司法解释及规范性文件。"
        "当用户询问法律依据、法条原文、法定权利义务或法律责任时使用此工具。"
        "输入必须是精炼的法律专业术语或法条关键词，严禁使用口语长句。"
        "示例：'买卖不破租赁'、'违法解除劳动合同赔偿金'、'举证责任倒置情形'"
    )
    collection_name: str = ""
    top_k: int = 5

    def __init__(self):
        settings = get_settings()
        super().__init__(
            collection_name=settings.MILVUS_COLLECTION_ARTICLES,
            top_k=settings.TOP_K_RESULTS
        )

    def _run(self, query: str) -> list[dict[str, Any]]:
        """执行咨询历史搜索"""
        return self._search_row(query)

    def _get_data_type_name(self) -> str:
        return "法律条文"


