"""法律案例搜索工具"""

from app.tools.searchTool.base_search_tool import BaseSearchTool
from app.core.config import get_settings
from typing import Any


class LawCaseSearchTool(BaseSearchTool):
    """法律案例搜索工具"""

    name: str = "search_law_cases"
    description: str = (
        "搜索法院裁判文书、典型司法判例及裁判要旨。"
        "当用户需要了解类似案件的判决结果、法院裁量尺度或胜诉可能性时使用此工具。"
        "输入应包含案件类型和核心争议事实，转化为简练的检索词。"
        "示例：'房屋租赁 提前解约 违约金'、'劳动争议 未签劳动合同 双倍工资'"
    )
    collection_name: str = ""
    top_k: int = 5

    def __init__(self):
        settings = get_settings()
        super().__init__(
            collection_name=settings.MILVUS_COLLECTION_CASES,
            top_k=settings.TOP_K_RESULTS
        )

    def _run(self, query: str) -> list[dict[str, Any]]:
        """执行咨询历史搜索"""
        return self._search_row(query)

    def _get_data_type_name(self) -> str:
        return "法律案例"