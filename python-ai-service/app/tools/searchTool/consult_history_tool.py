"""咨询历史搜索工具"""

from app.tools.searchTool.base_search_tool import BaseSearchTool
from app.core.config import get_settings
from typing import Any

class ConsultHistorySearchTool(BaseSearchTool):
    """咨询历史搜索工具"""

    name: str = "search_consult_history"
    description: str = (
        "搜索平台历史法律咨询记录及标准化解答。"
        "当用户问题属于高频常见咨询，或希望参考过往类似场景的处理建议时使用此工具。"
        "输入应概括用户的核心诉求和法律关系，去除无关的情绪化描述。"
        "示例：'试用期辞退赔偿标准'、'房东不退押金维权流程'、'工伤认定申请时效'"
    )
    collection_name: str = ""
    top_k: int = 5

    def __init__(self):
        settings = get_settings()
        super().__init__(
            collection_name=settings.MILVUS_COLLECTION_HISTORY,
            top_k=settings.TOP_K_RESULTS
        )

    def _run(self, query: str) -> list[dict[str, Any]]:
        """执行咨询历史搜索"""
        return self._search_row(query)

    def _get_data_type_name(self) -> str:
        return "历史咨询"