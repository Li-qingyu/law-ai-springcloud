"""
模型降级管理器
LLM调用失败时的优雅降级策略
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    priority: int
    timeout: int
    max_retries: int = 2
    description: str = ""


class ModelFallbackManager:
    """模型降级管理器"""
    
    # 降级策略链（按优先级排序）
    FALLBACK_CHAIN = [
        ModelConfig(
            name="qwen-plus",
            priority=1,
            timeout=10,
            max_retries=2,
            description="主模型，性能最佳"
        ),
        ModelConfig(
            name="qwen-turbo",
            priority=2,
            timeout=5,
            max_retries=1,
            description="快速模型，响应速度快"
        ),
        ModelConfig(
            name="qwen-long",
            priority=3,
            timeout=15,
            max_retries=1,
            description="长文本模型，支持长上下文"
        ),
    ]
    
    def __init__(self):
        """初始化模型降级管理器"""
        self.settings = get_settings()
        self._model_cache: Dict[str, Any] = {}
        self._call_stats: Dict[str, Dict[str, int]] = {}
    
    async def invoke_with_fallback(self, prompt: str, **kwargs) -> str:
        """
        带降级策略的LLM调用
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
            
        Raises:
            Exception: 所有模型调用失败时抛出异常
        """
        last_error = None
        
        for model_config in self.FALLBACK_CHAIN:
            try:
                result = await self._invoke_model_with_retry(
                    model_config,
                    prompt,
                    **kwargs
                )
                
                # 记录成功调用
                self._record_call(model_config.name, "success")
                
                logger.info(f"[模型降级] 成功使用模型: {model_config.name}")
                return result
                
            except Exception as e:
                last_error = e
                self._record_call(model_config.name, "failure")
                logger.warning(f"[模型降级] 模型 {model_config.name} 调用失败: {e}")
                continue
        
        # 所有模型都失败
        self._record_call("all", "failure")
        raise Exception(f"所有模型调用失败，最后错误: {last_error}")
    
    async def _invoke_model_with_retry(self, model_config: ModelConfig,
                                       prompt: str, **kwargs) -> str:
        """
        带重试的模型调用
        
        Args:
            model_config: 模型配置
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
        """
        last_error = None
        
        for attempt in range(model_config.max_retries):
            try:
                return await self._invoke_model(
                    model_config.name,
                    prompt,
                    timeout=model_config.timeout,
                    **kwargs
                )
            except Exception as e:
                last_error = e
                if attempt < model_config.max_retries - 1:
                    logger.info(f"[模型重试] {model_config.name} 第 {attempt + 1} 次重试")
                    await asyncio.sleep(0.5)  # 短暂等待后重试
        
        raise last_error
    
    async def _invoke_model(self, model_name: str, prompt: str,
                           timeout: int = 10, **kwargs) -> str:
        """
        调用指定模型
        
        Args:
            model_name: 模型名称
            prompt: 提示词
            timeout: 超时时间（秒）
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
        """
        from langchain_community.chat_models import ChatTongyi
        
        # 获取或创建模型实例
        if model_name not in self._model_cache:
            self._model_cache[model_name] = ChatTongyi(
                api_key=self.settings.DASHSCOPE_API_KEY,
                model=model_name,
                top_p=0.7,
            )
        
        llm = self._model_cache[model_name]
        
        # 带超时的调用
        try:
            result = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=timeout
            )
            return result.content
        except asyncio.TimeoutError:
            raise Exception(f"模型 {model_name} 调用超时 ({timeout}s)")
    
    def _record_call(self, model_name: str, status: str):
        """
        记录调用统计
        
        Args:
            model_name: 模型名称
            status: 调用状态（success/failure）
        """
        if model_name not in self._call_stats:
            self._call_stats[model_name] = {"success": 0, "failure": 0}
        
        self._call_stats[model_name][status] += 1
    
    def get_call_stats(self) -> Dict[str, Dict[str, int]]:
        """
        获取调用统计
        
        Returns:
            调用统计字典
        """
        return self._call_stats.copy()
    
    def get_model_info(self) -> List[Dict[str, Any]]:
        """
        获取模型信息
        
        Returns:
            模型信息列表
        """
        return [
            {
                "name": config.name,
                "priority": config.priority,
                "timeout": config.timeout,
                "max_retries": config.max_retries,
                "description": config.description
            }
            for config in self.FALLBACK_CHAIN
        ]
    
    def reset_stats(self):
        """重置调用统计"""
        self._call_stats.clear()


class SyncModelFallbackManager:
    """同步版本的模型降级管理器"""
    
    def __init__(self):
        """初始化同步模型降级管理器"""
        self.settings = get_settings()
        self._model_cache: Dict[str, Any] = {}
        self._call_stats: Dict[str, Dict[str, int]] = {}
    
    def invoke_with_fallback(self, prompt: str, **kwargs) -> str:
        """
        带降级策略的同步LLM调用
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
            
        Raises:
            Exception: 所有模型调用失败时抛出异常
        """
        last_error = None
        
        for model_config in ModelFallbackManager.FALLBACK_CHAIN:
            try:
                result = self._invoke_model_with_retry(
                    model_config,
                    prompt,
                    **kwargs
                )
                
                # 记录成功调用
                self._record_call(model_config.name, "success")
                
                logger.info(f"[模型降级] 成功使用模型: {model_config.name}")
                return result
                
            except Exception as e:
                last_error = e
                self._record_call(model_config.name, "failure")
                logger.warning(f"[模型降级] 模型 {model_config.name} 调用失败: {e}")
                continue
        
        # 所有模型都失败
        self._record_call("all", "failure")
        raise Exception(f"所有模型调用失败，最后错误: {last_error}")
    
    def _invoke_model_with_retry(self, model_config: ModelConfig,
                                 prompt: str, **kwargs) -> str:
        """
        带重试的同步模型调用
        
        Args:
            model_config: 模型配置
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
        """
        import time
        last_error = None
        
        for attempt in range(model_config.max_retries):
            try:
                return self._invoke_model(
                    model_config.name,
                    prompt,
                    **kwargs
                )
            except Exception as e:
                last_error = e
                if attempt < model_config.max_retries - 1:
                    logger.info(f"[模型重试] {model_config.name} 第 {attempt + 1} 次重试")
                    time.sleep(0.5)  # 短暂等待后重试
        
        raise last_error
    
    def _invoke_model(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        同步调用指定模型
        
        Args:
            model_name: 模型名称
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应内容
        """
        from langchain_community.chat_models import ChatTongyi
        
        # 获取或创建模型实例
        if model_name not in self._model_cache:
            self._model_cache[model_name] = ChatTongyi(
                api_key=self.settings.DASHSCOPE_API_KEY,
                model=model_name,
                top_p=0.7,
            )
        
        llm = self._model_cache[model_name]
        
        # 调用模型
        result = llm.invoke(prompt)
        return result.content
    
    def _record_call(self, model_name: str, status: str):
        """
        记录调用统计
        
        Args:
            model_name: 模型名称
            status: 调用状态（success/failure）
        """
        if model_name not in self._call_stats:
            self._call_stats[model_name] = {"success": 0, "failure": 0}
        
        self._call_stats[model_name][status] += 1
    
    def get_call_stats(self) -> Dict[str, Dict[str, int]]:
        """
        获取调用统计
        
        Returns:
            调用统计字典
        """
        return self._call_stats.copy()
