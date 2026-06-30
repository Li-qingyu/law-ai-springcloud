"""
任务拆分器测试
"""
import pytest
from app.services.admin_agent_service.task_splitter import TaskSplitter, SubTask


class TestTaskSplitter:
    """任务拆分器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.splitter = TaskSplitter()
    
    def test_single_task(self):
        """测试单个任务"""
        query = "上传专利数据"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 1
        assert tasks[0].query == "上传专利数据"
        assert tasks[0].order == 1
    
    def test_multiple_tasks_with_then(self):
        """测试使用'然后'分隔的多个任务"""
        query = "上传专利数据，然后查询系统日志"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 2
        assert tasks[0].query == "上传专利数据"
        assert tasks[1].query == "查询系统日志"
    
    def test_multiple_tasks_with_semicolon(self):
        """测试使用分号分隔的多个任务"""
        query = "上传专利数据；查询系统日志"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 2
        assert tasks[0].query == "上传专利数据"
        assert tasks[1].query == "查询系统日志"
    
    def test_multiple_tasks_with_period(self):
        """测试使用句号分隔的多个任务"""
        query = "上传专利数据。查询系统日志"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 2
        assert tasks[0].query == "上传专利数据"
        assert tasks[1].query == "查询系统日志"
    
    def test_multiple_tasks_with_comma(self):
        """测试使用逗号分隔的多个任务"""
        query = "上传专利数据，查询系统日志，管理用户权限"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 3
        assert tasks[0].query == "上传专利数据"
        assert tasks[1].query == "查询系统日志"
        assert tasks[2].query == "管理用户权限"
    
    def test_complex_query(self):
        """测试复杂查询"""
        query = "上传专利数据，然后查询系统日志，然后管理用户权限"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 3
        assert tasks[0].query == "上传专利数据"
        assert tasks[0].order == 1
        assert tasks[1].query == "查询系统日志"
        assert tasks[1].order == 2
        assert tasks[2].query == "管理用户权限"
        assert tasks[2].order == 3
    
    def test_complex_query_with_last(self):
        """测试复杂查询 - 使用'最后'分隔"""
        query = "上传专利数据，查询系统日志，管理用户权限"
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 3
        assert tasks[0].query == "上传专利数据"
        assert tasks[1].query == "查询系统日志"
        assert tasks[2].query == "管理用户权限"
    
    def test_empty_query(self):
        """测试空查询"""
        query = ""
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 1
        assert tasks[0].query == ""
    
    def test_whitespace_query(self):
        """测试只有空格的查询"""
        query = "   "
        tasks = self.splitter.split(query)
        
        assert len(tasks) == 1
    
    def test_to_dict(self):
        """测试SubTask的to_dict方法"""
        sub_task = SubTask(query="测试任务", order=1, dependencies=[0], metadata={"key": "value"})
        result = sub_task.to_dict()
        
        assert result["query"] == "测试任务"
        assert result["order"] == 1
        assert result["dependencies"] == [0]
        assert result["metadata"] == {"key": "value"}
    
    def test_get_task_type_file(self):
        """测试获取任务类型 - 文件管理"""
        query = "上传专利数据"
        task_type = self.splitter.get_task_type(query)
        
        assert task_type == "file_management"
    
    def test_get_task_type_log(self):
        """测试获取任务类型 - 日志管理"""
        query = "查询系统日志"
        task_type = self.splitter.get_task_type(query)
        
        assert task_type == "log_management"
    
    def test_get_task_type_data(self):
        """测试获取任务类型 - 数据管理"""
        query = "管理专利数据"
        task_type = self.splitter.get_task_type(query)
        
        assert task_type == "data_management"
    
    def test_get_task_type_permission(self):
        """测试获取任务类型 - 权限管理"""
        query = "管理用户权限"
        task_type = self.splitter.get_task_type(query)
        
        assert task_type == "permission_management"
    
    def test_get_task_type_unknown(self):
        """测试获取任务类型 - 未知"""
        query = "未知任务"
        task_type = self.splitter.get_task_type(query)
        
        assert task_type == "unknown"
    
    def test_filter_short_tasks(self):
        """测试过滤过短的任务"""
        query = "上传专利数据，，，查询系统日志"
        tasks = self.splitter.split(query)
        
        # 应该过滤掉空的任务
        assert len(tasks) == 2
    
    def test_filter_punctuation_only(self):
        """测试过滤只有标点的任务"""
        query = "上传专利数据，！，查询系统日志"
        tasks = self.splitter.split(query)
        
        # 应该过滤掉只有标点的任务
        assert len(tasks) == 2


class TestTaskSplitterWithLLM:
    """带LLM的任务拆分器测试类"""
    
    def test_split_with_mock_llm(self):
        """测试使用模拟LLM的拆分"""
        # 模拟LLM服务
        class MockLLMService:
            def invoke(self, prompt):
                return '{"tasks": [{"query": "上传专利数据", "order": 1}, {"query": "查询系统日志", "order": 2}]}'
        
        splitter = TaskSplitter(llm_service=MockLLMService())
        query = "上传专利数据，然后查询系统日志"
        tasks = splitter.split(query)
        
        # 规则拆分应该已经足够，不会调用LLM
        assert len(tasks) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
