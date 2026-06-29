import pytest
from app.agents.file_management_agent import create_file_management_agent
from app.services.admin_log_service import AdminLogService

def test_file_management_agent():
    """测试文件管理Agent"""
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
    
    # 验证日志已更新
    log = log_service.get_log(task_id)
    assert log.status == "success"
