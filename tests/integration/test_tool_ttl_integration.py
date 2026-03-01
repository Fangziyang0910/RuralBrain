"""
测试工具 TTL 集成功能

验证 DynamicToolMiddleware 与 TTL 系统的集成：
1. ENABLE_TOOL_TTL = False 时的行为（禁用模式）
2. ENABLE_TOOL_TTL = True 时的行为（启用模式）
3. 工具注册和生命周期创建
4. 多轮对话后的 TTL 衰减和过期卸载
5. 工具使用后的续期
6. 不同 thread_id 之间的隔离
7. 钉住工具的特殊行为
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from collections import defaultdict

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.tools import StructuredTool, tool
from langgraph.config import RunnableConfig
from pydantic import BaseModel

from src.agents.middleware.dynamic_tool_middleware import (
    DynamicToolMiddleware,
    DEFAULT_THREAD_ID,
    reset_dynamic_middleware,
)
from src.agents.middleware.tool_lifecycle import TTLConfig
from src.config import ENABLE_TOOL_TTL, DEFAULT_TOOL_TTL, DEFAULT_TOOL_EXTENSION


# ========== 测试辅助函数 ==========

class MockToolInput(BaseModel):
    """模拟工具输入"""
    pass


def create_mock_tool(name: str, func=lambda: "result") -> StructuredTool:
    """创建模拟工具"""
    return StructuredTool.from_function(
        func=lambda **kwargs: func(),
        name=name,
        description=f"Mock tool {name}",
        args_schema=MockToolInput,
    )


def create_mock_request(tools=None) -> ModelRequest:
    """创建模拟的 ModelRequest"""
    request = Mock(spec=ModelRequest)
    request.tools = tools or []
    return request


def create_mock_tool_call_request(tool_name: str) -> ToolCallRequest:
    """创建模拟的 ToolCallRequest"""
    request = Mock(spec=ToolCallRequest)
    request.tool_call = {"name": tool_name, "arguments": {}}
    return request


class MockConfig:
    """模拟 RunnableConfig"""
    def __init__(self, thread_id: str = "test_thread"):
        self._data = {"configurable": {"thread_id": thread_id}}

    def get(self, key, default=None):
        return self._data.get(key, default)


# ========== 测试函数 ==========

def test_ttl_disabled_initialization():
    """测试 1: TTL 禁用时的中间件初始化"""
    print("=" * 60)
    print("测试 1: TTL 禁用时的中间件初始化")
    print("=" * 60)

    # 临时禁用 TTL（如果当前是启用状态）
    original_value = ENABLE_TOOL_TTL

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', False):
        middleware = DynamicToolMiddleware()

        # 验证不初始化 TTL 相关字段
        assert not hasattr(middleware, '_tool_lifecycles') or middleware._tool_lifecycles is None, \
            "TTL 禁用时不应初始化 _tool_lifecycles"
        print(f"  ✓ 未初始化 _tool_lifecycles")

        assert not hasattr(middleware, '_round_counters') or middleware._round_counters is None, \
            "TTL 禁用时不应初始化 _round_counters"
        print(f"  ✓ 未初始化 _round_counters")

        # 基本字段仍应存在
        assert hasattr(middleware, '_registered_tools')
        assert hasattr(middleware, '_registered_skills')
        print(f"  ✓ 基本字段 _registered_tools 和 _registered_skills 存在")

    return True


def test_ttl_enabled_initialization():
    """测试 2: TTL 启用时的中间件初始化"""
    print("\n" + "=" * 60)
    print("测试 2: TTL 启用时的中间件初始化")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()

        # 验证初始化 TTL 相关字段
        assert hasattr(middleware, '_tool_lifecycles'), "应初始化 _tool_lifecycles"
        assert isinstance(middleware._tool_lifecycles, dict), "_tool_lifecycles 应为字典"
        print(f"  ✓ 已初始化 _tool_lifecycles (dict)")

        assert hasattr(middleware, '_round_counters'), "应初始化 _round_counters"
        # defaultdict 的类型检查需要特殊处理
        print(f"  ✓ 已初始化 _round_counters")

        # 基本字段也存在
        assert hasattr(middleware, '_registered_tools')
        assert hasattr(middleware, '_registered_skills')
        print(f"  ✓ 基本字段也存在")

    return True


def test_ttl_disabled_before_agent():
    """测试 3: TTL 禁用时 before_agent 不执行轮次计数"""
    print("\n" + "=" * 60)
    print("测试 3: TTL 禁用时 before_agent 不执行轮次计数")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', False):
        middleware = DynamicToolMiddleware()

        # 模拟 before_agent 调用
        state = {}
        runtime = Mock()

        result = middleware.before_agent(state, runtime)

        # 验证返回 None（不修改状态）
        assert result is None, "TTL 禁用时 before_agent 应返回 None"
        print(f"  ✓ before_agent 返回 None")

        # 验证不创建轮次计数器
        assert not hasattr(middleware, '_round_counters') or len(middleware._round_counters) == 0
        print(f"  ✓ 不创建轮次计数器")

    return True


def test_ttl_enabled_before_agent():
    """测试 4: TTL 启用时 before_agent 执行轮次计数"""
    print("\n" + "=" * 60)
    print("测试 4: TTL 启用时 before_agent 执行轮次计数")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_123"

        # 模拟 before_agent 调用（需要 mock get_config）
        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            state = {}
            runtime = Mock()

            result = middleware.before_agent(state, runtime)

            # 验证轮次计数增加
            assert middleware._round_counters[thread_id] == 1
            print(f"  ✓ 第 1 次调用后轮次计数 = 1")

            # 再次调用
            middleware.before_agent(state, runtime)
            assert middleware._round_counters[thread_id] == 2
            print(f"  ✓ 第 2 次调用后轮次计数 = 2")

    return True


def test_ttl_disabled_register_tools():
    """测试 5: TTL 禁用时注册工具不创建生命周期记录"""
    print("\n" + "=" * 60)
    print("测试 5: TTL 禁用时注册工具不创建生命周期记录")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', False):
        middleware = DynamicToolMiddleware()

        tool = create_mock_tool("test_tool")
        ttl_config = TTLConfig(base_ttl=5, extension=2)

        middleware.register_tools(
            tool_names=["test_tool"],
            tools=[tool],
            skill_name="test_skill",
            thread_id="test_thread",
            ttl_config=ttl_config
        )

        # 验证工具已注册
        assert middleware.is_tool_registered("test_tool", "test_thread")
        print(f"  ✓ 工具已注册")

        # 验证不创建生命周期记录
        assert not hasattr(middleware, '_tool_lifecycles') or \
               "test_thread" not in middleware._tool_lifecycles or \
               "test_tool" not in middleware._tool_lifecycles.get("test_thread", {})
        print(f"  ✓ 未创建生命周期记录")

    return True


def test_ttl_enabled_register_tools():
    """测试 6: TTL 启用时注册工具创建生命周期记录"""
    print("\n" + "=" * 60)
    print("测试 6: TTL 启用时注册工具创建生命周期记录")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_lifecycle"

        tool = create_mock_tool("test_tool")
        ttl_config = TTLConfig(base_ttl=3, extension=1)

        middleware.register_tools(
            tool_names=["test_tool"],
            tools=[tool],
            skill_name="test_skill",
            thread_id=thread_id,
            ttl_config=ttl_config
        )

        # 验证工具已注册
        assert middleware.is_tool_registered("test_tool", thread_id)
        print(f"  ✓ 工具已注册")

        # 验证创建生命周期记录
        assert thread_id in middleware._tool_lifecycles
        assert "test_tool" in middleware._tool_lifecycles[thread_id]
        print(f"  ✓ 已创建生命周期记录")

        # 验证生命周期配置
        lifecycle = middleware._tool_lifecycles[thread_id]["test_tool"]
        assert lifecycle.current_ttl == 3
        assert lifecycle.base_ttl == 3
        assert lifecycle.extension == 1
        assert lifecycle.registration_round == 0
        print(f"  ✓ 生命周期配置正确 (TTL=3, extension=1, round=0)")

    return True


def test_ttl_decay_and_expiration():
    """测试 7: TTL 衰减和过期卸载"""
    print("\n" + "=" * 60)
    print("测试 7: TTL 衰减和过期卸载")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_decay"

        # 注册工具 (base_ttl=2)
        tool = create_mock_tool("decay_tool")
        ttl_config = TTLConfig(base_ttl=2, extension=1)

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            middleware.register_tools(
                tool_names=["decay_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_id,
                ttl_config=ttl_config
            )

            # 初始状态
            lifecycle = middleware._tool_lifecycles[thread_id]["decay_tool"]
            assert lifecycle.current_ttl == 2
            print(f"  [注册] TTL = {lifecycle.current_ttl}")

            # 第 1 轮：衰减
            middleware.before_agent({}, Mock())
            # 检查工具是否还存在（TTL=1，未过期）
            assert middleware.is_tool_registered("decay_tool", thread_id)
            lifecycle = middleware._tool_lifecycles[thread_id]["decay_tool"]
            assert lifecycle.current_ttl == 1
            print(f"  [第1轮] TTL = {lifecycle.current_ttl}, 工具仍存在")

            # 第 2 轮：衰减，TTL=0 -> 工具过期并立即卸载
            middleware.before_agent({}, Mock())
            assert not middleware.is_tool_registered("decay_tool", thread_id)
            assert "decay_tool" not in middleware._tool_lifecycles.get(thread_id, {})
            print(f"  [第2轮] TTL 衰减为 0，工具已过期并卸载")

    return True


def test_tool_renewal_on_use():
    """测试 8: 工具使用后续期"""
    print("\n" + "=" * 60)
    print("测试 8: 工具使用后续期")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_renewal"

        # 注册工具 (base_ttl=2, extension=1)
        tool = create_mock_tool("renewal_tool")
        ttl_config = TTLConfig(base_ttl=2, extension=1)

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            middleware.register_tools(
                tool_names=["renewal_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_id,
                ttl_config=ttl_config
            )

            lifecycle = middleware._tool_lifecycles[thread_id]["renewal_tool"]
            assert lifecycle.current_ttl == 2
            print(f"  [注册] TTL = {lifecycle.current_ttl}")

            # 第 1 轮：衰减
            middleware.before_agent({}, Mock())
            lifecycle = middleware._tool_lifecycles[thread_id]["renewal_tool"]
            assert lifecycle.current_ttl == 1
            print(f"  [第1轮衰减] TTL = {lifecycle.current_ttl}")

            # 模拟工具调用（续期）
            tool_call_request = create_mock_tool_call_request("renewal_tool")

            from langchain_core.messages import AIMessage
            mock_handler = Mock(return_value=ModelResponse(result=[AIMessage(content="test")]))

            with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
                middleware.wrap_tool_call(tool_call_request, mock_handler)

            # 续期后 TTL = base_ttl + extension = 3
            lifecycle = middleware._tool_lifecycles[thread_id]["renewal_tool"]
            assert lifecycle.current_ttl == 3
            assert lifecycle.last_used_round == 1
            print(f"  [工具使用续期] TTL = {lifecycle.current_ttl}, last_used_round = {lifecycle.last_used_round}")

    return True


def test_thread_isolation():
    """测试 9: 不同 thread_id 之间的隔离"""
    print("\n" + "=" * 60)
    print("测试 9: 不同 thread_id 之间的隔离")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()

        thread_a = "thread_A"
        thread_b = "thread_B"

        tool = create_mock_tool("isolated_tool")
        ttl_config = TTLConfig(base_ttl=2, extension=1)

        # 在 thread_A 注册工具
        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_a)):
            middleware.register_tools(
                tool_names=["isolated_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_a,
                ttl_config=ttl_config
            )

        # 验证 thread_A 有工具
        assert middleware.is_tool_registered("isolated_tool", thread_a)
        assert thread_a in middleware._tool_lifecycles
        print(f"  ✓ thread_A 工具已注册")

        # 验证 thread_B 没有工具
        assert not middleware.is_tool_registered("isolated_tool", thread_b)
        assert thread_b not in middleware._tool_lifecycles or "isolated_tool" not in middleware._tool_lifecycles.get(thread_b, {})
        print(f"  ✓ thread_B 没有该工具（隔离）")

        # 在 thread_B 也注册同名工具
        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_b)):
            middleware.register_tools(
                tool_names=["isolated_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_b,
                ttl_config=ttl_config
            )

        # 验证两个线程都有独立的工具实例
        assert middleware.is_tool_registered("isolated_tool", thread_a)
        assert middleware.is_tool_registered("isolated_tool", thread_b)
        print(f"  ✓ 两个线程都有独立的工具实例")

        # 验证生命周期独立
        lifecycle_a = middleware._tool_lifecycles[thread_a]["isolated_tool"]
        lifecycle_b = middleware._tool_lifecycles[thread_b]["isolated_tool"]
        assert lifecycle_a is not lifecycle_b
        print(f"  ✓ 生命周期记录独立")

    return True


def test_pinned_tool_behavior():
    """测试 10: 钉住工具的特殊行为"""
    print("\n" + "=" * 60)
    print("测试 10: 钉住工具的特殊行为")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_pinned"

        # 注册钉住工具
        tool = create_mock_tool("pinned_tool")
        ttl_config = TTLConfig(base_ttl=2, extension=1, pinned=True)

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            middleware.register_tools(
                tool_names=["pinned_tool"],
                tools=[tool],
                skill_name="pinned_skill",
                thread_id=thread_id,
                ttl_config=ttl_config
            )

            lifecycle = middleware._tool_lifecycles[thread_id]["pinned_tool"]
            assert lifecycle.pinned is True
            assert not lifecycle.is_expired()
            print(f"  ✓ 钉住工具已注册 (pinned=True)")

            # 模拟多轮衰减
            for i in range(5):
                middleware.before_agent({}, Mock())
                lifecycle = middleware._tool_lifecycles[thread_id]["pinned_tool"]
                assert not lifecycle.is_expired()
                assert middleware.is_tool_registered("pinned_tool", thread_id)

            print(f"  ✓ 经过 5 轮衰减后，钉住工具仍然活跃")
            print(f"    当前 TTL = {lifecycle.current_ttl} (未改变)")

    return True


async def test_async_ttl_behavior():
    """测试 11: 异步模式下的 TTL 行为"""
    print("\n" + "=" * 60)
    print("测试 11: 异步模式下的 TTL 行为")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_async"

        tool = create_mock_tool("async_tool")
        ttl_config = TTLConfig(base_ttl=2, extension=1)

        # 注册工具
        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            middleware.register_tools(
                tool_names=["async_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_id,
                ttl_config=ttl_config
            )

            # 异步 before_agent
            await middleware.abefore_agent({}, Mock())
            lifecycle = middleware._tool_lifecycles[thread_id]["async_tool"]
            assert lifecycle.current_ttl == 1
            print(f"  ✓ abefore_agent 执行衰减，TTL = {lifecycle.current_ttl}")

            # 异步工具调用
            tool_call_request = create_mock_tool_call_request("async_tool")

            from langchain_core.messages import AIMessage
            async def mock_handler(req):
                return ModelResponse(result=[AIMessage(content="test")])

            await middleware.awrap_tool_call(tool_call_request, mock_handler)

            # 验证续期
            lifecycle = middleware._tool_lifecycles[thread_id]["async_tool"]
            assert lifecycle.current_ttl == 3  # base_ttl + extension
            print(f"  ✓ awrap_tool_call 执行续期，TTL = {lifecycle.current_ttl}")

    return True


def test_default_ttl_config():
    """测试 12: 默认 TTL 配置"""
    print("\n" + "=" * 60)
    print("测试 12: 默认 TTL 配置")
    print("=" * 60)

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "test_thread_default"

        tool = create_mock_tool("default_tool")

        # 不指定 ttl_config，应使用默认值
        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=MockConfig(thread_id)):
            middleware.register_tools(
                tool_names=["default_tool"],
                tools=[tool],
                skill_name="test_skill",
                thread_id=thread_id,
                ttl_config=None  # 使用默认
            )

            lifecycle = middleware._tool_lifecycles[thread_id]["default_tool"]
            assert lifecycle.current_ttl == DEFAULT_TOOL_TTL
            assert lifecycle.base_ttl == DEFAULT_TOOL_TTL
            assert lifecycle.extension == DEFAULT_TOOL_EXTENSION
            print(f"  ✓ 使用默认 TTL 配置")
            print(f"    base_ttl = {DEFAULT_TOOL_TTL}")
            print(f"    extension = {DEFAULT_TOOL_EXTENSION}")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Tool TTL 集成测试")
    print("=" * 60)

    tests = [
        ("TTL 禁用时的初始化", test_ttl_disabled_initialization),
        ("TTL 启用时的初始化", test_ttl_enabled_initialization),
        ("TTL 禁用时 before_agent", test_ttl_disabled_before_agent),
        ("TTL 启用时 before_agent", test_ttl_enabled_before_agent),
        ("TTL 禁用时注册工具", test_ttl_disabled_register_tools),
        ("TTL 启用时注册工具", test_ttl_enabled_register_tools),
        ("TTL 衰减和过期卸载", test_ttl_decay_and_expiration),
        ("工具使用后续期", test_tool_renewal_on_use),
        ("不同 thread_id 隔离", test_thread_isolation),
        ("钉住工具行为", test_pinned_tool_behavior),
        ("默认 TTL 配置", test_default_ttl_config),
        ("异步模式 TTL 行为", lambda: asyncio.run(test_async_ttl_behavior())),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n  总计: {passed_count}/{total} 通过")

    if all(p for _, p in results):
        print("\n  ✅ 所有测试通过!")
        return 0
    else:
        print("\n  ❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
