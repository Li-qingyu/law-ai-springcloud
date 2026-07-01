"""
Java API 客户端
统一封装对 Java 微服务的 HTTP 调用
"""
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class JavaApiClient:
    """Java API 客户端"""

    # API 路径映射 - 基于实际Java端API
    API_PATHS = {
        # 法律案例 /admin/case
        "law_case": {
            "query": "/admin/case",
            "create": "/admin/case",
            "update": "/admin/case",
            "delete": "/admin/case/{id}",
            "sync": "/admin/case/sync",
            "sync_status": "/admin/case/sync/status",
            "count": "/admin/case/count",
        },
        # 法律条文 /admin/law-articles
        "law_article": {
            "query": "/admin/law-articles",
            "create": "/admin/law-articles",
            "update": "/admin/law-articles/{id}",
            "delete": "/admin/law-articles/{ids}",
            "import": "/admin/law-articles/import",
            "sync": "/admin/law-articles/sync",
            "sync_status": "/admin/law-articles/sync/status",
            "count": "/admin/law-articles/count",
        },
        # 法律书籍 /admin/law-books
        "law_book": {
            "query": "/admin/law-books",
            "query_all": "/admin/law-books/all",
            "create": "/admin/law-books",
            "update": "/admin/law-books",
            "delete": "/admin/law-books/{ids}",
        },
        # 法律类型 /admin/types
        "law_type": {
            "query": "/admin/types/list",
            "query_all": "/admin/types/all",
            "create": "/admin/types",
            "update": "/admin/types",
            "delete": "/admin/types/{id}",
            "count": "/admin/types/count",
        },
        # 日志管理 (待Java端实现)
        "log": {
            "system": "/admin/logs/system",
            "operation": "/admin/logs/operation",
            "api": "/admin/logs/api",
            "agent": "/admin/logs/agent",
            "statistics": "/admin/logs/statistics",
            "export": "/admin/logs/export",
            "cleanup": "/admin/logs/cleanup",
        },
    }

    # HTTP方法映射
    METHOD_MAP = {
        "query": "GET",
        "query_all": "GET",
        "create": "POST",
        "update": "PUT",
        "delete": "DELETE",
        "sync": "POST",         # 默认 POST，law_article 特殊为 GET（见 _get_method）
        "sync_status": "GET",
        "count": "GET",
        "import": "POST",
        "statistics": "GET",
        "export": "POST",
        "cleanup": "POST",
    }

    # 部分 data_type+operation 的 HTTP 方法与默认不同
    METHOD_OVERRIDE = {
        ("law_article", "sync"): "GET",   # Java: @GetMapping("/sync")
    }

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.JAVA_API_BASE_URL
        self.timeout = settings.JAVA_API_TIMEOUT
        self.retry_count = settings.JAVA_API_RETRY_COUNT

    def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法 (GET/POST/PUT/DELETE)
            path: API 路径
            params: 查询参数
            json_data: JSON 请求体
            path_params: 路径参数

        Returns:
            响应数据
        """
        # 替换路径参数
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        logger.info(f"Java API 请求: {method} {path}")

        headers = {"X-Internal-Call": "true"}

        async with self._get_client() as client:
            for attempt in range(self.retry_count):
                try:
                    response = await client.request(
                        method=method,
                        url=path,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info(f"Java API 响应: {result}")
                    return result
                except httpx.HTTPStatusError as e:
                    logger.error(f"Java API HTTP 错误: {e.response.status_code} - {e.response.text}")
                    if attempt == self.retry_count - 1:
                        raise
                except httpx.RequestError as e:
                    logger.error(f"Java API 请求错误: {e}")
                    if attempt == self.retry_count - 1:
                        raise

        return {"code": 500, "message": "请求失败"}

    async def execute_data_operation(
        self,
        operation: str,
        data_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行数据操作

        Args:
            operation: 操作类型 (query/query_all/create/update/delete/sync/sync_status/count/import)
            data_type: 数据类型 (law_case/law_article/law_book/law_type)
            params: 操作参数

        Returns:
            操作结果
        """
        api_paths = self.API_PATHS.get(data_type)
        if not api_paths:
            return {"code": 400, "message": f"不支持的数据类型: {data_type}"}

        path = api_paths.get(operation)
        if not path:
            return {"code": 400, "message": f"不支持的操作: {data_type}.{operation}"}

        # 获取HTTP方法（优先查 METHOD_OVERRIDE）
        method = self.METHOD_OVERRIDE.get((data_type, operation), self.METHOD_MAP.get(operation, "GET"))

        # 构建请求参数
        request_params = params or {}
        path_params = {}

        # 提取路径参数
        if "{id}" in path and "id" in request_params:
            path_params["id"] = request_params.pop("id")
        if "{ids}" in path and "ids" in request_params:
            path_params["ids"] = request_params.pop("ids")

        # 对于GET请求，剩余参数作为查询参数
        # 对于非GET请求，作为JSON请求体
        return await self.request(
            method=method,
            path=path,
            params=request_params if method == "GET" else None,
            json_data=request_params if method != "GET" else None,
            path_params=path_params,
        )

    def request_sync(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """同步发送 HTTP 请求"""
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        logger.info(f"Java API 同步请求: {method} {path}")

        headers = {"X-Internal-Call": "true"}

        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            for attempt in range(self.retry_count):
                try:
                    response = client.request(
                        method=method,
                        url=path,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info(f"Java API 响应: {result}")
                    return result
                except httpx.HTTPStatusError as e:
                    logger.error(f"Java API HTTP 错误: {e.response.status_code} - {e.response.text}")
                    if attempt == self.retry_count - 1:
                        raise
                except httpx.RequestError as e:
                    logger.error(f"Java API 请求错误: {e}")
                    if attempt == self.retry_count - 1:
                        raise

        return {"code": 500, "message": "请求失败"}

    def execute_data_operation_sync(
        self,
        operation: str,
        data_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """同步执行数据操作"""
        api_paths = self.API_PATHS.get(data_type)
        if not api_paths:
            return {"code": 400, "message": f"不支持的数据类型: {data_type}"}

        path = api_paths.get(operation)
        if not path:
            return {"code": 400, "message": f"不支持的操作: {data_type}.{operation}"}

        method = self.METHOD_OVERRIDE.get((data_type, operation), self.METHOD_MAP.get(operation, "GET"))
        request_params = params or {}
        path_params = {}

        if "{id}" in path and "id" in request_params:
            path_params["id"] = request_params.pop("id")
        if "{ids}" in path and "ids" in request_params:
            path_params["ids"] = request_params.pop("ids")

        return self.request_sync(
            method=method,
            path=path,
            params=request_params if method == "GET" else None,
            json_data=request_params if method != "GET" else None,
            path_params=path_params,
        )

    async def execute_log_operation(
        self,
        operation: str,
        log_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行日志操作

        Args:
            operation: 操作类型 (query/statistics/export/cleanup)
            log_type: 日志类型 (system/operation/api/agent)
            params: 操作参数

        Returns:
            操作结果
        """
        api_paths = self.API_PATHS.get("log", {})

        # 构建路径
        if operation in ("statistics", "export", "cleanup"):
            path = api_paths.get(operation)
        else:
            path = api_paths.get(log_type)

        if not path:
            return {"code": 400, "message": f"不支持的日志操作: {operation}_{log_type}"}

        # 获取HTTP方法
        method = self.METHOD_MAP.get(operation, "GET")

        return await self.request(
            method=method,
            path=path,
            params=params if method == "GET" else None,
            json_data=params if method != "GET" else None,
        )


# 全局客户端实例
_java_api_client: Optional[JavaApiClient] = None


def get_java_api_client() -> JavaApiClient:
    """获取 Java API 客户端单例"""
    global _java_api_client
    if _java_api_client is None:
        _java_api_client = JavaApiClient()
    return _java_api_client

if __name__ == '__main__':
    from app.tools.adminTool.data_management_tool import DataManagementTool

    tool = DataManagementTool()
    # 测试查询法律条文
    result = tool._run(operation="count", data_type="law_article")
    print(result)
