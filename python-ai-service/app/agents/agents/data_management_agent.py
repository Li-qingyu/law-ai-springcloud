"""
数据管理Agent — LLM + Tools 模式
LLM 自主理解用户意图，决定调用哪个工具、传什么参数。
支持多轮工具调用（Agent ↔ Tools 循环），可处理需要多步推理的复杂请求。
"""
from typing import Annotated, Any, Dict, List, Optional, Literal
from typing_extensions import TypedDict
import operator
import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.tools.adminTool.data_management_tool import DataManagementTool
from app.services.admin_agent_service.admin_log_service import AdminLogService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个法律咨询管理后台的数据管理助手。你的职责是理解管理员的自然语言指令，调用合适的工具完成数据操作。

## 你能管理的数据类型
- law_article（法律条文）
- law_case（法律案例）
- law_book（法律书籍）
- law_type（法律类型）

## 你能执行的操作
- query: 查询（支持分页、条件筛选）
- query_all: 查询全部（仅 law_book、law_type 支持）
- create: 新增
- update: 修改（需要提供 id）
- delete: 删除（需要提供 id 或 ids）
- sync: 同步到向量库
- sync_status: 查询同步状态（需要 taskId）
- count: 统计数量
- import: 导入（仅 law_article 支持，需要 lawBookId）

## 数据关系
- law_article（条文）属于某本 law_book（书籍），通过 lawBookId 关联
- law_case（案例）可关联 law_type（类型），通过 typeId 关联

## 工作原则
1. 从用户的自然语言中提取 data_type、operation 和具体参数
2. 如果用户没有明确指定某些信息，使用合理默认值（如分页默认 page=1, pageSize=10）
3. 如果缺少必填参数且无法从上下文推断，向用户追问
4. 工具返回结果后，用简洁的中文总结结果

## 多步骤查询（重要）
当用户的请求涉及跨数据类型的信息时，你需要分多次工具调用完成：
- 例：用户说"查询民法典第485条"
  第一步：先查 law_book（书籍），找到"民法典"的 lawBookId
  第二步：再用 lawBookId 查 law_article（条文），筛选第485条
- 例：用户说"查看刑法类的案例"
  第一步：先查 law_type（类型），找到"刑法"的 typeId
  第二步：再用 typeId 查 law_case（案例）

不要跳步，每一步都从工具返回的结果中提取需要的 ID，再进行下一步查询。
"""

# 最大工具调用轮数，防止无限循环
MAX_TOOL_ROUNDS = 5


def _create_llm():
    """创建 Qwen LLM 实例"""
    settings = get_settings()
    return ChatTongyi(
        model=settings.OPENAI_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
    )


class DataManagementState(TypedDict):
    """数据管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]


def create_agent_node(log_service: Optional[AdminLogService] = None):
    """
    创建 LLM Agent 节点。
    每次被调用时，将系统提示 + 用户原始问题 + 历史工具消息一起发给 LLM，
    由 LLM 决定是继续调工具还是输出最终回复。
    """
    _log_service = log_service or AdminLogService()

    llm = _create_llm()
    tools = [DataManagementTool()]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: DataManagementState) -> Dict[str, Any]:
        """LLM 推理节点"""
        query = state["query"]
        log_id = state.get("log_id", "")

        logger.info(f"数据管理Agent推理中 (第 {len(state.get('messages', [])) // 2 + 1} 轮)")

        # 构建消息：系统提示 + 用户问题 + 历史工具交互
        messages: List[BaseMessage] = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]
        if state.get("messages"):
            messages.extend(state["messages"])

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            _log_service.update_log(log_id, {
                "agent_type": "data_management",
                "action": "llm_error",
                "status": "failed",
                "error": str(e),
            })
            return {
                "result": f"数据管理任务执行失败: {str(e)}",
                "messages": [],
            }

        # LLM 没有调用工具 → 最终回复
        if not response.tool_calls:
            content = response.content if hasattr(response, "content") else str(response)
            logger.info(f"LLM 最终回复: {content[:200]}")

            # 判断状态
            status = "success"
            if any(kw in content for kw in ["失败", "不支持", "缺少", "错误", "无法"]):
                status = "failed"

            _log_service.update_log(log_id, {
                "agent_type": "data_management",
                "action": "execute",
                "status": status,
                "result": content,
            })
            return {
                "result": content,
                "messages": [response],
            }

        # LLM 调用了工具 → 交给 ToolNode 执行
        logger.info(f"LLM 调用工具: {[tc['name'] for tc in response.tool_calls]}")
        return {
            "messages": [response],
        }

    return agent_node


def _should_continue(state: DataManagementState) -> Literal["tools", "end"]:
    """
    路由判断：
    - LLM 输出了工具调用 → 执行工具（循环回 agent）
    - LLM 直接回复（无工具调用）→ 结束
    - 超过最大轮数 → 结束（防止死循环）
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"

    # 检查轮数限制
    tool_rounds = sum(1 for m in messages if hasattr(m, "tool_calls") and m.tool_calls)
    if tool_rounds >= MAX_TOOL_ROUNDS:
        logger.warning(f"达到最大工具调用轮数 {MAX_TOOL_ROUNDS}，强制结束")
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def create_data_management_agent(log_service: Optional[AdminLogService] = None):
    """
    创建数据管理Agent — LLM + Tools 多轮循环模式

    流程：
    1. Agent 节点：LLM 理解用户意图，决定调用什么工具
    2. ToolNode：执行工具调用
    3. 回到 Agent：LLM 看到工具结果，决定继续调工具还是输出最终回复
    4. 循环直到 LLM 不再调用工具（或达到最大轮数）
    """
    tools = [DataManagementTool()]

    workflow = StateGraph(DataManagementState)

    # 添加节点
    workflow.add_node("agent", create_agent_node(log_service))
    workflow.add_node("tools", ToolNode(tools))

    # 设置入口
    workflow.set_entry_point("agent")

    # Agent → 有工具调用 → 执行工具；无工具调用 → 结束
    workflow.add_conditional_edges(
        "agent",
        _should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # 工具执行完 → 回到 Agent（LLM 看到结果后决定下一步）
    workflow.add_edge("tools", "agent")

    return workflow.compile()

