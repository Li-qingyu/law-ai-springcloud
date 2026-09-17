"""
数据管理Agent — LLM + Tools 模式
LLM 自主理解用户意图，决定调用哪个工具、传什么参数。
支持多轮工具调用（Agent ↔ Tools 循环），可处理需要多步推理的复杂请求。
"""
from typing import Annotated, Any, Dict, List, Optional, Literal
from typing_extensions import TypedDict
import operator
import logging
import time
import hashlib
import json
import re

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

from app.services.admin_agent_service.admin_log_service import AdminLogService
from app.services.admin_agent_service.permission_checker import PermissionChecker
from app.services.mcp_service.action_tool_map import TOOL_TO_ACTION
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _run_async(coro):
    """构建期(非事件循环线程)执行 async 工具拉取的桥接助手"""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        # 已在事件循环内(如经 run_in_executor 的 worker 是新线程,通常无 loop);
        # 保底另开线程跑,避免 loop 冲突
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


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
6. 【重要】执行 query 操作时*如果查询两次结果均为0条就是没有*
7. 【重要】执行 insert 操作时，如果用户提供信息不足直接先用户返回不足的信息，不要反复调用查询工具去获取信息。
8. 【重要】执行 update 操作时，必须先查询获取完整的原始记录，然后将用户要修改的字段和原始记录的其他字段一起传入，如果在2次查询工具没有获取完整记录的话直接将不足信息交给用户进行补充而不是反复调用工具，确保必填字段不为 null。例如更新法律条文的 content 时，也要传入原始的 articleTitle、lawBookId 等字段。
9. 【重要】执行 delete 操作时，必须先查询获取要删除的记录，确认是否存在（每个删除记录查询工具调用次数不超过2次），如果用户想要删除多条记录且有记录不存在则只删除存在的记录。查询到记录后直接调用删除工具（不要用文字询问用户确认），系统会自动处理确认流程。
10. 当你向用户追问缺失参数后，如果用户确认了你建议的参数值，直接使用这些值调用工具。
11. 【重要】当你从用户补充的信息中获取到所有必要参数后，必须立即调用工具执行操作，不要只用文字说"现在执行"或"即将创建"等描述性语句。你的回复中如果包含工具调用意图，就必须同时包含 tool_calls。
12. 【重要】如果工具返回的错误信息中包含"系统内部错误"、"字段值过长"、"必填字段不能为空"等具体错误原因，你应该：
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

# 最大工具调用轮数，防止无限循环
MAX_TOOL_ROUNDS = 7
# 超时时间（秒）
TASK_TIMEOUT_SECONDS = 300


def _create_llm():
    """创建 Qwen LLM 实例"""
    settings = get_settings()
    return ChatTongyi(
        model=settings.OPENAI_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
    )


def _tool_signature(tool_call: dict) -> str:
    """生成工具调用签名，用于去重检测"""
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    args_str = json.dumps(args, sort_keys=True, ensure_ascii=False)
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
    return f"{name}:{args.get('operation', '')}:{args.get('data_type', '')}:{args_hash}"


class DataManagementState(TypedDict):
    """数据管理Agent状态"""
    query: str
    user_id: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]
    # 控制字段
    started_at: float                              # 任务开始时间戳
    max_rounds: int                                # 当前任务的轮数上限
    error_count: int                               # 累计连续错误次数
    last_tool_signature: str                       # 上一次工具调用签名
    partial_results: Annotated[list, operator.add] # 每轮工具返回的中间结果摘要
    is_waiting_review: bool                        # 是否正在等待人工审核
    call_history: Annotated[list, operator.add]    # 每轮工具调用签名记录
    router_context: dict                           # 路由阶段预解析的信息
    resume_value: str                              # interrupt 恢复时用户传入的值
    pending_clarification: str                     # 待用户补充的追问内容
    user_role: str                                 # 用户角色（guard 节点做操作级权限校验）
    token: str                                     # 用户 token（MCP 工具调用凭证,仅内存持有）


