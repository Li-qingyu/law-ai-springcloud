import pytest
from app.tools.log_management_tool import LogManagementTool

def test_system_log_query():
    """测试系统日志查询"""
    tool = LogManagementTool()
    result = tool._run("查询系统日志")
    assert "系统日志" in result

def test_user_log_query():
    """测试用户操作日志查询"""
    tool = LogManagementTool()
    result = tool._run("查询用户操作日志")
    assert "用户操作日志" in result

def test_api_log_query():
    """测试API调用日志查询"""
    tool = LogManagementTool()
    result = tool._run("查询API调用日志")
    assert "API调用日志" in result

def test_log_analysis():
    """测试日志统计分析"""
    tool = LogManagementTool()
    result = tool._run("统计分析日志")
    assert "统计分析" in result

def test_unknown_operation():
    """测试未知操作"""
    tool = LogManagementTool()
    result = tool._run("未知操作")
    assert "请指定操作类型" in result
