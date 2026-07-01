"""
数据管理工具测试
mock Java API 客户端，覆盖全部数据类型、操作和错误场景
"""
import pytest
from unittest.mock import patch, MagicMock

from app.tools.adminTool.data_management_tool import (
    DataManagementTool,
    create_data_management_tool,
    VALID_DATA_TYPES,
    VALID_OPERATIONS,
)


@pytest.fixture
def tool():
    return DataManagementTool()


# ============================================================
# 查询操作
# ============================================================

class TestQueryOperations:
    """查询操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_query_law_article(self, mock_get_client, tool):
        """查询法律条文"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 1,
            "data": {"total": 100, "records": [{"id": 1}, {"id": 2}]},
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query", data_type="law_article", params={"pageNum": 1, "pageSize": 10})
        assert "法律条文" in result
        assert "100" in result
        mock_client.execute_data_operation_sync.assert_called_once_with(
            operation="query", data_type="law_article", params={"pageNum": 1, "pageSize": 10}
        )

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_query_law_case_list(self, mock_get_client, tool):
        """查询法律案例（返回列表）"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 1,
            "data": [{"id": 1, "title": "案例1"}, {"id": 2, "title": "案例2"}],
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query", data_type="law_case")
        assert "法律案例" in result
        assert "2" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_query_law_book_all(self, mock_get_client, tool):
        """查询全部法律书籍"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 1,
            "data": [{"id": 1}],
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query_all", data_type="law_book")
        assert "法律书籍" in result
        assert "1" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_query_law_type(self, mock_get_client, tool):
        """查询法律类型"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 1,
            "data": {"total": 5, "records": []},
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query", data_type="law_type")
        assert "法律类型" in result


# ============================================================
# 新增操作
# ============================================================

class TestCreateOperations:
    """新增操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_create_law_article(self, mock_get_client, tool):
        """新增法律条文"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 1,
            "data": 42,
        }
        mock_get_client.return_value = mock_client

        result = tool._run(
            operation="create",
            data_type="law_article",
            params={"title": "民法典第一条", "content": "..."},
        )
        assert "法律条文" in result
        assert "新增成功" in result
        assert "42" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_create_law_case(self, mock_get_client, tool):
        """新增法律案例"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": 10}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="create", data_type="law_case", params={"title": "案例标题"})
        assert "法律案例" in result
        assert "新增成功" in result


# ============================================================
# 修改操作
# ============================================================

class TestUpdateOperations:
    """修改操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_update_law_article(self, mock_get_client, tool):
        """修改法律条文"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": None}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="update", data_type="law_article", params={"id": 1, "title": "更新标题"})
        assert "法律条文" in result
        assert "修改成功" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_update_law_type(self, mock_get_client, tool):
        """修改法律类型"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": None}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="update", data_type="law_type", params={"id": 1, "name": "新类型名"})
        assert "法律类型" in result
        assert "修改成功" in result


# ============================================================
# 删除操作
# ============================================================

class TestDeleteOperations:
    """删除操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_delete_law_article(self, mock_get_client, tool):
        """删除法律条文"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": None}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="delete", data_type="law_article", params={"ids": "1,2,3"})
        assert "法律条文" in result
        assert "删除成功" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_delete_law_book(self, mock_get_client, tool):
        """删除法律书籍"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": None}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="delete", data_type="law_book", params={"ids": "5"})
        assert "法律书籍" in result
        assert "删除成功" in result


# ============================================================
# 统计操作
# ============================================================

class TestCountOperations:
    """统计操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_count_law_article(self, mock_get_client, tool):
        """统计法律条文数量"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": 256}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="count", data_type="law_article")
        assert "法律条文" in result
        assert "256" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_count_law_type(self, mock_get_client, tool):
        """统计法律类型数量"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": 12}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="count", data_type="law_type")
        assert "法律类型" in result
        assert "12" in result


# ============================================================
# 同步操作
# ============================================================

class TestSyncOperations:
    """同步操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_sync_law_article(self, mock_get_client, tool):
        """同步法律条文到向量库"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": "sync_task_001"}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="sync", data_type="law_article")
        assert "法律条文" in result
        assert "同步" in result
        assert "sync_task_001" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_sync_status_law_case(self, mock_get_client, tool):
        """查询法律案例同步状态"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": "completed"}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="sync_status", data_type="law_case")
        assert "法律案例" in result
        assert "completed" in result


# ============================================================
# 导入操作
# ============================================================

class TestImportOperations:
    """导入操作测试"""

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_import_law_article(self, mock_get_client, tool):
        """导入法律条文"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {"code": 1, "data": None}
        mock_get_client.return_value = mock_client

        result = tool._run(operation="import", data_type="law_article", params={"fileUrl": "http://example.com/data.xlsx"})
        assert "法律条文" in result
        assert "导入成功" in result


# ============================================================
# 错误场景
# ============================================================

class TestErrorScenarios:
    """错误场景测试"""

    def test_invalid_data_type(self, tool):
        """无效的数据类型"""
        result = tool._run(operation="query", data_type="invalid_type")
        assert "不支持的数据类型" in result
        assert "invalid_type" in result

    def test_invalid_operation(self, tool):
        """无效的操作类型"""
        result = tool._run(operation="magic", data_type="law_article")
        assert "不支持的操作" in result
        assert "magic" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_api_error_response(self, mock_get_client, tool):
        """API 返回错误"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 0,
            "msg": "数据库连接失败",
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query", data_type="law_article")
        assert "失败" in result
        assert "数据库连接失败" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_api_exception(self, mock_get_client, tool):
        """API 调用抛异常"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.side_effect = ConnectionError("网络不通")
        mock_get_client.return_value = mock_client

        result = tool._run(operation="query", data_type="law_article")
        assert "操作失败" in result
        assert "网络不通" in result

    @patch("app.tools.adminTool.data_management_tool.get_java_api_client")
    def test_api_error_with_msg_field(self, mock_get_client, tool):
        """API 返回错误（使用 msg 字段）"""
        mock_client = MagicMock()
        mock_client.execute_data_operation_sync.return_value = {
            "code": 0,
            "msg": "参数错误: 缺少必填字段",
        }
        mock_get_client.return_value = mock_client

        result = tool._run(operation="create", data_type="law_article", params={})
        assert "失败" in result
        assert "参数错误" in result


# ============================================================
# 工厂函数
# ============================================================

class TestFactory:
    """工厂函数测试"""

    def test_create_data_management_tool(self):
        """测试工厂函数创建工具实例"""
        tool = create_data_management_tool()
        assert isinstance(tool, DataManagementTool)
        assert tool.name == "data_management"


# ============================================================
# 常量验证
# ============================================================

class TestConstants:
    """常量验证测试"""

    def test_valid_data_types(self):
        """验证支持的数据类型"""
        assert VALID_DATA_TYPES == {"law_article", "law_case", "law_book", "law_type"}

    def test_valid_operations(self):
        """验证支持的操作类型"""
        expected = {"query", "query_all", "create", "update", "delete", "sync", "sync_status", "count", "import"}
        assert VALID_OPERATIONS == expected