def create_init_node():
    """创建初始化节点，设置控制字段的初始值。
    interrupt 恢复时跳过初始化，保留已有状态。
    """
    def init_node(state: DataManagementState) -> Dict[str, Any]:
        # interrupt 恢复：已有 messages，不需要重新初始化
        if state.get("messages"):
            logger.info("数据管理Agent恢复（跳过初始化）")
            result = {
                "router_context": state.get("router_context", {}),
                "resume_value": state.get("resume_value", ""),
            }
            # 如果有待补充的追问，将用户的最新回答与追问关联
            pending = state.get("pending_clarification", "")
            if pending:
                messages = state.get("messages", [])
                # 找到最后一条 HumanMessage（用户的回答）
                last_human = ""
                for m in reversed(messages):
                    if isinstance(m, HumanMessage):
                        last_human = m.content
                        break
                if last_human:
                    logger.info(f"检测到待补充追问，用户回答: {last_human[:100]}")
                    result["resume_value"] = last_human
                    result["pending_clarification"] = ""  # 清除
            return result

        logger.info("数据管理Agent初始化")
        return {
            "started_at": time.time(),
            "max_rounds": MAX_TOOL_ROUNDS,
            "error_count": 0,
            "last_tool_signature": "",
            "partial_results": [],
            "is_waiting_review": False,
            "call_history": [],
            "router_context": state.get("router_context", {}),
            "resume_value": "",
            "pending_clarification": "",
        }
    return init_node


# ─── 代码兜底：interrupt 恢复时直接重试工具调用 ───

_POSITIVE_ANSWERS = {"是", "yes", "y", "确认", "可以", "对", "好", "同意", "沿用", "使用", "行", "没问题"}

def _is_positive_answer(answer: str) -> bool:
    """判断用户回答是否为肯定答复"""
    normalized = answer.strip().lower()
    if normalized in _POSITIVE_ANSWERS:
        return True
    return any(kw in normalized for kw in ["可以", "确认", "沿用", "使用", "同意"])


def _extract_values_from_answer(answer: str) -> dict:
    """从用户回答中提取参数值"""
    values = {}
    # 提取日期
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', answer)
    if dates:
        # 根据上下文关键词分配
        if re.search(r'发布|publish', answer, re.IGNORECASE) and len(dates) >= 1:
            values["publishDate"] = dates[0]
        if re.search(r'生效|effective', answer, re.IGNORECASE):
            idx = 1 if "publishDate" in values and len(dates) >= 2 else 0
            values["effectiveDate"] = dates[min(idx, len(dates) - 1)]
        # 没有上下文关键词，按顺序分配
        if not values and len(dates) >= 1:
            values["publishDate"] = dates[0]
        if len(dates) >= 2 and "effectiveDate" not in values:
            values["effectiveDate"] = dates[1]
    return values


def _extract_suggested_values(question: str) -> dict:
    """
    从 LLM 追问文本中提取建议的参数值。
    例："发布日期（publishDate）：2020-12-25，生效日期（effectiveDate）：2021-02-28"
    → {"publishDate": "2020-12-25", "effectiveDate": "2021-02-28"}
    """
    values = {}

    # 匹配 yyyy-MM-dd 格式的日期
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', question)
    # 匹配参数名
    param_patterns = [
        (r'publishDate|发布日期', 'publishDate'),
        (r'effectiveDate|生效日期', 'effectiveDate'),
        (r'articleTitle|条文标题', 'articleTitle'),
        (r'bookTitle|书籍标题', 'bookTitle'),
    ]

    for pattern, param_name in param_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            # 找到参数名附近的值
            # 先尝试找紧跟的日期
            match = re.search(pattern + r'[^0-9]*(\d{4}-\d{2}-\d{2})', question, re.IGNORECASE)
            if match:
                values[param_name] = match.group(1)
            elif dates:
                # 没有明确关联，按顺序分配
                if param_name == 'publishDate' and len(dates) >= 1:
                    values[param_name] = dates[0]
                elif param_name == 'effectiveDate' and len(dates) >= 2:
                    values[param_name] = dates[1]
                elif param_name == 'effectiveDate' and len(dates) >= 1:
                    values[param_name] = dates[0]

    return values


def _find_last_failed_tool_call(messages: list) -> Optional[dict]:
    """从消息历史中找到最近一次因缺少参数失败的 MCP 工具调用(细粒度工具名在映射表内)"""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage) or not msg.tool_calls:
            continue
        for tc in msg.tool_calls:
            if tc.get("name", "") in TOOL_TO_ACTION:
                return tc
    return None


