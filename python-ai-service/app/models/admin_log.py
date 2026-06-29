from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AdminLog(BaseModel):
    """管理员操作日志模型"""
    id: Optional[int] = None
    task_id: str = Field(..., description="任务ID")
    user_id: int = Field(..., description="用户ID")
    agent_type: str = Field(..., description="Agent类型")
    action: str = Field(..., description="操作类型")
    status: str = Field(..., description="状态")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_ms: Optional[int] = Field(None, description="执行时长(毫秒)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True
