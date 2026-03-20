"""联网搜索开关状态管理测试"""
import pytest


class TestWebSearchSwitch:
    """联网搜索开关测试"""

    def test_set_web_search_switch_state(self):
        """测试设置开关状态"""
        from src.agents.middleware.dynamic_tool_middleware import (
            set_web_search_switch_state,
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        # 清理状态
        _web_search_switch_state.clear()

        set_web_search_switch_state("test-thread-1", True)
        assert get_web_search_switch_state("test-thread-1") is True

        set_web_search_switch_state("test-thread-1", False)
        assert get_web_search_switch_state("test-thread-1") is False

    def test_get_web_search_switch_state_default(self):
        """测试未设置时返回 None"""
        from src.agents.middleware.dynamic_tool_middleware import (
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        _web_search_switch_state.clear()
        result = get_web_search_switch_state("non-existent-thread")
        assert result is None

    def test_web_search_switch_isolation(self):
        """测试不同 thread_id 的开关状态隔离"""
        from src.agents.middleware.dynamic_tool_middleware import (
            set_web_search_switch_state,
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        _web_search_switch_state.clear()

        set_web_search_switch_state("thread-A", True)
        set_web_search_switch_state("thread-B", False)

        assert get_web_search_switch_state("thread-A") is True
        assert get_web_search_switch_state("thread-B") is False