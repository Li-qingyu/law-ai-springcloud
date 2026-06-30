"""
管理员Agent模块
提供多Agent协作的管理员系统
"""

from app.agents.agents.admin_router_agent import (
    create_classify_node,
    create_check_permission_node,
    route_to_sub_agent,
)
from app.agents.agents.file_management_agent import create_file_management_agent
from app.agents.agents.log_management_agent import create_log_management_agent
from app.agents.agents.data_management_agent import create_data_management_agent
from app.agents.agents.permission_management_agent import create_permission_management_agent

__all__ = [
    "create_classify_node",
    "create_check_permission_node",
    "route_to_sub_agent",
    "create_file_management_agent",
    "create_log_management_agent",
    "create_data_management_agent",
    "create_permission_management_agent",
]
