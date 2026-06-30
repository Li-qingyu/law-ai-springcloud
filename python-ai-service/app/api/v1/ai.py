from fastapi import  APIRouter
from fastapi.responses import StreamingResponse
from app.models.request import AiConsultRequest
from app.models.response import ClientState
from app.repositories.milvus_client import init_milvus
from app.services.rag_agent_service.agent_service import consult, consult_stream
from app.services.rag_agent_service.semantic_cache import SemanticCache
import logging

# 创建路由器
router =APIRouter(
    prefix="/v1/ai",
    tags=["AI Consult"],
    responses={404: {"description": "Not found"}}
)
_milvus_initialized = False
def ensure_milvus_ready():
    """确保 Milvus 已初始化（全局只初始化一次）"""
    global _milvus_initialized
    if not _milvus_initialized:
        try:
            init_milvus()
            _milvus_initialized = True
            logging.info("✓ Milvus 连接成功")
        except Exception as e:
            logging.error(f"Milvus 初始化失败: {e}")
            raise


@router.post("/consult")
async def ai_consult(request: AiConsultRequest)-> ClientState:
    logging.info(f"获取AI咨询请求: {request}")
    # 首先初始化 Milvus 连接
    logging.info("正在初始化 Milvus 连接...")
    try:
        ensure_milvus_ready()
        logging.info("✓ Milvus 连接成功")
        result = await consult(request)
        return ClientState(status="success", message="成功获取AI咨询结果", data=result)

    except Exception as e:
        logging.error(f"Milvus 连接失败: {e}")
        return ClientState(status="error", message="Milvus 连接失败", data=None)


@router.post("/consult/stream")
async def ai_consult_stream(request: AiConsultRequest):
    """流式 AI 咨询接口，返回 SSE 事件流"""
    logging.info(f"获取流式AI咨询请求: {request}")
    try:
        ensure_milvus_ready()
        logging.info("✓ Milvus 连接成功（流式模式）")
    except Exception as e:
        logging.error(f"Milvus 连接失败: {e}")
        async def error_stream():
            import json
            error_event = json.dumps({"type": "error", "message": "Milvus 连接失败"}, ensure_ascii=False)
            yield f"data: {error_event}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    return StreamingResponse(
        consult_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )



@router.get("/health")
async def health():
    # 检查服务是否正常
    return {"status": "ok"}


@router.post("/cache/cleanup")
async def cache_cleanup():
    """手动触发语义缓存过期清理"""
    try:
        ensure_milvus_ready()
        cache = SemanticCache()
        deleted = cache.cleanup_expired()
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        logging.error(f"缓存清理失败: {e}")
        return {"status": "error", "message": str(e), "deleted": 0}