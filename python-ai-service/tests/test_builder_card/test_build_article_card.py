
"""
数据卡片构建器测试
"""
import json
from app.builders.data_card_builder import DataCardBuilder


def test_build_law_article_cards():
    """测试法律条文卡片构建"""

    milvus_results = [
        {
            'id': 'law_article_1878',
            'score': 0.6456664204597473,
            'type': 'law_articles',
            'source_id': 1878,
            'content_json': {
                'id': 1878,
                'book_id': 1,
                'article_title': '第七百三十八条',
                'content': '依照法律、行政法规的规定，对于租赁物的经营使用应当取得行政许可的，出租人未取得行政许可不影响融资租赁合同的效力。'
            }
        },
        {
            'id': 'law_article_1870',
            'score': 0.6409986615180969,
            'type': 'law_articles',
            'source_id': 1870,
            'content_json': {
                'id': 1870,
                'book_id': 1,
                'article_title': '第七百三十条',
                'content': '当事人对租赁期限没有约定或者约定不明确，依据本法第五百一十条的规定仍不能确定的，视为不定期租赁；当事人可以随时解除合同，但是应当在合理期限之前通知对方。'
            }
        },
        {
            'id': 'law_article_1865',
            'score': 0.629721999168396,
            'type': 'law_articles',
            'source_id': 1865,
            'content_json': {
                'id': 1865,
                'book_id': 1,
                'article_title': '第七百二十五条',
                'content': '租赁物在承租人按照租赁合同占有期限内发生所有权变动的，不影响租赁合同的效力。'
            }
        }
    ]

    print("=" * 80)
    print("测试1: 构建法律条文数据卡片")
    print("=" * 80)

    cards = DataCardBuilder.from_milvus_result(milvus_results, "law_articles")

    print(f"\n✓ 成功构建 {len(cards)} 个法律条文卡片\n")

    for i, card in enumerate(cards, 1):
        print(f"--- 卡片 {i} ---")
        print(f"类型: {card.type}")
        print(f"ID: {card.id}")
        print(f"书籍ID: {card.book_id}")
        print(f"条文标题: {card.article_title}")
        print(f"内容: {card.content[:50]}...")
        print(f"相关度: {card.relevance:.4f}")
        print(f"详情URL: {card.detail_url}")
        print()

    return cards


def test_build_law_case_cards():
    """测试法律案例卡片构建"""

    milvus_results = [
        {
            'id': 'law_case_1001',
            'score': 0.85,
            'type': 'law_cases',
            'source_id': 1001,
            'content_json': {
                'id': 1001,
                'title': '张某与某公司房屋租赁合同纠纷案',
                'type_id': 2,
                'tags': '房屋租赁 押金返还 违约责任',
                'summary': '房东以卖房为由要求租客提前搬离并扣押押金的典型案例',
                'content': '原告张某与被告某公司签订房屋租赁合同...',
                'judgment': '判决被告返还原告押金5000元及利息',
                'cover': 'https://example.com/case1.jpg'
            }
        },
        {
            'id': 'law_case_1002',
            'score': 0.78,
            'type': 'law_cases',
            'source_id': 1002,
            'content_json': {
                'id': 1002,
                'title': '李某诉王某房屋租赁押金纠纷案',
                'type_id': 2,
                'tags': '房屋租赁 卫生清洁 押金扣除',
                'summary': '房东以卫生未打扫干净为由全额扣除押金的争议案件',
                'content': '本案涉及租赁合同终止后押金返还问题...',
                'judgment': '驳回被告全部扣款主张，判令全额返还押金',
                'cover': None
            }
        }
    ]

    print("=" * 80)
    print("测试2: 构建法律案例数据卡片")
    print("=" * 80)

    cards = DataCardBuilder.from_milvus_result(milvus_results, "law_cases")

    print(f"\n✓ 成功构建 {len(cards)} 个法律案例卡片\n")

    for i, card in enumerate(cards, 1):
        print(f"--- 卡片 {i} ---")
        print(f"类型: {card.type}")
        print(f"ID: {card.id}")
        print(f"标题: {card.title}")
        print(f"类型ID: {card.type_id}")
        print(f"标签: {card.tags}")
        print(f"摘要: {card.content[:50]}...")
        print(f"判决结果: {card.judgment}")
        print(f"封面: {card.cover}")
        print(f"相关度: {card.relevance:.4f}")
        print()

    return cards


