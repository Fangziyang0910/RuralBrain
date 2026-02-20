"""
技能中间件 - 实现 Progressive Disclosure

职责：
1. 将技能描述注入到系统提示词中
2. 支持动态工具注册（未来扩展）
3. 支持生产环境的技能刷新（智能重新加载策略）
"""
import time
from typing import Callable, List, TYPE_CHECKING

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from src.config import SKILL_RELOAD_INTERVAL, SKILL_RELOAD_STRATEGY

if TYPE_CHECKING:
    from ..skills.registry import SkillRegistry


class SkillMiddleware(AgentMiddleware):
    """
    技能中间件 - 实现 Progressive Disclosure 机制

    将技能描述列表注入到系统提示词中，Agent 通过 load_skill 工具
    按需加载完整内容，避免一次性加载所有技能内容。

    支持：
    - Progressive Disclosure（渐进式披露）
    - 动态工具注册（未来扩展）
    - 智能技能重新加载（可配置策略）

    重新加载策略（通过 SKILL_RELOAD_STRATEGY 配置）：
    - always: 每次请求都重新加载（适合开发环境）
    - timed: 按时间间隔重新加载（适合生产环境）
    - never: 从不自动重新加载（适合高性能环境）
    """

    def __init__(self, registry: "SkillRegistry"):
        """
        初始化技能中间件

        Args:
            registry: 技能注册中心
        """
        self.registry = registry
        self.reload_strategy = SKILL_RELOAD_STRATEGY
        self.reload_interval = SKILL_RELOAD_INTERVAL
        self._last_reload_time = 0

    def before_agent(self, state, runtime):
        """
        在 Agent 执行前智能刷新技能列表

        根据配置的策略决定是否重新加载：
        - always: 每次都重新加载
        - timed: 只有超过时间间隔时才重新加载
        - never: 从不自动重新加载
        """
        if self.reload_strategy == "always":
            self.registry.reload()
        elif self.reload_strategy == "timed":
            current_time = time.time()
            if current_time - self._last_reload_time >= self.reload_interval:
                self.registry.reload()
                self._last_reload_time = current_time
        # "never" 模式不执行任何操作
        return None

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """将技能描述注入到系统提示词中（同步版本）"""
        skills_prompt = self._build_skills_prompt()

        # 使用 request.override 动态修改系统提示词
        return handler(request.override(
            system_prompt=request.system_prompt + skills_prompt
        ))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """将技能描述注入到系统提示词中（异步版本）"""
        skills_prompt = self._build_skills_prompt()

        # 使用 request.override 动态修改系统提示词
        return await handler(request.override(
            system_prompt=request.system_prompt + skills_prompt
        ))

    def wrap_tool_call(self, request, handler):
        """
        处理动态工具注册（未来扩展）

        当加载技能时，动态注册该技能关联的工具。
        """
        # TODO: 实现动态工具注册
        # - 检测 load_skill 工具调用
        # - 根据技能的 tool_names 动态注册工具
        # - 更新 request.tools
        return handler(request)

    async def awrap_tool_call(self, request, handler):
        """
        处理动态工具注册（未来扩展，异步版本）
        """
        # TODO: 实现动态工具注册
        return await handler(request)

    def _build_skills_prompt(self) -> str:
        """构建技能描述"""
        descriptions = self.registry.get_skill_descriptions()
        return f"\n\n## 可用技能\n\n{descriptions}\n\n使用 load_skill 工具获取技能详细信息。"


__all__ = ["SkillMiddleware"]
