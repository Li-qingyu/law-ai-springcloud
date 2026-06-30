import json
import logging
import re
import time
from typing import List, AsyncGenerator
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.builders.data_card_builder import DataCardBuilder
from app.core.config import get_settings

# 检索优化模块
from app.retrieval.retriever import Retriever
from app.retrieval.strategies.vector_strategy import VectorStrategy
from app.retrieval.strategies.hybrid_strategy import HybridStrategy
from app.retrieval.strategies.multi_query_strategy import MultiQueryStrategy
from app.retrieval.pipelines.base import RetrievalPipeline
from app.retrieval.pipelines.dedup import DedupStep
from app.retrieval.pipelines.rerank import DashScopeReranker, NoopReranker, RerankStep
from app.retrieval.params import get_params

# ==================== Monkey-patch ChatTongyi streaming bug ====================
# langchain_community ChatTongyi 的 subtract_client_response 在流式 tool_calls 场景下
# 当前 chunk 的 tool_calls 数量 > 上一个 chunk 时，index 越界导致 IndexError。
# 上游 issue: https://github.com/langchain-ai/langchain/issues/28076
from langchain_community.chat_models.tongyi import ChatTongyi as _ChatTongyi


def _patched_subtract_client_response(self, resp, prev_resp):
    """修复版：处理 tool_calls 数量在流式过程中递增的情况"""
    resp_copy = json.loads(json.dumps(resp))
    choice = resp_copy["output"]["choices"][0]
    message = choice["message"]

    prev_resp_copy = json.loads(json.dumps(prev_resp))
    prev_choice = prev_resp_copy["output"]["choices"][0]
    prev_message = prev_choice["message"]

    message["content"] = message["content"].replace(prev_message["content"], "")

    if message.get("tool_calls"):
        prev_tool_calls = prev_message.get("tool_calls", [])
        for index, tool_call in enumerate(message["tool_calls"]):
            function = tool_call["function"]
            if index < len(prev_tool_calls):
                prev_function = prev_tool_calls[index]["function"]
                if "name" in function:
                    function["name"] = function["name"].replace(
                        prev_function["name"], ""
                    )
                if "arguments" in function:
                    function["arguments"] = function["arguments"].replace(
                        prev_function["arguments"], ""
                    )

    return resp_copy


_ChatTongyi.subtract_client_response = _patched_subtract_client_response
from app.models.request import AiConsultRequest
from app.models.response import AiConsultResponse
from app.repositories.milvus_client import init_milvus
from app.services.rag_agent_service.parallel_search import parallel_search_all_sync, build_tool_context_from_results
from app.services.rag_agent_service.semantic_cache import SemanticCache
from app.tools import create_search_tools
from app.memory.working_memory import WorkingMemory, build_memory_header, extract_reference_anchor
from app.memory.short_term_memory import ShortTermMemory
from app.memory.long_term_memory import LongTermMemory
from langchain_community.chat_models import ChatTongyi

# ==================== 两阶段分离架构 ====================
# 阶段 1: pre_analyze() — 轻量预分析（代词消解 + 意图分类），~0.5-1s
# 阶段 2: Agent 推理 — 不注入对话历史，token 消耗降低 40%+
# 阶段 3: 流式生成 — 注入对话历史 + 工具结果，生成最终回答

