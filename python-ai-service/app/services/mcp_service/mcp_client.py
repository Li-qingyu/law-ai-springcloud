"""
MCP 客户端模块
封装 law-ai-service MCP Server(STATELESS Streamable HTTP)的连接与工具拉取。

设计要点(实施设计文档 §4.2/§4.3,实测 ❹ 结论已定):
- HTTP 传输层 headers 挂在连接配置上(MCP 链路 initialize/tools/* 全程共用),
  因此「token 不同的会话」需要各自 client 实例 —— per-session client(会话闭包持有 token),
  实测 0.3.2 无 per-call headers 能力;
- client 构造工厂按 token 缓存在进程内(dict),同一 token 复用(会话级复用,不是进程级单值);
- 全量工具元数据可以无 token 拉取吗?不可:服务端 /mcp 强制用户 token(实测 401)。
  因此「工具元数据拉取」在管理后台首会话建立的带 token client 上做一次并进程缓存,
  元数据与用户无关,可安全复用。
"""
import logging
from typing import Any, Dict, List

from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 进程级缓存:token → client(token 对应合法用户会话,会话吊销后 client 失效但可由 TTL/重新登录解决;
# 管理员数量有限,缓存用量可控)
_clients: Dict[str, MultiServerMCPClient] = {}
settings=get_settings()

def get_mcp_client(token: str | None = None) -> MultiServerMCPClient:
    """
    获取/创建 MCP 客户端(按 token 缓存)。
    token 为空时返回无鉴权 client(仅期调试,服务端会 401 拒绝)。
    """
    if token is not None:
        cached = _clients.get(token)
        if cached is not None:
            return cached
        client = MultiServerMCPClient({
            "law-ai": {
                "transport": "http",   # streamable_http
                "url": settings.MCP_LAW_AI_URL,
                "headers": {"token": token},
            },
        })
        _clients[token] = client
        return client

    # 无 token:默认 client(调试用;正式启动链路必须传 token)
    return MultiServerMCPClient({
        "law-ai": {
            "transport": "http",
            "url": settings.MCP_LAW_AI_URL,
        },
    })


async def list_all_tools(token: str | None = None) -> List[Any]:
    """拉取 MCP Server 全量工具(LangChain Tool 列表,须带 token)。
    元数据与用户无关 —— 首次成功后写进程缓存。
    工具为 async-only(0.3.2 特性),包一层 sync 兼容壳供 ToolNode/代码兜底同步调用。"""
    client = get_mcp_client(token)
    tools = await client.get_tools()
    logger.info("MCP 工具拉取成功: %d 个", len(tools))
    return [_sync_compatible(t) for t in tools]


def _sync_compatible(tool: Any) -> Any:
    """
    给 StructuredTool 补 sync 调用通道。
    background: MCP 适配器的工具只实现了 coroutine(async);而本项目的子 Agent 图
    由同步线程(run_in_executor)驱动,ToolNode 回退 sync invoke 会报
    "StructuredTool does not support sync invocation"。
    这里为 func/_run 提供基于 asyncio.run 的同步实现(每次调用独立 event loop,
    与 httpx 流式请求兼容)。
    """
    if getattr(tool, "func", None) is not None:
        # 已有 sync 路径,不处理
        return tool

    import asyncio
    import functools

    async_orig = tool.coroutine

    @functools.wraps(async_orig)
    def _sync_run(*args, **kwargs):
        return asyncio.run(async_orig(*args, **kwargs))

    tool.func = _sync_run
    return tool


async def call_tool_direct(tool_name: str, arguments: Dict[str, Any], token: str | None = None) -> Any:
    """
    程序化直调 MCP 工具(供绑定期等非 LLM 场景使用,如二期 list_allowed_tools)。
    0.3.2 无公开 call_tool,走 session() 的原始低层调用。
    """
    client = get_mcp_client(token)
    async with client.session("law-ai") as session:
        result = await session.call_tool(tool_name, arguments or {})
        return result
