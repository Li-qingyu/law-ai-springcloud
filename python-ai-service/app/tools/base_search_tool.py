"""
搜索工具基类
提供通用的向量检索功能
"""
from abc import abstractmethod
from typing import List, Dict, Any, Optional,Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import logging

from app.repositories.milvus_client import search_by_text
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class SearchInput(BaseModel):
    """搜索工具输入参数"""
    query:str = Field(
        ...,
        description="搜索查询文本，应该简洁明确地表达用户想要查找的法律信息",
        examples=["劳动合同解除赔偿标准"]
    )

class BaseSearchTool(BaseTool):
    """搜索工具基类"""
    args_schema: Type[BaseModel] = SearchInput

    collection_name: str = ""
    top_k: int = 5


    def __init__(self, **data):
        """初始化工具"""
        settings = get_settings()
        if 'name' not in data:
            # 尝试从 Pydantic V2 的模型字段中获取默认值
            name_default = self.__class__.model_fields.get('name', {}).default
            data['name'] = name_default if name_default else 'base_search_tool'

        if 'description' not in data:
            desc_default = self.__class__.model_fields.get('description', {}).default
            data['description'] = desc_default if desc_default else '基础搜索工具'

        # 设置 collection_name
        if 'collection_name' not in data or not data['collection_name']:
            data['collection_name'] = getattr(self, 'collection_name', '')

        # 设置 top_k
        if 'top_k' not in data or data['top_k'] == 5:
            data['top_k'] = getattr(self, 'top_k', settings.TOP_K_RESULTS)

        # 调用父类初始化
        super().__init__(**data)

    def _search_and_format(self, query: str) -> str:
        """
        执行搜索并格式化结果

        Args:
            query: 搜索查询

        Returns:
            格式化的搜索结果字符串
        """
        try:
            logger.info(f"[{self.name}] 搜索: {query}")

            results = search_by_text(
                collection_name=self.collection_name,
                query_text=query,
                top_k=self.top_k,
                output_fields=["source_id", "content_json"]
            )

            if not results:
                return f"未找到相关的{self._get_data_type_name()}"

            # 格式化结果
            formatted_results = []
            for i, result in enumerate(results, 1):
                milvus_id = result.get('id')
                score = result.get('score', 0.0)
                content_json = result.get('content_json', '{}')

                formatted_results.append(
                    f"{i}. [ID: {milvus_id}] [相关度: {score:.2f}] {content_json}"
                )

            result_text = "\n".join(formatted_results)
            logger.info(f"[{self.name}] 找到 {len(results)} 条结果")

            return result_text

        except Exception as e:
            logger.error(f"[{self.name}] 搜索失败: {e}", exc_info=True)
            return f"搜索失败: {str(e)}"

    def _search_row (self, query: str) -> List[Dict[str, Any]]:
        """
        执行搜索并返回结果行

        Args:
            query: 搜索查询

        Returns:
            搜索结果行列表
        """
        try:
            logger.info(f"[{self.name}] 搜索: {query}")
            results=search_by_text(
                collection_name=self.collection_name,
                query_text=query,
                top_k=self.top_k,
                output_fields=["source_id", "content_json"]
            )
            logger.info(f"[{self.name}] 找到 {len(results)} 条原始结果")
            return results
        except Exception as e:
            logger.error(f"[{self.name}] 搜索失败: {e}", exc_info=True)
            return []


    def _get_data_type_name(self) -> str:
        return "数据"

    @abstractmethod
    def _run(self, query: str) -> str:
        pass
    async def _arun(self, query: str) -> str:
        """异步执行（暂不支持，同步执行）"""
        return self._run(query)
