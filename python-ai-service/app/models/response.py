from typing import Optional, List,Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DataCardType(str, Enum):
    """数据卡片类型枚举"""

    LAW_ARTICLE = "law_article"
    LAW_CASE = "law_case"
    CONSULT_HISTORY = "consult_history"


class LawArticleDataCard(BaseModel):
    """法律条文数据卡片"""

    type: Literal["law_article"] = Field(
        "law_article",
        description="数据类型：法律条文"
    )

    id: int = Field(
        ...,
        description="法律条文ID（对应MySQL表主键）",
        examples=[456]
    )

    book_id: Optional[int] = Field(
        None,
        description="法律书籍ID",
        examples=[123]
    )

    article_title: str = Field(
        ...,
        description="条文标题",
        examples=["中华人民共和国劳动合同法第四十六条"]
    )

    content: str = Field(
        ...,
        description="条文内容摘要",
        examples=["用人单位解除劳动合同的经济补偿规定"]
    )

    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="相关度评分（0-1）",
        examples=[0.92]
    )

    detail_url: Optional[str] = Field(
        None,
        description="详情页URL（前端生成）"
    )


class LawCaseDataCard(BaseModel):
    """法律案例数据卡片"""

    type: Literal["law_case"] = Field(
        "law_case",
        description="数据类型：法律案例"
    )

    id: int = Field(
        ...,
        description="案例ID（对应MySQL表主键）",
        examples=[789]
    )

    title: str = Field(
        ...,
        description="案例标题",
        examples=["张某与某公司劳动争议案"]
    )

    type_id: Optional[int] = Field(
        None,
        description="案例类型ID",
        examples=[1]
    )

    tags: Optional[str] = Field(
        None,
        description="案例标签",
        examples=["劳动争议 合同"]
    )

    content: str = Field(
        ...,
        description="案例摘要",
        examples=["关于违法解除劳动合同赔偿金的典型案例"]
    )

    judgment: Optional[str] = Field(
        None,
        description="判决结果",
        examples=["法院判决公司支付赔偿金XX元"]
    )

    cover: Optional[str] = Field(
        None,
        description="封面图片URL",
        examples=["https://example.com/judgment.pdf"]
    )

    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="相关度评分（0-1）",
        examples=[0.85]
    )

    detail_url: Optional[str] = Field(
        None,
        description="详情页URL（前端生成）"
    )


class ConsultHistoryDataCard(BaseModel):
    """咨询历史数据卡片"""

    type: Literal["consult_history"] = Field(
        "consult_history",
        description="数据类型：咨询历史"
    )

    id: int = Field(
        ...,
        description="咨询记录ID（对应MySQL表主键）",
        examples=[123]
    )

    user_id: Optional[int] = Field(
        None,
        description="用户ID",
        examples=[123]
    )

    session_id: Optional[str] = Field(
        None,
        description="会话ID",
        examples=["uuid-generated-by-frontend"]
    )

    question: str = Field(
        ...,
        description="历史问题",
        examples=["劳动合同解除需要赔偿吗？"]
    )

    answer: str = Field(
        ...,
        description="历史答案",
        examples=["根据《劳动合同法》第46条规定..."]
    )

    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="相关度评分（0-1）",
        examples=[0.75]
    )

    detail_url: Optional[str] = Field(
        None,
        description="详情页URL（前端生成）"
    )


DataCard = LawArticleDataCard | LawCaseDataCard | ConsultHistoryDataCard


