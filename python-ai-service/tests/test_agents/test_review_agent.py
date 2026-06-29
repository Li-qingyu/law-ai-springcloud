from app.agents.review_agent import create_review_agent
from app.services.admin_log_service import AdminLogService

def test_review_agent_success():
    """测试审查Agent - 成功案例"""
    # 创建日志服务
    log_service = AdminLogService()

    # 创建日志
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "file_management",
        "query": "上传文件"
    })

    # 更新日志为成功状态
    log_service.update_log(task_id, {
        "status": "success",
        "result": "文件上传成功"
    })

    # 创建Agent（传入日志服务）
    agent = create_review_agent(log_service=log_service)

    # 执行Agent
    result = agent.invoke({
        "log_id": task_id,
        "result": "文件上传成功"
    })

    assert result is not None
    assert "review_result" in result

    # 验证审查结果
    review_result = result["review_result"]
    assert review_result is not None
    assert review_result.task_id == task_id
    assert review_result.overall_assessment == "执行成功"
    assert len(review_result.issues) == 0

def test_review_agent_failure():
    """测试审查Agent - 失败案例"""
    log_service = AdminLogService()

    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "file_management",
        "query": "上传文件"
    })

    # 更新日志为失败状态
    log_service.update_log(task_id, {
        "status": "failed",
        "error": "文件格式不支持"
    })

    agent = create_review_agent(log_service=log_service)

    result = agent.invoke({
        "log_id": task_id,
        "result": "文件格式不支持"
    })

    assert result is not None
    assert "review_result" in result

    review_result = result["review_result"]
    assert review_result is not None
    assert review_result.task_id == task_id
    assert "执行失败" in review_result.overall_assessment
    assert review_result.requires_manual_review is True

def test_review_agent_nonexistent_log():
    """测试审查Agent - 日志不存在"""
    log_service = AdminLogService()

    agent = create_review_agent(log_service=log_service)

    result = agent.invoke({
        "log_id": "nonexistent_task",
        "result": "测试"
    })

    assert result is not None
    assert "review_result" in result
    assert result["review_result"] is None
