"""
数据管理工具
支持法律条文、法律案例、法律书籍、法律类型的增删改查
"""
import logging
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.admin_agent_service.java_api_client import get_java_api_client

logger = logging.getLogger(__name__)

# 合法的数据类型和操作
VALID_DATA_TYPES = {"law_article", "law_case", "law_book", "law_type"}
VALID_OPERATIONS = {"query", "query_all", "create", "update", "delete", "sync", "sync_status", "count", "import"}

# 每种 data_type 支持的操作
DATA_TYPE_OPERATIONS = {
    "law_article": {"query", "create", "update", "delete", "import", "sync", "sync_status", "count"},
    "law_case":    {"query", "create", "update", "delete", "sync", "sync_status", "count"},
    "law_book":    {"query", "query_all", "create", "update", "delete"},
    "law_type":    {"query", "query_all", "create", "update", "delete", "count"},
}

# 每种操作的必填和可选参数定义
OPERATION_PARAMS = {
    # ── law_article ──────────────────────────────────────
    ("law_article", "query"): {
        "required": {},
        "optional": {
            "page": "页码(Integer, 默认1)",
            "pageSize": "每页条数(Integer, 默认10)",
            "lawBookId": "所属书籍ID(Integer)",
            "articleTitle": "条文标题(String, 模糊搜索)",
        },
    },
    ("law_article", "create"): {
        "required": {
            "lawBookId": "所属书籍ID(Integer, 必填)",
            "articleTitle": "条文标题(String, 必填)",
            "content": "条文内容(String, 必填)",
            "publishDate": "发布日期(String, 格式yyyy-MM-dd)",
            "effectiveDate": "生效日期(String, 格式yyyy-MM-dd)",
        },
        "optional": {
            "bookTitle": "书籍标题(String)",
            "articleOrder": "条文排序(Integer)",
        },
    },
    ("law_article", "update"): {
        "required": {
            "id": "条文ID(Long, 必填)",
            "articleTitle": "条文标题(String, 必填，更新时必须传入原标题或新标题)",
            "content": "条文内容(String, 必填)",
        },
        "optional": {
            "lawBookId": "所属书籍ID(Integer)",
            "bookTitle": "书籍标题(String)",
            "publishDate": "发布日期(String, 格式yyyy-MM-dd)",
            "effectiveDate": "生效日期(String, 格式yyyy-MM-dd)",
            "articleOrder": "条文排序(Integer)",
        },
    },
    ("law_article", "delete"): {
        "required": {
            "ids": "条文ID列表(List[Long], 必填, 如[1,2,3])",
        },
        "optional": {},
    },
    ("law_article", "import"): {
        "required": {
            "lawBookId": "所属书籍ID(Integer, 必填)",
        },
        "optional": {},
    },
    ("law_article", "sync"): {
        "required": {
            "lawBookId": "所属书籍ID(Integer, 必填)",
        },
        "optional": {},
    },
    ("law_article", "sync_status"): {
        "required": {
            "taskId": "任务ID(String, 必填)",
        },
        "optional": {},
    },
    ("law_article", "count"): {
        "required": {},
        "optional": {},
    },
    # ── law_case ─────────────────────────────────────────
    ("law_case", "query"): {
        "required": {},
        "optional": {
            "page": "页码(Integer, 默认1)",
            "pageSize": "每页条数(Integer, 默认10)",
            "title": "案例标题(String, 模糊搜索)",
            "typeId": "类型ID(Long)",
            "tags": "标签(String)",
            "status": "状态(Integer, 0下架/1上架)",
        },
    },
    ("law_case", "create"): {
        "required": {
            "title": "案例标题(String, 必填)",
            "content": "案例内容(String, 必填)",
        },
        "optional": {
            "typeId": "类型ID(Integer)",
            "tags": "标签(String)",
            "judgment": "判决结果(String)",
            "cover": "封面图URL(String)",
            "status": "状态(Integer, 0下架/1上架)",
        },
    },
    ("law_case", "update"): {
        "required": {
            "id": "案例ID(Long, 必填)",
        },
        "optional": {
            "title": "案例标题(String)",
            "content": "案例内容(String)",
            "typeId": "类型ID(Integer)",
            "tags": "标签(String)",
            "judgment": "判决结果(String)",
            "cover": "封面图URL(String)",
            "status": "状态(Integer)",
        },
    },
    ("law_case", "delete"): {
        "required": {
            "id": "案例ID(Long, 必填)",
        },
        "optional": {},
    },
    ("law_case", "sync"): {
        "required": {},
        "optional": {},
    },
    ("law_case", "sync_status"): {
        "required": {
            "taskId": "任务ID(String, 必填)",
        },
        "optional": {},
    },
    ("law_case", "count"): {
        "required": {},
        "optional": {},
    },
    # ── law_book ─────────────────────────────────────────
    ("law_book", "query"): {
        "required": {},
        "optional": {
            "page": "页码(Integer, 默认1)",
            "pageSize": "每页条数(Integer, 默认10)",
            "name": "书籍名称(String, 模糊搜索)",
        },
    },
    ("law_book", "query_all"): {
        "required": {},
        "optional": {},
    },
    ("law_book", "create"): {
        "required": {
            "name": "书籍名称(String, 必填)",
        },
        "optional": {},
    },
    ("law_book", "update"): {
        "required": {
            "id": "书籍ID(Long, 必填)",
        },
        "optional": {
            "name": "书籍名称(String)",
        },
    },
    ("law_book", "delete"): {
        "required": {
            "ids": "书籍ID列表(List[Long], 必填, 如[1,2,3])",
        },
        "optional": {},
    },
    # ── law_type ─────────────────────────────────────────
    ("law_type", "query"): {
        "required": {},
        "optional": {
            "name": "类型名称(String, 模糊搜索)",
        },
    },
    ("law_type", "query_all"): {
        "required": {},
        "optional": {},
    },
    ("law_type", "create"): {
        "required": {
            "name": "类型名称(String, 必填)",
        },
        "optional": {
            "description": "类型描述(String)",
        },
    },
    ("law_type", "update"): {
        "required": {
            "id": "类型ID(Integer, 必填)",
        },
        "optional": {
            "name": "类型名称(String)",
            "description": "类型描述(String)",
        },
    },
    ("law_type", "delete"): {
        "required": {
            "id": "类型ID(Integer, 必填)",
        },
        "optional": {},
    },
    ("law_type", "count"): {
        "required": {},
        "optional": {},
    },
}


