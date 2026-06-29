"""
工具模块
提供LangChain搜索工具和管理工具
"""
from app.tools.searchTool.base_search_tool import BaseSearchTool, SearchInput
from app.tools.searchTool.law_article_tool import LawArticleSearchTool
from app.tools.searchTool.law_case_tool import LawCaseSearchTool
from app.tools.searchTool.consult_history_tool import ConsultHistorySearchTool
from app.tools.adminTool.file_management_tool import FileManagementTool
from app.tools.adminTool.log_management_tool import LogManagementTool
from app.tools.adminTool.data_management_tool import DataManagementTool
from app.tools.adminTool.permission_tool import PermissionTool


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
    "LogManagementTool",
    "DataManagementTool",
    "PermissionTool",
    "create_search_tools"
]
