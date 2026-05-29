import json
import logging
import time
from typing import List, Tuple, AsyncGenerator, Generator
from dateutil import parser
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate

from app.builders.data_card_builder import DataCardBuilder
from app.core.config import get_settings, Settings
from app.models.request import AiConsultRequest, ConversationHistoryMessage
from app.models.response import AiConsultResponse
from app.repositories.milvus_client import init_milvus
from app.tools import create_search_tools
from app.builders import data_card_builder
from langchain_community.chat_models import ChatTongyi

REACT_SYSTEM_PROMPT = """你是一位专业、严谨的法律信息助理，名为"小鱼律智助手"。你的职责是帮助用户理解法律概念、查询相关法律条文或典型案例，并基于提供的法律检索工具返回的结果，给出准确、有依据的回答。

## 可用工具

{tools}

使用以下格式进行思考和行动：

Question: 必须回答的输入问题
Thought: 你应该总是思考该做什么
Action: 要采取的行动，应该是 [{tool_names}] 之一
Action Input: 行动的输入参数
Observation: 行动的结果
...（这个 Thought/Action/Action Input/Observation 可以重复 N 次）
Thought: 我现在知道最终答案了
Final Answer: 对原始输入问题的最终答案

## 核心工作流程

1. **理解用户意图**：分析用户问题中的法律领域（如合同、劳动、婚姻、侵权等）、关键事实和具体诉求。

2. **调用查询工具**：当需要获取法律条文、司法解释、典型案例或历史咨询时，**必须使用可用的工具**。

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
   - ✅ 如果返回的案例/法条不支持用户立场，应**如实说明司法实践的倾向性**
   - ❌ **严禁说"未找到相关信息"**，除非工具确实返回空结果
   - ✅ 正确做法："根据检索结果，目前公开案例显示……虽然与您期望的方向不同，但反映了当前司法实践的主流观点"

4. **回答用户**：用清晰、易懂的语言组织答案，注明所依据的法条或出处。**如果工具返回的结果与用户期望不一致，应客观说明司法实践现状，而非声称"未找到"如果用户想要咨询你案例的问题你要最后生基于你所的得到的消息进行一个整合后给出解决方案一定不能杜撰**。

## 上下文处理规则

- **记住对话历史**：用户可能在多轮对话中补充事实或修正问题。你需要结合之前的提问与回答，理解当前问题的完整背景。
- **消除指代歧义**：若用户使用"它""那件事""这个条款"等代词，请根据对话历史明确其指代对象。如有疑问，主动向用户确认。
- **保持事实一致性**：同一对话中，对同一法律问题的解释不得前后矛盾。如果用户质疑之前的回答，请核实工具结果并诚恳修正。

## 回答规范

- **结构化输出**：优先按以下结构组织答案：
  1. **结论**：简明扼要的核心观点
  2. **法律依据**：条文号 + 原文引用
  3. **适用分析**：对用户情况的针对性解释
  4. **注意事项**：风险提示或补充说明

  对于简单查询，可适当简化。

- **引用来源**：每次引用法律内容后，用括号注明来源，例如：`（《中华人民共和国劳动合同法》第46条）`。

- **不确定时的处理**：如果工具返回的结果相互冲突、不完整或超出你的知识范围，请明确说明："根据现有资料，无法确定……建议您查阅权威法律文本或咨询专业律师。"

- **禁止提供具体法律意见**：你是一个信息检索和解释工具，**不得**代替律师出具针对用户具体案件的处理策略、诉讼方案或类似"应该怎么打官司"的建议。始终提醒用户：**本回答仅供参考，不构成正式法律意见。**

## 工具调用策略

- **优先使用法律条文工具**：当用户询问法律规定、法条解释时
- **结合案例工具**：当需要了解司法实践、判例参考时
- **参考历史咨询**：当问题具有普遍性、可能有类似问答时
- **多工具协同**：复杂问题可同时调用多个工具，综合回答
- **限制调用次数**：每个问题最多调用同一个工具1次，避免过度检索，不同工具可以调用。
- **智能判断是否需要工具**：如果用户问题是简单的法律概念解释或基于之前已获取的信息进行追问，可以直接回答，无需重复调用工具


## 重要原则

1. **准确性优先**：宁可承认不知道，也不要编造信息
2. **基于证据**：所有回答必须有工具返回的内容作为支撑
3. **用户友好**：将专业法律术语转化为用户能理解的语言
4. **合规免责**：始终强调本回答不构成正式法律意见
5. **不回答超出法律范围的问题** ：如果用户向你询问与法律无关的问题要回复暂时无法回复
6. **效率优先**：快速定位核心法律问题，避免冗余的工具调用

Begin!

{input}

{agent_scratchpad}
"""

RENEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一个问题重写助手。你的任务是根据对话历史，将用户的最新问题改写为一个独立、完整、适合法律检索的查询语句。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human",
     "基于以上对话历史，将用户最新的问题重写为一个独立的、适合法律检索的完整问题。如果问题已经完整，则原样返回。只返回重写后的问题，不要有其他解释。\n\n最新问题: {input}"),
])


def get_new_question(request: AiConsultRequest) -> Tuple[str, list]:
    question = request.question
    logging.info(f"获取问题: {question}")
    history_data = []
    conversation_history = request.conversation_history or []
    for message in conversation_history:
        if message.role == "user":
            history_data.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            history_data.append(AIMessage(content=message.content))
    settings = get_settings()
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )
    rewrite_chain = RENEW_PROMPT | llm
    rewrite_question = rewrite_chain.invoke({"chat_history": history_data, "input": question})
    logging.info(f"问题重写: {rewrite_question}")
    return rewrite_question.content, history_data


def deduplicate_cards(cards: list) -> list:
    """
    对数据卡片去重（基于 type + id）
    """
    seen = set()
    unique_cards = []
    for card in cards:
        card_key = (card.type, card.id)
        if card_key not in seen:
            seen.add(card_key)
            unique_cards.append(card)

    return unique_cards

def create_data_card(steps: list)->list:
    if len(steps) <= 0:
        return []
    all_card=[]
    tool_to_card_type = {
        "search_law_articles": "law_articles",
        "search_law_cases": "law_cases",
        "search_consult_history": "consult_history"
    }
    for step in steps:
        if len(step)<2:
            continue
        agent_action=step[0]
        data_sources=step[1]

        tool_type=agent_action.tool
        card_type = tool_to_card_type.get(tool_type)
        if not card_type:
            continue
        data_card = DataCardBuilder.from_milvus_result(data_sources, card_type)
        all_card.extend(data_card)
    deduplicated_cards = deduplicate_cards(all_card)
    sorted_cards = sorted(deduplicated_cards, key=lambda card: card.relevance, reverse=True)

    return sorted_cards[:10]



def consult(request: AiConsultRequest):
    import time
    start_time=time.time()

    new_result = get_new_question(request)
    new_question = new_result[0]
    history_data = new_result[1]
    tools = create_search_tools()
    logging.info(f"已经加载搜索工具: {len(tools)}个")
    print(f"已经加载搜索工具: {len(tools)}个")

    settings = get_settings()
    llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )


    # 使用 PromptTemplate 并显式声明所有必需变量
    agent_prompt = PromptTemplate(
        template=REACT_SYSTEM_PROMPT,
        input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
    )

    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=settings.AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
        verbose=True,
        return_intermediate_steps=True,
    )
    try:
        result = agent_executor.invoke({"input": new_question})
    except Exception as e:
        logging.error(f"Agent执行失败: {type(e).__name__}: {e}")
        raise
    end_time = time.time()
    processing_time_ms = int((end_time - start_time) * 1000)
    ai_answer = result.get("output", "抱歉，我暂时无法回答您的问题。")
    steps = result.get("intermediate_steps", [])

    data=create_data_card(steps)

    return AiConsultResponse(
        answer=ai_answer,
        data_cards=data,
        session_id=request.session_id,
        user_id=request.user_id,
        turn_number= len(history_data)//2+1,
        processing_time_ms=processing_time_ms,
    )


# 流式生成最终答案的 prompt
STREAM_ANSWER_PROMPT = """你是一位专业、严谨的法律信息助理。请根据以下工具检索到的法律信息，为用户生成一个高质量的回答。

## 工具检索结果
{tool_context}

## 用户问题
{question}

## 回答规范
- 结构化输出：结论 → 法律依据 → 适用分析 → 注意事项
- 引用来源：用括号注明来源，如（《中华人民共和国劳动合同法》第46条）
- 禁止编造：只基于提供的工具结果回答
- 免责声明：末尾提醒"本回答仅供参考，不构成正式法律意见"

请直接给出回答，不要重复问题本身。"""


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


