"""
对话记忆管理模块单元测试

覆盖范围：
- WorkingMemory: 窗口管理、token 截断、当前轮保护
- build_memory_header: 会话元信息摘要头
- extract_reference_anchor: 法条引用锚点
- ShortTermMemory: add_round、compress_pending（mock Redis + LLM）
- 纯函数: _normalize_key、_merge_facts、_merge_law_points 等
- 集成: build_chat_history_text

运行: cd python-ai-service && python -m pytest tests/test_memory/test_memory.py -v
"""
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock


# ==================== 辅助 ====================

def _msg(role: str, content: str) -> SimpleNamespace:
    """构造模拟 ConversationHistoryMessage"""
    return SimpleNamespace(role=role, content=content, timestamp=None)


def _q(text: str) -> SimpleNamespace:
    return _msg("user", text)


def _a(text: str) -> SimpleNamespace:
    return _msg("assistant", text)


# ==================== WorkingMemory ====================

class TestWorkingMemory:

    def test_empty_history(self):
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=2500)
        assert wm.build_context([]) == ""

    def test_single_round_preserved(self):
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=2500)
        history = [_q("什么是劳动合同"), _a("劳动合同是...")]
        result = wm.build_context(history)
        assert "什么是劳动合同" in result
        assert "劳动合同是" in result

    def test_multiple_rounds_within_limit(self):
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=2500)
        history = [
            _q("问题1"), _a("回答1"),
            _q("问题2"), _a("回答2"),
            _q("问题3"), _a("回答3"),
        ]
        result = wm.build_context(history)
        assert "问题1" in result
        assert "问题3" in result

    def test_current_turn_always_protected(self):
        """当前轮（最后 2 条消息）必须完整保留，即使超出 token 上限"""
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=2, max_tokens=200)
        # 当前轮很长，超过 token 上限
        long_answer = "很长的回答" * 200
        history = [
            _q("旧问题1"), _a("旧回答1"),
            _q("旧问题2"), _a("旧回答2"),
            _q("当前问题"), _a(long_answer),
        ]
        result = wm.build_context(history)
        # 当前轮必须在
        assert "当前问题" in result
        assert long_answer in result

    def test_earlier_rounds_truncated_by_turn_limit(self):
        """超出 max_turns 的早期轮次应被丢弃"""
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=2, max_tokens=5000)
        history = [
            _q("第1轮问题"), _a("第1轮回答"),
            _q("第2轮问题"), _a("第2轮回答"),
            _q("第3轮问题"), _a("第3轮回答"),
            _q("第4轮问题"), _a("第4轮回答"),  # 当前轮
        ]
        result = wm.build_context(history)
        # max_turns=2 → 保留当前轮 + 1 轮早期 → 第3轮和第4轮
        assert "第1轮问题" not in result
        assert "第2轮问题" not in result
        assert "第3轮问题" in result
        assert "第4轮问题" in result

    def test_token_limit_enforcement(self):
        """早期轮次超出 token 预算时应被截断"""
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=100)
        long_text = "这是一段很长的法律分析" * 50
        history = [
            _q("旧问题"), _a(long_text),
            _q("当前问题"), _a("当前回答"),
        ]
        result = wm.build_context(history)
        # 旧轮次太长，应被截断
        assert "旧问题" not in result
        assert "当前问题" in result

    def test_get_working_turns_for_history(self):
        """返回原始消息对象列表"""
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=2500)
        history = [
            _q("问题1"), _a("回答1"),
            _q("问题2"), _a("回答2"),
        ]
        turns = wm.get_working_turns_for_history(history)
        assert len(turns) == 4
        assert turns[0].role == "user"
        assert turns[0].content == "问题1"

    def test_get_working_turns_empty(self):
        from app.memory.working_memory import WorkingMemory
        wm = WorkingMemory(max_turns=3, max_tokens=2500)
        assert wm.get_working_turns_for_history([]) == []


# ==================== build_memory_header ====================