def _find_tool_error_for_call(messages: list, tool_call_id: str) -> str:
    """找到指定工具调用的错误信息"""
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.tool_call_id == tool_call_id:
            if msg.content and "缺少" in msg.content:
                return msg.content
    return ""


def _try_resume_with_code(
    state: DataManagementState,
    resume_value: str,
    log_service: Optional[AdminLogService],
    log_id: str,
) -> Optional[Dict[str, Any]]:
    """
    代码兜底：如果用户给了肯定回答且之前有因缺少参数失败的工具调用，
    直接重试工具调用，不经过 LLM，避免 prompt 注入风险。
    """
    if not _is_positive_answer(resume_value):
        logger.info(f"代码兜底: 非肯定回答 '{resume_value}'，跳过")
        return None

    messages = state.get("messages", [])
    if not messages:
        return None

    # 找到最近的失败工具调用
    last_tc = _find_last_failed_tool_call(messages)
    if not last_tc:
        logger.info("代码兜底: 未找到失败的工具调用")
        return None

    # 找到该工具调用的错误信息
    error_msg = _find_tool_error_for_call(messages, last_tc["id"])
    if not error_msg:
        logger.info("代码兜底: 未找到缺少参数的错误信息")
        return None

    logger.info(f"代码兜底: 找到失败工具调用 {last_tc['name']}, 错误: {error_msg[:200]}")

    # 从错误信息中提取缺失参数名
    missing_params = re.findall(r'缺少必填参数:\s*(.+?)(?:。|$)', error_msg)
    if not missing_params:
        logger.info("代码兜底: 无法解析缺失参数")
        return None

    # 从追问文本中提取建议值
    question = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content and not m.tool_calls:
            question = m.content
            break

    suggested = _extract_suggested_values(question)
    logger.info(f"代码兜底: 从追问提取建议值={suggested}")

    # 追问中没提取到，从用户回答中提取
    if not suggested:
        suggested = _extract_values_from_answer(resume_value)
        logger.info(f"代码兜底: 从用户回答提取值={suggested}")

    if not suggested:
        logger.info("代码兜底: 未找到任何可提取的值")
        return None

    # 合并原始参数和建议值(MCP 工具参数是扁平的:直接把建议值合并进 args)
    original_args = dict(last_tc["args"])
    original_params = dict(original_args.get("params", {}))
    for k, v in suggested.items():
        if k not in original_args or not original_args[k]:
            original_args[k] = v
    original_args.pop("params", None)

    # 检查是否所有必填参数都有值
    missing_text = missing_params[0]
    required_fields = re.findall(r'(\w+)\(', missing_text)
    still_missing = [f for f in required_fields if f not in original_args or not original_args[f]]
    if still_missing:
        logger.info(f"代码兜底: 仍有缺失参数 {still_missing}，无法直接重试")
        return None

    # 直接调用 MCP 工具(与 LLM 绑定同源;token 来自 state)
    logger.info(f"代码兜底: 直接调用 MCP 工具 {last_tc.get('name')}, args-keys={list(original_args.keys())}")
    token = state.get("token") or ""
    try:
        from app.services.mcp_service.mcp_client import call_tool_direct
        raw = _run_async(call_tool_direct(last_tc["name"], original_args, token or None))
        result = "".join(c.text for c in raw.content) if getattr(raw, "content", None) else str(raw)
        logger.info(f"代码兜底: 工具执行结果: {result[:200]}")

        tool_message = ToolMessage(content=result, tool_call_id=last_tc["id"], name=last_tc["name"])
        ai_response = AIMessage(content=result)

        log_service.update_log(log_id, {
            "agent_type": "data_management",
            "action": "resume_code_fallback",
            "status": "success",
            "result": result[:500],
        })

        return {
            "result": result,
            "messages": [tool_message, ai_response],
            "status": "success" if "失败" not in result else "failed",
        }
    except Exception as e:
        logger.error(f"代码兜底: 工具执行失败: {e}")
        return None


