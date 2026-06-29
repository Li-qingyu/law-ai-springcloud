"""
工具模块
提供LangChain搜索工具
"""
from app.tools.base_search_tool import BaseSearchTool, SearchInput
from app.tools.law_article_tool import LawArticleSearchTool
from app.tools.law_case_tool import LawCaseSearchTool
from app.tools.consult_history_tool import ConsultHistorySearchTool
from app.tools.file_management_tool import FileManagementTool


def create_search_tools():
    """创建所有搜索工具实例"""
    return [
        LawArticleSearchTool(),
        LawCaseSearchTool(),
        ConsultHistorySearchTool()
    ]


__all__ = [
    "BaseSearchTool",
    "SearchInput",
    "LawArticleSearchTool",
    "LawCaseSearchTool",
    "ConsultHistorySearchTool",
    "FileManagementTool",
    "create_search_tools"
]
