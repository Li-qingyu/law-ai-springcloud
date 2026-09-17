"""
权限检查器
基于角色的权限控制，支持超级管理员和普通管理员两级权限体系
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PermissionChecker:
    """权限检查器"""

    # 权限矩阵配置
    # 角色说明: user=普通用户(无管理权限), super_admin=超级管理员, admin=普通管理员
    # 普通管理员(admin)的 data_management 与后端权限矩阵对齐：知识库完整维护（增删改查+导入+同步）；
    # 文件管理、日志管理、权限管理对其不可用。—— 权限权威在后端 Java 服务层，本矩阵为过渡期执行点。
    # v2(MCP化): 删除 statistics —— DATA_TYPE_OPERATIONS 无对应操作且 Java 端无承载接口,保留会造成 ACTION_TOOL_MAP 映射缺口;
    PERMISSION_MATRIX: Dict[str, Dict[str, List[str]]] = {
        "super_admin": {
            "file_management": ["upload", "parse", "import", "list", "delete"],
            "data_management": ["query", "query_all", "count", "create", "update", "delete", "import", "sync", "sync_status"],
            "log_management": ["query", "statistics", "export", "cleanup"],
            "permission_management": ["query", "create", "update", "delete"],
        },
        "admin": {
            "file_management": [],
            "data_management": ["query", "query_all", "count", "create", "update", "delete", "import", "sync", "sync_status"],
            "log_management": [],
            "permission_management": [],
        },
        "user": {
            "file_management": [],
            "data_management": [],
            "log_management": [],
            "permission_management": [],
        },
    }

    # 任务类型到操作的默认映射
    TASK_DEFAULT_ACTION: Dict[str, str] = {
        "file_management": "list",
        "data_management": "query",
        "log_management": "query",
        "permission_management": "query",
    }

    def check(self, user_role: str, agent_type: str, action: Optional[str] = None) -> bool:
        """
        检查用户是否有权限执行指定操作

        Args:
            user_role: 用户角色
            agent_type: Agent类型（任务类型）
            action: 操作类型，如果为 None 则使用默认操作

        Returns:
            是否有权限
        """
        if not action:
            action = self.TASK_DEFAULT_ACTION.get(agent_type, "query")

        allowed_actions = self.PERMISSION_MATRIX.get(user_role, {}).get(agent_type, [])
        has_permission = action in allowed_actions

        logger.info(
            f"权限检查: role={user_role}, agent={agent_type}, action={action}, "
            f"result={'允许' if has_permission else '拒绝'}"
        )
        return has_permission

    def get_allowed_actions(self, user_role: str, agent_type: str) -> List[str]:
        """
        获取用户在指定Agent类型下允许的操作列表

        Args:
            user_role: 用户角色
            agent_type: Agent类型

        Returns:
            允许的操作列表
        """
        return self.PERMISSION_MATRIX.get(user_role, {}).get(agent_type, [])

    def get_allowed_agent_types(self, user_role: str) -> List[str]:
        """
        获取用户允许访问的Agent类型列表

        Args:
            user_role: 用户角色

        Returns:
            允许的Agent类型列表
        """
        role_permissions = self.PERMISSION_MATRIX.get(user_role, {})
        return [agent_type for agent_type, actions in role_permissions.items() if actions]
