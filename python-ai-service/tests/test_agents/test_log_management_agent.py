from app.agents.log_management_agent import create_log_management_agent
from app.services.admin_log_service import AdminLogService

def test_log_management_agent_system_log():
    """测试日志管理Agent - 系统日志查询"""
    # 创建日志服务
    log_service = AdminLogService()
    
    # 创建日志
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "log_management",
        "query": "查询系统日志"
    })
    
    # 创建Agent（传入日志服务）
    agent = create_log_management_agent(log_service)
    
    # 执行Agent
    result = agent.invoke({
        "query": "查询系统日志",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "系统日志" in result["result"]
    
    # 验证日志已更新
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_log_management_agent_user_log():
    """测试日志管理Agent - 用户操作日志查询"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "log_management",
        "query": "查询用户操作日志"
    })
    
    agent = create_log_management_agent(log_service)
    
    result = agent.invoke({
        "query": "查询用户操作日志",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "用户操作日志" in result["result"]
    
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_log_management_agent_api_log():
    """测试日志管理Agent - API调用日志查询"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "log_management",
        "query": "查询API调用日志"
    })
    
    agent = create_log_management_agent(log_service)
    
    result = agent.invoke({
        "query": "查询API调用日志",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "API调用日志" in result["result"]
    
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_log_management_agent_analysis():
    """测试日志管理Agent - 统计分析"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "log_management",
        "query": "统计分析日志"
    })
    
    agent = create_log_management_agent(log_service)
    
    result = agent.invoke({
        "query": "统计分析日志",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "统计分析" in result["result"]
    
    log = log_service.get_log(task_id)
    assert log.status == "success"