def _build_tool_description() -> str:
    """根据 OPERATION_PARAMS 动态生成工具描述，让 AI 精确知道每个操作需要什么参数"""
    lines = [
        "数据管理工具，支持法律条文、案例、书籍、类型的增删改查。",
        "",
        "【重要】调用时必须在 params 中传入对应操作要求的参数字段，否则 Java 端校验会失败。",
        "",
    ]

    # 按 data_type 分组
    for data_type in ["law_article", "law_case", "law_book", "law_type"]:
        type_names = {
            "law_article": "法律条文",
            "law_case": "法律案例",
            "law_book": "法律书籍",
            "law_type": "法律类型",
        }
        ops = DATA_TYPE_OPERATIONS[data_type]
        lines.append(f"## {type_names[data_type]} ({data_type})")

        for op in sorted(ops):
            param_def = OPERATION_PARAMS.get((data_type, op))
            if not param_def:
                continue
            required = param_def["required"]
            optional = param_def["optional"]

            if required:
                req_str = ", ".join(f"{k}: {v}" for k, v in required.items())
                lines.append(f"  - {op}: 必填参数 → {req_str}")
            else:
                lines.append(f"  - {op}: 无必填参数")

            if optional:
                opt_str = ", ".join(f"{k}: {v}" for k, v in optional.items())
                lines.append(f"    可选参数 → {opt_str}")

        lines.append("")

    return "\n".join(lines)


class DataManagementInput(BaseModel):
    """数据管理工具输入"""
    operation: str = Field(description="操作类型: query/query_all/create/update/delete/sync/sync_status/count/import")
    data_type: str = Field(description="数据类型: law_article/law_case/law_book/law_type")
    params: Optional[dict] = Field(default=None, description="操作参数，根据操作类型和数据类型传入不同字段，详见工具描述")


