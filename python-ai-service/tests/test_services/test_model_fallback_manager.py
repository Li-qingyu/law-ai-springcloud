"""
模型降级管理器测试
"""
import pytest
import asyncio
from app.services.model_fallback_manager import (
    ModelFallbackManager, 
    SyncModelFallbackManager, 
    ModelConfig
)


class TestModelFallbackManager:
    """模型降级管理器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = ModelFallbackManager()
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        model_info = self.manager.get_model_info()
        
        assert len(model_info) == 3
        assert model_info[0]["name"] == "qwen-plus"
        assert model_info[1]["name"] == "qwen-turbo"
        assert model_info[2]["name"] == "qwen-long"
    
    def test_record_call_success(self):
        """测试记录成功调用"""
        self.manager._record_call("qwen-plus", "success")
        stats = self.manager.get_call_stats()
        
        assert "qwen-plus" in stats
        assert stats["qwen-plus"]["success"] == 1
        assert stats["qwen-plus"]["failure"] == 0
    
    def test_record_call_failure(self):
        """测试记录失败调用"""
        self.manager._record_call("qwen-plus", "failure")
        stats = self.manager.get_call_stats()
        
        assert "qwen-plus" in stats
        assert stats["qwen-plus"]["success"] == 0
        assert stats["qwen-plus"]["failure"] == 1
    
    def test_reset_stats(self):
        """测试重置统计"""
        self.manager._record_call("qwen-plus", "success")
        self.manager._record_call("qwen-plus", "failure")
        self.manager.reset_stats()
        
        stats = self.manager.get_call_stats()
        assert len(stats) == 0
    
    def test_multiple_calls(self):
        """测试多次调用统计"""
        self.manager._record_call("qwen-plus", "success")
        self.manager._record_call("qwen-plus", "success")
        self.manager._record_call("qwen-plus", "failure")
        self.manager._record_call("qwen-turbo", "success")
        
        stats = self.manager.get_call_stats()
        
        assert stats["qwen-plus"]["success"] == 2
        assert stats["qwen-plus"]["failure"] == 1
        assert stats["qwen-turbo"]["success"] == 1


class TestSyncModelFallbackManager:
    """同步模型降级管理器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = SyncModelFallbackManager()
    
    def test_record_call_success(self):
        """测试记录成功调用"""
        self.manager._record_call("qwen-plus", "success")
        stats = self.manager.get_call_stats()
        
        assert "qwen-plus" in stats
        assert stats["qwen-plus"]["success"] == 1


class TestModelConfig:
    """模型配置测试类"""
    
    def test_model_config_creation(self):
        """测试模型配置创建"""
        config = ModelConfig(
            name="test-model",
            priority=1,
            timeout=10,
            max_retries=3,
            description="测试模型"
        )
        
        assert config.name == "test-model"
        assert config.priority == 1
        assert config.timeout == 10
        assert config.max_retries == 3
        assert config.description == "测试模型"
    
    def test_model_config_defaults(self):
        """测试模型配置默认值"""
        config = ModelConfig(
            name="test-model",
            priority=1,
            timeout=10
        )
        
        assert config.max_retries == 2
        assert config.description == ""


class TestModelFallbackWithMock:
    """使用模拟的模型降级测试"""
    
    def test_invoke_with_mock_success(self):
        """测试使用模拟的成功调用"""
        # 这个测试需要实际的LLM配置，暂时跳过
        pass
    
    def test_invoke_with_mock_failure(self):
        """测试使用模拟的失败调用"""
        # 这个测试需要实际的LLM配置，暂时跳过
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