class TestBuildMemoryHeader:

    def test_empty_summary(self):
        from app.memory.working_memory import build_memory_header
        assert build_memory_header({}, 0) == ""

    def test_none_summary(self):
        from app.memory.working_memory import build_memory_header
        assert build_memory_header(None, 0) == ""

    def test_full_summary(self):
        from app.memory.working_memory import build_memory_header
        summary = {
            "核心诉求": "离婚财产分割",
            "已确认事实": [
                {"事实": "婚后购房一套", "依据": "用户陈述", "状态": "已确认"},
                {"事实": "无子女", "依据": "用户陈述", "状态": "已确认"},
            ],
            "已讨论法律要点": [
                {"法条或原则": "民法典第1087条", "适用结论": "共同财产均等分割", "是否存疑": False},
            ],
        }
        header = build_memory_header(summary, 4)
        assert "4 轮" in header
        assert "离婚财产分割" in header
        assert "婚后购房一套" in header
        assert "民法典第1087条" in header

    def test_partial_summary(self):
        """只有核心诉求，无事实和法条"""
        from app.memory.working_memory import build_memory_header
        summary = {"核心诉求": "劳动纠纷"}
        header = build_memory_header(summary, 1)
        assert "劳动纠纷" in header
        assert "无" in header  # 事实和法条显示"无"


# ==================== extract_reference_anchor ====================

class TestExtractReferenceAnchor:

    def test_short_history(self):
        """少于 4 条消息时返回空"""
        from app.memory.working_memory import extract_reference_anchor
        history = [_q("问题"), _a("回答")]
        assert extract_reference_anchor(history) == ""

    def test_empty_history(self):
        from app.memory.working_memory import extract_reference_anchor
        assert extract_reference_anchor([]) == ""

    def test_with_law_reference(self):
        from app.memory.working_memory import extract_reference_anchor
        history = [
            _q("问题1"), _a("回答1"),
            _q("问题2"), _a("根据《劳动合同法》第46条，用人单位应当支付经济补偿。"),
        ]
        anchor = extract_reference_anchor(history)
        assert "劳动合同法" in anchor
        assert "第46条" in anchor

    def test_no_law_reference(self):
        from app.memory.working_memory import extract_reference_anchor
        history = [
            _q("问题1"), _a("回答1"),
            _q("问题2"), _a("这是一般性的回答，没有引用法条。"),
        ]
        assert extract_reference_anchor(history) == ""

    def test_multiple_refs_only_last_two(self):
        """多条法条引用只保留最后 2 条"""
        from app.memory.working_memory import extract_reference_anchor
        history = [
            _q("问题1"), _a("根据《民法典》第107条和《劳动法》第3条..."),
            _q("问题2"), _a("根据《劳动合同法》第46条和《民法典》第1087条..."),
        ]
        anchor = extract_reference_anchor(history)
        assert "劳动合同法" in anchor
        assert "民法典" in anchor


# ==================== _normalize_key ====================

class TestNormalizeKey:

    def test_removes_punctuation(self):
        from app.memory.short_term_memory import _normalize_key
        assert _normalize_key("婚后购房一套，") == _normalize_key("婚后购房一套")

    def test_removes_whitespace(self):
        from app.memory.short_term_memory import _normalize_key
        assert _normalize_key("婚后 购房 一套") == _normalize_key("婚后购房一套")

    def test_case_insensitive(self):
        from app.memory.short_term_memory import _normalize_key
        assert _normalize_key("ABC") == _normalize_key("abc")

    def test_different_texts_different_keys(self):
        from app.memory.short_term_memory import _normalize_key
        assert _normalize_key("婚后购房一套") != _normalize_key("婚后购车一辆")

    def test_empty_string(self):
        from app.memory.short_term_memory import _normalize_key
        assert _normalize_key("") == ""


# ==================== _merge_facts ====================

