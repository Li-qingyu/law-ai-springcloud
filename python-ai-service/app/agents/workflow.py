"""
LangGraph 工作流编排
管理端Agent的核心工作流定义
"""
import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from app.agents.agents.admin_router_agent import (
    create_classify_node,
    create_check_permission_node,
    route_to_sub_agent,
)
from app.agents.state.AdminRouterState import AdminRouterState
from app.api.v1.admin import AdminRequest
from app.services.admin_agent_service.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)


def create_workflow(request: AdminRequest, log_service: Optional[AdminLogService] = None):
    """
    创建管理工作流

    流程：
    1. 意图分类 (classify_task)
    2. 权限检查 (check_permission)
    3. 路由到子Agent (file/data/log/permission)
    4. 结束

    Args:
        request: 管理请求
        log_service: 日志服务实例

    Returns:
        编译后的工作流
    """
    # 延迟导入子Agent，避免循环依赖
    from app.agents import (
        create_file_management_agent,
        create_log_management_agent,
        create_data_management_agent,
        create_permission_management_agent,
    )

    workflow = StateGraph(AdminRouterState)

    # 添加节点
    workflow.add_node("classify_task", create_classify_node(log_service))
    workflow.add_node("check_permission", create_check_permission_node(log_service))
    workflow.add_node("file_management", create_file_management_agent(log_service))
    workflow.add_node("log_management", create_log_management_agent(log_service))
    workflow.add_node("data_management", create_data_management_agent(log_service))
    workflow.add_node("permission_management", create_permission_management_agent(log_service))

    # 设置入口
    workflow.set_entry_point("classify_task")

    # 添加边：分类 -> 权限检查
    workflow.add_edge("classify_task", "check_permission")

    # 添加条件边：权限检查后路由到子Agent或结束
    workflow.add_conditional_edges(
        "check_permission",
        route_to_sub_agent,
        {
            "file_management": "file_management",
            "log_management": "log_management",
            "data_management": "data_management",
            "permission_management": "permission_management",
            END: END,
        },
    )

    # 所有子Agent执行完后结束
    workflow.add_edge("file_management", END)
    workflow.add_edge("log_management", END)
    workflow.add_edge("data_management", END)
    workflow.add_edge("permission_management", END)

    logger.info("管理工作流创建完成")

    return workflow.compile()
