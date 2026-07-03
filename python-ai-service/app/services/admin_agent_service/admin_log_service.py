import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.admin_log import AdminLog

logger = logging.getLogger(__name__)

class AdminLogService:
    """管理员日志服务"""
    
    def __init__(self):
        # 在实际实现中，这里会初始化数据库连接
        self.logs: Dict[str, AdminLog] = {}
    
    def create_log(self, data: Dict[str, Any]) -> str:
        """创建新的操作日志"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        log = AdminLog(
            task_id=task_id,
            user_id=data.get("user_id", 0),
            agent_type=data.get("task_type", "unknown"),
            action="start",
            status="running",
            input_data=data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.logs[task_id] = log
        logger.info(f"创建日志: {task_id}")
        return task_id
    
    def update_log(self, task_id: str, data: Dict[str, Any]) -> bool:
        """更新操作日志"""
        if task_id not in self.logs:
            logger.warning(f"日志不存在: {task_id}")
            return False
        
        log = self.logs[task_id]
        
        # 更新字段
        if "status" in data:
            log.status = data["status"]
        if "result" in data:
            log.output_data = {"result": data["result"]}
        if "error" in data:
            log.error_message = data["error"]
        if "agent_type" in data:
            log.agent_type = data["agent_type"]
        if "action" in data:
            log.action = data["action"]
        if "rounds_used" in data:
            log.rounds_used = data["rounds_used"]
        if "token_usage" in data:
            log.token_usage = data["token_usage"]
        if "timeout_reached" in data:
            log.timeout_reached = data["timeout_reached"]
        
        log.updated_at = datetime.now()
        
        # 计算执行时长
        if log.status in ["success", "failed", "permission_denied"]:
            duration = (log.updated_at - log.created_at).total_seconds() * 1000
            log.duration_ms = int(duration)
        
        logger.info(f"更新日志: {task_id}, 状态: {log.status}")
        return True
    
    def get_log(self, task_id: str) -> Optional[AdminLog]:
        """获取操作日志"""
        return self.logs.get(task_id)
    
    def get_logs_by_user(self, user_id: int) -> List[AdminLog]:
        """获取用户的操作日志"""
        return [log for log in self.logs.values() if log.user_id == user_id]
    
    def get_logs_by_agent_type(self, agent_type: str) -> List[AdminLog]:
        """获取指定Agent类型的操作日志"""
        return [log for log in self.logs.values() if log.agent_type == agent_type]
    
    def get_logs_by_status(self, status: str) -> List[AdminLog]:
        """获取指定状态的操作日志"""
        return [log for log in self.logs.values() if log.status == status]
