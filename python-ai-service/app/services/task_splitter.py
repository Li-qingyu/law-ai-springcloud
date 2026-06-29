"""
任务拆分器
将复杂请求拆分为多个子任务
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """子任务"""
    query: str
    order: int
    dependencies: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "order": self.order,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }

class TaskSplitter:
    """任务拆分器"""
    
    # 分隔符模式
    SEPARATOR_PATTERNS = [
        # 中文分隔符（带逗号）
        (r'[，,]\s*然后', 'then'),
        (r'[，,]\s*接着', 'then'),
        (r'[，,]\s*之后', 'then'),
        (r'[，,]\s*最后', 'then'),
        (r'[，,]\s*再', 'then'),
        # 中文分隔符（不带逗号）
        (r'\s*然后\s*', 'then'),
        (r'\s*接着\s*', 'then'),
        (r'\s*之后\s*', 'then'),
        (r'\s*最后\s*', 'then'),
        (r'\s*再\s*', 'then'),
        # 其他分隔符
        (r'[；;]', 'then'),
        (r'[。！!？?]', 'then'),
        # 英文分隔符
        (r',\s*then', 'then'),
        (r';\s*then', 'then'),
        (r'\.\s*Then', 'then'),
        # 纯逗号分隔（需要语义判断）
        (r'[，,]', 'comma'),
    ]
    
    # 任务关键词模式（优先级从高到低）
    TASK_KEYWORDS = {
        "permission_management": ["用户", "权限", "角色"],  # 优先级最高
        "file_management": ["上传", "导入", "文件", "解析"],
        "log_management": ["日志", "查询", "统计", "分析"],
        "data_management": ["数据", "管理", "专利", "公司", "诉讼", "法律"],
    }
    
    def __init__(self, llm_service=None):
        """
        初始化任务拆分器
        
        Args:
            llm_service: LLM服务，用于语义拆分（可选）
        """
        self.llm_service = llm_service
    
    def split(self, query: str) -> List[SubTask]:
        """
        将复杂请求拆分为多个子任务
        
        Args:
            query: 用户输入的复杂请求
            
        Returns:
            子任务列表
            
        示例：
            输入: "上传专利数据，然后查询系统日志，最后管理用户权限"
            输出: [
                SubTask(query="上传专利数据", order=1),
                SubTask(query="查询系统日志", order=2),
                SubTask(query="管理用户权限", order=3)
            ]
        """
        if not query or not query.strip():
            return [SubTask(query=query, order=1)]
        
        # 第一步：基于分隔符的规则拆分
        tasks = self._split_by_separators(query)
        
        # 如果只有一个任务，直接返回
        if len(tasks) <= 1:
            return [SubTask(query=query.strip(), order=1)]
        
        # 第二步：验证拆分结果
        validated_tasks = self._validate_tasks(tasks)
        
        # 第三步：如果任务数量异常，尝试LLM语义拆分
        if len(validated_tasks) > 5 and self.llm_service:
            try:
                llm_tasks = self._split_by_llm(query)
                if llm_tasks and len(llm_tasks) < len(validated_tasks):
                    validated_tasks = llm_tasks
            except Exception as e:
                logger.warning(f"LLM任务拆分失败，使用规则拆分结果: {e}")
        
        # 第四步：排序并返回
        return self._sort_tasks(validated_tasks)
    
    def _split_by_separators(self, query: str) -> List[str]:
        """
        基于分隔符拆分任务
        
        Args:
            query: 用户输入
            
        Returns:
            拆分后的任务字符串列表
        """
        # 首先尝试强分隔符（然后、接着、之后、最后等）
        strong_separators = [
            r'[，,]\s*然后', r'[，,]\s*接着', r'[，,]\s*之后', 
            r'[，,]\s*最后', r'[，,]\s*再',
            r'\s+然后\s+', r'\s+接着\s+', r'\s+之后\s+',
            r'\s+最后\s+', r'\s+再\s+',
            r'[；;]', r'[。！!？?]'
        ]
        
        for pattern in strong_separators:
            parts = re.split(pattern, query)
            if len(parts) > 1:
                # 过滤空字符串
                return [part.strip() for part in parts if part.strip()]
        
        # 如果没有强分隔符，尝试逗号分隔
        parts = re.split(r'[，,]', query)
        if len(parts) > 1:
            # 检查每个部分是否包含任务关键词
            valid_parts = []
            for part in parts:
                part = part.strip()
                if part and self._contains_task_keyword(part):
                    valid_parts.append(part)
            
            if len(valid_parts) > 1:
                return valid_parts
        
        # 如果都没有匹配，返回原始查询
        return [query.strip()]
    
    def _contains_task_keyword(self, text: str) -> bool:
        """
        检查文本是否包含任务关键词
        
        Args:
            text: 待检查的文本
            
        Returns:
            是否包含任务关键词
        """
        for keywords in self.TASK_KEYWORDS.values():
            for keyword in keywords:
                if keyword in text:
                    return True
        return False
    
    def _validate_tasks(self, tasks: List[str]) -> List[str]:
        """
        验证拆分结果
        
        Args:
            tasks: 拆分后的任务列表
            
        Returns:
            验证后的任务列表
        """
        validated = []
        
        for task in tasks:
            # 过滤过短的任务（可能是误拆分）
            if len(task) < 2:
                continue
            
            # 过滤只包含标点符号的任务
            if re.match(r'^[，,。！!？?\s]+$', task):
                continue
            
            validated.append(task)
        
        return validated
    
    def _sort_tasks(self, tasks: List[str]) -> List[SubTask]:
        """
        排序任务并转换为SubTask对象
        
        Args:
            tasks: 任务字符串列表
            
        Returns:
            排序后的SubTask列表
        """
        sub_tasks = []
        
        for i, task in enumerate(tasks, 1):
            sub_task = SubTask(
                query=task,
                order=i,
                dependencies=[],
                metadata={"source": "rule_split"}
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    def _split_by_llm(self, query: str) -> Optional[List[SubTask]]:
        """
        使用LLM进行语义拆分
        
        Args:
            query: 用户输入
            
        Returns:
            拆分后的SubTask列表，如果失败返回None
        """
        prompt = f"""请将以下管理任务请求拆分为独立的子任务。

请求：{query}

请以JSON格式返回拆分结果：
{{
    "tasks": [
        {{"query": "子任务1", "order": 1}},
        {{"query": "子任务2", "order": 2}}
    ]
}}

注意：
1. 每个子任务应该是独立的、可执行的
2. 保持原始请求的语义
3. 如果只有一个任务，返回单个任务的列表
4. 不要添加额外的任务

JSON:"""
        
        try:
            result = self.llm_service.invoke(prompt)
            
            # 解析JSON结果
            import json
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                tasks = data.get("tasks", [])
                
                sub_tasks = []
                for task in tasks:
                    sub_task = SubTask(
                        query=task["query"],
                        order=task.get("order", len(sub_tasks) + 1),
                        dependencies=task.get("dependencies", []),
                        metadata={"source": "llm_split"}
                    )
                    sub_tasks.append(sub_task)
                
                return sub_tasks
        except Exception as e:
            logger.error(f"LLM任务拆分解析失败: {e}")
        
        return None
    
    def get_task_type(self, query: str) -> str:
        """
        根据查询内容判断任务类型
        
        Args:
            query: 任务查询
            
        Returns:
            任务类型
        """
        for task_type, keywords in self.TASK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return task_type
        return "unknown"
