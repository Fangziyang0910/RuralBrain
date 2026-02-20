"""
技能中间件 - 实现 Progressive Disclosure

职责：
1. 将技能描述注入到系统提示词中
2. 支持动态工具注册（未来扩展）
3. 支持生产环境的技能刷新
"""
from typing import Callable, List, TYPE_CHECKING

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

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
    - 生产环境的技能刷新
    """

    def __init__(self, registry: "SkillRegistry"):
        """
        初始化技能中间件

        Args:
            registry: 技能注册中心
        """
        self.registry = registry

    def before_agent(self, state, runtime):
        """
        在 Agent 执行前刷新技能列表（生产环境考虑）

        这允许技能定期刷新，反映最新的变更。
        """
        self.registry.reload()
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
