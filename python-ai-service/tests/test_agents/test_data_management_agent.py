"""
数据管理Agent测试 — LLM + Tools 模式
注意：这些测试会调用真实的 LLM 和 Java API，确保服务可用再运行。
"""
from app.agents.agents.data_management_agent import create_data_management_agent
from app.services.admin_agent_service.admin_log_service import AdminLogService
from langgraph.types import Command


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

def test_data_management_agent_delete_article():
    """测试数据管理Agent - 删除法律条文（带人工确认）"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "删除中华人民共和国劳动合同法的第四八条和第四九条"
    })
    agent = create_data_management_agent(log_service)

    config = {"configurable": {"thread_id": "test-delete-1"}}

    # 第一次调用：LLM 查询记录 → 准备删除 → interrupt 暂停等待确认
    result = agent.invoke({
        "query": "删除中华人民共和国劳动合同法的第四十九条",
        "user_id": 123,
        "log_id": task_id,
    }, config=config)

    # 检查是否触发了 interrupt（LangGraph 返回 dict 带 __interrupt__ key）
    if isinstance(result, dict) and '__interrupt__' in result:
        interrupt_info = result['__interrupt__'][0].value.get("question")
        print(f"等待用户确认: {interrupt_info}")
        user_input = input("请确认删除 (yes/no): ")

        # 第二次调用：传入用户的实际输入
        result = agent.invoke(Command(resume=user_input), config=config)

        # 如果又触发了 interrupt，再处理一次
        if isinstance(result, dict) and '__interrupt__' in result:
            print(f"再次等待确认: {result['__interrupt__'][0].value}")
            user_input = input("请确认删除 (yes/no): ")
            result = agent.invoke(Command(resume=user_input), config=config)

    assert result is not None
    assert "result" in result
    print(f"删除结果: {result}")

def test_data_management_agent_insert_article():
    """测试数据管理Agent - 插入法律条文"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "插入一条法律条文,中华人民共和国劳动合同法的第四九条，内容如下： 用人单位违反本法规定解除或者终止劳动合同，劳动者要求继续履行劳动合同的，用人单位应当继续履行；劳动者不要求继续履行劳动合同或者劳动合同已经不能继续履行的，用人单位应当依照本法第八十七条规定支付赔偿金。"
    })
    agent = create_data_management_agent(log_service)
    result = agent.invoke({
        "query": "插入一条法律条文,中华人民共和国劳动合同法的第四九条，内容如下： 用人单位违反本法规定解除或者终止劳动合同，劳动者要求继续履行劳动合同的，用人单位应当继续履行；劳动者不要求继续履行劳动合同或者劳动合同已经不能继续履行的，用人单位应当依照本法第八十七条规定支付赔偿金。- 发布日期：2012-12-28- 生效日期：2013-07-01",
        "user_id": 123,
        "log_id": task_id,
    })
    assert result is not None
    assert "result" in result
    print(f"插入法律条文结果: {result['result']}")
    assert result["result"]  # 应该有非空结果
    print(f"插入法律条文结果: {result['result']}")

def test_data_management_agent_update_article():
    """测试数据管理Agent - 更新法律条文"""
    log_service = AdminLogService()
    task_id = log_service.create_log({
        "user_id": 123,
        "task_type": "data_management",
        "query": "更新法律条文,中华人民共和国劳动合同法的第四八条，内容如下：1111111111"
    })
    agent = create_data_management_agent(log_service)
    result = agent.invoke({
        "query": "更新法律条文,中华人民共和国劳动合同法的第四八条，内容如下：222222222222222",
        "user_id": 123,
        "log_id": task_id,
    })
    assert result is not None
    assert "result" in result
    print(f"更新法律条文结果: {result['result']}")
    assert result["result"]  # 应该有非空结果
    print(f"更新法律条文结果: {result['result']}")


if __name__ == '__main__':
    # test_data_management_agent_insert_article()

    # test_data_management_agent_update_article()
    test_data_management_agent_delete_article()

