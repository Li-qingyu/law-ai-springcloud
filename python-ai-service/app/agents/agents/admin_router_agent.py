"""
管理端路由Agent
基于LLM的智能路由，集成意图识别和权限检查
"""
import logging
from typing import Any, Dict, Optional

from langgraph.graph import END

from app.agents.state.AdminRouterState import AdminRouterState
from app.services.admin_agent_service.admin_log_service import AdminLogService
from app.services.admin_agent_service.intent_classifier import IntentClassifier, IntentType
from app.services.admin_agent_service.permission_checker import PermissionChecker

logger = logging.getLogger(__name__)

# 全局实例
_intent_classifier: Optional[IntentClassifier] = None
_permission_checker: Optional[PermissionChecker] = None


def _create_llm():
    """创建LLM模型用于意图识别"""
    try:
        from langchain_deepseek import ChatDeepSeek
        from app.core.config import get_settings
        settings = get_settings()
        return ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE_URL,
        )
    except Exception as e:
        logger.warning(f"创建LLM失败，意图识别将仅使用规则: {e}")
        return None


def _get_intent_classifier() -> IntentClassifier:
    """获取意图识别器单例"""
    global _intent_classifier
    if _intent_classifier is None:
        llm = _create_llm()
        _intent_classifier = IntentClassifier(llm_service=llm)
    return _intent_classifier


def _get_permission_checker() -> PermissionChecker:
    """获取权限检查器单例"""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker


def _ensure_log_service(log_service: Optional[AdminLogService]) -> AdminLogService:
    """确保日志服务实例存在"""
    if log_service is None:
        return AdminLogService()
    return log_service


def create_classify_node(log_service: Optional[AdminLogService] = None):
    """
    创建分类节点

    使用规则+LLM混合意图识别，提取意图和实体
    """
    # 在闭包外层初始化日志服务
    _log_service = _ensure_log_service(log_service)

    def classify_admin_task(state: AdminRouterState) -> Dict[str, Any]:
        """分类管理任务"""
        query = state["query"]
        user_id = state.get("user_id", 0)
        user_role = state.get("user_role", "")

        logger.info(f"开始分类任务: query={query[:50]}, user_id={user_id}, role={user_role}")

        # 使用意图识别器
        classifier = _get_intent_classifier()
        intent_result = classifier.classify(query)

        task_type = intent_result.intent.value
        confidence = intent_result.confidence
        entities = intent_result.entities

        # 处理 help 意图
        if task_type == "help":
            from app.agents.prompts.router_prompt import HELP_PROMPT
            log_id = _log_service.create_log({
                "task_type": "help",
                "query": query,
                "user_id": user_id,
                "user_role": user_role,
            })
            _log_service.update_log(log_id, {
                "status": "success",
                "result": HELP_PROMPT,
            })
            return {
                "task_type": "help",
                "intent": "help",
                "confidence": 1.0,
                "task_params_parsed": {},
                "log_id": log_id,
                "result": HELP_PROMPT,
                "status": "success",
            }

        # 处理 unknown 意图
        if task_type == "unknown":
            log_id = _log_service.create_log({
                "task_type": "unknown",
                "query": query,
                "user_id": user_id,
                "user_role": user_role,
            })
            error_msg = "抱歉，我无法理解您的指令。请输入'帮助'查看支持的操作。"
            _log_service.update_log(log_id, {
                "status": "failed",
                "error": error_msg,
            })
            return {
                "task_type": "unknown",
                "intent": "unknown",
                "confidence": confidence,
                "task_params_parsed": {},
                "log_id": log_id,
                "result": error_msg,
                "status": "failed",
            }

        # 记录日志
        log_id = _log_service.create_log({
            "task_type": task_type,
            "query": query,
            "user_id": user_id,
            "user_role": user_role,
        })

        logger.info(f"任务分类完成: task_type={task_type}, confidence={confidence}, log_id={log_id}")

        return {
            "task_type": task_type,
            "intent": task_type,
            "confidence": confidence,
            "task_params_parsed": entities,
            "log_id": log_id,
            "status": "running",
        }

    return classify_admin_task


def create_check_permission_node(log_service: Optional[AdminLogService] = None):
    """
    创建权限检查节点

    根据用户角色和任务类型检查权限
    """
    # 在闭包外层初始化日志服务
    _log_service = _ensure_log_service(log_service)

    def check_permission(state: AdminRouterState) -> Dict[str, Any]:
        """检查权限"""
        user_role = state.get("user_role", "")
        task_type = state.get("task_type", "")
        log_id = state.get("log_id", "")

        logger.info(f"权限检查: role={user_role}, task_type={task_type}")

        # 如果已经是终态（help/unknown），跳过权限检查
        if state.get("result"):
            return {}

        # 权限检查
        checker = _get_permission_checker()
        has_permission = checker.check(user_role, task_type)

        if not has_permission:
            error_msg = f"权限不足：您的角色 [{user_role}] 无权执行 [{task_type}] 类型的操作"

            _log_service.update_log(log_id, {
                "status": "permission_denied",
                "error": error_msg,
            })

            logger.warning(f"权限检查失败: {error_msg}")

            return {
                "result": error_msg,
                "status": "permission_denied",
                "error": error_msg,
            }

        logger.info(f"权限检查通过: role={user_role}, task_type={task_type}")
        return {}

    return check_permission


def route_to_sub_agent(state: AdminRouterState) -> str:
    """
    路由到子Agent

    根据任务类型和状态决定路由目标
    """
    # 如果已有结果（help/unknown/permission_denied），直接结束
    if state.get("result"):
        return END

    task_type = state.get("task_type", "")

    # 路由映射
    route_map = {
        "file_management": "file_management",
        "log_management": "log_management",
        "data_management": "data_management",
        "permission_management": "permission_management",
    }

    target = route_map.get(task_type)
    if target:
        logger.info(f"路由到子Agent: {target}")
        return target

    logger.warning(f"未知任务类型，路由结束: {task_type}")
    return END

if __name__ == '__main__':

    def test_classify(query: str, user_role: str = "super_admin"):
        """测试单条查询的分类+权限+路由全流程"""
        state = AdminRouterState(
            query=query,
            user_id=123,
            user_role=user_role,
            session_id="test_session",
            task_params={},
            intent="",
            confidence=0.0,
            task_type="",
            task_params_parsed={},
            log_id="",
            messages=[],
            result="",
            status="",
            error="",
        )

        classify_node = create_classify_node()
        result1 = classify_node(state)
        state.update(result1)
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"分类结果: task_type={result1.get('task_type')}, confidence={result1.get('confidence')}")

        check_node = create_check_permission_node()
        result2 = check_node(state)
        state.update(result2)
        print(f"权限结果: status={state.get('status')}")

        target = route_to_sub_agent(state)
        print(f"路由目标: {target}")
        print(f"{'='*60}")

    # ---- 测试用例 ----

    # 1. 规则能直接命中的
    #test_classify("上传合同文件")
    #test_classify("查询所有法律条文")
    #test_classify("帮助")

    # 2. 需要 LLM 兜底的模糊查询（规则置信度 < 0.8）
    #test_classify("我想看看系统里有哪些资料")
    test_classify("把之前的那个东西删掉")
    #test_classify("帮我整理一下数据")

    # 3. 权限不足的场景
    #test_classify("删除用户权限", user_role="admin")





