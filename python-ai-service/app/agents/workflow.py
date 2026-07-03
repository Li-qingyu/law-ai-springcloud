"""
LangGraph 工作流编排
管理端Agent的核心工作流定义

架构说明：
- create_router_workflow() 仅做意图分类 + 权限检查 + 路由决策，不调用子Agent
- 子Agent 通过 get_sub_agent() 单例获取，由 API 层直接调用
- 这样设计的原因：LangGraph 的 interrupt/resume 需要 checkpointer 持久化，
  如果子Agent嵌套在父图中，interrupt 状态无法正确传递到 API 层。
"""
import logging
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from app.agents.agents.admin_router_agent import (
    create_classify_node,
    create_check_permission_node,
)
from app.agents.state.AdminRouterState import AdminRouterState
from app.services.admin_agent_service.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

# ─── 子Agent单例缓存 ───
# 每个子Agent编译后带独立的 MemorySaver checkpointer，
# 必须在进程生命周期内保持同一实例，否则 interrupt 状态丢失。
_sub_agent_cache: Dict[str, Any] = {}


def get_sub_agent(agent_type: str, log_service: Optional[AdminLogService] = None):
    """
    获取子Agent单例（带 checkpointer）。
    同一 agent_type 在进程内始终返回同一实例，确保 interrupt/resume 状态不丢失。
    """
    if agent_type in _sub_agent_cache:
        return _sub_agent_cache[agent_type]

    from app.agents import (
        create_file_management_agent,
        create_log_management_agent,
        create_data_management_agent,
        create_permission_management_agent,
    )

    factory_map = {
        "file_management": create_file_management_agent,
        "log_management": create_log_management_agent,
        "data_management": create_data_management_agent,
        "permission_management": create_permission_management_agent,
    }

    factory = factory_map.get(agent_type)
    if not factory:
        raise ValueError(f"未知的子Agent类型: {agent_type}")

    agent = factory(log_service)
    _sub_agent_cache[agent_type] = agent
    logger.info(f"创建子Agent单例: {agent_type}")
    return agent


def create_router_workflow(log_service: Optional[AdminLogService] = None):
    """
    创建路由工作流（仅分类 + 权限检查，不调用子Agent）。

    流程：
    1. 意图分类 (classify_task)
    2. 权限检查 (check_permission)
    3. 路由决策 → 返回 task_type / result / status

    Returns:
        编译后的工作流
    """
    workflow = StateGraph(AdminRouterState)

    workflow.add_node("classify_task", create_classify_node(log_service))
    workflow.add_node("check_permission", create_check_permission_node(log_service))

    workflow.set_entry_point("classify_task")
    workflow.add_edge("classify_task", "check_permission")

    # 权限检查后：如果已有结果（help/unknown/permission_denied）→ END，否则 → 路由决策节点
    def after_permission(state: AdminRouterState) -> str:
        if state.get("result"):
            return END
        return "route_decision"

    workflow.add_node("route_decision", lambda state: {
        "task_type": state.get("task_type", ""),
        "status": "routed",
    })
    workflow.add_conditional_edges("check_permission", after_permission, {
        "route_decision": "route_decision",
        END: END,
    })
    workflow.add_edge("route_decision", END)

    logger.info("路由工作流创建完成")
    return workflow.compile()


