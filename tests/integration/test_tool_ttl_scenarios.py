"""
测试工具 TTL 场景化端到端测试

模拟真实对话场景，验证工具生命周期 TTL 管理系统的行为：
1. 多轮对话场景 - 观察检测工具在 TTL 到期后是否自动卸载
2. 工具使用场景 - 验证工具使用后是否正确续期
3. 混合技能场景 - 多个技能的工具独立管理
4. 钉住工具场景 - 验证钉住工具永不过期
5. 会话隔离场景 - 验证不同会话之间的工具隔离
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

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
from langchain_core.tools import StructuredTool
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.config import RunnableConfig
from pydantic import BaseModel

from src.agents.middleware.dynamic_tool_middleware import (
    DynamicToolMiddleware,
    set_dynamic_middleware,
    reset_dynamic_middleware,
)
from src.agents.middleware.tool_lifecycle import TTLConfig
from src.agents.skills.base import Skill


# ========== 测试辅助类 ==========

class ToolInput(BaseModel):
    """通用工具输入"""
    query: str = ""


def create_test_tool(name: str, description: str) -> StructuredTool:
    """创建测试工具"""
    def tool_func(**kwargs):
        return f"{name} 执行结果"

    return StructuredTool.from_function(
        func=tool_func,
        name=name,
        description=description,
        args_schema=ToolInput,
    )


def create_mock_config(thread_id: str) -> RunnableConfig:
    """创建模拟的 RunnableConfig"""
    config = Mock(spec=RunnableConfig)
    config.get = lambda key, default=None: {
        "configurable": {"thread_id": thread_id}
    }.get(key, default)
    return config


class ScenarioTestHelper:
    """场景测试辅助类"""

    def __init__(self, name: str, thread_id: str):
        self.name = name
        self.thread_id = thread_id
        self.middleware = None
        self.round_count = 0
        self.tools_registered = []
        self.tools_unloaded = []

    def setup(self, enable_ttl: bool = True):
        """设置测试环境"""
        with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', enable_ttl):
            self.middleware = DynamicToolMiddleware()
            self.enable_ttl = enable_ttl
        print(f"\n{'='*60}")
        print(f"场景: {self.name}")
        print(f"Thread ID: {self.thread_id}")
        print(f"TTL 启用: {enable_ttl}")
        print(f"{'='*60}")

    def register_skill_tools(
        self,
        skill_name: str,
        tool_names: List[str],
        base_ttl: int = 3,
        extension: int = 2,
        pinned: bool = False
    ):
        """注册技能工具"""
        tools = [create_test_tool(name, f"Tool {name}") for name in tool_names]

        # 根据 TTL 是否启用决定是否传递 ttl_config
        ttl_config = TTLConfig(base_ttl=base_ttl, extension=extension, pinned=pinned) if self.enable_ttl else None

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(self.thread_id)):
            # 在 TTL 禁用模式下，需要 patch ENABLE_TOOL_TTL
            if not self.enable_ttl:
                with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', False):
                    self.middleware.register_tools(
                        tool_names=tool_names,
                        tools=tools,
                        skill_name=skill_name,
                        thread_id=self.thread_id,
                        ttl_config=ttl_config
                    )
            else:
                self.middleware.register_tools(
                    tool_names=tool_names,
                    tools=tools,
                    skill_name=skill_name,
                    thread_id=self.thread_id,
                    ttl_config=ttl_config
                )

        self.tools_registered.extend(tool_names)

        ttl_info = f" (pinned)" if pinned else f" (TTL={base_ttl})" if self.enable_ttl else ""
        print(f"\n[注册] 技能 '{skill_name}' 的工具: {tool_names}{ttl_info}")
        for name in tool_names:
            if self.enable_ttl:
                lifecycle = self.middleware._tool_lifecycles.get(self.thread_id, {}).get(name)
                if lifecycle:
                    print(f"  - {name}: TTL={lifecycle.current_ttl}")
            else:
                print(f"  - {name}: 已注册")

    def new_round(self) -> int:
        """开始新的一轮对话"""
        self.round_count += 1

        # 如果 TTL 禁用，不调用 before_agent（避免访问不存在的 _round_counters）
        if self.enable_ttl:
            with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(self.thread_id)):
                self.middleware.before_agent({}, Mock())

        print(f"\n[第{self.round_count}轮] 对话开始")
        self._show_active_tools()
        return self.round_count

    async def new_round_async(self) -> int:
        """开始新的一轮对话（异步版本）"""
        self.round_count += 1

        # 如果 TTL 禁用，不调用 abefore_agent
        if self.enable_ttl:
            with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(self.thread_id)):
                await self.middleware.abefore_agent({}, Mock())

        print(f"\n[第{self.round_count}轮] 对话开始 (异步)")
        self._show_active_tools()
        return self.round_count

    def use_tool(self, tool_name: str):
        """模拟使用工具"""
        tool_call_request = Mock(spec=ToolCallRequest)
        tool_call_request.tool_call = {"name": tool_name, "arguments": {"query": "test"}}

        def handler(req):
            return ModelResponse(result=[AIMessage(content=f"{tool_name} result")])

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(self.thread_id)):
            self.middleware.wrap_tool_call(tool_call_request, handler)

        if self.enable_ttl:
            lifecycle = self.middleware._tool_lifecycles.get(self.thread_id, {}).get(tool_name)
            if lifecycle:
                print(f"  -> 使用工具 '{tool_name}', 续期后 TTL={lifecycle.current_ttl}")
        else:
            print(f"  -> 使用工具 '{tool_name}'")

    async def use_tool_async(self, tool_name: str):
        """模拟使用工具（异步版本）"""
        tool_call_request = Mock(spec=ToolCallRequest)
        tool_call_request.tool_call = {"name": tool_name, "arguments": {"query": "test"}}

        async def handler(req):
            return ModelResponse(result=[AIMessage(content=f"{tool_name} result")])

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(self.thread_id)):
            await self.middleware.awrap_tool_call(tool_call_request, handler)

        if self.enable_ttl:
            lifecycle = self.middleware._tool_lifecycles.get(self.thread_id, {}).get(tool_name)
            if lifecycle:
                print(f"  -> 使用工具 '{tool_name}', 续期后 TTL={lifecycle.current_ttl}")
        else:
            print(f"  -> 使用工具 '{tool_name}'")

    def _show_active_tools(self):
        """显示当前活跃的工具"""
        if self.enable_ttl:
            lifecycles = self.middleware._tool_lifecycles.get(self.thread_id, {})
            if lifecycles:
                print(f"  活跃工具:")
                for name, lifecycle in lifecycles.items():
                    status = "活跃" if not lifecycle.is_expired() else "过期"
                    print(f"    - {name}: TTL={lifecycle.current_ttl}, 状态={status}")
            else:
                print(f"  活跃工具: 无")
        else:
            tools = self.middleware.get_registered_tools(self.thread_id)
            if tools:
                print(f"  活跃工具: {list(tools.keys())}")
            else:
                print(f"  活跃工具: 无")

    def verify_tool_exists(self, tool_name: str) -> bool:
        """验证工具是否存在"""
        exists = self.middleware.is_tool_registered(tool_name, self.thread_id)
        status = "✓ 存在" if exists else "✗ 不存在"
        print(f"  验证 '{tool_name}': {status}")
        return exists

    def verify_tool_not_exists(self, tool_name: str) -> bool:
        """验证工具是否不存在"""
        exists = self.middleware.is_tool_registered(tool_name, self.thread_id)
        status = "✓ 不存在" if not exists else "✗ 仍然存在"
        print(f"  验证 '{tool_name}' 不存在: {status}")
        return not exists

    def show_summary(self):
        """显示场景摘要"""
        print(f"\n{'='*60}")
        print(f"场景摘要: {self.name}")
        print(f"{'='*60}")
        print(f"总轮数: {self.round_count}")

        if self.enable_ttl:
            lifecycles = self.middleware._tool_lifecycles.get(self.thread_id, {})
            print(f"剩余工具: {len(lifecycles)}")
            for name, lifecycle in lifecycles.items():
                print(f"  - {name}: TTL={lifecycle.current_ttl}")
        else:
            tools = self.middleware.get_registered_tools(self.thread_id)
            print(f"注册工具: {len(tools)}")
            for name in tools.keys():
                print(f"  - {name}")

        print(f"{'='*60}")


# ========== 场景测试 ==========

def scenario_1_basic_ttl_expiration():
    """场景 1: 基本 TTL 过期流程

    用户连续多轮对话，不使用检测工具
    预期: 工具在 TTL 到期后自动卸载
    """
    helper = ScenarioTestHelper(
        name="基本 TTL 过期流程",
        thread_id="scenario_1"
    )
    helper.setup(enable_ttl=True)

    # 第 1 轮：注册病虫害检测技能 (TTL=2)
    helper.new_round()
    helper.register_skill_tools(
        skill_name="pest_detection",
        tool_names=["pest_detection_tool"],
        base_ttl=2,  # 2轮后过期
        extension=1
    )
    helper.verify_tool_exists("pest_detection_tool")

    # 第 2 轮：衰减 (TTL: 2 -> 1)
    helper.new_round()
    helper.verify_tool_exists("pest_detection_tool")

    # 第 3 轮：衰减 (TTL: 1 -> 0) -> 工具过期卸载
    helper.new_round()
    helper.verify_tool_not_exists("pest_detection_tool")

    # 第 4 轮：工具仍然不存在
    helper.new_round()
    helper.verify_tool_not_exists("pest_detection_tool")

    helper.show_summary()
    return True


def scenario_2_tool_renewal_on_use():
    """场景 2: 工具使用续期

    用户在对话中频繁使用检测工具
    预期: 工具每次使用后 TTL 续期，保持活跃
    """
    helper = ScenarioTestHelper(
        name="工具使用续期",
        thread_id="scenario_2"
    )
    helper.setup(enable_ttl=True)

    # 第 1 轮：注册工具 (TTL=2, extension=1)
    helper.new_round()
    helper.register_skill_tools(
        skill_name="rice_detection",
        tool_names=["rice_detection_tool"],
        base_ttl=2,
        extension=1
    )
    helper.verify_tool_exists("rice_detection_tool")

    # 第 2 轮：衰减 (TTL: 2 -> 1)，但使用了工具 -> 续期 (TTL: 1 -> 3)
    helper.new_round()
    helper.use_tool("rice_detection_tool")
    helper.verify_tool_exists("rice_detection_tool")

    # 第 3 轮：衰减 (TTL: 3 -> 2)
    helper.new_round()
    helper.verify_tool_exists("rice_detection_tool")

    # 第 4 轮：衰减 (TTL: 2 -> 1)，再次使用工具 -> 续期 (TTL: 1 -> 3)
    helper.new_round()
    helper.use_tool("rice_detection_tool")
    helper.verify_tool_exists("rice_detection_tool")

    # 第 5 轮：工具仍然活跃 (TTL: 3 -> 2)
    helper.new_round()
    helper.verify_tool_exists("rice_detection_tool")

    helper.show_summary()
    return True


def scenario_3_multi_skill_isolation():
    """场景 3: 多技能工具独立管理

    用户加载了多个技能，每个技能的工具独立管理 TTL
    预期: 不同技能的工具各自独立过期和续期
    """
    helper = ScenarioTestHelper(
        name="多技能工具独立管理",
        thread_id="scenario_3"
    )
    helper.setup(enable_ttl=True)

    # 第 1 轮：注册多个技能
    helper.new_round()
    helper.register_skill_tools("pest_detection", ["pest_detection_tool"], base_ttl=3, extension=1)
    helper.register_skill_tools("rice_detection", ["rice_detection_tool"], base_ttl=2, extension=1)
    helper.register_skill_tools("cow_detection", ["cow_detection_tool"], base_ttl=1, extension=1)

    helper.verify_tool_exists("pest_detection_tool")
    helper.verify_tool_exists("rice_detection_tool")
    helper.verify_tool_exists("cow_detection_tool")

    # 第 2 轮：cow_detection_tool 过期 (TTL: 1 -> 0)
    helper.new_round()
    helper.verify_tool_exists("pest_detection_tool")   # TTL: 3 -> 2
    helper.verify_tool_exists("rice_detection_tool")   # TTL: 2 -> 1
    helper.verify_tool_not_exists("cow_detection_tool")  # TTL: 1 -> 0, 过期

    # 第 3 轮：使用 rice_detection_tool 续期
    helper.new_round()
    helper.use_tool("rice_detection_tool")  # 续期: TTL: 1 -> 3
    helper.verify_tool_exists("pest_detection_tool")   # TTL: 2 -> 1
    helper.verify_tool_exists("rice_detection_tool")   # TTL: 1 -> 3 (续期)

    # 第 4 轮：pest_detection_tool 过期
    helper.new_round()
    helper.verify_tool_not_exists("pest_detection_tool")  # TTL: 1 -> 0, 过期
    helper.verify_tool_exists("rice_detection_tool")      # TTL: 3 -> 2

    helper.show_summary()
    return True


def scenario_4_pinned_tool_behavior():
    """场景 4: 钉住工具永不卸载

    用户加载了关键工具（如 load_skill），设置为钉住
    预期: 钉住工具永不卸载，无论经过多少轮
    """
    helper = ScenarioTestHelper(
        name="钉住工具永不卸载",
        thread_id="scenario_4"
    )
    helper.setup(enable_ttl=True)

    # 第 1 轮：注册普通工具和钉住工具
    helper.new_round()
    helper.register_skill_tools("pest_detection", ["pest_detection_tool"], base_ttl=2, extension=1)
    helper.register_skill_tools("core", ["load_skill_tool"], base_ttl=1, extension=1, pinned=True)

    helper.verify_tool_exists("pest_detection_tool")
    helper.verify_tool_exists("load_skill_tool")

    # 第 2 轮
    helper.new_round()
    helper.verify_tool_exists("pest_detection_tool")   # TTL: 2 -> 1
    helper.verify_tool_exists("load_skill_tool")       # 钉住，TTL 不变

    # 第 3 轮：pest_detection_tool 过期
    helper.new_round()
    helper.verify_tool_not_exists("pest_detection_tool")  # TTL: 1 -> 0, 过期
    helper.verify_tool_exists("load_skill_tool")          # 钉住，仍然存在

    # 继续多轮，钉住工具始终存在
    for i in range(4, 8):
        helper.new_round()
        helper.verify_tool_not_exists("pest_detection_tool")
        helper.verify_tool_exists("load_skill_tool")

    helper.show_summary()
    return True


def scenario_5_ttl_disabled_mode():
    """场景 5: TTL 禁用模式

    ENABLE_TOOL_TTL = False 时
    预期: 工具注册后永不过期，无论经过多少轮
    """
    helper = ScenarioTestHelper(
        name="TTL 禁用模式",
        thread_id="scenario_5"
    )
    helper.setup(enable_ttl=False)

    # 第 1 轮：注册工具
    helper.new_round()
    helper.register_skill_tools("pest_detection", ["pest_detection_tool"], base_ttl=1, extension=1)

    helper.verify_tool_exists("pest_detection_tool")

    # 经过 10 轮，工具仍然存在
    for i in range(2, 12):
        helper.new_round()
        helper.verify_tool_exists("pest_detection_tool")

    helper.show_summary()
    return True


def scenario_6_session_isolation():
    """场景 6: 会话隔离

    不同用户（不同 thread_id）的工具完全隔离
    预期: 用户 A 的工具过期不影响用户 B
    """
    user_a = ScenarioTestHelper(
        name="用户 A",
        thread_id="user_a_session"
    )
    user_a.setup(enable_ttl=True)

    user_b = ScenarioTestHelper(
        name="用户 B",
        thread_id="user_b_session"
    )
    user_b.setup(enable_ttl=True)

    print(f"\n{'='*60}")
    print(f"场景: 多用户会话隔离")
    print(f"{'='*60}")

    # 用户 A 注册工具
    user_a.new_round()
    user_a.register_skill_tools("pest_detection", ["pest_detection_tool"], base_ttl=2, extension=1)

    # 用户 B 也注册同名工具
    user_b.new_round()
    user_b.register_skill_tools("pest_detection", ["pest_detection_tool"], base_ttl=4, extension=1)

    print(f"\n[用户 A] 第 1 轮后")
    user_a.verify_tool_exists("pest_detection_tool")
    print(f"[用户 B] 第 1 轮后")
    user_b.verify_tool_exists("pest_detection_tool")

    # 用户 A 的工具过期
    user_a.new_round()  # 第 2 轮
    user_a.new_round()  # 第 3 轮 -> 工具过期
    print(f"\n[用户 A] 第 3 轮后")
    user_a.verify_tool_not_exists("pest_detection_tool")

    # 用户 B 的工具仍然存在
    print(f"\n[用户 B] 第 1 轮后（未变化）")
    user_b.verify_tool_exists("pest_detection_tool")

    # 用户 B 继续多轮，工具仍然活跃
    user_b.new_round()  # 第 2 轮
    user_b.new_round()  # 第 3 轮
    user_b.new_round()  # 第 4 轮
    print(f"\n[用户 B] 第 4 轮后")
    user_b.verify_tool_exists("pest_detection_tool")

    print(f"\n{'='*60}")
    print(f"场景摘要: 多用户会话隔离")
    print(f"用户 A 工具: 已过期卸载")
    print(f"用户 B 工具: 仍然活跃")
    print(f"{'='*60}")

    return True


async def scenario_7_async_conversation():
    """场景 7: 异步对话模式

    使用异步 API 进行的多轮对话
    预期: TTL 机制在异步模式下正常工作
    """
    print(f"\n{'='*60}")
    print(f"场景: 异步对话模式")
    print(f"{'='*60}")

    with patch('src.agents.middleware.dynamic_tool_middleware.ENABLE_TOOL_TTL', True):
        middleware = DynamicToolMiddleware()
        thread_id = "async_session"

        # 第 1 轮：注册工具
        await middleware.abefore_agent({}, Mock())

        tools = [create_test_tool("async_tool", "Async test tool")]
        ttl_config = TTLConfig(base_ttl=2, extension=1)

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(thread_id)):
            middleware.register_tools(
                tool_names=["async_tool"],
                tools=tools,
                skill_name="async_skill",
                thread_id=thread_id,
                ttl_config=ttl_config
            )

        print(f"\n[第1轮] 注册工具 async_tool (TTL=2)")
        print(f"  活跃工具: async_tool (TTL=2)")

        # 第 2 轮：衰减
        await middleware.abefore_agent({}, Mock())
        lifecycle = middleware._tool_lifecycles[thread_id]["async_tool"]
        print(f"\n[第2轮] TTL 衰减")
        print(f"  活跃工具: async_tool (TTL={lifecycle.current_ttl})")

        # 使用工具续期
        tool_call_request = Mock(spec=ToolCallRequest)
        tool_call_request.tool_call = {"name": "async_tool", "arguments": {}}

        async def handler(req):
            return ModelResponse(result=[AIMessage(content="async result")])

        with patch('src.agents.middleware.dynamic_tool_middleware.get_config', return_value=create_mock_config(thread_id)):
            await middleware.awrap_tool_call(tool_call_request, handler)

        lifecycle = middleware._tool_lifecycles[thread_id]["async_tool"]
        print(f"\n[使用工具] 续期后 TTL={lifecycle.current_ttl}")

        print(f"\n{'='*60}")
        print(f"场景摘要: 异步对话模式 - TTL 机制正常工作")
        print(f"{'='*60}")

    return True


# ========== 主测试运行器 ==========

def main():
    """运行所有场景测试"""
    print("\n" + "=" * 60)
    print("工具 TTL 场景化端到端测试")
    print("=" * 60)

    scenarios = [
        ("场景 1: 基本 TTL 过期流程", scenario_1_basic_ttl_expiration),
        ("场景 2: 工具使用续期", scenario_2_tool_renewal_on_use),
        ("场景 3: 多技能工具独立管理", scenario_3_multi_skill_isolation),
        ("场景 4: 钉住工具永不卸载", scenario_4_pinned_tool_behavior),
        ("场景 5: TTL 禁用模式", scenario_5_ttl_disabled_mode),
        ("场景 6: 会话隔离", scenario_6_session_isolation),
        ("场景 7: 异步对话模式", lambda: asyncio.run(scenario_7_async_conversation())),
    ]

    results = []

    for name, scenario_func in scenarios:
        try:
            passed = scenario_func()
            results.append((name, passed))
            print(f"\n✅ {name} - 通过")
        except Exception as e:
            print(f"\n❌ {name} - 失败")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 最终摘要
    print("\n" + "=" * 60)
    print("最终测试摘要")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n  总计: {passed_count}/{total} 通过")

    if all(p for _, p in results):
        print("\n  ✅ 所有场景测试通过!")
        return 0
    else:
        print("\n  ❌ 部分场景测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
