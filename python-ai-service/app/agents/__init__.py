"""
管理员Agent模块
提供多Agent协作的管理员系统
"""

from app.agents.admin_router_agent import create_admin_router_agent
from app.agents.file_management_agent import create_file_management_agent
from app.agents.log_management_agent import create_log_management_agent
from app.agents.data_management_agent import create_data_management_agent
from app.agents.permission_management_agent import create_permission_management_agent
from app.agents.review_agent import create_review_agent

__all__ = [
    "create_admin_router_agent",
    "create_file_management_agent",
    "create_log_management_agent",
    "create_data_management_agent",
    "create_permission_management_agent",
    "create_review_agent"
]