class AiConsultResponse(BaseModel):
    """AI法律咨询响应模型（Python → Java）"""

    answer: str = Field(
        ...,
        description="AI生成的答案（Markdown格式）",
        examples=["根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同..."]
    )

    data_cards: List[DataCard] = Field(
        default_factory=list,
        description="相关数据卡片列表"
    )

    session_id: str = Field(
        ...,
        description="会话ID（原样返回）",
        examples=["uuid-generated-by-frontend"]
    )

    turn_number: int = Field(
        ...,
        description="当前轮次（Java计算）",
        examples=[3]
    )

    processing_time_ms: Optional[int] = Field(
        None,
        description="处理耗时（毫秒）",
        examples=[1250]
    )
    user_id: Optional[int] = Field(
        None,
        title="用户ID",
        description="用户ID（Java传递）",
        examples=[1],
    )


    class Config:
        json_schema_extra = {
            "example": {
                "answer": "根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同...",
                "data_cards": [
                    {
                        "type": "law_article",
                        "id": 456,
                        "book_id": 123,
                        "article_title": "中华人民共和国劳动合同法第四十六条",
                        "content": "用人单位解除劳动合同的经济补偿规定",
                        "relevance": 0.92,
                        "detail_url": None
                    },
                    {
                        "type": "law_case",
                        "id": 789,
                        "title": "张某与某公司劳动争议案",
                        "type_id": 1,
                        "tags": "劳动争议 合同",
                        "content": "关于违法解除劳动合同赔偿金的典型案例",
                        "judgment": "法院判决公司支付赔偿金",
                        "cover": "https://example.com/judgment.pdf",
                        "relevance": 0.85,
                        "detail_url": None
                    }
                ],
                "session_id": "uuid-generated-by-frontend",
                "turn_number": 3,
                "processing_time_ms": 1250,
                "user_id": 1
            }
        }


class ClientState(BaseModel):
    """本次连接客户端状态"""

    status: str = Field(
        ...,
        description="状态码：success/error/warning",
        examples=["success"]
    )

    data: Optional[AiConsultResponse] = Field(
        None,
        description="业务数据"
    )

    message: str = Field(
        ...,
        description="状态描述信息",
        examples=["操作成功"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "session_id": "uuid-generated-by-frontend",
                    "turn_number": 3
                },
                "message": "操作成功"
            }
        }


class StreamTokenResponse(BaseModel):
    """流式响应Token片段"""

    type: str = Field(
        "token",
        description="消息类型：token（文本片段）"
    )

    content: str = Field(
        ...,
        description="文本内容片段"
    )

    timestamp: Optional[float] = Field(
        None,
        description="时间戳"
    )


class StreamCompleteResponse(BaseModel):
    """流式响应完成消息"""

    type: str = Field(
        "complete",
        description="消息类型：complete（完成）"
    )

    session_id: str = Field(
        ...,
        description="会话ID"
    )

    turn_number: int = Field(
        ...,
        description="当前对话轮次"
    )

    data_cards: List[DataCard] = Field(
        default_factory=list,
        description="相关数据卡片列表"
    )

    total_tokens: Optional[int] = Field(
        None,
        description="总Token数"
    )

    processing_time_ms: Optional[int] = Field(
        None,
        description="总处理耗时（毫秒）"
    )


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error_code: str = Field(
        ...,
        description="错误代码",
        examples=["INVALID_REQUEST", "SERVICE_UNAVAILABLE", "LLM_API_ERROR"]
    )

    error_message: str = Field(
        ...,
        description="错误描述",
        examples=["问题内容不能为空", "LLM服务暂时不可用"]
    )

    request_id: Optional[str] = Field(
        None,
        description="请求ID（用于追踪）",
        examples=["req_xyz789"]
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="错误发生时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_REQUEST",
                "error_message": "问题内容不能为空",
                "request_id": "req_abc123",
                "timestamp": "2026-04-17T10:30:00Z"
            }
        }

class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""

    status: str = Field(
        ...,
        description="服务状态",
        examples=["ok", "degraded", "unhealthy"]
    )

    version: str = Field(
        ...,
        description="服务版本",
        examples=["0.1.0"]
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="检查时间"
    )

    services: Optional[dict] = Field(
        None,
        description="依赖服务状态",
        examples=[{
            "milvus": "connected",
            "redis": "connected",
            "llm": "available"
        }]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "timestamp": "2026-04-17T10:30:00Z",
                "services": {
                    "milvus": "connected",
                    "redis": "connected",
                    "llm": "available"
                }
            }
        }