class TestMergeFacts:

    def test_no_duplicates(self):
        from app.memory.short_term_memory import _merge_facts
        old = [{"事实": "婚后购房一套", "依据": "用户陈述"}]
        new = [{"事实": "无子女", "依据": "用户陈述"}]
        result = _merge_facts(old, new)
        assert len(result) == 2

    def test_exact_duplicate_removed(self):
        from app.memory.short_term_memory import _merge_facts
        old = [{"事实": "婚后购房一套", "依据": "用户陈述"}]
        new = [{"事实": "婚后购房一套", "依据": "用户陈述"}]
        result = _merge_facts(old, new)
        assert len(result) == 1

    def test_punctuation_difference_deduped(self):
        """标点差异应被去重"""
        from app.memory.short_term_memory import _merge_facts
        old = [{"事实": "婚后购房一套，", "依据": "用户陈述"}]
        new = [{"事实": "婚后购房一套", "依据": "模型推断"}]
        result = _merge_facts(old, new)
        assert len(result) == 1

    def test_similar_start_different_content_kept(self):
        """前几字相同但全文不同的事实应保留"""
        from app.memory.short_term_memory import _merge_facts
        old = [{"事实": "婚后购房一套位于北京市朝阳区", "依据": "用户陈述"}]
        new = [{"事实": "婚后购车一辆为奔驰C200", "依据": "用户陈述"}]
        result = _merge_facts(old, new)
        assert len(result) == 2

    def test_new_before_old_order(self):
        """新事实应排在旧事实前面"""
        from app.memory.short_term_memory import _merge_facts
        old = [{"事实": "旧事实"}]
        new = [{"事实": "新事实"}]
        result = _merge_facts(old, new)
        assert result[0]["事实"] == "新事实"
        assert result[1]["事实"] == "旧事实"

    def test_empty_facts(self):
        from app.memory.short_term_memory import _merge_facts
        assert _merge_facts([], []) == []
        assert _merge_facts([{"事实": "A"}], []) == [{"事实": "A"}]
        assert _merge_facts([], [{"事实": "B"}]) == [{"事实": "B"}]


# ==================== _merge_law_points ====================

class TestMergeLawPoints:

    def test_no_duplicates(self):
        from app.memory.short_term_memory import _merge_law_points
        old = [{"法条或原则": "民法典第1087条", "适用结论": "均等分割"}]
        new = [{"法条或原则": "劳动合同法第46条", "适用结论": "支付补偿"}]
        result = _merge_law_points(old, new)
        assert len(result) == 2

    def test_duplicate_law_deduped(self):
        from app.memory.short_term_memory import _merge_law_points
        old = [{"法条或原则": "民法典第1087条", "适用结论": "均等分割"}]
        new = [{"法条或原则": "民法典第1087条", "适用结论": "共同财产均等分割"}]
        result = _merge_law_points(old, new)
        assert len(result) == 1


# ==================== _merge_special_terms ====================

class TestMergeSpecialTerms:

    def test_both_empty(self):
        from app.memory.short_term_memory import _merge_special_terms
        assert _merge_special_terms("", "") == ""

    def test_old_empty(self):
        from app.memory.short_term_memory import _merge_special_terms
        assert _merge_special_terms("", "新表述") == "新表述"

    def test_new_empty(self):
        from app.memory.short_term_memory import _merge_special_terms
        assert _merge_special_terms("旧表述", "") == "旧表述"

    def test_new_subset_of_old(self):
        from app.memory.short_term_memory import _merge_special_terms
        assert _merge_special_terms("对方说房子是他父母出的钱", "房子") == "对方说房子是他父母出的钱"

    def test_different_terms_merged(self):
        from app.memory.short_term_memory import _merge_special_terms
        result = _merge_special_terms("对方说房子是他父母出的钱", "对方强调口头约定有效")
        assert "；" in result
        assert "父母出的钱" in result
        assert "口头约定" in result


# ==================== _deduplicate_list ====================

class TestDeduplicateList:

    def test_no_duplicates(self):
        from app.memory.short_term_memory import _deduplicate_list
        assert _deduplicate_list(["A", "B", "C"]) == ["A", "B", "C"]

    def test_with_duplicates(self):
        from app.memory.short_term_memory import _deduplicate_list
        assert _deduplicate_list(["A", "B", "A", "C", "B"]) == ["A", "B", "C"]

    def test_empty(self):
        from app.memory.short_term_memory import _deduplicate_list
        assert _deduplicate_list([]) == []


# ==================== _merge_summaries ====================

