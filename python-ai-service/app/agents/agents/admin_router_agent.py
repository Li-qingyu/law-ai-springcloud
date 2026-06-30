"""
管理员路由Agent
接收请求，识别意图，路由到相应子Agent
"""
import logging
from typing import Any, Dict, Optional

from langgraph.graph import END

from app.agents.state.AdminRouterState import AdminRouterState
from app.services.admin_agent_service.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)


def create_classify_node(log_service: Optional[AdminLogService] = None,):
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