class DataManagementTool(BaseTool):
    """数据管理工具，支持法律条文、案例、书籍、类型的增删改查"""

    name: str = "data_management"
    description: str = _build_tool_description()
    args_schema: Type[BaseModel] = DataManagementInput

    def _validate_params(self, operation: str, data_type: str, params: Optional[dict]) -> Optional[str]:
        """
        校验参数是否满足 Java 端要求。
        返回 None 表示通过，返回错误信息字符串表示失败。
        """
        # 检查 data_type + operation 组合是否合法
        allowed_ops = DATA_TYPE_OPERATIONS.get(data_type, set())
        if operation not in allowed_ops:
            return (
                f"{data_type} 不支持 {operation} 操作，"
                f"支持的操作: {', '.join(sorted(allowed_ops))}。"
                f"请根据用户意图选择正确的操作类型。"
            )

        param_def = OPERATION_PARAMS.get((data_type, operation))
        if not param_def:
            return None  # 没有参数定义，跳过校验

        required = param_def["required"]
        if not required:
            return None  # 无必填参数

        effective = params or {}
        missing = [f"{k}({v})" for k, v in required.items() if k not in effective]
        if missing:
            return (
                f"缺少必填参数: {', '.join(missing)}。"
                f"请从用户的原始请求中提取这些字段，或向用户确认后重新调用工具。"
            )

        return None

    def _prepare_params(self, operation: str, data_type: str, params: Optional[dict]) -> dict:
        """
        准备最终参数：补默认值、类型转换等。
        """
        effective = dict(params) if params else {}

        # query 操作补默认分页，避免 Java 端 page=null 导致 NPE
        if operation == "query":
            effective.setdefault("page", 1)
            effective.setdefault("pageSize", 10)

        return effective

    def _run(
        self,
        operation: str,
        data_type: str,
        params: Optional[dict] = None,
    ) -> str:
        """同步执行数据管理操作"""
        logger.info(f"DataManagementTool._run 调用: operation={operation}, data_type={data_type}, params={params}")

        # 基础校验
        if data_type not in VALID_DATA_TYPES:
            return (
                f"不支持的数据类型: {data_type}，"
                f"支持的类型: {', '.join(sorted(VALID_DATA_TYPES))}。"
                f"请向用户确认要操作的数据类型后重新调用。"
            )
        if operation not in VALID_OPERATIONS:
            return (
                f"不支持的操作: {operation}，"
                f"支持的操作: {', '.join(sorted(VALID_OPERATIONS))}。"
                f"请根据用户意图选择正确的操作。"
            )

        # 参数校验（检查必填字段）
        validation_error = self._validate_params(operation, data_type, params)
        if validation_error:
            return f"参数错误: {validation_error}"

        logger.info(f"执行数据管理: operation={operation}, data_type={data_type}, params={params}")

        effective_params = self._prepare_params(operation, data_type, params)
        logger.info(f"准备参数完成: effective_params={effective_params}")

        client = get_java_api_client()

        try:
            result = client.execute_data_operation_sync(
                operation=operation,
                data_type=data_type,
                params=effective_params,
            )
            logger.info(f"Java API 返回结果: {result}")
            return self._format_result(operation, data_type, result)
        except Exception as e:
            logger.error(f"数据管理操作失败: {e}", exc_info=True)
            return f"操作失败: {str(e)}"

    async def _arun(
        self,
        operation: str,
        data_type: str,
        params: Optional[dict] = None,
    ) -> str:
        """异步执行数据管理操作"""
        if data_type not in VALID_DATA_TYPES:
            return (
                f"不支持的数据类型: {data_type}，"
                f"支持的类型: {', '.join(sorted(VALID_DATA_TYPES))}。"
                f"请向用户确认要操作的数据类型后重新调用。"
            )
        if operation not in VALID_OPERATIONS:
            return (
                f"不支持的操作: {operation}，"
                f"支持的操作: {', '.join(sorted(VALID_OPERATIONS))}。"
                f"请根据用户意图选择正确的操作。"
            )

        validation_error = self._validate_params(operation, data_type, params)
        if validation_error:
            return f"参数错误: {validation_error}"

        logger.info(f"执行数据管理(异步): operation={operation}, data_type={data_type}, params={params}")

        effective_params = self._prepare_params(operation, data_type, params)
        client = get_java_api_client()

        try:
            result = await client.execute_data_operation(
                operation=operation,
                data_type=data_type,
                params=effective_params,
            )
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

        logger.info(f"Java API 原始响应: {result}")

        # Java 端 code=1 表示成功
        if result.get("code") == 1 or result.get("code") == 200:
            data = result.get("data")
            if operation == "count":
                return f"{type_name}总数: {data}"
            elif operation in ("query", "query_all"):
                if isinstance(data, dict) and "total" in data:
                    records = data.get("records", data.get("list", []))
                    total = data['total']
                    count = len(records) if isinstance(records, list) else 0
                    summary = f"{type_name}查询成功，共 {total} 条记录，当前返回 {count} 条"
                    if records and isinstance(records, list):
                        import json
                        records_str = json.dumps(records, ensure_ascii=False, indent=2)
                        # 限制返回长度，避免 token 过多
                        if len(records_str) > 4000:
                            records_str = records_str[:4000] + "\n... (结果过长已截断)"
                        return f"{summary}\n\n数据内容:\n{records_str}"
                    return summary
                elif isinstance(data, list):
                    summary = f"{type_name}查询成功，共 {len(data)} 条记录"
                    if data:
                        import json
                        records_str = json.dumps(data, ensure_ascii=False, indent=2)
                        if len(records_str) > 4000:
                            records_str = records_str[:4000] + "\n... (结果过长已截断)"
                        return f"{summary}\n\n数据内容:\n{records_str}"
                    return summary
                return f"{type_name}查询成功"
            elif operation == "sync":
                return f"{type_name}同步任务已提交，任务ID: {data}"
            elif operation == "sync_status":
                return f"{type_name}同步状态: {data}"
            elif operation == "create":
                return f"{type_name}新增成功，ID: {data}"
            elif operation == "delete":
                return f"{type_name}删除成功"
            elif operation == "update":
                return f"{type_name}修改成功"
            elif operation == "import":
                return f"{type_name}导入成功"
            else:
                return f"{type_name}{op_name}成功"
        else:
            message = result.get("msg") or result.get("message") or "未知错误"
            return f"{type_name}{op_name}失败: {message}"