class TestMergeSummaries:

    def test_empty_existing(self):
        from app.memory.short_term_memory import _merge_summaries
        new = {"核心诉求": "离婚", "已确认事实": [], "已讨论法律要点": [], "待跟进事项": [], "当事人特殊表述": ""}
        result = _merge_summaries({}, new)
        assert result["核心诉求"] == "离婚"

    def test_full_merge(self):
        from app.memory.short_term_memory import _merge_summaries
        existing = {
            "核心诉求": "离婚",
            "已确认事实": [{"事实": "婚后购房"}],
            "已讨论法律要点": [{"法条或原则": "民法典第1087条"}],
            "待跟进事项": ["确认房产证"],
            "当事人特殊表述": "",
        }
        new = {
            "核心诉求": "离婚财产分割",
            "已确认事实": [{"事实": "无子女"}],
            "已讨论法律要点": [{"法条或原则": "劳动合同法第46条"}],
            "待跟进事项": ["确认工资流水"],
            "当事人特殊表述": "对方说房子是他父母出的钱",
        }
        result = _merge_summaries(existing, new)
        assert result["核心诉求"] == "离婚财产分割"  # new 优先
        assert len(result["已确认事实"]) == 2
        assert len(result["已讨论法律要点"]) == 2
        assert len(result["待跟进事项"]) == 2

    def test_size_limit_facts(self):
        """事实超过 5 条时截断"""
        from app.memory.short_term_memory import _merge_summaries
        existing = {"已确认事实": [{"事实": f"事实{i}"} for i in range(4)]}
        new = {"已确认事实": [{"事实": f"新事实{i}"} for i in range(3)]}
        result = _merge_summaries(existing, new)
        assert len(result["已确认事实"]) <= 5

    def test_size_limit_law_points(self):
        """法律要点超过 4 条时截断"""
        from app.memory.short_term_memory import _merge_summaries
        existing = {"已讨论法律要点": [{"法条或原则": f"法条{i}"} for i in range(3)]}
        new = {"已讨论法律要点": [{"法条或原则": f"新法条{i}"} for i in range(3)]}
        result = _merge_summaries(existing, new)
        assert len(result["已讨论法律要点"]) <= 4


# ==================== _format_rounds_for_summary ====================

class TestFormatRoundsForSummary:

    def test_basic_format(self):
        from app.memory.short_term_memory import _format_rounds_for_summary
        rounds = [{"q": "什么是劳动合同", "a": "劳动合同是..."}]
        result = _format_rounds_for_summary(rounds)
        assert "【第1轮】" in result
        assert "用户：什么是劳动合同" in result
        assert "助手：劳动合同是..." in result

    def test_long_answer_truncated(self):
        from app.memory.short_term_memory import _format_rounds_for_summary
        rounds = [{"q": "问题", "a": "A" * 2000}]
        result = _format_rounds_for_summary(rounds)
        assert "..." in result
        assert len(result) < 1500  # 截断后不应太长

    def test_multiple_rounds(self):
        from app.memory.short_term_memory import _format_rounds_for_summary
        rounds = [
            {"q": "问题1", "a": "回答1"},
            {"q": "问题2", "a": "回答2"},
        ]
        result = _format_rounds_for_summary(rounds)
        assert "【第1轮】" in result
        assert "【第2轮】" in result


# ==================== ShortTermMemory（mock Redis） ====================

def _create_mock_redis():
    """创建带内存存储的 mock Redis，每次调用返回全新实例"""
    store = {}

    def mock_get(key):
        return store.get(key)

    def mock_set(key, value):
        store[key] = value

    def mock_expire(key, ttl):
        pass

    r = MagicMock()
    r.get = MagicMock(side_effect=mock_get)
    r.set = MagicMock(side_effect=mock_set)
    r.expire = MagicMock(side_effect=mock_expire)
    return r, store


