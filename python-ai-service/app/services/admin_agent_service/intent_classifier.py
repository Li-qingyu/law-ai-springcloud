"""
意图识别器
规则+LLM混合识别，提高准确性
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型"""
    FILE_MANAGEMENT = "file_management"
    LOG_MANAGEMENT = "log_management"
    DATA_MANAGEMENT = "data_management"
    PERMISSION_MANAGEMENT = "permission_management"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    entities: Dict[str, str]
    source: str  # "rule" or "llm"
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "source": self.source
        }


class IntentClassifier:
    """意图识别器 - 规则+LLM混合"""
    
    # 规则模式（按优先级排序）
    # 注意：更具体的模式应该放在前面
    RULE_PATTERNS = {
        IntentType.PERMISSION_MANAGEMENT: [
            (r"用户.*权限|权限.*用户", 0.95),
            (r"分配.*权限|权限.*分配", 0.95),
            (r"创建.*用户|用户.*创建", 0.95),
            (r"删除.*用户|用户.*删除", 0.95),
            (r"修改.*权限|权限.*修改", 0.95),
            (r"角色.*管理|管理.*角色", 0.90),
            (r"用户|权限|角色", 0.85),
        ],
        IntentType.FILE_MANAGEMENT: [
            (r"上传.*文件|文件.*上传", 0.95),
            (r"导入.*文件|文件.*导入", 0.95),
            (r"解析.*文件|文件.*解析", 0.95),
            (r"批量.*导入|导入.*批量", 0.90),
            (r"上传|导入", 0.85),
        ],
        IntentType.LOG_MANAGEMENT: [
            (r"查询.*日志|日志.*查询", 0.95),
            (r"系统.*日志|日志.*系统", 0.90),
            (r"用户.*操作.*日志|日志.*用户.*操作", 0.90),
            (r"API.*日志|日志.*API", 0.90),
            (r"统计.*分析|分析.*统计", 0.85),
            (r"日志|统计|分析", 0.80),
        ],
        IntentType.DATA_MANAGEMENT: [
            (r"专利.*数据|数据.*专利", 0.95),
            (r"公司.*数据|数据.*公司", 0.95),
            (r"诉讼.*数据|数据.*诉讼", 0.95),
            (r"法律.*数据|数据.*法律", 0.95),
            (r"增删改查|数据.*管理|管理.*数据", 0.90),
            (r"修改.*记录|记录.*修改", 0.85),
            (r"删除.*记录|记录.*删除", 0.85),
            (r"添加.*记录|记录.*添加", 0.85),
            (r"数据|专利|公司|诉讼|法律", 0.80),
        ],
    }
    
    def __init__(self, llm_service=None):
        """
        初始化意图识别器
        
        Args:
            llm_service: LLM服务，用于复杂意图识别（可选）
        """
        self.llm_service = llm_service
    
    def classify(self, query: str, context: Dict = None) -> IntentResult:
        """
        混合意图识别
        
        Args:
            query: 用户输入
            context: 上下文信息（可选）
            
        Returns:
            意图识别结果
        """
        if not query or not query.strip():
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                source="rule"
            )
        
        # 第一步：规则匹配
        rule_result = self._rule_classify(query)
        
        # 如果规则置信度高，直接返回
        if rule_result.confidence >= 0.8:
            logger.info(f"[意图识别] 规则命中: {rule_result.intent.value}, 置信度: {rule_result.confidence}")
            return rule_result
        
        # 第二步：LLM识别（如果可用）
        if self.llm_service:
            try:
                llm_result = self._llm_classify(query, context)
                # 合并结果
                merged_result = self._merge_results(rule_result, llm_result)
                logger.info(f"[意图识别] LLM识别: {merged_result.intent.value}, 置信度: {merged_result.confidence}")
                return merged_result
            except Exception as e:
                logger.warning(f"[意图识别] LLM识别失败，降级到规则结果: {e}")
                return rule_result
        
        # 如果没有LLM服务，返回规则结果
        logger.info(f"[意图识别] 使用规则结果: {rule_result.intent.value}, 置信度: {rule_result.confidence}")
        return rule_result
    
    def _rule_classify(self, query: str) -> IntentResult:
        """
        规则匹配
        
        Args:
            query: 用户输入
            
        Returns:
            意图识别结果
        """
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        best_pattern = None
        
        for intent, patterns in self.RULE_PATTERNS.items():
            for pattern, confidence in patterns:
                if re.search(pattern, query):
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
                        best_pattern = pattern
        
        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            entities=self._extract_entities(query),
            source="rule"
        )
    
    def _llm_classify(self, query: str, context: Dict = None) -> IntentResult:
        """
        LLM识别
        
        Args:
            query: 用户输入
            context: 上下文信息
            
        Returns:
            意图识别结果
        """
        prompt = self._build_classify_prompt(query, context)
        
        # 调用LLM
        result = self.llm_service.invoke(prompt)
        
        # 解析结果
        return self._parse_llm_result(result)
    
    def _build_classify_prompt(self, query: str, context: Dict = None) -> str:
        """
        构建LLM提示词
        
        Args:
            query: 用户输入
            context: 上下文信息
            
        Returns:
            提示词
        """
        context_str = ""
        if context:
            context_str = f"\n上下文信息：{json.dumps(context, ensure_ascii=False)}"
        
        return f"""你是一个意图识别专家。请分析以下管理任务请求，识别其意图类型。

请求：{query}{context_str}

请从以下意图类型中选择最匹配的一个：
- file_management: 文件管理（上传、导入、解析文件等）
- log_management: 日志管理（查询、统计、分析日志等）
- data_management: 数据管理（管理专利、公司、诉讼、法律数据等）
- permission_management: 权限管理（用户、角色、权限管理等）
- unknown: 无法识别

请以JSON格式返回结果：
{{
    "intent": "意图类型",
    "confidence": 0.95,
    "entities": {{"关键实体": "值"}},
    "reasoning": "识别理由"
}}

注意：
1. confidence 是 0-1 之间的浮点数，表示识别置信度
2. entities 提取请求中的关键实体（如文件名、数据类型等）
3. reasoning 简要说明识别理由

JSON:"""
    
    def _parse_llm_result(self, result: str) -> IntentResult:
        """
        解析LLM结果
        
        Args:
            result: LLM返回的结果
            
        Returns:
            意图识别结果
        """
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                intent_str = data.get("intent", "unknown")
                confidence = data.get("confidence", 0.5)
                entities = data.get("entities", {})
                reasoning = data.get("reasoning", "")
                
                # 转换意图类型
                try:
                    intent = IntentType(intent_str)
                except ValueError:
                    intent = IntentType.UNKNOWN
                
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    entities=entities,
                    source="llm",
                    raw_response=result
                )
        except Exception as e:
            logger.error(f"解析LLM结果失败: {e}")
        
        # 解析失败，返回默认结果
        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            entities={},
            source="llm",
            raw_response=result
        )
    
    def _merge_results(self, rule_result: IntentResult, 
                       llm_result: IntentResult) -> IntentResult:
        """
        合并规则和LLM结果
        
        Args:
            rule_result: 规则识别结果
            llm_result: LLM识别结果
            
        Returns:
            合并后的结果
        """
        # 如果规则和LLM结果一致，提高置信度
        if rule_result.intent == llm_result.intent:
            merged_confidence = min(1.0, (rule_result.confidence + llm_result.confidence) / 2 + 0.1)
            return IntentResult(
                intent=rule_result.intent,
                confidence=merged_confidence,
                entities={**rule_result.entities, **llm_result.entities},
                source="merged"
            )
        
        # 如果LLM置信度更高，使用LLM结果
        if llm_result.confidence > rule_result.confidence:
            return llm_result
        
        # 否则使用规则结果
        return rule_result
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """
        提取实体
        
        Args:
            query: 用户输入
            
        Returns:
            实体字典
        """
        entities = {}
        
        # 提取文件名（只匹配文件名部分，不包含前面的动词）
        file_match = re.search(r'(?:上传|导入|解析)?\s*([\w\-\.]+\.(xlsx|csv|pdf|docx?))', query)
        if file_match:
            entities['file_name'] = file_match.group(1)
        
        # 提取数据类型
        data_types = ['专利', '公司', '诉讼', '法律']
        for dt in data_types:
            if dt in query:
                entities['data_type'] = dt
                break
        
        # 提取操作类型
        operations = ['上传', '导入', '查询', '统计', '管理', '删除', '修改', '添加']
        for op in operations:
            if op in query:
                entities['operation'] = op
                break
        
        return entities
    
    def get_supported_intents(self) -> List[str]:
        """
        获取支持的意图类型
        
        Returns:
            意图类型列表
        """
        return [intent.value for intent in IntentType]