"""
    常量
"""
# 提示词 — OpenAI Tools Agent 格式（支持并行工具调用）
AGENT_SYSTEM_PROMPT = """你是一位专业、严谨的法律信息助理，名为"小鱼律智助手"。你的职责是帮助用户理解法律概念、查询相关法律条文或典型案例，并基于提供的法律检索工具返回的结果，给出准确、有依据的回答。

## 核心工作流程

1. **理解用户意图**：分析用户问题中的法律领域（如合同、劳动、婚姻、侵权等）、关键事实和具体诉求。
   - 注意：当前问题已经过预分析处理，代词已替换为具体实体，可直接用于检索。

2. **调用查询工具**：当需要获取法律条文、司法解释、典型案例或历史咨询时，**必须使用可用的工具**。可以同时调用多个工具并行检索。

   **重要原则 - 关键词转化策略**：
   - ⚠️ **严禁直接使用用户口语化问题进行检索！**
   - 每次调用前，必须将用户问题转化为**精炼的法律专业术语**
   - 转化规则：
     * 提取核心法律关系（如：租赁合同解除、押金返还、违约责任）
     * 使用标准法律术语（如："买卖不破租赁"而非"卖房不影响租房"）
     * 明确争议焦点（如："承租人保管义务"而非"卫生打扫干净"）

   **转化示例**：
     * 用户问："房东卖房要我搬走合法吗？"
       → 检索词："买卖不破租赁 租赁合同存续期间所有权变动"
     * 用户问："扣我押金说卫生不干净"
       → 检索词："租赁合同押金返还 承租人保管义务 正常使用损耗"
     * 用户问："公司辞退我要赔钱吗？"
       → 检索词："违法解除劳动合同 经济补偿金 赔偿金计算标准"
     * 用户问："借钱不还怎么办？"
       → 检索词："民间借贷合同纠纷 违约责任 诉讼时效中断"

3. **整合工具返回结果**：工具会返回格式化的法律信息（包含ID、相关度评分、内容摘要等）。你必须**严格基于工具返回的真实内容**进行回答，不得编造或补充工具未提供的信息。

   **重要理解原则**：
   - ✅ **工具返回任何结果都是"有效信息"**，即使结果与用户期望不符
   - ✅ 如果返回的案例/法条不支持用户立场，应*如实说明司法实践的倾向性*
   - ❌ **禁止说"未找到相关信息"**，除非工具确实返回空结果
   - ✅ 正确做法："根据检索结果，目前公开案例显示……虽然与您期望的方向不同，但反映了当前司法实践的主流观点"

4. **回答用户**：用清晰、易懂的语言组织答案，注明所依据的法条或出处。*如果工具返回的结果与用户期望不一致，应客观说明司法实践现状，而非声称"未找到"。如果用户想要咨询你案例的问题你要最后生基于你所的得到的消息进行一个整合后给出解决方案一定不能杜撰*。

## 上下文处理规则

- 当提供了对话历史时，结合历史理解当前问题的完整背景，特别是代词（"它"、"那个"、"这个"）的指代对象。
- 当未提供对话历史时，直接基于问题内容进行检索和回答。
- 保持事实一致性：回答应基于工具返回的真实内容，不编造信息。

## 回答规范

- **结构化输出**：优先按以下结构组织答案：
  1. **结论**：简明扼要的核心观点
  2. **法律依据**：条文号 + 原文引用
  3. **适用分析**：对用户情况的针对性解释
  4. **注意事项**：风险提示或补充说明

  对于简单查询，可适当简化。

- **引用来源**：每次引用法律内容后，用括号注明来源，例如：`（《中华人民共和国劳动合同法》第46条）`

- **不确定时的处理**：如果工具返回的结果相互冲突、不完整或超出你的知识范围，请明确说明："根据现有资料，无法确定……建议您查阅权威法律文本或咨询专业律师。"

- **禁止提供具体法律意见**：你是一个信息检索和解释工具，**不得**代替律师出具针对用户具体案件的处理策略、诉讼方案或类似"应该怎么打官司"的建议。始终提醒用户：**本回答仅供参考，不构成正式法律意见。**

## 工具调用策略

- **优先使用法律条文工具**：当用户询问法律规定、法条解释时
- **结合案例工具**：当需要了解司法实践、判例参考时
- **参考历史咨询**：当问题具有普遍性、可能有类似问答时
- **多工具协同**：复杂问题应同时调用多个工具并行检索，综合回答
- **限制调用次数**：每个问题最多调用同一个工具2次，避免过度检索，不同工具可以调用
- **智能判断是否需要工具**：如果用户问题是简单的法律概念解释或基于之前已获取的信息进行追问，可以直接回答，无需重复调用工具

## 重要原则

1. **准确性优先**：宁可承认不知道，也不要编造信息
2. **基于证据**：所有回答必须有工具返回的内容作为支撑
3. **用户友好**：将专业法律术语转化为用户能理解的语言
4. **合规免责**：始终强调本回答不构成正式法律意见
5. **不回答超出法律范围的问题**：如果用户向你询问与法律无关的问题要回答暂时无法回答
6. **效率优先**：快速定位核心法律问题，避免冗余的工具调用
"""

