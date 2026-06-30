from app.agents.agents.permission_management_agent import create_permission_management_agent
from app.services.admin_agent_service.admin_log_service import AdminLogService

def test_permission_management_agent_user():
    """测试权限管理Agent - 用户管理"""
    # 创建日志服务
    log_service = AdminLogService()

    # 创建日志
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "permission_management",
        "query": "管理用户"
    })

    # 创建Agent（传入日志服务）
    agent = create_permission_management_agent(log_service)

    # 执行Agent
    result = agent.invoke({
        "query": "管理用户",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "用户管理" in result["result"]

    # 验证日志已更新
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_permission_management_agent_role():
    """测试权限管理Agent - 角色管理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "permission_management",
        "query": "管理角色"
    })

    agent = create_permission_management_agent(log_service)

    result = agent.invoke({
        "query": "管理角色",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "角色管理" in result["result"]

    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_permission_management_agent_permission():
    """测试权限管理Agent - 权限管理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "permission_management",
        "query": "管理权限"
    })

    agent = create_permission_management_agent(log_service)

    result = agent.invoke({
        "query": "管理权限",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "权限管理" in result["result"]

    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_permission_management_agent_unknown():
    """测试权限管理Agent - 未知操作"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "permission_management",
        "query": "未知操作"
    })

    agent = create_permission_management_agent(log_service)

    result = agent.invoke({
        "query": "未知操作",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "请指定操作类型" in result["result"]

    # 验证日志标记为失败
    log = log_service.get_log(task_id)
    assert log.status == "failed"
