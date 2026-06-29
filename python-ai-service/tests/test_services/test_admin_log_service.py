import pytest
from app.services.admin_log_service import AdminLogService

def test_create_log():
    """测试创建日志"""
    service = AdminLogService()
    data = {
        "user_id": 123,
        "task_type": "file_management",
        "query": "上传文件"
    }
    
    task_id = service.create_log(data)
    
    assert task_id is not None
    assert task_id.startswith("task_")
    
    log = service.get_log(task_id)
    assert log is not None
    assert log.user_id == 123
    assert log.agent_type == "file_management"
    assert log.status == "running"

def test_update_log():
    """测试更新日志"""
    service = AdminLogService()
    data = {
        "user_id": 123,
        "task_type": "file_management",
        "query": "上传文件"
    }
    
    task_id = service.create_log(data)
    
    # 更新日志
    update_data = {
        "status": "success",
        "result": "文件上传成功"
    }
    
    result = service.update_log(task_id, update_data)
    assert result is True
    
    log = service.get_log(task_id)
    assert log.status == "success"
    assert log.output_data == {"result": "文件上传成功"}

def test_update_nonexistent_log():
    """测试更新不存在的日志"""
    service = AdminLogService()
    
    result = service.update_log("nonexistent_task", {"status": "success"})
    assert result is False

def test_get_logs_by_user():
    """测试获取用户的操作日志"""
    service = AdminLogService()
    
    # 创建多个日志
    service.create_log({"user_id": 123, "task_type": "file_management"})
    service.create_log({"user_id": 123, "task_type": "log_management"})
    service.create_log({"user_id": 456, "task_type": "data_management"})
    
    logs = service.get_logs_by_user(123)
    assert len(logs) == 2

def test_get_logs_by_agent_type():
    """测试获取指定Agent类型的操作日志"""
    service = AdminLogService()
    
    # 创建多个日志
    service.create_log({"user_id": 123, "task_type": "file_management"})
    service.create_log({"user_id": 456, "task_type": "file_management"})
    service.create_log({"user_id": 123, "task_type": "log_management"})
    
    logs = service.get_logs_by_agent_type("file_management")
    assert len(logs) == 2