# 开头招呼语言
GREETINGS="""
你好！我是小鱼律智助手，专注于为你提供准确、有依据的法律信息支持。  
你可以随时提出关于合同、劳动、婚姻家事、房产、侵权、公司、知识产权等领域的法律问题，例如：  
- “租房到期后房东不退押金怎么办？”  
- “公司没签劳动合同，能要双倍工资吗？”  
- “交通事故对方全责，赔偿项目有哪些？”  

请描述你的具体情况或疑问，我会基于现行法律法规和司法实践，为你检索并解读相关条文或案例。
"""

# 预分析模块提示词
PRE_ANALYZE_PROMPT = """你是一个法律咨询助手的预分析模块。请完成两个任务：

1. **代词消解**：如果当前问题包含代词（"它"、"那个"、"这个"、"他"、"她"等），根据对话上下文将其替换为具体实体
2. **意图分类**：判断用户意图类别

对话上下文：
{context}

当前问题：{question}

输出 JSON（不要输出其他内容）：
{{"resolved_question": "替换代词后的完整问题（如无需替换则原样输出）", "intent": "simple_query/consultation/follow_up/chitchat"}}

分类标准：
- simple_query：查询具体法条、法律定义、简单事实查询
- consultation：需要分析的法律问题、维权建议、案例咨询
- follow_up：基于之前对话的追问（如"那赔偿怎么算"、"还有什么要注意的"）
- chitchat：闲聊、问候、与法律无关的问题"""
# ==================== 意图分类规则 ====================
CHITCHAT_PATTERNS = [
    r"^(你好|您好|嗨|hi|hello|hey|谢谢|感谢|再见|拜拜|辛苦)",
    r".*(天气|笑话|新闻|游戏|音乐|电影).*",
    r"^(你是谁|你叫什么|你能做什么|你是什么)",
]
SIMPLE_QUERY_PATTERNS = [
    r".*第\s*\d+\s*条.*",
    r".*(法条|法律|法规|规定|条款)\s*(是|怎么|如何)\s*(什么|说|规定).*",
    r".*是什么(意思|含义).*",
]

# 流式生成最终答案的 prompt
STREAM_ANSWER_PROMPT = """你是一位专业、严谨的法律信息助理。请根据以下工具检索到的法律信息，为用户生成一个高质量的回答。

## 对话历史
{chat_history}

## 工具检索结果
{tool_context}

## 用户问题
{question}

## 回答规范
- 结构化输出：结论 → 法律依据 → 适用分析 → 注意事项
- 引用来源：用括号注明来源，如（《中华人民共和国劳动合同法》第46条）
- 禁止编造：只基于提供的工具结果回答
- 免责声明：末尾提醒"本回答仅供参考，不构成正式法律意见"
- 最后格式按照md文档对应格式生成。

请直接给出回答，不要重复问题本身。"""


def build_retriever(intent: str, llm=None) -> Retriever:
    """
    根据意图构建 Retriever 实例
    - 策略决定"怎么召回"（向量 / 多路改写）
    - 管道决定"怎么处理"（去重 + 精排）
    """
    params = get_params(intent)
    settings = get_settings()

    # 基础检索策略（向量 or 混合）
    if params.use_hybrid and settings.HYBRID_SEARCH_ENABLED:
        base_strategy = HybridStrategy()
    else:
        base_strategy = VectorStrategy()

    # 多路改写包装（可叠加在任何基础策略之上）
    if params.use_multi_query and settings.MULTI_QUERY_ENABLED and llm:
        strategy = MultiQueryStrategy(llm=llm, inner_strategy=base_strategy)
    else:
        strategy = base_strategy

    # 选精排器
    if settings.RERANK_ENABLED:
        reranker = DashScopeReranker(api_key=settings.DASHSCOPE_API_KEY)
    else:
        reranker = NoopReranker()

    # 组装管道
    pipeline = RetrievalPipeline(steps=[
        DedupStep(),
        RerankStep(reranker, top_n=params.final_k),
    ])

    return Retriever(strategy=strategy, pipeline=pipeline)


def build_chat_history_text(conversation_history: list, memory_header: str = "") -> str:
    """
    将对话历史格式化为可读文本，用于流式生成阶段注入。
    使用工作记忆窗口管理，仅保留最近 2-3 轮，避免 token 浪费。
    """
    parts = []

    # 1. 注入会话元信息摘要头（来自短期记忆）
    if memory_header:
        parts.append(memory_header)

    # 2. 工作记忆：最近 2-3 轮
    wm = WorkingMemory()
    working_context = wm.build_context(conversation_history)
    if working_context:
        parts.append(working_context)
    elif not parts:
        return "无对话历史"

    # 3. 引用锚点
    anchor = extract_reference_anchor(conversation_history)
    if anchor:
        parts.append(anchor)

    return "\n".join(parts)


