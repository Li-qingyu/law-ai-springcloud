from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.agents.admin_router_agent import create_admin_router_agent
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
        agent = create_admin_router_agent(log_service)

        result = agent.invoke({
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

@router.post("/file/upload", response_model=AdminResponse)
async def upload_file(request: AdminRequest):
    """文件上传"""
    try:
        log_service = AdminLogService()
        agent = create_admin_router_agent(log_service)

        result = agent.invoke({
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

@router.post("/logs/query", response_model=AdminResponse)
async def query_logs(request: AdminRequest):
    """日志查询"""
    try:
        log_service = AdminLogService()
        agent = create_admin_router_agent(log_service)

        result = agent.invoke({
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

@router.post("/data/manage", response_model=AdminResponse)
async def manage_data(request: AdminRequest):
    """数据管理"""
    try:
        log_service = AdminLogService()
        agent = create_admin_router_agent(log_service)

        result = agent.invoke({
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

@router.post("/permission/manage", response_model=AdminResponse)
async def manage_permission(request: AdminRequest):
    """权限管理"""
    try:
        log_service = AdminLogService()
        agent = create_admin_router_agent(log_service)

        result = agent.invoke({
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