def create_agent_node(log_service: Optional[AdminLogService] = None,
                      tools: Optional[list] = None):
    """
    创建 LLM Agent 节点。
    每次被调用时，将系统提示 + 用户原始问题 + 历史工具交互一起发给 LLM，
    由 LLM 决定是继续调工具还是输出最终回复。
    tools 由工厂传入(MCP 绑定期预筛选后的列表)。
    """
    _log_service = log_service or AdminLogService()

    llm = _create_llm()
    tools = tools or []
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: DataManagementState) -> Dict[str, Any]:
        """LLM 推理节点"""
        query = state["query"]
        log_id = state.get("log_id", "")
        round_start = time.time()
        resume_value = state.get("resume_value", "")

        # 计算当前轮数
        tool_rounds = sum(1 for m in state.get("messages", []) if hasattr(m, "tool_calls") and m.tool_calls)
        logger.info(f"数据管理Agent推理中 (第 {tool_rounds + 1} 轮), resume={bool(resume_value)}, resume_value='{resume_value[:50] if resume_value else ''}'")

        # 构建消息：系统提示 + 路由上下文（如有）+ 用户问题 + 历史工具交互
        system_content = SYSTEM_PROMPT
        router_ctx = state.get("router_context", {})
        if router_ctx and (router_ctx.get("operation") or router_ctx.get("data_type")):
            ctx_hints = []
            if router_ctx.get("operation"):
                ctx_hints.append(f"预识别操作: {router_ctx['operation']}")
            if router_ctx.get("data_type"):
                ctx_hints.append(f"预识别数据类型: {router_ctx['data_type']}")
            system_content += "\n\n## 路由预解析信息（仅供参考，以实际工具返回为准）\n"
            system_content += "\n".join(f"- {h}" for h in ctx_hints)
            system_content += "\n你可以直接使用这些信息，减少不必要的推理步骤。"
            logger.info(f"注入路由上下文: {router_ctx}")

        # interrupt 恢复：尝试用代码直接重试工具调用，不经过 LLM
        if resume_value:
            retry_result = _try_resume_with_code(state, resume_value, log_service, log_id)
            if retry_result:
                logger.info("代码兜底：直接重试工具调用成功")
                return retry_result
            # 兜底失败，走正常 LLM 流程（用户回答已在 messages 中）
            logger.info("代码兜底未命中，走 LLM 流程")

        messages: List[BaseMessage] = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]
        if state.get("messages"):
            messages.extend(state["messages"])

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            round_elapsed = time.time() - round_start
            logger.info(f"本轮LLM调用耗时: {round_elapsed:.2f}s (失败)")
            _log_service.update_log(log_id, {
                "agent_type": "data_management",
                "action": "llm_error",
                "status": "failed",
                "error": str(e),
            })
            return {
                "result": f"数据管理任务执行失败: {str(e)}",
                "messages": [],
                "error_count": state.get("error_count", 0) + 1,
            }

        # 计算本轮耗时和 token 消耗
        round_elapsed = time.time() - round_start
        token_usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }
            logger.info(f"本轮Token消耗: {token_usage}")
        logger.info(f"本轮LLM调用耗时: {round_elapsed:.2f}s")

        # 记录到日志
        _log_service.update_log(log_id, {
            "agent_type": "data_management",
            "action": f"llm_round_{tool_rounds + 1}",
            "status": "running",
            "token_usage": token_usage if token_usage else None,
        })

        # LLM 没有调用工具 → 最终回复 或 追问
        if not response.tool_calls:
            content = response.content if hasattr(response, "content") else str(response)

            # LLM 兜底：空内容检查
            if not content or not content.strip():
                logger.warning("LLM 返回空内容，触发兜底回复")
                content = "抱歉，系统暂时无法处理您的请求。请稍后重试或联系管理员。"

            logger.info(f"LLM 回复: {content[:200]}")

            # interrupt 恢复后的首轮：跳过追问检测，让 LLM 直接执行
            if resume_value:
                logger.info(f"interrupt 恢复后首轮回复，跳过追问检测")
                # 安全网：如果 LLM 回复暗示要执行操作但没有调用工具，强制重试
                action_keywords = ["执行", "创建", "新增", "修改", "更新", "删除", "同步"]
                if any(kw in content for kw in action_keywords):
                    logger.warning("LLM 回复包含操作意图但未调用工具，强制重试")
                    retry_messages = messages + [
                        AIMessage(content=content),
                        HumanMessage(content="请直接调用 data_management 工具执行上述操作，不要只输出文字描述。")
                    ]
                    try:
                        retry_response = llm_with_tools.invoke(retry_messages)
                        if retry_response.tool_calls:
                            logger.info(f"重试成功，LLM 调用了工具: {[tc['name'] for tc in retry_response.tool_calls]}")
                            sigs = [_tool_signature(tc) for tc in retry_response.tool_calls]
                            return {
                                "messages": [retry_response],
                                "last_tool_signature": sigs[0] if sigs else "",
                                "call_history": [{"signature": s, "success": True} for s in sigs],
                            }
                        else:
                            logger.warning("重试仍未调用工具，返回文本回复")
                    except Exception as e:
                        logger.error(f"重试 LLM 调用失败: {e}")

            # 判断是否是追问（信息不足，需要用户补充）— 恢复后首轮不检测
            elif _is_clarification_question(content):
                logger.info("LLM 追问信息不足，设置 pending_clarification 状态")
                return {
                    "messages": [response],
                    "pending_clarification": content,
                }

            # 最终回复
            status = "success"
            if any(kw in content for kw in ["失败", "不支持", "缺少", "错误", "无法"]):
                status = "failed"

            _log_service.update_log(log_id, {
                "agent_type": "data_management",
                "action": "execute",
                "status": status,
                "result": content,
                "rounds_used": tool_rounds + 1,
                "token_usage": token_usage if token_usage else None,
            })
            return {
                "result": content,
                "messages": [response],
            }

        # LLM 调用了工具 → 交给 guard 节点检查后执行
        logger.info(f"LLM 调用工具: {[tc['name'] for tc in response.tool_calls]}")

        # 记录所有工具调用签名
        sigs = [_tool_signature(tc) for tc in response.tool_calls]
        sig = sigs[0] if sigs else ""

        return {
            "messages": [response],
            "last_tool_signature": sig,
            "call_history": [{"signature": s, "success": True} for s in sigs],
        }

    return agent_node


