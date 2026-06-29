from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ReviewIssue(BaseModel):
    """审查问题模型"""
    type: str = Field(..., description="问题类型")
    description: str = Field(..., description="问题描述")
    severity: str = Field(..., description="严重程度")
    suggestion: str = Field(..., description="修改建议")

class ReviewResult(BaseModel):
    """审查结果模型"""
    id: Optional[int] = None
    task_id: str = Field(..., description="任务ID")
    agent_type: str = Field(..., description="Agent类型")
    issues: List[ReviewIssue] = Field(default_factory=list, description="问题列表")
    overall_assessment: str = Field(..., description="整体评估")
    requires_manual_review: bool = Field(False, description="是否需要人工审查")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    model_config = ConfigDict(from_attributes=True)