class TestShortTermMemory:

    def _make_stm(self, session_id="test-session"):
        """每次创建全新的 mock Redis + ShortTermMemory，确保完全隔离"""
        r, store = _create_mock_redis()
        # 清除 lru_cache 确保 patch 生效
        from app.repositories.redis_client import get_redis
        get_redis.cache_clear()
        patcher = patch("app.memory.short_term_memory.get_redis", return_value=r)
        patcher.start()
        from app.memory.short_term_memory import ShortTermMemory
        stm = ShortTermMemory(session_id)
        return stm, store, patcher

    def test_fresh_session(self):
        stm, store, patcher = self._make_stm()
        try:
            assert stm.get_summary() == {}
            assert stm.get_round_count() == 0
            assert stm.get_pending_rounds() == []
        finally:
            patcher.stop()

    def test_add_round_below_threshold(self):
        stm, store, patcher = self._make_stm()
        try:
            need_compress = stm.add_round("问题1", "回答1")
            assert need_compress is False
            assert stm.get_round_count() == 1
            assert len(stm.get_pending_rounds()) == 1
        finally:
            patcher.stop()

    def test_add_round_at_threshold(self):
        stm, store, patcher = self._make_stm()
        try:
            for i in range(5):
                need_compress = stm.add_round(f"问题{i}", f"回答{i}")
            assert need_compress is True
            assert stm.get_round_count() == 5
            assert len(stm.get_pending_rounds()) == 5
        finally:
            patcher.stop()

    @pytest.mark.asyncio
    async def test_compress_pending(self):
        stm, store, patcher = self._make_stm()
        try:
            for i in range(5):
                stm.add_round(f"问题{i}", f"回答{i}")

            mock_summary = {
                "核心诉求": "测试诉求",
                "已确认事实": [{"事实": "测试事实", "依据": "用户陈述", "状态": "已确认"}],
                "已讨论法律要点": [],
                "待跟进事项": [],
                "当事人特殊表述": "",
            }

            with patch("app.memory.short_term_memory._call_llm_summary",
                       new_callable=AsyncMock, return_value=mock_summary):
                result = await stm.compress_pending()

            assert result["核心诉求"] == "测试诉求"
            assert len(result["已确认事实"]) == 1
            assert stm.get_pending_rounds() == []
            assert stm.get_round_count() == 5
        finally:
            patcher.stop()

    @pytest.mark.asyncio
    async def test_compress_pending_empty(self):
        """没有 pending rounds 时压缩应直接返回空摘要"""
        stm, store, patcher = self._make_stm()
        try:
            result = await stm.compress_pending()
            assert result == {}
        finally:
            patcher.stop()

    @pytest.mark.asyncio
    async def test_incremental_compression(self):
        """多次压缩应增量合并摘要"""
        stm, store, patcher = self._make_stm()
        try:
            summary1 = {
                "核心诉求": "离婚",
                "已确认事实": [{"事实": "婚后购房", "依据": "用户陈述", "状态": "已确认"}],
                "已讨论法律要点": [],
                "待跟进事项": [],
                "当事人特殊表述": "",
            }
            summary2 = {
                "核心诉求": "离婚财产分割",
                "已确认事实": [{"事实": "无子女", "依据": "用户陈述", "状态": "已确认"}],
                "已讨论法律要点": [{"法条或原则": "民法典第1087条", "适用结论": "均等分割", "是否存疑": False}],
                "待跟进事项": ["确认房产证"],
                "当事人特殊表述": "",
            }

            # 第一次压缩
            with patch("app.memory.short_term_memory._call_llm_summary",
                       new_callable=AsyncMock, return_value=summary1):
                for i in range(5):
                    stm.add_round(f"q{i}", f"a{i}")
                await stm.compress_pending()

            # 第二次压缩
            with patch("app.memory.short_term_memory._call_llm_summary",
                       new_callable=AsyncMock, return_value=summary2):
                for i in range(5):
                    stm.add_round(f"q{i+5}", f"a{i+5}")
                await stm.compress_pending()

            final = stm.get_summary()
            assert final["核心诉求"] == "离婚财产分割"
            assert len(final["已确认事实"]) == 2
            assert len(final["已讨论法律要点"]) == 1
            assert stm.get_round_count() == 10
        finally:
            patcher.stop()


# ==================== 集成: build_chat_history_text ====================