def _is_clarification_question(content: str) -> bool:
    """
    判断 LLM 回复是否是追问（信息不足，需要用户补充）。
    区分"追问"和"最终回复"：追问通常包含问号且有明确的信息需求关键词。
    """
    clarification_keywords = ["请提供", "请问", "请确认", "需要您", "缺少", "具体是", "哪些", "哪部", "哪个"]
    has_question_mark = "？" in content or "?" in content
    has_clarification_keyword = any(kw in content for kw in clarification_keywords)
    # 同时有问号和追问关键词 → 大概率是追问
    return has_question_mark and has_clarification_keyword


def _has_pending_delete(state: DataManagementState) -> bool:
    """检查是否有待执行的删除操作(MCP 细粒度工具名 == *_delete)"""
    messages = state.get("messages", [])
    if not messages:
        return False
    last_message = messages[-1]
    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        return False
    return any(
        mapping is not None and mapping[1] == "delete"
        for mapping in (TOOL_TO_ACTION.get(tc.get("name", "")) for tc in last_message.tool_calls)
    )


def _should_continue(state: DataManagementState) -> Literal["guard", "human_review", "aggregate", "waiting_for_user", "end"]:
    """
    路由判断：
    - 超时 → 聚合部分结果后结束
    - 超过最大轮数 → 聚合部分结果后结束
    - LLM 输出了删除工具调用 → 人工审查
    - LLM 输出了其他工具调用 → guard 检查后执行
    - LLM 直接回复（无工具调用）→ 结束
    """
    messages = state.get("messages", [])
    if not messages:
        logger.info("_should_continue: 无消息，返回 end")
        return "end"

    # 超时检查（interrupt 等待期间不计入超时）
    started_at = state.get("started_at", 0)
    is_waiting_review = state.get("is_waiting_review", False)
    if started_at and not is_waiting_review:
        elapsed = time.time() - started_at
        if elapsed > TASK_TIMEOUT_SECONDS:
            logger.warning(f"任务超时 ({elapsed:.1f}s > {TASK_TIMEOUT_SECONDS}s)，强制终止")
            return "aggregate"

    # 检查轮数限制
    max_rounds = state.get("max_rounds", MAX_TOOL_ROUNDS)
    tool_rounds = sum(1 for m in messages if hasattr(m, "tool_calls") and m.tool_calls)
    if tool_rounds >= max_rounds:
        logger.warning(f"达到最大工具调用轮数 {max_rounds}，进入聚合节点")
        return "aggregate"

    # 检查是否有待用户补充的信息
    if state.get("pending_clarification"):
        logger.info("_should_continue: 检测到 pending_clarification，路由到 waiting_for_user")
        return "waiting_for_user"

    last_message = messages[-1]
    has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls
    logger.info(f"_should_continue: 消息数={len(messages)}, has_tool_calls={has_tool_calls}, is_waiting_review={is_waiting_review}")

    if has_tool_calls:
        # 删除操作需要人工确认
        if _has_pending_delete(state):
            logger.info("_should_continue: 检测到删除操作，路由到 human_review")
            return "human_review"
        logger.info("_should_continue: 其他工具调用，路由到 guard")
        return "guard"
    logger.info("_should_continue: 无工具调用，返回 end")
    return "end"