def build_history_messages(conversation_history: list) -> List:
    """将对话历史转为 LangChain Message 列表，仅包含工作记忆窗口内的消息"""
    wm = WorkingMemory()
    working_turns = wm.get_working_turns_for_history(conversation_history)
    history_data = []
    for message in working_turns:
        if message.role == "user":
            history_data.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            history_data.append(AIMessage(content=message.content))
    return history_data





def _rule_classify(question: str, has_history: bool) -> str | None:
    """规则快速分类，返回 None 表示需要 LLM 兜底"""
    q = question.strip()

    # 闲聊检测
    for pattern in CHITCHAT_PATTERNS:
        if re.match(pattern, q, re.IGNORECASE):
            return "chitchat"

    # 简单查询检测
    for pattern in SIMPLE_QUERY_PATTERNS:
        if re.match(pattern, q):
            return "simple_query"

    # 追问检测：有历史 + 短问题
    if has_history and len(q) < 30:
        return "follow_up"

    return None


def _build_minimal_context(conversation_history: list) -> str:
    """构建最简上下文（仅保留最近 2 轮的关键信息，用于 pre_analyze）"""
    if not conversation_history:
        return "无"

    lines = []
    # 取最近 4 条消息（2 轮）
    recent = conversation_history[-4:]
    for msg in recent:
        role = "用户" if msg.role == "user" else "助手"
        # 只取前 150 字
        content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
        lines.append(f"{role}：{content}")
    return "\n".join(lines)




async def pre_analyze(question: str, conversation_history: list,
                      memory_context: str = "") -> dict:
    """
    轻量预分析：代词消解 + 意图分类
    - 无历史时：纯规则分类，不调用 LLM（< 10ms）
    - 有历史时：规则优先，LLM 兜底（0.5-1s）
    - memory_context: 短期记忆摘要头，当 conversation_history 为空时作为上下文补充
    """
    import asyncio
    has_history = bool(conversation_history) or bool(memory_context)

    # 1. 规则快速分类
    intent = _rule_classify(question, has_history)

    # 2. 无历史且规则命中 → 直接返回
    if intent and not has_history:
        logging.info(f"[pre_analyze] 规则分类: intent={intent}, question={question[:50]}")
        return {"resolved_question": question, "intent": intent}

    # 3. 有历史或规则未命中 → LLM 兜底（在线程池中执行，避免阻塞事件循环）
    settings = get_settings()
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
    )

    # 优先用 conversation_history，没有时用 memory_context
    if conversation_history:
        context = _build_minimal_context(conversation_history)
    elif memory_context:
        context = memory_context
    else:
        context = "无"
    prompt = PRE_ANALYZE_PROMPT.format(context=context, question=question)

    try:
        # 使用 run_in_executor 避免阻塞事件循环
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, llm.invoke, prompt)
        content = result.content.strip()
        # 提取 JSON（处理可能的 markdown 包裹）
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        analysis = json.loads(content)
        resolved = analysis.get("resolved_question", question)
        intent = analysis.get("intent", "consultation")
        logging.info(f"[pre_analyze] LLM分类: intent={intent}, resolved={resolved[:50]}")
        return {"resolved_question": resolved, "intent": intent}
    except Exception as e:
        logging.warning(f"[pre_analyze] LLM分类失败，降级为规则结果: {e}")
        return {
            "resolved_question": question,
            "intent": intent or "consultation",
        }



# 创建agent
def _build_agent_executor(settings) -> AgentExecutor:
    """
    构建 OpenAI Tools Agent 执行器。
    Tools Agent 支持 LLM 单步返回多个工具调用，
    AgentExecutor._aiter_next_step 通过 asyncio.gather 并发执行。
    """
    tools = create_search_tools()
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",  AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=settings.AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
        verbose=True,
        return_intermediate_steps=True,
    )

#  去重卡片
def deduplicate_cards(cards: list) -> list:
    """对数据卡片去重（基于 type + id）"""
    seen = set()
    unique_cards = []
    for card in cards:
        card_key = (card.type, card.id)
        if card_key not in seen:
            seen.add(card_key)
            unique_cards.append(card)
    return unique_cards

