"""
权限管理Agent
处理用户管理、角色管理和权限管理操作
"""
from typing import TypedDict, Annotated, Any, Dict, Optional
import operator
import logging
from langgraph.graph import StateGraph, END
from app.tools.adminTool.permission_tool import PermissionTool
from app.services.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

class PermissionManagementState(TypedDict):
    """权限管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]

def create_execute_node(log_service: Optional[AdminLogService] = None):
    """创建执行节点，支持依赖注入"""
    def execute_permission_management(state: PermissionManagementState) -> Dict[str, Any]:
        """执行权限管理任务"""
        logger.info(f"执行权限管理任务: {state['query']}")

        tool = PermissionTool()

        # 使用注入的日志服务或创建新实例
        nonlocal log_service
        if log_service is None:
            log_service = AdminLogService()

        try:
            result = tool._run(state["query"])
        except Exception as e:
            logger.error(f"权限管理任务执行异常: {e}")
            log_service.update_log(state["log_id"], {
                "agent_type": "permission_management",
                "action": "execute",
                "status": "failed",
                "error": str(e)
            })
            return {"result": f"权限管理任务执行失败: {str(e)}"}

        # 检查是否为无法识别的查询（工具返回了回退提示消息）
        status = "success"
        if result.startswith("请指定操作类型"):
            status = "failed"

        log_service.update_log(state["log_id"], {
            "agent_type": "permission_management",
            "action": "execute",
            "status": status,
            "result": result
        })

        return {"result": result}
    return execute_permission_management

def create_permission_management_agent(log_service: Optional[AdminLogService] = None):
    """创建权限管理Agent"""
    workflow = StateGraph(PermissionManagementState)

    # 添加节点
    workflow.add_node("execute", create_execute_node(log_service))

    # 设置入口
    workflow.set_entry_point("execute")

    # 添加结束边
    workflow.add_edge("execute", END)

    return workflow.compile()
