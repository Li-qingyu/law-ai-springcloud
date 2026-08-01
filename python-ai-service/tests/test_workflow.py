"""
端到端工作流测试
测试：用户请求 → 意图分类 → 权限检查 → 子Agent调用 → 结果
"""
import uuid
from app.agents.workflow import create_router_workflow, invoke_sub_agent
from app.services.admin_agent_service.admin_log_service import AdminLogService


def _run_workflow(query: str, user_role: str = "super_admin"):
    """通用测试执行器：路由 → 子Agent"""
    log_service = AdminLogService()
    user_id = 1

    # 第一阶段：路由
    router = create_router_workflow(log_service)
    route_result = router.invoke({
        "query": query,
        "user_id": user_id,
        "user_role": user_role,
        "task_params": {},
    })

    task_type = route_result.get("task_type", "")

    # 路由阶段已有结果（help / unknown / permission_denied）
    if route_result.get("result"):
        return route_result

    # 第二阶段：调用子Agent
    thread_id = f"test-{uuid.uuid4().hex[:8]}-{task_type}"
    log_id = route_result.get("log_id", "")
    task_params = route_result.get("task_params_parsed", {})
    router_context = {
        "operation": task_params.get("operation", ""),
        "data_type": task_params.get("data_type", ""),
        "confidence": route_result.get("confidence", 0.0),
    }

    sub_result = invoke_sub_agent(
        agent_type=task_type,
        query=query,
        user_id=user_id,
        log_id=log_id,
        thread_id=thread_id,
        router_context=router_context,
        log_service=log_service,
    )

    return {
        "task_type": task_type,
        "status": sub_result.get("status", ""),
        "result": sub_result.get("result", ""),
        "is_pending_confirm": sub_result.get("is_pending_confirm", False),
        "thread_id": sub_result.get("thread_id", ""),
    }


def test_query_article_485():
    """测试：查询民法典第485条（多步骤：先查书 → 再查条文）"""
    result = _run_workflow("查询民法典第四百八十五条")
    print(f"\n{'='*60}")
    print(f"[查询民法典第485条]")
    print(f"task_type: {result.get('task_type')}")
    print(f"status:    {result.get('status')}")
    print(f"result:    {result.get('result', '')[:500]}")
    print(f"{'='*60}")
    assert result is not None
    assert result.get("result")


def test_query_all_articles():
    """测试：查询所有法律条文"""
    result = _run_workflow("查询所有法律条文")
    print(f"\n{'='*60}")
    print(f"[查询所有法律条文]")
    print(f"task_type: {result.get('task_type')}")
    print(f"status:    {result.get('status')}")
    print(f"result:    {result.get('result', '')[:500]}")
    print(f"{'='*60}")
    assert result is not None
    assert result.get("result")


def test_count_cases():
    """测试：统计案例数量"""
    result = _run_workflow("统计法律案例有多少条")
    print(f"\n{'='*60}")
    print(f"[统计案例数量]")
    print(f"task_type: {result.get('task_type')}")
    print(f"status:    {result.get('status')}")
    print(f"result:    {result.get('result', '')[:500]}")
    print(f"{'='*60}")
    assert result is not None
    assert result.get("result")


def test_permission_denied():
    """测试：普通管理员尝试删除（应被权限拦截）"""
    result = _run_workflow("删除法律条文", user_role="admin")
    print(f"\n{'='*60}")
    print(f"[权限拒绝测试]")
    print(f"task_type: {result.get('task_type')}")
    print(f"status:    {result.get('status')}")
    print(f"result:    {result.get('result', '')[:300]}")
    print(f"{'='*60}")
    assert result.get("status") == "permission_denied"


def test_unknown_intent():
    """测试：无法识别的意图"""
    result = _run_workflow("今天天气怎么样")
    print(f"\n{'='*60}")
    print(f"[未知意图]")
    print(f"task_type: {result.get('task_type')}")
    print(f"status:    {result.get('status')}")
    print(f"result:    {result.get('result', '')[:300]}")
    print(f"{'='*60}")
    assert result.get("task_type") == "unknown"


if __name__ == "__main__":
    test_query_article_485()
    # test_query_all_articles()
    # test_count_cases()
    # test_permission_denied()
    # test_unknown_intent()
