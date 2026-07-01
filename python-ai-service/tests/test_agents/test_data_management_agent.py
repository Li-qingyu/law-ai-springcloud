"""
数据管理Agent测试 — LLM + Tools 模式
注意：这些测试会调用真实的 LLM 和 Java API，确保服务可用再运行。
"""
from app.agents.agents.data_management_agent import create_data_management_agent
from app.services.admin_agent_service.admin_log_service import AdminLogService


def test_data_management_agent_query_articles():
    """测试数据管理Agent - 查询法律条文"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "查询所有法律条文"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "查询所有法律条文",
        "user_id": 123,
        "log_id": task_id,
    })

    assert result is not None
    assert "result" in result
    assert result["result"]  # 应该有非空结果
    print(f"查询条文结果: {result['result']}")


def test_data_management_agent_count():
    """测试数据管理Agent - 统计数量"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "统计法律案例有多少条"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "统计法律案例有多少条",
        "user_id": 123,
        "log_id": task_id,
    })

    assert result is not None
    assert "result" in result
    print(f"统计结果: {result['result']}")


def test_data_management_agent_clarification():
    """测试数据管理Agent - 参数不足时追问"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "删掉那个"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "删掉那个",
        "user_id": 123,
        "log_id": task_id,
    })

    assert result is not None
    assert "result" in result
    # LLM 应该会追问而不是直接执行
    print(f"追问结果: {result['result']}")


def test_data_management_agent_unknown():
    """测试数据管理Agent - 模糊请求的处理"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "帮我处理一下数据"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "帮我处理一下数据",
        "user_id": 123,
        "log_id": task_id,
    })

    assert result is not None
    assert "result" in result
    # LLM 应该会追问具体要做什么
    print(f"模糊请求结果: {result['result']}")

def test_data_management_agent_query_article_486():
    """测试数据管理Agent - 查询民法典的第四百八十六条"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "查询民法典的第四百八十六条"
    })

    agent = create_data_management_agent(log_service)

    result = agent.invoke({
        "query": "查询民法典的第四百八十六条",
        "user_id": 123,
        "log_id": task_id,
    })

    assert result is not None
    assert "result" in result
    print(f"查询民法典的第四百八十六条: {result['result']}")


if __name__ == '__main__':
    test_data_management_agent_query_article_486()