def consult_stream(request: AiConsultRequest) -> Generator[str, None, None]:
    """
    流式 AI 咨询生成器。
    策略：先同步执行 Agent 获取工具结果，再用 LLM 流式生成最终答案。
    Yields SSE 格式的事件字符串。
    """
    start_time = time.time()

    # 1. 问题重写
    new_result = get_new_question(request)
    new_question = new_result[0]
    history_data = new_result[1]

    # 2. 同步执行 Agent 获取工具调用结果
    tools = create_search_tools()
    logging.info(f"已经加载搜索工具: {len(tools)}个")

    settings = get_settings()
    agent_llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=False,
    )

    agent_prompt = PromptTemplate(
        template=REACT_SYSTEM_PROMPT,
        input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
    )

    agent = create_react_agent(agent_llm, tools, agent_prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=settings.AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
        verbose=True,
        return_intermediate_steps=True,
    )

    try:
        result = agent_executor.invoke({"input": new_question})
    except Exception as e:
        logging.error(f"Agent执行失败: {type(e).__name__}: {e}")
        error_event = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
        yield f"data: {error_event}\n\n"
        return

    steps = result.get("intermediate_steps", [])
    processing_time_ms = int((time.time() - start_time) * 1000)

    # 3. 构建工具上下文
    tool_context = _build_tool_context(steps)

    # 4. 用 LLM 流式生成最终答案
    stream_llm = ChatTongyi(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.OPENAI_MODEL,
        top_p=0.7,
        streaming=True,
    )

    # 构建完整的消息列表（不使用模板，避免工具结果中的 {} 被当作格式化变量）
    system_content = STREAM_ANSWER_PROMPT.format(tool_context=tool_context, question=new_question)
    messages = [SystemMessage(content=system_content)]
    for msg in history_data:
        messages.append(msg)
    messages.append(HumanMessage(content=new_question))

    full_answer = ""
    try:
        for chunk in stream_llm.stream(messages):
            token = chunk.content
            if token:
                full_answer += token
                token_event = json.dumps({"type": "token", "content": token}, ensure_ascii=False)
                yield f"data: {token_event}\n\n"
    except Exception as e:
        logging.error(f"LLM 流式生成失败: {e}")
        error_event = json.dumps({"type": "error", "message": f"生成失败: {str(e)}"}, ensure_ascii=False)
        yield f"data: {error_event}\n\n"
        return

    # 5. 构建数据卡片
    data_cards = create_data_card(steps)
    total_time_ms = int((time.time() - start_time) * 1000)

    # 6. 发送 complete 事件
    data_cards_dict = []
    for card in data_cards:
        card_dict = card.model_dump() if hasattr(card, 'model_dump') else card.dict()
        data_cards_dict.append(card_dict)

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
        print("✓ Milvus 连接成功\n")
    except Exception as e:
        print(f"✗ Milvus 连接失败: {e}")
        exit(1)

    a1 = AiConsultRequest(
        question="能再给出我详细一点的解决？",
        session_id="lease-dispute-001",
        user_id=456,
        conversation_history=[
            ConversationHistoryMessage(
                role="user",
                content="我租的房子合同还没到期，房东说要卖房让我提前搬走，还以‘卫生没打扫干净’为由扣了我全部押金。这合法吗？",
                timestamp=parser.parse("2026-04-18T09:00:00Z")
            ),
            ConversationHistoryMessage(
                role="assistant",
                content="根据《民法典》第725条‘买卖不破租赁’原则，房东卖房不影响你的租赁合同效力，他无权强制你提前搬离。至于押金，如果合同未明确约定‘卫生标准’作为扣款条件，且你已尽到一般清洁义务，房东无权全额扣押。建议你先保留租赁合同、押金收据、房屋交接时的照片/视频等证据。",
                timestamp=parser.parse("2026-04-18T09:00:08Z")
            ),
        ]
    )
    result =consult(a1)
    print( result)