def create_aggregate_node(log_service: Optional[AdminLogService] = None):
    """
    聚合节点 — 当超时或轮数耗尽时，将已有的中间结果聚合为保底输出。
    """
    _log_service = log_service or AdminLogService()

    def aggregate_node(state: DataManagementState) -> Dict[str, Any]:
        log_id = state.get("log_id", "")
        partial_results = state.get("partial_results", [])
        messages = state.get("messages", [])

        # 判断终止原因
        started_at = state.get("started_at", 0)
        elapsed = time.time() - started_at if started_at else 0
        is_timeout = elapsed > TASK_TIMEOUT_SECONDS
        reason = "超时" if is_timeout else "轮数耗尽"

        # 从 messages 中提取工具返回的最后结果
        tool_results = []
        for m in messages:
            if hasattr(m, "content") and hasattr(m, "tool_call_id"):
                # 这是 ToolMessage
                tool_results.append(m.content[:500] if m.content else "")

        # 拼接聚合结果
        result_parts = [f"任务因{reason}被终止（已执行 {elapsed:.1f}秒）。已完成的部分结果："]
        if partial_results:
            for i, pr in enumerate(partial_results, 1):
                result_parts.append(f"{i}. {pr}")
        elif tool_results:
            for i, tr in enumerate(tool_results, 1):
                result_parts.append(f"{i}. {tr[:300]}")
        else:
            result_parts.append("（无中间结果）")

        aggregated = "\n".join(result_parts)
        logger.warning(f"聚合输出: {aggregated[:300]}")

        # 计算实际轮数
        tool_rounds = sum(1 for m in messages if hasattr(m, "tool_calls") and m.tool_calls)

        _log_service.update_log(log_id, {
            "agent_type": "data_management",
            "action": "aggregate",
            "status": "partial",
            "result": aggregated,
            "rounds_used": tool_rounds,
            "timeout_reached": is_timeout,
        })

        return {
            "result": aggregated,
            "messages": [AIMessage(content=aggregated)],
        }

    return aggregate_node


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

    logger.info(f"人工审查节点: 待删除调用数量={len(delete_calls)}")

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

    logger.info(f"人工审查节点恢复: user_response={user_response}, type={type(user_response)}")

    # 用户确认 → 让 tools 节点执行（AI message 已在 state 中）
    if isinstance(user_response, str) and user_response.lower().strip() in ("yes", "y", "确认", "是"):
        logger.info("用户确认删除，继续执行工具调用")
        # 确保 tool_calls 仍然在 messages 中，让 tools 节点能执行
        return {"is_waiting_review": False}

    # 用户拒绝 → 结束
    logger.info("用户取消删除操作")
    return Command(goto=END, update={
        "result": "删除操作已取消。",
        "messages": [AIMessage(content="删除操作已取消，未执行任何删除。")],
        "is_waiting_review": False,
    })


def _waiting_for_user_node(state: DataManagementState):
    """
    等待用户补充信息节点。
    agent_node 检测到信息不足时设置 pending_clarification，
    路由到此节点后用 interrupt() 暂停，等待用户回答。
    """
    question = state.get("pending_clarification", "请补充缺失的信息")
    logger.info(f"等待用户补充信息: {question[:200]}")

    user_answer = interrupt({
        "question": question,
        "type": "clarify",
    })

    logger.info(f"用户补充信息: {user_answer[:100]}")

    # 将用户的回答作为 HumanMessage 加入对话，清除 pending 状态
    return {
        "messages": [HumanMessage(content=user_answer)],
        "pending_clarification": "",
        "resume_value": user_answer,
    }


