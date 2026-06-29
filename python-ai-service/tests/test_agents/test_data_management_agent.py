from app.agents.data_management_agent import create_data_management_agent
from app.services.admin_log_service import AdminLogService

def test_data_management_agent_patent():
    """测试数据管理Agent - 专利数据管理"""
    # 创建日志服务
    log_service = AdminLogService()

    # 创建日志
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "管理专利数据"
    })

    # 创建Agent（传入日志服务）
    agent = create_data_management_agent(log_service)

    # 执行Agent
    result = agent.invoke({
        "query": "管理专利数据",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "专利数据" in result["result"]

    # 验证日志已更新
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_data_management_agent_company():
    """测试数据管理Agent - 公司数据管理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "管理公司数据"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "管理公司数据",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "公司数据" in result["result"]

    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_data_management_agent_lawsuit():
    """测试数据管理Agent - 诉讼数据管理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "管理诉讼数据"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "管理诉讼数据",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "诉讼数据" in result["result"]

    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_data_management_agent_law():
    """测试数据管理Agent - 法律数据管理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "管理法律数据"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "管理法律数据",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "法律数据" in result["result"]

    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_data_management_agent_unknown():
    """测试数据管理Agent - 未知操作"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "未知操作"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "未知操作",
        "user_id": 123,
        "log_id": task_id
    })

    assert result is not None
    assert "result" in result
    assert "请指定数据类型" in result["result"]

    # 验证日志标记为失败
    log = log_service.get_log(task_id)
    assert log.status == "failed"