def test_build_consult_history_cards():
    """测试咨询历史卡片构建"""

    milvus_results = [
        {
            'id': 'consult_5001',
            'score': 0.72,
            'type': 'consult_history',
            'source_id': 5001,
            'content_json': {
                'id': 5001,
                'user_id': 123,
                'session_id': 'session-abc-123',
                'question': '房东提前解约可以扣押金吗？',
                'answer': '根据《民法典》相关规定，房东无权单方面以卖房为由解除租赁合同。关于押金，除非合同明确约定且您确实造成了实际损失，否则房东无权扣除。'
            }
        },
        {
            'id': 'consult_5002',
            'score': 0.68,
            'type': 'consult_history',
            'source_id': 5002,
            'content_json': {
                'id': 5002,
                'user_id': 456,
                'session_id': 'session-def-456',
                'question': '买卖不破租赁是什么意思？',
                'answer': '买卖不破租赁是指租赁物在租赁期间发生所有权变动的，不影响租赁合同的效力。即新房东必须继续履行原租赁合同。'
            }
        }
    ]

    print("=" * 80)
    print("测试3: 构建咨询历史数据卡片")
    print("=" * 80)

    cards = DataCardBuilder.from_milvus_result(milvus_results, "consult_history")

    print(f"\n✓ 成功构建 {len(cards)} 个咨询历史卡片\n")

    for i, card in enumerate(cards, 1):
        print(f"--- 卡片 {i} ---")
        print(f"类型: {card.type}")
        print(f"ID: {card.id}")
        print(f"用户ID: {card.user_id}")
        print(f"会话ID: {card.session_id}")
        print(f"问题: {card.question}")
        print(f"答案: {card.answer[:80]}...")
        print(f"相关度: {card.relevance:.4f}")
        print()

    return cards


def test_empty_results():
    """测试空结果处理"""

    print("=" * 80)
    print("测试4: 空结果处理")
    print("=" * 80)

    cards = DataCardBuilder.from_milvus_result([], "law_articles")
    print(f"空列表结果: {len(cards)} 个卡片 ✓\n")

    cards = DataCardBuilder.from_milvus_result(
        [{'id': 'test', 'score': 0.5, 'type': 'law_articles', 'source_id': 1, 'content_json': {}}],
        "invalid_type"
    )
    print(f"无效类型结果: {len(cards)} 个卡片 ✓\n")


def test_deduplication():
    """测试去重功能（模拟同一法条被多次检索）"""

    print("=" * 80)
    print("测试5: 去重功能")
    print("=" * 80)

    milvus_results = [
        {
            'id': 'law_article_1865',
            'score': 0.85,
            'type': 'law_articles',
            'source_id': 1865,
            'content_json': {
                'id': 1865,
                'book_id': 1,
                'article_title': '第七百二十五条',
                'content': '租赁物在承租人按照租赁合同占有期限内发生所有权变动的，不影响租赁合同的效力。'
            }
        },
        {
            'id': 'law_article_1865',
            'score': 0.75,
            'type': 'law_articles',
            'source_id': 1865,
            'content_json': {
                'id': 1865,
                'book_id': 1,
                'article_title': '第七百二十五条',
                'content': '租赁物在承租人按照租赁合同占有期限内发生所有权变动的，不影响租赁合同的效力。'
            }
        }
    ]

    cards = DataCardBuilder.from_milvus_result(milvus_results, "law_articles")
    print(f"输入: 2 条重复记录")
    print(f"输出: {len(cards)} 个唯一卡片")
    print(f"最高相关度: {cards[0].relevance if cards else 0:.4f} ✓\n")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("数据卡片构建器 - 完整测试套件")
    print("=" * 80 + "\n")

    try:
        test_build_law_article_cards()
        test_build_law_case_cards()
        test_build_consult_history_cards()
        test_empty_results()
        test_deduplication()

        print("=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
