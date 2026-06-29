"""
日志管理Agent
处理系统日志查询、用户操作日志查询、API调用日志查询和日志统计分析
"""
from typing import TypedDict, Annotated, Any, Dict, Optional
import operator
import logging
from langgraph.graph import StateGraph, END
from app.tools.log_management_tool import LogManagementTool
from app.services.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

class LogManagementState(TypedDict):
    """日志管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]

def create_execute_node(log_service: Optional[AdminLogService] = None):
    """创建执行节点，支持依赖注入"""
    def execute_log_management(state: LogManagementState) -> Dict[str, Any]:
        """执行日志管理任务"""
        logger.info(f"执行日志管理任务: {state['query']}")
        
        tool = LogManagementTool()
        result = tool._run(state["query"])
        
        # 使用注入的日志服务或创建新实例
        nonlocal log_service
        if log_service is None:
            log_service = AdminLogService()
        
        log_service.update_log(state["log_id"], {
            "agent_type": "log_management",
            "action": "execute",
            "status": "success",
            "result": result
        })
        
        return {"result": result}
    return execute_log_management

def create_log_management_agent(log_service: Optional[AdminLogService] = None):
    """创建日志管理Agent"""
    workflow = StateGraph(LogManagementState)
    
    # 添加节点
    workflow.add_node("execute", create_execute_node(log_service))
    
    # 设置入口
    workflow.set_entry_point("execute")
    
    # 添加结束边
    workflow.add_edge("execute", END)
    
    return workflow.compile()
