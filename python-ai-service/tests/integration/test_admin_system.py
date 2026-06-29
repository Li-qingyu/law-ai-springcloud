"""
管理员系统集成测试
测试完整的工作流程
"""
from app.agents.admin_router_agent import create_admin_router_agent
from app.services.admin_log_service import AdminLogService

def test_full_workflow_file_management():
    """测试完整的文件管理工作流程"""
    # 创建日志服务
    log_service = AdminLogService()

    # 创建Agent
    agent = create_admin_router_agent(log_service)

    # 执行文件上传任务
    result = agent.invoke({
        "query": "上传文件 patent_data.xlsx",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    assert "result" in result
    assert "文件上传成功" in result["result"]

    # 验证日志记录
    logs = log_service.get_logs_by_user(123)
    assert len(logs) > 0

def test_full_workflow_log_management():
    """测试完整的日志管理工作流程"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "查询系统日志",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    assert "result" in result
    assert "系统日志" in result["result"]

def test_full_workflow_data_management():
    """测试完整的数据管理工作流程"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "管理专利数据",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    assert "result" in result
    assert "专利数据" in result["result"]

def test_full_workflow_permission_management():
    """测试完整的权限管理工作流程"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "管理用户",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    assert "result" in result
    assert "用户管理" in result["result"]

def test_full_workflow_permission_denied():
    """测试权限拒绝的工作流程"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    # 尝试执行无权限的任务
    result = agent.invoke({
        "query": "上传文件 patent_data.xlsx",
        "user_id": 123,
        "user_role": "log_admin"  # 日志管理员没有文件管理权限
    })

    assert result is not None
    assert "result" in result
    assert "权限不足" in result["result"]

    # 验证日志记录
    logs = log_service.get_logs_by_user(123)
    assert len(logs) > 0

    # 验证权限拒绝状态
    latest_log = logs[-1]
    assert latest_log.status == "permission_denied"

def test_multiple_tasks():
    """测试多个任务执行"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    # 执行多个任务
    tasks = [
        {"query": "上传文件 patent_data.xlsx", "user_id": 123, "user_role": "super_admin"},
        {"query": "查询系统日志", "user_id": 123, "user_role": "super_admin"},
        {"query": "管理专利数据", "user_id": 123, "user_role": "super_admin"},
        {"query": "管理用户", "user_id": 123, "user_role": "super_admin"}
    ]

    for task in tasks:
        result = agent.invoke(task)
        assert result is not None
        assert "result" in result

    # 验证日志记录
    logs = log_service.get_logs_by_user(123)
    assert len(logs) == 4
