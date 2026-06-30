"""
数据管理Agent
处理专利数据、公司数据、诉讼数据和法律数据的管理操作
"""
from typing import Annotated, Any, Dict, Optional
from typing_extensions import TypedDict
import operator
import logging
from langgraph.graph import StateGraph, END
from app.tools.adminTool.data_management_tool import DataManagementTool
from app.services.admin_agent_service.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

class DataManagementState(TypedDict):
    """数据管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]

def create_execute_node(log_service: Optional[AdminLogService] = None):
    """创建执行节点，支持依赖注入"""
    def execute_data_management(state: DataManagementState) -> Dict[str, Any]:
        """执行数据管理任务"""
        logger.info(f"执行数据管理任务: {state['query']}")

        tool = DataManagementTool()

        # 使用注入的日志服务或创建新实例
        nonlocal log_service
        if log_service is None:
            log_service = AdminLogService()

        try:
            result = tool._run(state["query"])
        except Exception as e:
            logger.error(f"数据管理任务执行异常: {e}")
            log_service.update_log(state["log_id"], {
                "agent_type": "data_management",
                "action": "execute",
                "status": "failed",
                "error": str(e)
            })
            return {"result": f"数据管理任务执行失败: {str(e)}"}

        # 检查是否为无法识别的查询（工具返回了回退提示消息）
        status = "success"
        if result.startswith("请指定数据类型"):
            status = "failed"

        log_service.update_log(state["log_id"], {
            "agent_type": "data_management",
            "action": "execute",
            "status": status,
            "result": result
        })

        return {"result": result}
    return execute_data_management

def create_data_management_agent(log_service: Optional[AdminLogService] = None):
    """创建数据管理Agent"""
    workflow = StateGraph(DataManagementState)

    # 添加节点
    workflow.add_node("execute", create_execute_node(log_service))

    # 设置入口
    workflow.set_entry_point("execute")

    # 添加结束边
    workflow.add_edge("execute", END)

    return workflow.compile()