def invoke_sub_agent(agent_type: str, query: str, user_id: int,
                     log_id: str, thread_id: str,
                     router_context: Optional[Dict] = None,
                     log_service: Optional[AdminLogService] = None) -> Dict[str, Any]:
    """
    调用子Agent（支持 interrupt/resume）。

    Args:
        agent_type: 子Agent类型 (file_management / data_management / ...)
        query: 用户查询
        user_id: 用户ID
        log_id: 日志ID
        thread_id: 线程ID（checkpointer 用，同一会话必须保持一致）
        router_context: 路由阶段预解析的信息
        log_service: 日志服务

    Returns:
        {"result": "...", "status": "...", "is_pending_confirm": bool,
         "confirm_question": "...", "thread_id": "..."}
    """
    agent = get_sub_agent(agent_type, log_service)

    sub_input = {
        "query": query,
        "user_id": str(user_id),
        "log_id": log_id,
        "router_context": router_context or {},
    }
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"[{agent_type}] 调用子Agent，thread_id={thread_id}，router_context={router_context}")

    try:
        result = agent.invoke(sub_input, config=config)
    except Exception as e:
        logger.error(f"[{agent_type}] 子Agent执行失败: {e}")
        return {
            "result": f"任务执行失败: {str(e)}",
            "status": "failed",
            "is_pending_confirm": False,
        }

    # 检查是否被 interrupt 暂停
    is_pending = _check_interrupt(agent, thread_id)

    if is_pending:
        interrupt_info = _get_interrupt_info(agent, thread_id)
        interrupt_type = interrupt_info.get("type", "confirm")  # "clarify" 或 "confirm"
        logger.info(f"[{agent_type}] 子Agent等待用户响应，type={interrupt_type}，thread_id={thread_id}")
        return {
            "result": interrupt_info.get("question", "请确认操作"),
            "status": "pending_confirm",
            "is_pending_confirm": True,
            "confirm_type": interrupt_type,
            "confirm_question": interrupt_info.get("question", ""),
            "thread_id": thread_id,
        }

    return {
        "result": result.get("result", ""),
        "status": result.get("status", "success"),
        "is_pending_confirm": False,
        "thread_id": thread_id,
    }


def resume_sub_agent(agent_type: str, thread_id: str, user_answer: str,
                     log_service: Optional[AdminLogService] = None) -> Dict[str, Any]:
    """
    恢复被 interrupt 暂停的子Agent。

    Args:
        agent_type: 子Agent类型
        thread_id: 线程ID（必须与 interrupt 时一致）
        user_answer: 用户确认/取消的回答
        log_service: 日志服务

    Returns:
        {"result": "...", "status": "..."}
    """
    from langgraph.types import Command

    agent = get_sub_agent(agent_type, log_service)
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"[{agent_type}] 恢复子Agent，thread_id={thread_id}，answer={user_answer}")

    # 先检查当前状态
    try:
        current_state = agent.get_state(config)
        logger.info(f"[{agent_type}] 恢复前状态: next={current_state.next}, tasks={len(current_state.tasks) if current_state.tasks else 0}")
    except Exception as e:
        logger.warning(f"[{agent_type}] 获取恢复前状态失败: {e}")

    try:
        result = agent.invoke(Command(resume=user_answer), config=config)
        logger.info(f"[{agent_type}] 恢复执行完成，result_keys={list(result.keys()) if result else 'None'}")
    except Exception as e:
        logger.error(f"[{agent_type}] 恢复子Agent失败: {e}", exc_info=True)
        return {
            "result": f"恢复执行失败: {str(e)}",
            "status": "failed",
        }

    return {
        "result": result.get("result", ""),
        "status": result.get("status", "success"),
    }


def _check_interrupt(agent, thread_id: str) -> bool:
    """检查子Agent是否处于 interrupt 暂停状态"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent.get_state(config)
        has_next = bool(state.next)
        has_tasks_with_interrupts = False
        if state.tasks:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    has_tasks_with_interrupts = True
                    break
        is_pending = has_next or has_tasks_with_interrupts
        logger.info(f"中断检测 thread_id={thread_id}: next={state.next}, has_interrupts={has_tasks_with_interrupts}, is_pending={is_pending}")
        return is_pending
    except Exception as e:
        logger.warning(f"中断检测异常: {e}")
        return False


def _get_interrupt_info(agent, thread_id: str) -> Dict[str, Any]:
    """获取 interrupt 暂停时的信息（question、pending_tool_calls 等）"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent.get_state(config)
        logger.info(f"获取中断信息: next={state.next}, tasks_count={len(state.tasks) if state.tasks else 0}")

        if state.tasks:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    interrupt = task.interrupts[0]
                    logger.info(f"中断值类型: {type(interrupt.value)}")
                    if hasattr(interrupt, "value"):
                        if isinstance(interrupt.value, dict):
                            return interrupt.value
                        return {"question": str(interrupt.value)}
        return {}
    except Exception as e:
        logger.warning(f"获取 interrupt 信息失败: {e}")
        return {}