# agent_service.py 导入链依赖 pymilvus/langchain 等重型依赖
# 通过 mock 导入链来隔离
_MOCK_MODULES = {
    "pymilvus": MagicMock(),
    "pymilvus.connections": MagicMock(),
    "pymilvus.Collection": MagicMock(),
    "pymilvus.AnnSearchRequest": MagicMock(),
    "pymilvus.RRFRanker": MagicMock(),
    "pymilvus.FieldSchema": MagicMock(),
    "pymilvus.CollectionSchema": MagicMock(),
    "pymilvus.DataType": MagicMock(),
    "pymilvus.utility": MagicMock(),
    "langchain_classic": MagicMock(),
    "langchain_classic.agents": MagicMock(),
    "langchain_core": MagicMock(),
    "langchain_core.messages": MagicMock(),
    "langchain_core.prompts": MagicMock(),
    "langchain_core.tools": MagicMock(),
    "langchain_community": MagicMock(),
    "langchain_community.chat_models": MagicMock(),
    "langchain_community.chat_models.tongyi": MagicMock(),
    "langchain_community.embeddings": MagicMock(),
    "dashscope": MagicMock(),
    "httpx": MagicMock(),
    "app.utils.embedding": MagicMock(),
    "app.repositories.milvus_client": MagicMock(),
    "app.retrieval": MagicMock(),
    "app.retrieval.retriever": MagicMock(),
    "app.retrieval.strategies": MagicMock(),
    "app.retrieval.strategies.base": MagicMock(),
    "app.retrieval.strategies.vector_strategy": MagicMock(),
    "app.retrieval.strategies.hybrid_strategy": MagicMock(),
    "app.retrieval.strategies.multi_query_strategy": MagicMock(),
    "app.retrieval.pipelines": MagicMock(),
    "app.retrieval.pipelines.base": MagicMock(),
    "app.retrieval.pipelines.dedup": MagicMock(),
    "app.retrieval.pipelines.rerank": MagicMock(),
    "app.retrieval.pipelines.fusion": MagicMock(),
    "app.retrieval.params": MagicMock(),
    "app.tools": MagicMock(),
    "app.tools.base_search_tool": MagicMock(),
    "app.services.parallel_search": MagicMock(),
    "app.services.semantic_cache": MagicMock(),
    "app.builders": MagicMock(),
    "app.builders.data_card_builder": MagicMock(),
}


@pytest.fixture(autouse=False)
def mock_heavy_imports():
    """Mock 掉 pymilvus、langchain 等重型依赖"""
    # 清除已缓存的模块，强制重新导入
    modules_to_clear = [m for m in sys.modules if m.startswith("app.")]
    for m in modules_to_clear:
        del sys.modules[m]

    with patch.dict("sys.modules", _MOCK_MODULES):
        yield


class TestBuildChatHistoryText:

    def test_no_history_no_header(self, mock_heavy_imports):
        from app.services.rag_agent_service.agent_service import build_chat_history_text
        result = build_chat_history_text([], "")
        assert result == "无对话历史"

    def test_with_memory_header(self, mock_heavy_imports):
        from app.services.rag_agent_service.agent_service import build_chat_history_text
        history = [_q("问题"), _a("回答")]
        header = "【本次咨询已进行 2 轮，核心诉求：离婚】"
        result = build_chat_history_text(history, header)
        assert "离婚" in result
        assert "问题" in result

    def test_without_memory_header(self, mock_heavy_imports):
        from app.services.rag_agent_service.agent_service import build_chat_history_text
        history = [_q("问题"), _a("回答")]
        result = build_chat_history_text(history, "")
        assert "问题" in result

    def test_anchor_included(self, mock_heavy_imports):
        """有法条引用时应包含引用锚点"""
        from app.services.rag_agent_service.agent_service import build_chat_history_text
        history = [
            _q("问题1"), _a("回答1"),
            _q("问题2"), _a("根据《劳动合同法》第46条，应支付补偿。"),
        ]
        result = build_chat_history_text(history, "")
        assert "前述已引用" in result

    def test_history_messages_use_working_memory(self, mock_heavy_imports):
        """build_history_messages 应只返回工作记忆窗口内的消息数量"""
        from app.services.rag_agent_service.agent_service import build_history_messages
        history = [
            _q("第1轮"), _a("回答1"),
            _q("第2轮"), _a("回答2"),
            _q("第3轮"), _a("回答3"),
            _q("第4轮"), _a("回答4"),
        ]
        messages = build_history_messages(history)
        # 默认 max_turns=3，应保留后 6 条（3 轮），丢弃前 2 条（第 1 轮）
        assert len(messages) == 6
