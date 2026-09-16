from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio
import logging
import uuid

from app.agents.workflow import (
    create_router_workflow,
    invoke_sub_agent,
    resume_sub_agent,
)
from app.services.admin_agent_service.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理员"])

class AdminRequest(BaseModel):
    """管理员请求模型"""
    query: str
    user_id: int
    user_role: str
    session_id: Optional[str] = None
    task_params: Optional[Dict[str, Any]] = None

class AdminConfirmRequest(BaseModel):
    """删除确认/追问补充请求模型"""
    thread_id: str
    agent_type: str
    answer: str  # "yes" / "no" 或用户补充的信息
    user_id: int
    user_role: str

class AdminStreamRequest(BaseModel):
    """管理员流式请求模型"""
    query: str
    user_id: int
    user_role: str
    session_id: Optional[str] = None
    task_params: Optional[Dict[str, Any]] = None

class AdminResponse(BaseModel):
    """管理员响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[Dict[str, Any]] = None

def _send_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """格式化SSE事件"""
    event_data = {"type": event_type, **data}
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@router.post("/manage", response_model=AdminResponse)
async def manage(request: AdminRequest):
    """
    统一管理接口 — 两阶段调用模式。

    流程：
    1. 路由工作流：意图分类 + 权限检查 → 得到 task_type
    2. 直接调用子Agent（单例，带 checkpointer）
    3. 如果子Agent interrupt → 返回 pending_confirm 状态 + thread_id
    4. 前端收到 pending_confirm 后调用 /admin/manage/confirm 恢复
    """
    try:
        log_service = AdminLogService()

        # ── 第一阶段：路由 ──
        router_workflow = create_router_workflow(log_service)
        route_result = router_workflow.invoke({
            "query": request.query,
            "user_id": request.user_id,
            "user_role": request.user_role,
            "task_params": request.task_params or {},
        })

        task_type = route_result.get("task_type", "")
        status = route_result.get("status", "")

        # 路由阶段已有结果（help / unknown / permission_denied）→ 直接返回
        if route_result.get("result"):
            return AdminResponse(
                code=200 if status == "success" else 403,
                message=status,
                data={
                    "result": route_result["result"],
                    "task_type": task_type,
                    "status": status,
                },
            )

        # ── 第二阶段：调用子Agent ──
        thread_id = f"{request.session_id or 'session'}-{task_type}-{uuid.uuid4().hex[:8]}"
        log_id = route_result.get("log_id", "")

        task_params = route_result.get("task_params_parsed", {})
        router_context = {
            "operation": task_params.get("operation", ""),
            "data_type": task_params.get("data_type", ""),
            "confidence": route_result.get("confidence", 0.0),
        }

        sub_result = invoke_sub_agent(
            agent_type=task_type,
            query=request.query,
            user_id=request.user_id,
            log_id=log_id,
            thread_id=thread_id,
            router_context=router_context,
            log_service=log_service,
            user_role=request.user_role,
        )

        # ── 子Agent返回结果 ──
        if sub_result.get("is_pending_confirm"):
            # 需要用户响应（追问补充信息 / 删除确认）
            return AdminResponse(
                code=200,
                message="pending_confirm",
                data={
                    "result": sub_result.get("confirm_question", "请确认操作"),
                    "task_type": task_type,
                    "status": "pending_confirm",
                    "confirm_type": sub_result.get("confirm_type", "confirm"),
                    "thread_id": sub_result["thread_id"],
                    "agent_type": task_type,
                },
            )

        return AdminResponse(
            code=200,
            message="success",
            data={
                "result": sub_result.get("result", ""),
                "task_type": task_type,
                "status": sub_result.get("status", "success"),
            },
        )
    except Exception as e:
        logger.error(f"管理请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage/confirm", response_model=AdminResponse)
async def manage_confirm(request: AdminConfirmRequest):
    """
    删除操作确认接口 — 恢复被 interrupt 暂停的子Agent。

    前端收到 pending_confirm 状态后，弹窗让用户确认，
    用户操作后调用此接口传入 thread_id + answer 恢复执行。
    """
    try:
        log_service = AdminLogService()

        result = resume_sub_agent(
            agent_type=request.agent_type,
            thread_id=request.thread_id,
            user_answer=request.answer,
            log_service=log_service,
        )

        return AdminResponse(
            code=200,
            message="success",
            data={
                "result": result.get("result", ""),
                "status": result.get("status", "success"),
            },
        )
    except Exception as e:
        logger.error(f"确认操作失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage/stream")
async def manage_stream(request: AdminStreamRequest):
    """统一管理接口（流式SSE）— 兼容旧接口"""
    logger.info(f"流式管理请求: query={request.query}, user_id={request.user_id}")

    async def event_generator():
        try:
            yield _send_sse_event("status", {"content": "正在分析您的请求..."})

            log_service = AdminLogService()

            yield _send_sse_event("progress", {"step": "classify", "detail": "正在识别意图..."})

            # 路由
            router_workflow = create_router_workflow(log_service)
            loop = asyncio.get_event_loop()
            route_result = await loop.run_in_executor(
                None,
                lambda: router_workflow.invoke({
                    "query": request.query,
                    "user_id": request.user_id,
                    "user_role": request.user_role,
                    "task_params": request.task_params or {},
                }),
            )

            task_type = route_result.get("task_type", "unknown")

            # 路由阶段已有结果（help / unknown / permission_denied）
            if route_result.get("result"):
                result_text = route_result["result"]
                status = route_result.get("status", "success")
                yield _send_sse_event("complete", {
                    "answer": result_text,
                    "task_type": task_type,
                    "status": status,
                    "log_id": route_result.get("log_id", ""),
                })
                return

            yield _send_sse_event("progress", {
                "step": "execute",
                "detail": f"正在执行 {task_type} 任务...",
            })

            # 调用子Agent
            thread_id = f"{request.session_id or 'session'}-{task_type}-{uuid.uuid4().hex[:8]}"
            log_id = route_result.get("log_id", "")
            task_params = route_result.get("task_params_parsed", {})
            router_context = {
                "operation": task_params.get("operation", ""),
                "data_type": task_params.get("data_type", ""),
                "confidence": route_result.get("confidence", 0.0),
            }

            sub_result = await loop.run_in_executor(
                None,
                lambda: invoke_sub_agent(
                    agent_type=task_type,
                    query=request.query,
                    user_id=request.user_id,
                    log_id=log_id,
                    thread_id=thread_id,
                    router_context=router_context,
                    log_service=log_service,
                    user_role=request.user_role,
                ),
            )

            # 需要确认
            if sub_result.get("is_pending_confirm"):
                yield _send_sse_event("confirm", {
                    "confirm_type": sub_result.get("confirm_type", "confirm"),
                    "message": sub_result.get("confirm_question", "请确认操作"),
                    "thread_id": sub_result["thread_id"],
                    "agent_type": task_type,
                })
                return

            result_text = sub_result.get("result", "")
            status = sub_result.get("status", "success")

            # 流式输出结果
            if result_text:
                chunk_size = 20
                for i in range(0, len(result_text), chunk_size):
                    chunk = result_text[i:i + chunk_size]
                    yield _send_sse_event("token", {"content": chunk})
                    await asyncio.sleep(0.02)

            yield _send_sse_event("complete", {
                "answer": result_text,
                "task_type": task_type,
                "status": status,
                "log_id": log_id,
            })

        except Exception as e:
            logger.error(f"流式管理请求失败: {e}", exc_info=True)
            yield _send_sse_event("error", {"message": f"处理失败: {str(e)}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
