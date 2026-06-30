import operator
from typing import Annotated, TypedDict

class AdminRouterState(TypedDict):
    """管理员路由Agent状态"""
    query: str
    user_id: str
    user_role: str
    task_type: str
    task_params: dict
    result: str
    log_id: str
    messages: Annotated[list, operator.add]