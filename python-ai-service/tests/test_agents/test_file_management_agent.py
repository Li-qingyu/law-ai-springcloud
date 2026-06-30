from app.agents.agents.file_management_agent import create_file_management_agent
from app.services.admin_log_service import AdminLogService

def test_file_management_agent():
    """测试文件管理Agent - 上传操作"""
    # 创建日志服务
    log_service = AdminLogService()
    
    # 创建日志
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "file_management",
        "query": "上传文件 patent_data.xlsx"
    })
    
    # 创建Agent（传入日志服务）
    agent = create_file_management_agent(log_service)
    
    # 执行Agent
    result = agent.invoke({
        "query": "上传文件 patent_data.xlsx",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "上传成功" in result["result"]
    
    # 验证日志已更新
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_file_management_agent_parse():
    """测试文件管理Agent - 解析操作"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "file_management",
        "query": "解析文件 patent_data.pdf"
    })
    
    agent = create_file_management_agent(log_service)
    
    result = agent.invoke({
        "query": "解析文件 patent_data.pdf",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "解析完成" in result["result"]
    
    log = log_service.get_log(task_id)
    assert log.status == "success"

def test_file_management_agent_import():
    """测试文件管理Agent - 导入操作"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "file_management",
        "query": "导入数据 patent_data.csv"
    })
    
    agent = create_file_management_agent(log_service)
    
    result = agent.invoke({
        "query": "导入数据 patent_data.csv",
        "user_id": 123,
        "log_id": task_id
    })
    
    assert result is not None
    assert "result" in result
    assert "导入完成" in result["result"]
    
    log = log_service.get_log(task_id)
    assert log.status == "success"
