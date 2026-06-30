import operator
from typing import Annotated, TypedDict, Optional


class AdminRouterState(TypedDict):
    """管理员路由Agent状态"""

    # 输入
    query: str                       # 用户自然语言查询
    user_id: int                     # 用户ID
    user_role: str                   # 用户角色 (super_admin / admin)
    session_id: str                  # 会话ID
    task_params: dict                # 任务参数

    # 中间状态
    intent: str                      # 识别的意图
    confidence: float                # 意图置信度
    task_type: str                   # 任务类型（路由目标）
    task_params_parsed: dict         # 解析后的任务参数
    log_id: str                      # 日志ID
    messages: Annotated[list, operator.add]  # 对话消息

    # 输出
    result: str                      # 执行结果
    status: str                      # 执行状态 (running/success/failed/permission_denied)
    error: str                       # 错误信息