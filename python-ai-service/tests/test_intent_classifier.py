"""
意图识别器测试
验证规则匹配和LLM兜底是否正常工作
"""
from app.services.admin_agent_service.intent_classifier import IntentClassifier, IntentType


def get_llm():
    """创建LLM实例"""
    try:
        from langchain_deepseek import ChatDeepSeek
        from app.core.config import get_settings
        settings = get_settings()
        return ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
        )
    except Exception as e:
        print(f"创建LLM失败: {e}")
        return None


def test_classifier(llm_service=None):
    """测试意图分类器"""
    classifier = IntentClassifier(llm_service=llm_service)

    test_cases = [
        # (query, expected_intent, description)
        # 规则直接命中
        ("上传合同文件", "file_management", "规则命中-上传文件"),
        ("查询所有法律条文", "data_management", "规则命中-查询条文"),
        ("帮助", "help", "规则命中-帮助"),
        ("查询日志", "log_management", "规则命中-日志"),
        ("分配用户权限", "permission_management", "规则命中-权限"),

        # 需要LLM兜底的模糊表达
        ("我想看看系统里有哪些资料", "data_management", "LLM兜底-模糊资料"),
        ("把之前的那个东西删掉", "data_management", "LLM兜底-模糊删除"),
        ("帮我整理一下数据", "data_management", "LLM兜底-整理数据"),
        ("最近有什么操作记录吗", "log_management", "LLM兜底-操作记录"),
        ("这个文件我不想要了", "file_management", "LLM兜底-删除文件"),
    ]

    print(f"\n{'='*70}")
    print(f"意图识别器测试 (LLM: {'已启用' if llm_service else '未启用'})")
    print(f"{'='*70}")

    passed = 0
    failed = 0

    for query, expected, desc in test_cases:
        result = classifier.classify(query)
        actual = result.intent.value
        ok = actual == expected
        status = "PASS" if ok else "FAIL"

        if ok:
            passed += 1
        else:
            failed += 1

        print(f"\n[{status}] {desc}")
        print(f"  查询: {query}")
        print(f"  期望: {expected}")
        print(f"  实际: {actual} (置信度: {result.confidence:.2f}, 来源: {result.source})")
        if result.entities:
            print(f"  实体: {result.entities}")

    print(f"\n{'='*70}")
    print(f"结果: {passed} 通过, {failed} 失败, 共 {len(test_cases)} 条")
    print(f"{'='*70}")


if __name__ == "__main__":
    # 测试1: 无LLM，纯规则
    test_classifier(llm_service=None)

    # 测试2: 有LLM，规则+LLM混合
    llm = get_llm()
    if llm:
        test_classifier(llm_service=llm)
    else:
        print("\n跳过LLM测试：LLM服务不可用")
