"""
文件管理Agent
处理文件上传、解析和批量导入操作
"""
import os
from typing import Annotated, Optional, Literal,TypedDict
import operator
import logging

from langchain_classic.agents import create_openai_tools_agent
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langgraph.types import Command
from langgraph.graph import StateGraph, END
from app.tools.adminTool.file_management_tool import FileManagementTool
from app.services.admin_agent_service.admin_log_service import AdminLogService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 获取当前文件所在的目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(CURRENT_DIR, "../prompts")
# 加载提示词模板
SYSTEM_PROMPT = """
    
           """
class FileManagementState(TypedDict):
    """文件管理Agent状态"""
    query: str
    user_id: str
    user_role: str
    url: str
    log_id: str
    result: str
    messages: Annotated[list, operator.add]


def get_llm(model_type: str = "qwen"):
    """获取LLM模型"""
    settings = get_settings()
    if model_type == "qwen":
        model = settings.OPENAI_MODEL
        return ChatTongyi(
            model=model,
            api_key=settings.DASHSCOPE_API_KEY,
        )
    elif model_type == "deepseek":
        model = settings.DEEPSEEK_MODEL
        return ChatDeepSeek(
            model=model,
            api_key=settings.DEEPSEEK_API_KEY,
        )
    return None


def file_management_tool() :
    """文件管理工具函数"""
    try:
        tool = [FileManagementTool()]
        return tool
    except Exception as e:
        return f"文件操作失败: {str(e)}"


class FileManagementAgent:
    """文件管理智能体"""

    def __init__(self, model_type: str = "qwen", log_service: Optional[AdminLogService] = None):
        self.model_type = model_type
        self.log_service = log_service or AdminLogService()

    async def __call__(self, state: FileManagementState, config=None) -> Command[Literal["tool_node", "__end__"]]:
        """处理文件管理智能体逻辑"""
        try:
            query = state["query"]
            user_id = state["user_id"]
            log_id = state.get("log_id", "")

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "{messages}")
            ])

            # 构建系统提示词
            system_prompt = prompt.partial(
                query=query,
                user_id=user_id
            )

            # 获取LLM并绑定工具
            llm = get_llm(model_type=self.model_type)
            tools =  file_management_tool()
            agent=create_openai_tools_agent(llm,tools,system_prompt)
            # 调用LLM
            response = await agent.ainvoke(
                {"messages": state.get("messages", [])},
                config
            )

            # 更新日志
            if log_id:
                self.log_service.update_log(log_id, {
                    "agent_type": "file_management",
                    "action": "execute",
                    "status": "success",
                    "result": response.content if hasattr(response, 'content') else str(response)
                })

            # 判断是否需要调用工具
            goto = "tool_node" if response.tool_calls else "__end__"

            return Command(
                update={
                    "messages": [response],
                    "result": response.content if hasattr(response, 'content') else str(response)
                },
                goto=goto
            )

        except Exception as e:
            logger.error(f"文件管理Agent执行失败: {str(e)}")

            # 记录错误日志
            if state.get("log_id"):
                self.log_service.update_log(state["log_id"], {
                    "agent_type": "file_management",
                    "action": "execute",
                    "status": "error",
                    "error": str(e)
                })

            return Command(
                update={
                    "result": f"文件管理操作失败: {str(e)}",
                    "messages": []
                },
                goto="__end__"
            )


def create_file_management_agent(log_service: Optional[AdminLogService] = None):
    """创建文件管理Agent（兼容旧接口）"""
    agent = FileManagementAgent(log_service=log_service)

    workflow = StateGraph(FileManagementState)

    # 添加节点
    async def execute_node(state: FileManagementState, config=None):
        return await agent(state, config)

    workflow.add_node("execute", execute_node)

    # 设置入口
    workflow.set_entry_point("execute")

    # 添加结束边
    workflow.add_edge("execute", END)

    return workflow.compile()


