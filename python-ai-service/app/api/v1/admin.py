from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.agents.workflow import create_workflow
from app.services.admin_log_service import AdminLogService

router = APIRouter(prefix="/admin", tags=["管理员"])

class AdminRequest(BaseModel):
    """管理员请求模型"""
    query: str
    user_id: int
    user_role: str
    task_params: Optional[Dict[str, Any]] = None

class AdminResponse(BaseModel):
    """管理员响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[Dict[str, Any]] = None

@router.post("/manage", response_model=AdminResponse)
async def manage(request: AdminRequest):
    """统一管理接口"""
    try:
        log_service = AdminLogService()
        workflow = create_workflow(request,log_service=log_service)

        result = workflow.invoke({
            "query": request.query,
            "user_id": request.user_id,
            "user_role": request.user_role,
            "task_params": request.task_params or {}
        })

        return AdminResponse(
            code=200,
            message="success",
            data={"result": result.get("result", "")}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
