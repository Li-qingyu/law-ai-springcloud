"""
ACTION_TOOL_MAP:action(operation) → MCP 工具名 的静态桥接表
绑定期预筛选(tool_filter)的映射基础;覆盖必须与 DATA_TYPE_OPERATIONS 完全一致
(MCP 实施设计文档 §7 核对清单:映射漏一条 = 该权限位形同虚设)。
"""
from typing import Dict

LAW_ARTICLE: Dict[str, str] = {
    "query": "law_article_query",
    "create": "law_article_create",
    "update": "law_article_update",
    "delete": "law_article_delete",
    "import": "law_article_import",
    "sync": "law_article_sync",
    "sync_status": "law_article_sync_status",
    "count": "law_article_count",
}

LAW_CASE: Dict[str, str] = {
    "query": "law_case_query",
    "create": "law_case_create",
    "update": "law_case_update",
    "delete": "law_case_delete",
    "sync": "law_case_sync",
    "sync_status": "law_case_sync_status",
    "count": "law_case_count",
}

LAW_BOOK: Dict[str, str] = {
    "query": "law_book_query",
    "query_all": "law_book_query_all",
    "create": "law_book_create",
    "update": "law_book_update",
    "delete": "law_book_delete",
}

LAW_TYPE: Dict[str, str] = {
    "query": "law_type_query",
    "query_all": "law_type_query_all",
    "create": "law_type_create",
    "update": "law_type_update",
    "delete": "law_type_delete",
    "count": "law_type_count",
}

# data_type → {operation: tool_name}
ACTION_TOOL_MAPS: Dict[str, Dict[str, str]] = {
    "law_article": LAW_ARTICLE,
    "law_case": LAW_CASE,
    "law_book": LAW_BOOK,
    "law_type": LAW_TYPE,
}

# 反查表:tool_name → (data_type, operation);构建时生成,查 O(1)
TOOL_TO_ACTION: Dict[str, tuple] = {
    tool_name: (dt, op)
    for dt, m in ACTION_TOOL_MAPS.items()
    for op, tool_name in m.items()
}