def _adjust_max_rounds(state: DataManagementState) -> int:
    """根据调用历史动态调整轮数上限"""
    base = MAX_TOOL_ROUNDS
    call_history = state.get("call_history", [])

    if len(call_history) >= 2:
        # 检测跨类型操作（不同 data_type）
        data_types = set()
        for entry in call_history:
            sig = entry.get("signature", "")
            parts = sig.split(":")
            if len(parts) >= 2 and parts[1]:
                data_types.add(parts[1])
        if len(data_types) > 1:
            base += 2
            logger.info(f"检测到跨类型操作 ({data_types})，轮数上限调整为 {base}")

    # 连续错误收缩
    error_count = state.get("error_count", 0)
    if error_count >= 2:
        base -= 1
        logger.info(f"连续错误 {error_count} 次，轮数上限收缩为 {base}")

    return max(base, 3)


def create_guard_node():
    """
    Guard 节点 — 插在 agent 和 tools 之间。
    职责：
    1. 错误去重：如果上一轮同样的工具调用失败了，过滤掉并注入错误提示
    2. 调用限流：防止连续两次完全相同的调用
    3. 动态轮数：根据调用历史调整 max_rounds
    4. 权限兜底：按用户角色对每个工具调用的 operation 做 action 级校验，
       未授权的操作回填拒绝 ToolMessage（双保险：路由阶段已做过一次 action 校验）
    """
    _permission_checker = PermissionChecker()

    def guard_node(state: DataManagementState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
            return {}

        user_role = state.get("user_role") or "user"

        # 动态调整轮数
        new_max_rounds = _adjust_max_rounds(state)

        # 收集上一轮失败的调用签名
        failed_signatures = set()
        call_history = state.get("call_history", [])
        for entry in call_history:
            if not entry.get("success", True):
                failed_signatures.add(entry["signature"])

        # 检查当前调用是否与失败调用重复
        current_calls = last_message.tool_calls
        valid_calls = []
        error_messages = []
        new_history = []

        for tc in current_calls:
            sig = _tool_signature(tc)

            # ── 权限兜底(L2):MCP 细粒度工具名反查 (data_type, operation) → 矩阵校验 ──
            tool_name = tc.get("name", "")
            mapping = TOOL_TO_ACTION.get(tool_name)
            if mapping is not None:
                data_type, operation = mapping
                if not _permission_checker.check(user_role, "data_management", operation):
                    error_messages.append(ToolMessage(
                        content=f"权限不足：您的角色 [{user_role}] 无权执行 [{operation}] 操作（{data_type}）。"
                                f"请如实告知用户该操作未被授权，不要重试其他变体。",
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    ))
                    new_history.append({"signature": sig, "success": False})
                    continue

            if sig in failed_signatures:
                # 这个调用之前已经失败过，过滤掉
                error_msg = f"该操作已失败（签名: {sig}），不允许重复调用相同参数。请调整参数或告知用户操作失败。"
                logger.warning(f"Guard: 过滤重复失败调用 {sig}")
                error_messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
                new_history.append({"signature": sig, "success": False})
            else:
                valid_calls.append(tc)
                new_history.append({"signature": sig, "success": True})

        # 所有调用都被过滤（权限/去重）→ 注入错误提示让 LLM 重新决策或结束
        if not valid_calls and error_messages:
            logger.warning("Guard: 所有工具调用均被过滤（权限不足或重复失败），注入错误提示让 LLM 重新决策")
            return {
                "messages": error_messages,
                "call_history": new_history,
                "error_count": state.get("error_count", 0) + 1,
                "max_rounds": new_max_rounds,
            }

        # 部分调用被过滤：注入拒绝/错误提示；保留有效调用继续执行
        if error_messages:
            logger.info(f"Guard: 过滤 {len(error_messages)} 个被拒调用，保留 {len(valid_calls)} 个有效调用")

            # 替换最后一条消息的 tool_calls 为有效调用
            if valid_calls:
                filtered_ai_message = AIMessage(
                    content=last_message.content,
                    tool_calls=valid_calls,
                )
                return {
                    "messages": [filtered_ai_message] + error_messages,
                    "call_history": new_history,
                    "max_rounds": new_max_rounds,
                }
            return {
                "messages": error_messages,
                "call_history": new_history,
                "max_rounds": new_max_rounds,
            }

        # 全部有效，正常传递
        return {
            "call_history": new_history,
            "max_rounds": new_max_rounds,
        }

    return guard_node


def create_tool_result_collector_node():
    """
    工具结果收集节点 — 包装 ToolNode，在执行工具后收集中间结果到 partial_results。
    插在 tools 节点之后，用于提取工具返回摘要。
    """
    def collect_node(state: DataManagementState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        logger.info(f"工具结果收集: 当前消息数量={len(messages)}")

        if not messages:
            return {"partial_results": []}

        # 取最后一条消息（应该是 ToolNode 刚写入的 ToolMessage）
        last_msg = messages[-1]
        logger.info(f"最后消息类型: {type(last_msg).__name__}, has_content={hasattr(last_msg, 'content')}")

        if hasattr(last_msg, "content") and last_msg.content:
            summary = last_msg.content[:300]
            logger.info(f"工具结果摘要: {summary[:100]}")
            return {"partial_results": [summary]}
        return {"partial_results": []}

    return collect_node


def create_data_management_agent(log_service: Optional[AdminLogService] = None,
                                 user_role: Optional[str] = None,
                                 token: Optional[str] = None):
    """
    创建数据管理Agent — LLM + Tools 多轮循环模式

    流程：
    1. init_node：初始化控制字段
    2. Agent 节点：LLM 理解用户意图，决定调用什么工具
    3. 删除操作 → human_review 节点 → interrupt 暂停等待用户确认
    4. 其他操作 → ToolNode 直接执行
    5. 超时/轮数耗尽 → aggregate 节点聚合部分结果
    6. 回到 Agent：LLM 看到工具结果，决定继续调工具还是输出最终回复
    7. 循环直到 LLM 不再调用工具（或达到限制）

    MCP 化(实施设计文档 §4.3):
    - tools 来自 MCP(law-ai-server 经 token 拉取)经绑定期预筛选(tool_filter,按 user_role);
    - 绑定期白名单 = L1 主防线:越权工具对 LLM 不可见;
    - DataManagementTool 退役(不再绑定),guard 保留做 L2 兜底。
    """
    from app.services.mcp_service.tool_filter import get_allowed_tools

    if token:
        from app.services.mcp_service.mcp_client import list_all_tools
        try:
            mcp_tools = _run_async(list_all_tools(token))
            tools = get_allowed_tools("data_management", user_role or "user", mcp_tools)
        except Exception as e:
            # fail-closed:MCP 不可达 → 空工具集(绝不降级本地矩阵)
            logger.error("MCP 工具拉取失败,绑定为空集(白名单 fail-closed): %s", e)
            tools = []
    else:
        # 无 token(MCP 化前的旧调用路径):绑定空集,行为=不可执行任何 MCP 工具
        logger.warning("create_data_management_agent 未收到 token,工具绑定为空集")
        tools = []

    workflow = StateGraph(DataManagementState)

    # 添加节点
    workflow.add_node("init", create_init_node())
    workflow.add_node("agent", create_agent_node(log_service, tools=tools))
    workflow.add_node("guard", create_guard_node())
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("collect_results", create_tool_result_collector_node())
    workflow.add_node("human_review", _human_review_node)
    workflow.add_node("waiting_for_user", _waiting_for_user_node)
    workflow.add_node("aggregate", create_aggregate_node(log_service))

    # 设置入口
    workflow.set_entry_point("init")

    # init → agent
    workflow.add_edge("init", "agent")

    # Agent → 路由判断
    workflow.add_conditional_edges(
        "agent",
        _should_continue,
        {
            "guard": "guard",
            "human_review": "human_review",
            "aggregate": "aggregate",
            "waiting_for_user": "waiting_for_user",
            "end": END,
        },
    )

    # guard（错误去重+限流）→ tools
    workflow.add_edge("guard", "tools")

    # tools → collect_results → agent（收集中间结果后回到 agent）
    workflow.add_edge("tools", "collect_results")
    workflow.add_edge("collect_results", "agent")

    # human_review → 用户确认后执行工具（已确认的删除跳过 guard）
    workflow.add_edge("human_review", "tools")

    # waiting_for_user → 用户补充信息后回到 agent 继续推理
    workflow.add_edge("waiting_for_user", "agent")

    # aggregate → END
    workflow.add_edge("aggregate", END)

    # checkpointer 是 interrupt/resume 的必要条件
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