# 创建卡片
def create_data_card(steps: list) -> list:
    if len(steps) <= 0:
        return []
    all_card = []
    tool_to_card_type = {
        "search_law_articles": "law_articles",
        "search_law_cases": "law_cases",
        "search_consult_history": "consult_history"
    }
    for step in steps:
        if len(step) < 2:
            continue
        agent_action = step[0]
        data_sources = step[1]
        tool_type = agent_action.tool
        card_type = tool_to_card_type.get(tool_type)
        if not card_type:
            continue
        data_card = DataCardBuilder.from_milvus_result(data_sources, card_type)
        all_card.extend(data_card)
    deduplicated_cards = deduplicate_cards(all_card)
    sorted_cards = sorted(deduplicated_cards, key=lambda card: card.relevance, reverse=True)
    return sorted_cards[:10]

# 阻塞回答
async def consult(request: AiConsultRequest):
    """
    非流式 AI 咨询（两阶段分离架构）。
    阶段 0: 语义缓存检查
    阶段 1: pre_analyze — 代词消解 + 意图分类
    阶段 2: Agent 推理 / 简单查询快速通道
    阶段 3: 生成最终回答
    """
    start_time = time.time()

    question = request.question
    conversation_history = request.conversation_history or []

    # 加载短期记忆，构建记忆上下文（必须在 pre_analyze 之前，为意图识别提供上下文）
    stm = ShortTermMemory(request.session_id)
    short_term_summary = stm.get_summary()
    round_count = stm.get_round_count()
    memory_header = build_memory_header(short_term_summary, round_count) if short_term_summary else ""

    # 短期记忆缺失时，查询长期记忆
    long_term_context = ""
    if not short_term_summary:
        ltm = LongTermMemory()
        long_term_context = ltm.recall(request.user_id, question, short_term_summary)
        if long_term_context:
            logging.info(f"[长期记忆] 命中跨会话历史: user_id={request.user_id}")

    # 阶段 0: 语义缓存检查（提前到 pre_analyze 之前，缓存命中直接返回）
    cache = SemanticCache()
    cached = cache.get(question)
    if cached and not cached.get("need_refresh"):
        logging.info(f"[缓存命中] score={cached['score']:.4f}")
        processing_time_ms = int((time.time() - start_time) * 1000)
        return AiConsultResponse(
            answer=cached["answer"],
            data_cards=[],
            session_id=request.session_id,
            user_id=request.user_id,
            turn_number=round_count + 1,
            processing_time_ms=processing_time_ms,
        )

    # 阶段 1: 轻量预分析（传入 memory_header 作为上下文补充）
    analysis = await pre_analyze(question, conversation_history, memory_header)

    history_data = build_history_messages(conversation_history)
    chat_history_text = build_chat_history_text(conversation_history, memory_header)

    # 注入长期记忆到上下文前面
    if long_term_context:
        chat_history_text = long_term_context + "\n\n" + chat_history_text

    logging.info(f"原始问题: {question}")
    logging.info(f"对话历史轮次: {len(conversation_history)}, 记忆轮次: {round_count}")
    resolved_question = analysis["resolved_question"]
    intent = analysis["intent"]
    logging.info(f"[阶段1] 预分析完成: intent={intent}, resolved={resolved_question[:50]}")

    # 闲聊快速返回
    if intent == "chitchat":
        processing_time_ms = int((time.time() - start_time) * 1000)
        return AiConsultResponse(
            answer="您好，我是法律咨询助手小鱼律智助手，请问有什么法律问题需要帮助？",
            data_cards=[],
            session_id=request.session_id,
            user_id=request.user_id,
            turn_number=len(history_data) // 2 + 1,
            processing_time_ms=processing_time_ms,
        )

    settings = get_settings()
    steps = []

    # 构建 Retriever 并设置全局实例
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )
    retriever = build_retriever(intent, llm=llm)
    from app.tools.searchTool.base_search_tool import set_retriever
    set_retriever(retriever)

    if intent == "simple_query":
        # 简单查询快速通道：并行检索，跳过 Agent
        search_results = parallel_search_all_sync(resolved_question, top_k=5)
        from types import SimpleNamespace
        for tool_name, items in search_results.items():
            if items:
                action = SimpleNamespace(tool=f"search_{tool_name}")
                steps.append((action, items))
        ai_answer = _generate_answer_from_context(
            build_tool_context_from_results(search_results),
            question, chat_history_text, history_data, settings
        )
    else:
        # Agent 推理 — OpenAI Tools Agent，支持并行工具调用
        logging.info("已加载搜索工具: 3个 (OpenAI Tools Agent)")
        agent_executor = _build_agent_executor(settings)

        # follow_up 追问时注入对话历史，让 Agent 理解上下文
        agent_chat_history = history_data if intent == "follow_up" else []

        try:
            result = await agent_executor.ainvoke({
                "input": resolved_question,
                "chat_history": agent_chat_history,
            })
        except Exception as e:
            logging.error(f"Agent执行失败: {type(e).__name__}: {e}")
            raise

        steps = result.get("intermediate_steps", [])
        ai_answer = result.get("output", "抱歉，我暂时无法回答您的问题。")

    end_time = time.time()
    processing_time_ms = int((end_time - start_time) * 1000)
    data = create_data_card(steps)

    # 写入语义缓存
    data_cards_dict = [card.model_dump() if hasattr(card, 'model_dump') else card.dict() for card in data]
    try:
        cache.set(question, ai_answer, data_cards_dict)
    except Exception as e:
        logging.warning(f"缓存写入失败: {e}")

    # 更新短期记忆
    try:
        need_compress = stm.add_round(question, ai_answer)
        if need_compress:
            await stm.compress_pending(llm)
            logging.info(f"[记忆] 短期记忆压缩完成: session={request.session_id}")
    except Exception as e:
        logging.warning(f"[记忆] 短期记忆更新失败: {e}")

    return AiConsultResponse(
        answer=ai_answer,
        data_cards=data,
        session_id=request.session_id,
        user_id=request.user_id,
        turn_number=len(history_data) // 2 + 1,
        processing_time_ms=processing_time_ms,
    )


