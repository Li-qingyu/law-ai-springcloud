from app.agents.agents.admin_router_agent import create_admin_router_agent
from app.services.admin_log_service import AdminLogService

def test_admin_router_agent_file_management():
    """测试统一入口Agent路由到文件管理"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "上传文件 patent_data.xlsx",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    assert "result" in result
    assert "文件上传成功" in result["result"]

def test_admin_router_agent_log_management():
    """测试统一入口Agent路由到日志管理"""
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

def test_admin_router_agent_data_management():
    """测试统一入口Agent路由到数据管理"""
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

def test_admin_router_agent_permission_management():
    """测试统一入口Agent路由到权限管理"""
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

def test_admin_router_agent_permission_denied():
    """测试统一入口Agent权限拒绝"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "上传文件 patent_data.xlsx",
        "user_id": 123,
        "user_role": "log_admin"  # 日志管理员没有文件管理权限
    })

    assert result is not None
    assert "result" in result
    assert "权限不足" in result["result"]

def test_admin_router_agent_unknown_task():
    """测试统一入口Agent未知任务"""
    log_service = AdminLogService()
    agent = create_admin_router_agent(log_service)

    result = agent.invoke({
        "query": "未知任务",
        "user_id": 123,
        "user_role": "super_admin"
    })

    assert result is not None
    # 未知任务会被路由到 END，result 可能为空