def create_data_management_tool() -> DataManagementTool:
    """创建数据管理工具实例"""
    return DataManagementTool()


if __name__ == '__main__':
    import json

    tool = DataManagementTool()

    def run_test(desc: str, **kwargs):
        """运行单条测试并打印结果"""
        print(f"\n{'-' * 60}")
        print(f"[测试] {desc}")
        print(f"[参数] {json.dumps(kwargs, ensure_ascii=False)}")
        result = tool._run(**kwargs)
        status = "PASS" if "失败" not in result and "不支持" not in result else "FAIL"
        print(f"[{status}] {result}")
        return result

    print("=" * 60)
    print("数据管理工具 - 查询类边界测试（只读，不污染数据）")
    print("=" * 60)

    # tool_prompt=_build_tool_description()
    # print(tool_prompt)
    # ─────────────────────────────────────────────
    # 1. 四种数据类型的 count
    # ─────────────────────────────────────────────
    run_test("统计法律条文数量", operation="count", data_type="law_article")
    run_test("统计法律案例数量", operation="count", data_type="law_case")
    run_test("统计法律书籍数量", operation="count", data_type="law_book")
    run_test("统计法律类型数量", operation="count", data_type="law_type")

    # ─────────────────────────────────────────────
    # 2. 四种数据类型的 query（默认分页）
    # ─────────────────────────────────────────────
    run_test("查询法律条文（默认）", operation="query", data_type="law_article")
    run_test("查询法律案例（默认）", operation="query", data_type="law_case")
    run_test("查询法律书籍（默认）", operation="query", data_type="law_book")
    run_test("查询法律类型（默认）", operation="query", data_type="law_type")

    # ─────────────────────────────────────────────
    # 3. query_all（law_book / law_type 支持）
    # ─────────────────────────────────────────────
    run_test("查询全部法律书籍", operation="query_all", data_type="law_book")
    run_test("查询全部法律类型", operation="query_all", data_type="law_type")

    # ─────────────────────────────────────────────
    # 4. 带分页参数的 query
    # ─────────────────────────────────────────────
    run_test("查询条文-第1页每页5条", operation="query", data_type="law_article",
             params={"pageNum": 1, "pageSize": 5})
    run_test("查询条文-第2页每页3条", operation="query", data_type="law_article",
             params={"pageNum": 2, "pageSize": 3})
    run_test("查询案例-第1页每页10条", operation="query", data_type="law_case",
             params={"pageNum": 1, "pageSize": 10})


    # # ─────────────────────────────────────────────
    # # 5. 边界：空 params / None params
    # # ─────────────────────────────────────────────
    # run_test("查询条文-空dict params", operation="query", data_type="law_article", params={})
    # run_test("查询条文-None params", operation="query", data_type="law_article", params=None)
    #
    # # ─────────────────────────────────────────────
    # # 6. sync_status 查询
    # # ─────────────────────────────────────────────
    # run_test("查询条文同步状态", operation="sync_status", data_type="law_article")
    # run_test("查询案例同步状态", operation="sync_status", data_type="law_case")
    #
    # # ─────────────────────────────────────────────
    # # 7. 错误：无效数据类型
    # # ─────────────────────────────────────────────
    # run_test("无效数据类型", operation="query", data_type="patent")
    # run_test("空数据类型", operation="query", data_type="")
    #
    # # ─────────────────────────────────────────────
    # # 8. 错误：无效操作
    # # ─────────────────────────────────────────────
    # run_test("无效操作类型", operation="drop_table", data_type="law_article")
    # run_test("空操作类型", operation="", data_type="law_article")
    #
    # # ─────────────────────────────────────────────
    # # 9. 不支持的 operation+data_type 组合
    # # ─────────────────────────────────────────────
    # run_test("law_article 不支持 query_all", operation="query_all", data_type="law_article")
    # run_test("law_case 不支持 query_all", operation="query_all", data_type="law_case")
    # run_test("law_book 不支持 sync", operation="sync", data_type="law_book")
    # run_test("law_book 不支持 count", operation="count", data_type="law_book")
    # run_test("law_type 不支持 sync", operation="sync", data_type="law_type")
    # run_test("law_type 不支持 import", operation="import", data_type="law_type")

    print(f"\n{'=' * 60}")
    print("测试完成")
    print(f"{'=' * 60}")
