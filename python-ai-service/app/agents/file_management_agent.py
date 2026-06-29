"""
文件管理Agent
处理文件上传、解析和批量导入操作
"""
from typing import TypedDict, Annotated, Any, Dict, Optional
import operator
import logging
from langgraph.graph import StateGraph, END
from app.tools.file_management_tool import FileManagementTool
from app.services.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

class FileManagementState(TypedDict):
    """文件管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]

def create_execute_node(log_service: Optional[AdminLogService] = None):
    """创建执行节点，支持依赖注入"""
    def execute_file_management(state: FileManagementState) -> Dict[str, Any]:
        """执行文件管理任务"""
        logger.info(f"执行文件管理任务: {state['query']}")
        
        tool = FileManagementTool()
        result = tool._run(state["query"])
        
        # 使用注入的日志服务或创建新实例
        nonlocal log_service
        if log_service is None:
            log_service = AdminLogService()
        
        log_service.update_log(state["log_id"], {
            "agent_type": "file_management",
            "action": "execute",
            "status": "success",
            "result": result
        })
        
        return {"result": result}
    return execute_file_management

def create_file_management_agent(log_service: Optional[AdminLogService] = None):
    """创建文件管理Agent"""
    workflow = StateGraph(FileManagementState)
    
    # 添加节点
    workflow.add_node("execute", create_execute_node(log_service))
    
    # 设置入口
    workflow.set_entry_point("execute")
    
    # 添加结束边
    workflow.add_edge("execute", END)
    
    return workflow.compile()