def _generate_answer_from_context(tool_context: str, question: str,
                                   chat_history_text: str, history_data: list,
                                   settings) -> str:
    """从工具上下文直接生成回答（用于简单查询快速通道，非流式）"""
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )
    system_content = STREAM_ANSWER_PROMPT.format(
        tool_context=tool_context,
        question=question,
        chat_history=chat_history_text,
    )
    messages = [SystemMessage(content=system_content)]
    for msg in history_data:
        messages.append(msg)
    messages.append(HumanMessage(content=question))

    result = llm.invoke(messages)
    return result.content


def _sse_event(event_type: str, data) -> str:
    """构建 SSE 事件字符串"""
    payload = {"type": event_type, "content": data} if isinstance(data, str) else {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

def _build_tool_context(steps: list) -> str:
    """从 Agent 中间步骤构建工具上下文文本"""
    if not steps:
        return "无工具检索结果"
    context_parts = []
    for i, step in enumerate(steps):
        if len(step) < 2:
            continue
        agent_action = step[0]
        observation = step[1]
        tool_name = agent_action.tool
        tool_input = agent_action.tool_input
        context_parts.append(f"### 工具调用 {i+1}: {tool_name}\n查询: {tool_input}\n结果:\n{observation}")
    return "\n\n".join(context_parts) if context_parts else "无工具检索结果"


async def consult_stream(request: AiConsultRequest) -> AsyncGenerator[str, None]:
    """
    流式 AI 咨询异步生成器（两阶段分离架构）。
    阶段 1: pre_analyze — 代词消解 + 意图分类（0.5-1s）
    阶段 2: Agent 推理 — OpenAI Tools Agent 支持并行工具调用（10-30s）
    阶段 3: 流式生成 — 注入对话历史 + 工具结果（3-8s）
    Yields SSE 格式的事件字符串。
    """
    start_time = time.time()

    question = request.question
    conversation_history = request.conversation_history or []

    # 加载短期记忆，构建记忆上下文（必须在 pre_analyze 之前，为意图识别提供上下文）
    stm = ShortTermMemory(request.session_id)
    short_term_summary = stm.get_summary()
    round_count = stm.get_round_count()
    memory_header = build_memory_header(short_term_summary, round_count) if short_term_summary else ""

    # 短期记忆缺失时，查询长期记忆
    long_term_context = ""
    if not short_term_summary:
        ltm = LongTermMemory()
        long_term_context = ltm.recall(request.user_id, question, short_term_summary)
        if long_term_context:
            logging.info(f"[长期记忆] 命中跨会话历史: user_id={request.user_id}")

    # ==================== 语义缓存检查 ====================
    cache = SemanticCache()
    cached = cache.get(question)
    if cached and not cached.get("need_refresh"):
        logging.info(f"[缓存命中] score={cached['score']:.4f}")
        yield _sse_event("status", "命中缓存，正在返回...")
        yield _sse_event("token", cached["answer"])
        total_time_ms = int((time.time() - start_time) * 1000)
        complete_data = {
            "type": "complete",
            "answer": cached["answer"],
            "data_cards": cached["data_cards"],
            "session_id": request.session_id,
            "user_id": request.user_id,
            "turn_number": round_count + 1,
            "processing_time_ms": total_time_ms,
        }
        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
        return

    # ==================== 阶段 1: 轻量预分析 ====================
    yield _sse_event("status", "正在分析您的问题...")
    analysis = await pre_analyze(question, conversation_history, memory_header)
    resolved_question = analysis["resolved_question"]

    # pre_analyze 完成后构建历史上下文（供后续阶段使用）
    history_data = build_history_messages(conversation_history)
    chat_history_text = build_chat_history_text(conversation_history, memory_header)
    if long_term_context:
        chat_history_text = long_term_context + "\n\n" + chat_history_text
    logging.info(f"原始问题: {question}")
    logging.info(f"对话历史轮次: {len(conversation_history)}, 记忆轮次: {round_count}")
    intent = analysis["intent"]
    logging.info(f"[阶段1] 预分析完成: intent={intent}, resolved={resolved_question[:50]}")

    # 闲聊快速返回
    if intent == "chitchat":
        yield _sse_event("token", GREETINGS)
        total_time_ms = int((time.time() - start_time) * 1000)
        complete_data = {
            "type": "complete",
            "answer": GREETINGS,
            "data_cards": [],
            "session_id": request.session_id,
            "user_id": request.user_id,
            "turn_number": len(history_data) // 2 + 1,
            "processing_time_ms": total_time_ms,
        }
        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
        return

    settings = get_settings()
    tool_context = ""
    steps = []

    # 构建 Retriever 并设置全局实例
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )
    retriever = build_retriever(intent, llm=llm)
    from app.tools.searchTool.base_search_tool import set_retriever
    set_retriever(retriever)

    if intent == "simple_query":
        # ==================== 简单查询快速通道：并行检索 + 直接生成 ====================
        yield _sse_event("status", "正在检索法律信息...")
        search_results = parallel_search_all_sync(resolved_question, top_k=5)
        tool_context = build_tool_context_from_results(search_results)
        # 构造 fake steps 用于 create_data_card
        from types import SimpleNamespace
        for tool_name, items in search_results.items():
            if items:
                action = SimpleNamespace(tool=f"search_{tool_name}")
                steps.append((action, items))
        agent_time_ms = int((time.time() - start_time) * 1000)
        logging.info(f"[快速通道] 并行检索完成: {agent_time_ms}ms, 结果 {sum(len(v) for v in search_results.values())} 条")
        yield _sse_event("status", f"检索完成，正在生成回答...")
    else:
        # ==================== 阶段 2: Agent 推理（并行工具调用） ====================
        yield _sse_event("status", "正在检索法律信息...")
        logging.info("已加载搜索工具: 3个 (OpenAI Tools Agent)")
        agent_executor = _build_agent_executor(settings)

        # follow_up 追问时注入对话历史，让 Agent 理解上下文
        agent_chat_history = history_data if intent == "follow_up" else []

        steps = []
        tool_context = ""
        try:
            # 使用 astream_events 获取实时进度
            async for event in agent_executor.astream_events({
                "input": resolved_question,
                "chat_history": agent_chat_history,
            }, version="v2"):
                event_kind = event.get("event")
                if event_kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    logging.info(f"[Agent] 工具调用开始: {tool_name}")
                    yield _sse_event("progress", {
                        "step": "tool_call",
                        "tool": tool_name,
                        "status": "calling"
                    })
                elif event_kind == "on_tool_end":
                    logging.info(f"[Agent] 工具调用完成")
                    yield _sse_event("progress", {
                        "step": "tool_result",
                        "status": "complete"
                    })
                elif event_kind == "on_chain_end" and event.get("name") == "AgentExecutor":
                    result = event.get("data", {}).get("output", {})
                    steps = result.get("intermediate_steps", [])
                    tool_context = _build_tool_context(steps)
        except Exception as e:
            logging.error(f"Agent执行失败: {type(e).__name__}: {e}")
            yield _sse_event("error", {"message": str(e)})
            return

        agent_time_ms = int((time.time() - start_time) * 1000)
        logging.info(f"[阶段2] Agent 推理完成: {agent_time_ms}ms, 工具调用 {len(steps)} 次")
        yield _sse_event("status", f"找到 {len(steps)} 条相关信息，正在生成回答...")

    # ==================== 阶段 3: 流式生成（注入历史） ====================
    stream_llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=True,
    )

    # 构建完整的消息列表（不使用模板，避免工具结果中的 {} 被当作格式化变量）
    system_content = STREAM_ANSWER_PROMPT.format(
        tool_context=tool_context,
        question=question,
        chat_history=chat_history_text,
    )
    messages = [SystemMessage(content=system_content)]
    for msg in history_data:
        messages.append(msg)
    messages.append(HumanMessage(content=question))

    full_answer = ""
    try:
        for chunk in stream_llm.stream(messages):
            token = chunk.content
            if token:
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logging.error(f"LLM 流式生成失败: {e}")
        yield _sse_event("error", {"message": f"生成失败: {str(e)}"})
        return

    # ==================== 发送 complete 事件 ====================
    data_cards = create_data_card(steps)
    total_time_ms = int((time.time() - start_time) * 1000)

    data_cards_dict = []
    for card in data_cards:
        card_dict = card.model_dump() if hasattr(card, 'model_dump') else card.dict()
        data_cards_dict.append(card_dict)

    # 写入语义缓存（异步，不阻塞响应）
    try:
        cache.set(question, full_answer, data_cards_dict)
    except Exception as e:
        logging.warning(f"缓存写入失败: {e}")

    # 更新短期记忆
    try:
        need_compress = stm.add_round(question, full_answer)
        if need_compress:
            await stm.compress_pending()
            logging.info(f"[记忆] 短期记忆压缩完成: session={request.session_id}")
    except Exception as e:
        logging.warning(f"[记忆] 短期记忆更新失败: {e}")

    logging.info(f"花费时间: {total_time_ms} ms")
    complete_event = json.dumps({
        "type": "complete",
        "answer": full_answer,
        "data_cards": data_cards_dict,
        "session_id": request.session_id,
        "user_id": request.user_id,
        "turn_number": len(history_data) // 2 + 1,
        "processing_time_ms": total_time_ms,
    }, ensure_ascii=False, default=str)
    yield f"data: {complete_event}\n\n"


