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
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

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
5. 如果工具调用返回了错误或失败信息，你可以自行评估该错误是否自己可以处理，还是需要用户确认，如果需要用户处理，你需要如实告知用户操作失败，不要编造成功结果，然后不在进行工具调用。
6. 【重要】执行 insert 操作时，如果用户提供信息不足直接先用户返回不足的信息，不要反复调用查询工具去获取信息。
7. 【重要】执行 update 操作时，必须先查询获取完整的原始记录，然后将用户要修改的字段和原始记录的其他字段一起传入，如果在2次查询工具没有获取完整记录的话直接将不足信息交给用户进行补充而不是反复调用工具，确保必填字段不为 null。例如更新法律条文的 content 时，也要传入原始的 articleTitle、lawBookId 等字段。
8. 【重要】执行 delete 操作时，必须先查询获取要删除的记录，确认是否存在（每个删除记录查询工具调用次数不超过2次），如果用户想要删除多条记录且有记录不存在则只删除存在的记录。查询到记录后直接调用删除工具（不要用文字询问用户确认），系统会自动处理确认流程。
9. 【重要】如果工具返回的错误信息中包含"系统内部错误"、"字段值过长"、"必填字段不能为空"等具体错误原因，你应该：
   - 如果错误原因是参数格式问题（如字段超长、缺少必填字段），请根据错误提示调整参数后重新调用，不要重复使用相同的参数
   - 如果错误原因是数据已存在，请告知用户数据已存在，不要重复调用，告诉用户具体错误信息直接返回即可
   - 如果错误原因是系统内部错误且无法自行修复，请如实告知用户操作失败的具体原因，不要继续重试
## 多步骤查询（重要）
当用户的请求涉及跨数据类型的信息时，你需要分多次工具调用完成：
- 例：用户说"查询民法典第485条"
  第一步：先查 law_book（书籍），找到"民法典"的 lawBookId
  第二步：再用 lawBookId 查 law_article（条文），筛选第485条
- 例：用户说"查看刑法类的案例"
  第一步：先查 law_type（类型），找到"刑法"的 typeId
  第二步：再用 typeId 查 law_case（案例）
- 例：用户说"删除中华人民共和国劳动合同法的第四十九条，第四百二十条"
  第一步：先查 law_book（书籍），找到"中华人民共和国劳动合同法"的 lawBookId
  第二步：再用 lawBookId 查 law_article（条文），筛选第四十九条和第四百二十条（四十九条如果不存在则跳过查询四百二十条，而不是反复查询）
  第三步：直接调用删除工具，传入查到的 ID 列表，不要用文字询问用户确认
不要跳步，每一步都从工具返回的结果中提取需要的 ID，再进行下一步查询。
"""
# 最大工具调用轮数，防止无限循环，
MAX_TOOL_ROUNDS = 7


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


def _has_pending_delete(state: DataManagementState) -> bool:
    """检查是否有待执行的删除操作"""
    messages = state.get("messages", [])
    if not messages:
        return False
    last_message = messages[-1]
    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        return False
    return any(
        tc["name"] == "data_management" and tc["args"].get("operation") == "delete"
        for tc in last_message.tool_calls
    )


def _should_continue(state: DataManagementState) -> Literal["tools", "human_review", "end"]:
    """
    路由判断：
    - LLM 输出了删除工具调用 → 人工审查
    - LLM 输出了其他工具调用 → 执行工具
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
        # 删除操作需要人工确认
        if _has_pending_delete(state):
            return "human_review"
        return "tools"
    return "end"


def _human_review_node(state: DataManagementState):
    """
    人类审查节点 — 删除操作前的确认。
    interrupt() 暂停图执行，等待外部传入 Command(resume=...) 恢复。
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    # 提取所有待执行的删除调用
    delete_calls = [
        tc for tc in last_message.tool_calls
        if tc["name"] == "data_management" and tc["args"].get("operation") == "delete"
    ]

    # 构建可读的删除信息
    details = []
    for tc in delete_calls:
        args = tc["args"]
        details.append(f"数据类型: {args.get('data_type')}, 参数: {args.get('params')}")
    detail_text = "\n".join(details)

    # interrupt 暂停，返回值是外部 Command(resume=...) 传入的内容
    user_response = interrupt({
        "question": f"即将执行以下删除操作，请确认：\n{detail_text}\n\n输入 yes 确认，no 取消：",
        "pending_tool_calls": delete_calls,
    })

    # 用户确认 → 让 tools 节点执行（AI message 已在 state 中）
    if isinstance(user_response, str) and user_response.lower().strip() in ("yes", "y", "确认", "是"):
        logger.info("用户确认删除，继续执行")
        return {}

    # 用户拒绝 → 结束
    logger.info("用户取消删除操作")
    return Command(goto=END, update={
        "result": "删除操作已取消。",
        "messages": [AIMessage(content="删除操作已取消，未执行任何删除。")],
    })


def create_data_management_agent(log_service: Optional[AdminLogService] = None):
    """
    创建数据管理Agent — LLM + Tools 多轮循环模式

    流程：
    1. Agent 节点：LLM 理解用户意图，决定调用什么工具
    2. 删除操作 → human_review 节点 → interrupt 暂停等待用户确认
    3. 其他操作 → ToolNode 直接执行
    4. 回到 Agent：LLM 看到工具结果，决定继续调工具还是输出最终回复
    5. 循环直到 LLM 不再调用工具（或达到最大轮数）
    """
    tools = [DataManagementTool()]

    workflow = StateGraph(DataManagementState)

    # 添加节点
    workflow.add_node("agent", create_agent_node(log_service))
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("human_review", _human_review_node)

    # 设置入口
    workflow.set_entry_point("agent")

    # Agent → 路由判断
    workflow.add_conditional_edges(
        "agent",
        _should_continue,
        {
            "tools": "tools",
            "human_review": "human_review",
            "end": END,
        },
    )

    # human_review → 用户确认后执行工具
    workflow.add_edge("human_review", "tools")

    # 工具执行完 → 回到 Agent（LLM 看到结果后决定下一步）
    workflow.add_edge("tools", "agent")

    # checkpointer 是 interrupt/resume 的必要条件
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

