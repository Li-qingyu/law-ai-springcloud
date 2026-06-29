"""
审查Agent
审查所有子Agent的执行结果，返回修改意见
"""
from typing import TypedDict, Annotated, Any, Dict, Optional
import operator
import logging
from langgraph.graph import StateGraph, END
from app.services.admin_log_service import AdminLogService
from app.services.review_service import ReviewService

logger = logging.getLogger(__name__)

class ReviewState(TypedDict):
    """审查Agent状态"""
    log_id: str
    result: str
    review_result: Any
    messages: Annotated[list, operator.add]

def create_review_node(log_service: Optional[AdminLogService] = None,
                       review_service: Optional[ReviewService] = None):
    """创建审查节点，支持依赖注入"""
    def review_execution(state: ReviewState) -> Dict[str, Any]:
        """审查执行结果"""
        logger.info(f"审查执行结果: {state['log_id']}")

        # 使用注入的服务或创建新实例
        nonlocal log_service, review_service
        if log_service is None:
            log_service = AdminLogService()
        if review_service is None:
            review_service = ReviewService()

        try:
            # 获取执行日志
            log = log_service.get_log(state["log_id"])

            if log is None:
                logger.error(f"日志不存在: {state['log_id']}")
                return {"review_result": None}

            # 审查执行结果
            review_result = review_service.review(log)

            # 记录审查日志
            log_service.update_log(state["log_id"], {
                "review_result": review_result.model_dump() if hasattr(review_result, 'model_dump') else review_result.dict(),
                "status": "reviewed"
            })

            logger.info(f"审查完成: {review_result.overall_assessment}")
            return {"review_result": review_result}

        except Exception as e:
            logger.error(f"审查过程异常: {e}")
            return {"review_result": None}

    return review_execution

def create_review_agent(log_service: Optional[AdminLogService] = None,
                        review_service: Optional[ReviewService] = None):
    """创建审查Agent"""
    workflow = StateGraph(ReviewState)

    # 添加节点
    workflow.add_node("review", create_review_node(log_service, review_service))

    # 设置入口
    workflow.set_entry_point("review")

    # 添加结束边
    workflow.add_edge("review", END)

    return workflow.compile()
