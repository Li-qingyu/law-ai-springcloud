"""
数据管理工具
支持法律条文、法律案例、法律书籍、法律类型的增删改查
"""
import logging
import asyncio
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.admin_agent_service.java_api_client import get_java_api_client

logger = logging.getLogger(__name__)


class DataManagementInput(BaseModel):
    """数据管理工具输入"""
    operation: str = Field(description="操作类型: query/query_all/create/update/delete/sync/sync_status/count")
    data_type: str = Field(description="数据类型: law_article/law_case/law_book/law_type")
    params: Optional[dict] = Field(default=None, description="操作参数")


class DataManagementTool(BaseTool):
    """数据管理工具，支持法律条文、案例、书籍、类型的增删改查"""

    name: str = "data_management"
    description: str = """数据管理工具，支持以下数据类型和操作：
    - law_article (法律条文): query/create/update/delete/import/sync/sync_status/count
    - law_case (法律案例): query/create/update/delete/sync/sync_status/count
    - law_book (法律书籍): query/query_all/create/update/delete
    - law_type (法律类型): query/query_all/create/update/delete/count
    """
    args_schema: Type[BaseModel] = DataManagementInput

    def _run(
        self,
        operation: str,
        data_type: str,
        params: Optional[dict] = None,
    ) -> str:
        """同步执行数据管理操作"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(operation, data_type, params))

    async def _arun(
        self,
        operation: str,
        data_type: str,
        params: Optional[dict] = None,
    ) -> str:
        """异步执行数据管理操作"""
        logger.info(f"执行数据管理: operation={operation}, data_type={data_type}, params={params}")

        client = get_java_api_client()

        try:
            result = await client.execute_data_operation(
                operation=operation,
                data_type=data_type,
                params=params or {},
            )

            # 格式化返回结果
            return self._format_result(operation, data_type, result)
        except Exception as e:
            logger.error(f"数据管理操作失败: {e}")
            return f"操作失败: {str(e)}"

    def _format_result(self, operation: str, data_type: str, result: dict) -> str:
        """格式化结果为可读字符串"""
        data_type_names = {
            "law_article": "法律条文",
            "law_case": "法律案例",
            "law_book": "法律书籍",
            "law_type": "法律类型",
        }
        operation_names = {
            "query": "查询",
            "query_all": "查询全部",
            "create": "新增",
            "update": "修改",
            "delete": "删除",
            "sync": "同步",
            "sync_status": "同步状态",
            "count": "统计",
            "import": "导入",
        }

        type_name = data_type_names.get(data_type, data_type)
        op_name = operation_names.get(operation, operation)

        if result.get("code") == 200:
            data = result.get("data")
            if operation == "count":
                return f"{type_name}总数: {data}"
            elif operation in ("query", "query_all"):
                if isinstance(data, dict) and "total" in data:
                    return f"{type_name}查询成功，共 {data['total']} 条记录"
                elif isinstance(data, list):
                    return f"{type_name}查询成功，共 {len(data)} 条记录"
                return f"{type_name}查询成功"
            elif operation == "sync":
                return f"{type_name}同步任务已提交，任务ID: {data}"
            elif operation == "sync_status":
                return f"{type_name}同步状态: {data}"
            else:
                return f"{type_name}{op_name}成功"
        else:
            message = result.get("message", "未知错误")
            return f"{type_name}{op_name}失败: {message}"


def create_data_management_tool() -> DataManagementTool:
    """创建数据管理工具实例"""
    return DataManagementTool()
