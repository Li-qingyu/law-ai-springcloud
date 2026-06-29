from app.services.review_service import ReviewService
from app.models.admin_log import AdminLog
from datetime import datetime

def test_review_success_log():
    """测试审查成功日志"""
    service = ReviewService()

    log = AdminLog(
        task_id="task_123",
        user_id=123,
        agent_type="file_management",
        action="execute",
        status="success",
        input_data={"query": "上传文件"},
        output_data={"result": "文件上传成功"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    result = service.review(log)

    assert result is not None
    assert result.task_id == "task_123"
    assert result.overall_assessment == "执行成功"
    assert len(result.issues) == 0
    assert result.requires_manual_review is False

def test_review_failed_log():
    """测试审查失败日志"""
    service = ReviewService()

    log = AdminLog(
        task_id="task_456",
        user_id=123,
        agent_type="file_management",
        action="execute",
        status="failed",
        input_data={"query": "上传文件"},
        error_message="文件格式不支持",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    result = service.review(log)

    assert result is not None
    assert result.task_id == "task_456"
    assert "执行失败" in result.overall_assessment
    assert len(result.issues) > 0
    assert result.requires_manual_review is True

def test_review_performance_issue():
    """测试审查性能问题"""
    service = ReviewService()

    log = AdminLog(
        task_id="task_789",
        user_id=123,
        agent_type="file_management",
        action="execute",
        status="success",
        input_data={"query": "上传文件"},
        output_data={"result": "文件上传成功"},
        duration_ms=10000,  # 10秒，超过5秒阈值
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    result = service.review(log)

    assert result is not None
    assert "执行完成，但存在问题" in result.overall_assessment
    assert any(issue.type == "performance_issue" for issue in result.issues)
    assert result.requires_manual_review is False

def test_review_missing_output():
    """测试审查缺少输出"""
    service = ReviewService()

    log = AdminLog(
        task_id="task_101",
        user_id=123,
        agent_type="file_management",
        action="execute",
        status="success",
        input_data={"query": "上传文件"},
        output_data=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    result = service.review(log)

    assert result is not None
    assert any(issue.type == "missing_output" for issue in result.issues)
