"""
意图识别器 — 路由分类
规则+LLM混合识别，仅判断意图类型（路由目标），不提取业务参数。
业务参数由各子Agent自主识别。
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
    HELP = "help"
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
        IntentType.HELP: [
            (r"帮助|帮忙|有什么功能|能做什么|怎么用|使用说明", 0.95),
            (r"功能介绍|操作指南|使用帮助", 0.90),
            (r"帮助|help", 0.85),
        ],
        IntentType.FILE_MANAGEMENT: [
            (r"上传.*文件|文件.*上传", 0.95),
            (r"导入.*文件|文件.*导入", 0.95),
            (r"解析.*文件|文件.*解析", 0.95),
            (r"查询.*文件|文件.*查询|查看.*文件|文件.*查看", 0.95),
            (r"删除.*文件|文件.*删除", 0.95),
            (r"所有文件|全部文件|文件列表", 0.90),
            (r"批量.*导入|导入.*批量", 0.90),
            (r"上传|导入|文件", 0.85),
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
            # 法律条文相关
            (r"法律条文|法条|条文", 0.95),
            (r"查询.*条文|条文.*查询", 0.95),
            (r"新增.*条文|添加.*条文|条文.*新增", 0.95),
            (r"修改.*条文|更新.*条文|条文.*修改", 0.95),
            (r"删除.*条文|条文.*删除", 0.95),
            (r"同步.*条文|条文.*同步|条文.*向量", 0.95),
            # 法律案例相关
            (r"法律案例|案例", 0.95),
            (r"查询.*案例|案例.*查询", 0.95),
            (r"新增.*案例|添加.*案例|案例.*新增", 0.95),
            (r"修改.*案例|更新.*案例|案例.*修改", 0.95),
            (r"删除.*案例|案例.*删除", 0.95),
            (r"同步.*案例|案例.*同步|案例.*向量", 0.95),
            # 法律书籍相关
            (r"法律书籍|法律书|书籍", 0.95),
            (r"查询.*书籍|书籍.*查询", 0.95),
            (r"新增.*书籍|添加.*书籍|书籍.*新增", 0.95),
            (r"修改.*书籍|更新.*书籍|书籍.*修改", 0.95),
            (r"删除.*书籍|书籍.*删除", 0.95),
            # 法律类型相关
            (r"法律类型|法条类型|类型", 0.95),
            (r"查询.*类型|类型.*查询", 0.95),
            (r"新增.*类型|添加.*类型|类型.*新增", 0.95),
            (r"修改.*类型|更新.*类型|类型.*修改", 0.95),
            (r"删除.*类型|类型.*删除", 0.95),
            # 通用数据管理
            (r"增删改查|数据.*管理|管理.*数据", 0.90),
            (r"同步.*数据|数据.*同步|同步.*向量库", 0.90),
            (r"统计.*数量|数量.*统计", 0.85),
            (r"数据|法律", 0.75),
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
        response = self.llm_service.invoke(prompt)

        # 兼容 LangChain 消息对象和纯字符串
        result = response.content if hasattr(response, "content") else str(response)

        # 解析结果
        return self._parse_llm_result(result)
    
    def _build_classify_prompt(self, query: str, context: Dict = None) -> str:
        """
        构建LLM提示词 — 仅做路由分类，不提取业务参数

        Args:
            query: 用户输入
            context: 上下文信息

        Returns:
            提示词
        """
        context_str = ""
        if context:
            context_str = f"\n上下文信息：{json.dumps(context, ensure_ascii=False)}"

        return f"""你是一个法律咨询管理后台的意图分类专家。请分析管理员的操作请求，判断应该交给哪个子系统处理。

系统背景：这是一个法律咨询管理后台，主要功能包括管理法律条文、法律案例、法律书籍、法律类型等数据，以及文件上传解析、日志查询、权限管理等。

请求：{query}{context_str}

请从以下意图类型中选择最匹配的一个：
- file_management: 文件管理（上传文件、导入文件、解析文件、删除已上传的文件等，强调对物理文件本身的操作）
- log_management: 日志管理（查询操作日志、统计分析、查看操作记录等）
- data_management: 数据管理（管理法律条文、案例、书籍、类型等业务数据的增删改查和同步，这是系统的核心功能）
- permission_management: 权限管理（用户、角色、权限的增删改查）
- unknown: 无法识别

判断规则：
1. "资料""数据""条文""案例""书籍""内容"等通常指业务数据 → data_management
2. 没有明确上下文时的模糊删除/修改操作，默认指业务数据操作 → data_management
3. 只有明确提到"文件""上传""附件""导入文件"等才归为 file_management
4. "记录""日志""操作历史"等 → log_management

请以JSON格式返回结果：
{{
    "intent": "意图类型",
    "confidence": 0.95,
    "reasoning": "识别理由"
}}

注意：
1. confidence 是 0-1 之间的浮点数，表示识别置信度
2. 只需要判断意图类型，不需要提取具体参数

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

                # 转换意图类型
                try:
                    intent = IntentType(intent_str)
                except ValueError:
                    intent = IntentType.UNKNOWN

                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    entities={},
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
                entities={},
                source="merged"
            )

        # 如果LLM置信度更高，使用LLM结果
        if llm_result.confidence > rule_result.confidence:
            return llm_result

        # 否则使用规则结果
        return rule_result
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """
        提取实体 — 仅用于辅助路由，不提取业务参数。
        业务参数由各子Agent自主识别。

        Args:
            query: 用户输入

        Returns:
            实体字典，包含 operation 和 data_type（可能为空）
        """
        entities = {}

        # 提取 operation
        operation_patterns = [
            (r"查询|查看|统计|有多少|查询所有|查看所有|列出", "query"),
            (r"新增|添加|插入|创建|新建", "create"),
            (r"修改|更新|编辑|改动", "update"),
            (r"删除|删掉|移除|去掉|清空", "delete"),
            (r"同步|向量|导入", "sync"),
        ]
        for pattern, op in operation_patterns:
            if re.search(pattern, query):
                entities["operation"] = op
                break

        # 提取 data_type
        data_type_patterns = [
            (r"条文|法条|法律条文", "law_article"),
            (r"案例|法律案例|判例", "law_case"),
            (r"书籍|法律书|法律书籍", "law_book"),
            (r"类型|法律类型|法条类型", "law_type"),
        ]
        for pattern, dt in data_type_patterns:
            if re.search(pattern, query):
                entities["data_type"] = dt
                break

        return entities
    
    def get_supported_intents(self) -> List[str]:
        """
        获取支持的意图类型
        
        Returns:
            意图类型列表
        """
        return [intent.value for intent in IntentType]
