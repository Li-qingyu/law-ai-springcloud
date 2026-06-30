"""
意图识别器测试
"""
import pytest
from app.services.admin_agent_service.intent_classifier import IntentClassifier, IntentType, IntentResult


class TestIntentClassifier:
    """意图识别器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.classifier = IntentClassifier()
    
    def test_file_management_upload(self):
        """测试文件管理 - 上传"""
        query = "上传专利数据文件"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.FILE_MANAGEMENT
        assert result.confidence >= 0.8
        assert result.source == "rule"
    
    def test_file_management_import(self):
        """测试文件管理 - 导入"""
        query = "导入Excel数据"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.FILE_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_log_management_query(self):
        """测试日志管理 - 查询"""
        query = "查询系统日志"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.LOG_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_log_management_statistics(self):
        """测试日志管理 - 统计"""
        query = "统计分析日志"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.LOG_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_data_management_patent(self):
        """测试数据管理 - 专利"""
        query = "管理专利数据"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.DATA_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_data_management_company(self):
        """测试数据管理 - 公司"""
        query = "公司数据管理"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.DATA_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_permission_management_user(self):
        """测试权限管理 - 用户"""
        query = "管理用户权限"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.PERMISSION_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_permission_management_role(self):
        """测试权限管理 - 角色"""
        query = "角色管理"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.PERMISSION_MANAGEMENT
        assert result.confidence >= 0.8
    
    def test_unknown_intent(self):
        """测试未知意图"""
        query = "未知任务"
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence < 0.8
    
    def test_empty_query(self):
        """测试空查询"""
        query = ""
        result = self.classifier.classify(query)
        
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0
    
    def test_extract_entities_file(self):
        """测试提取实体 - 文件"""
        query = "上传patent_data.xlsx"
        result = self.classifier.classify(query)
        
        assert 'file_name' in result.entities
        assert result.entities['file_name'] == 'patent_data.xlsx'
    
    def test_extract_entities_data_type(self):
        """测试提取实体 - 数据类型"""
        query = "管理专利数据"
        result = self.classifier.classify(query)
        
        assert 'data_type' in result.entities
        assert result.entities['data_type'] == '专利'
    
    def test_extract_entities_operation(self):
        """测试提取实体 - 操作类型"""
        query = "上传专利数据"
        result = self.classifier.classify(query)
        
        assert 'operation' in result.entities
        assert result.entities['operation'] == '上传'
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = IntentResult(
            intent=IntentType.FILE_MANAGEMENT,
            confidence=0.95,
            entities={"file_name": "test.xlsx"},
            source="rule"
        )
        result_dict = result.to_dict()
        
        assert result_dict["intent"] == "file_management"
        assert result_dict["confidence"] == 0.95
        assert result_dict["entities"] == {"file_name": "test.xlsx"}
        assert result_dict["source"] == "rule"
    
    def test_get_supported_intents(self):
        """测试获取支持的意图类型"""
        intents = self.classifier.get_supported_intents()
        
        assert "file_management" in intents
        assert "log_management" in intents
        assert "data_management" in intents
        assert "permission_management" in intents
        assert "unknown" in intents


class TestIntentClassifierWithLLM:
    """带LLM的意图识别器测试类"""
    
    def test_classify_with_mock_llm(self):
        """测试使用模拟LLM的识别"""
        # 模拟LLM服务
        class MockLLMService:
            def invoke(self, prompt):
                return '{"intent": "file_management", "confidence": 0.95, "entities": {"file_name": "test.xlsx"}, "reasoning": "包含上传和文件关键词"}'
        
        classifier = IntentClassifier(llm_service=MockLLMService())
        
        # 使用一个规则置信度较低的查询（没有明确的关键词）
        query = "处理一下那个文档"
        result = classifier.classify(query)
        
        # 应该使用LLM结果（因为规则置信度低）
        assert result.intent == IntentType.FILE_MANAGEMENT
        assert result.source == "llm"
    
    def test_classify_llm_failure_fallback(self):
        """测试LLM失败时降级到规则结果"""
        # 模拟失败的LLM服务
        class FailingLLMService:
            def invoke(self, prompt):
                raise Exception("LLM调用失败")
        
        classifier = IntentClassifier(llm_service=FailingLLMService())
        
        # 使用一个规则能识别的查询
        query = "上传专利数据文件"
        result = classifier.classify(query)
        
        # 应该降级到规则结果
        assert result.intent == IntentType.FILE_MANAGEMENT
        assert result.source == "rule"
    
    def test_merge_results_same_intent(self):
        """测试合并相同意图的结果"""
        classifier = IntentClassifier()
        
        rule_result = IntentResult(
            intent=IntentType.FILE_MANAGEMENT,
            confidence=0.85,
            entities={"operation": "上传"},
            source="rule"
        )
        
        llm_result = IntentResult(
            intent=IntentType.FILE_MANAGEMENT,
            confidence=0.90,
            entities={"file_name": "test.xlsx"},
            source="llm"
        )
        
        merged = classifier._merge_results(rule_result, llm_result)
        
        assert merged.intent == IntentType.FILE_MANAGEMENT
        assert merged.confidence > 0.85  # 应该提高置信度
        assert merged.source == "merged"
        assert "operation" in merged.entities
        assert "file_name" in merged.entities
    
    def test_merge_results_different_intent(self):
        """测试合并不同意图的结果"""
        classifier = IntentClassifier()
        
        rule_result = IntentResult(
            intent=IntentType.FILE_MANAGEMENT,
            confidence=0.85,
            entities={},
            source="rule"
        )
        
        llm_result = IntentResult(
            intent=IntentType.DATA_MANAGEMENT,
            confidence=0.90,
            entities={},
            source="llm"
        )
        
        merged = classifier._merge_results(rule_result, llm_result)
        
        # 应该使用置信度更高的LLM结果
        assert merged.intent == IntentType.DATA_MANAGEMENT
        assert merged.confidence == 0.90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
