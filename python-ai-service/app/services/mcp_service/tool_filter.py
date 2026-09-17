"""
绑定期预筛选工具过滤(实施设计文档 §4.3,L1 主防线)

数据来源全部是代码常量/结构,LLM 不参与筛选:
  DATA_TYPE_OPERATIONS × ACTION_TOOL_MAP × PermissionChecker.PERMISSION_MATRIX

安全语义:
1. 白名单语义:未映射到 (data_type, operation) 的未知工具 → 丢弃 + warning;
2. 空角色 = 零工具:未知/无权限角色返回空列表,子 Agent 无任何 MCP 工具自然拒绝。
"""
import logging
from typing import Any, List

from app.services.admin_agent_service.permission_checker import PermissionChecker
from app.services.mcp_service.action_tool_map import TOOL_TO_ACTION

logger = logging.getLogger(__name__)


def get_allowed_tools(agent_type: str, user_role: str, mcp_tools: List[Any]) -> List[Any]:
    """
    从 MCP 全量工具中筛出该角色在指定 Agent 域内允许的工具(绑定期主防线)。
    Args:
        agent_type: "data_management"(当前阶段);后续扩展其余 agent 域
        user_role: super_admin / admin / user
        mcp_tools: mcp_client.list_all_tools() 全量工具
    """
    allowed_actions = PermissionChecker().get_allowed_actions(user_role, agent_type)
    result = []
    for tool in mcp_tools:
        mapping = TOOL_TO_ACTION.get(tool.name)
        if mapping is None:
            # 未知工具(Java 新增未同步映射):白名单语义 = 不可见 + warning
            logger.warning("MCP工具 %s 无 ACTION_TOOL_MAP 映射,绑定期丢弃", tool.name)
            continue
        data_type, operation = mapping
        if operation in allowed_actions:
            result.append(tool)
    logger.info(
        "绑定期预筛选: role=%s agent=%s → %d/%d 工具绑定",
        user_role, agent_type, len(result), len(mcp_tools),
    )
    return result