if __name__ == '__main__':
    # 首先初始化 Milvus 连接
    print("正在初始化 Milvus 连接...")
    try:
        init_milvus()
        print("Milvus 连接成功\n")
    except Exception as e:
        print(f"Milvus 连接失败: {e}")
        exit(1)

    a1 = AiConsultRequest(
        # question="能再给出我详细一点的解决",
        question="我租的房子合同还没到期，房东说要卖房让我提前搬走，还以'卫生没打扫干净'为由扣了我全部押金。这合法吗？",
        session_id="lease-dispute-001",
        user_id=456,
        conversation_history=[
            # ConversationHistoryMessage(
            #     role="user",
            #     content="我租的房子合同还没到期，房东说要卖房让我提前搬走，还以'卫生没打扫干净'为由扣了我全部押金。这合法吗？",
            #     timestamp=parser.parse("2026-04-18T09:00:00Z")
            # ),
            # ConversationHistoryMessage(
            #     role="assistant",
            #     content="根据《民法典》第725条'买卖不破租赁'原则，房东卖房不影响你的租赁合同效力，他无权强制你提前搬离。至于押金，如果合同未明确约定'卫生标准'作为扣款条件，且你已尽到一般清洁义务，房东无权全额扣押。建议你先保留租赁合同、押金收据、房屋交接时的照片/视频等证据。",
            #     timestamp=parser.parse("2026-04-18T09:00:08Z")
            # ),
        ]
    )
    import asyncio
    result = asyncio.run(consult(a1))
    print(result)