"""
管理员路由Agent
接收请求，识别意图，路由到相应子Agent
"""
from typing import TypedDict, Annotated, Any, Dict, Optional
import operator
import logging
from langgraph.graph import StateGraph, END
from app.agents.file_management_agent import create_file_management_agent
from app.agents.log_management_agent import create_log_management_agent
from app.agents.data_management_agent import create_data_management_agent
from app.agents.permission_management_agent import create_permission_management_agent
from app.agents.review_agent import create_review_agent
from app.services.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

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

def create_classify_node(log_service: Optional[AdminLogService] = None):
    """创建分类节点，支持依赖注入"""
    def classify_admin_task(state: AdminRouterState) -> Dict[str, Any]:
        """分类管理任务"""
        query = state["query"]

        # 使用规则匹配进行意图识别
        # 注意：权限管理关键词优先级高于数据管理
        if any(keyword in query for keyword in ["上传", "文件", "导入"]):
            task_type = "file_management"
        elif any(keyword in query for keyword in ["日志", "查询", "统计"]):
            task_type = "log_management"
        elif any(keyword in query for keyword in ["用户", "权限", "角色"]):
            task_type = "permission_management"
        elif any(keyword in query for keyword in ["数据", "管理", "增删改查", "专利", "公司", "诉讼", "法律"]):
            task_type = "data_management"
        else:
            task_type = "unknown"

        logger.info(f"任务分类: {task_type}, 查询: {query[:50]}")

        # 使用注入的日志服务或创建新实例
        nonlocal log_service
        if log_service is None:
            log_service = AdminLogService()

        # 记录日志
        log_id = log_service.create_log({
            "task_type": task_type,
            "query": query,
            "user_id": state["user_id"],
            "user_role": state["user_role"]
        })

        return {"task_type": task_type, "log_id": log_id}

    return classify_admin_task

def create_check_permission_node(log_service: Optional[AdminLogService] = None):
    """创建权限检查节点，支持依赖注入"""
    def check_permission(state: AdminRouterState) -> Dict[str, Any]:
        """检查权限"""
        user_role = state.get("user_role", "")
        task_type = state.get("task_type", "")

        # 权限检查逻辑
        permission_map = {
            "super_admin": ["file_management", "log_management", "data_management", "permission_management"],
            "data_admin": ["file_management", "data_management"],
            "log_admin": ["log_management"],
            "user_admin": ["permission_management"]
        }

        allowed_tasks = permission_map.get(user_role, [])
        if task_type not in allowed_tasks:
            # 使用注入的日志服务或创建新实例
            nonlocal log_service
            if log_service is None:
                log_service = AdminLogService()

            # 记录权限错误日志
            log_service.update_log(state["log_id"], {
                "status": "permission_denied",
                "error": "权限不足，无法执行此操作"
            })
            return {"result": "权限不足，无法执行此操作"}

        return {}

    return check_permission

def route_to_sub_agent(state: AdminRouterState) -> str:
    """路由到子Agent"""
    if state.get("result"):
        return END

    task_type = state.get("task_type", "")
    if task_type == "file_management":
        return "file_management"
    elif task_type == "log_management":
        return "log_management"
    elif task_type == "data_management":
        return "data_management"
    elif task_type == "permission_management":
        return "permission_management"
    else:
        return END

def create_admin_router_agent(log_service: Optional[AdminLogService] = None):
    """创建管理员路由Agent"""
    workflow = StateGraph(AdminRouterState)

    # 添加节点
    workflow.add_node("classify_task", create_classify_node(log_service))
    workflow.add_node("check_permission", create_check_permission_node(log_service))
    workflow.add_node("file_management", create_file_management_agent(log_service))
    workflow.add_node("log_management", create_log_management_agent(log_service))
    workflow.add_node("data_management", create_data_management_agent(log_service))
    workflow.add_node("permission_management", create_permission_management_agent(log_service))
    workflow.add_node("review", create_review_agent(log_service=log_service))

    # 设置入口
    workflow.set_entry_point("classify_task")

    # 添加边
    workflow.add_edge("classify_task", "check_permission")

    # 添加条件边
    workflow.add_conditional_edges(
        "check_permission",
        route_to_sub_agent,
        {
            "file_management": "file_management",
            "log_management": "log_management",
            "data_management": "data_management",
            "permission_management": "permission_management",
            END: END
        }
    )

    # 所有子Agent执行完后都到审查Agent
    workflow.add_edge("file_management", "review")
    workflow.add_edge("log_management", "review")
    workflow.add_edge("data_management", "review")
    workflow.add_edge("permission_management", "review")

    # 审查Agent执行完后结束
    workflow.add_edge("review", END)

    return workflow.compile()
