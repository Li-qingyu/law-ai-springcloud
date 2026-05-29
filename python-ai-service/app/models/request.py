from typing import Optional,List,Literal
from pydantic import BaseModel,Field,ConfigDict
from datetime import  datetime

class ConversationHistoryMessage(BaseModel):
    """
    对话消息格式
    """

    role :Literal["user", "assistant"]= Field(
        title="角色",
        description="对话历史角色：user:assistant",
        examples=["user","assistant"],
    )
    content :str = Field(
        title="内容",
        description="对话内容",
        examples=["你好"],
    )
    timestamp :Optional[datetime]= Field(
        None,
        description="时间戳",
        examples=["2026-04-16T10:30:00Z"],
    )

class AiConsultRequest(BaseModel):
    """
    AI咨询请求（java）
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "能再给出我详细一点的解决？",
                "turn_number": 2,
                "session_id": "lease-dispute-001",
                "user_id": 456,
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "我租的房子合同还没到期，房东说要卖房让我提前搬走，还以'卫生没打扫干净'为由扣了我全部押金。这合法吗？",
                        "timestamp": "2026-04-18T09:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "根据《民法典》第725条'买卖不破租赁'原则，房东卖房不影响你的租赁合同效力，他无权强制你提前搬离。至于押金，如果合同未明确约定'卫生标准'作为扣款条件，且你已尽到一般清洁义务，房东无权全额扣押。建议你先保留租赁合同、押金收据、房屋交接时的照片/视频等证据。",
                        "timestamp": "2026-04-18T09:00:08Z"
                    }
                ]
            }
        }
    )
    question:str = Field(
        title="问题",
        min_length=1,
        max_length=5000,
        description="用户当前问题",
        examples=["你好"],
    )
    session_id:str = Field(
        title="会话ID",
        min_length=1,
        description="会话ID",
        examples=["uuid-generated-by-frontend"],
    )
    user_id:Optional[int]= Field(
        None,
        title="用户ID",
        description="用户ID（Java传递）",
        examples=[1],
    )
    conversation_history:Optional[List[ConversationHistoryMessage]]= Field(
        None,
        title="对话历史",
        description="最近5轮对话历史（Java组装）",
        examples=[
            [
                {"role": "user", "content": "劳动合同解除需要赔偿吗？","timestamp": "2026-04-16T10:30:00Z"},
                {"role": "assistant", "content": "根据《劳动合同法》第46条...","timestamp": "2026-04-16T10:30:05Z"}
            ]
        ]
    )

