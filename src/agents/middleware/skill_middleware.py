"""
技能中间件 - 实现 Progressive Disclosure

职责：
1. 将技能描述注入到系统消息中
2. 不再负责定义工具（由 tools/load_skill_tool.py 接管）
"""
from typing import Callable, Optional

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage

from ..skills.registry import get_registry


class SkillMiddleware(AgentMiddleware):
    """技能中间件 - 实现 Progressive Disclosure 机制

    将技能描述列表注入到系统消息中，Agent 通过 load_skill 工具
    按需加载完整内容，避免一次性加载所有技能内容。
    """

    def __init__(self, skills: Optional[list] = None):
        """初始化技能中间件

        Args:
            skills: 保留参数以兼容现有代码，但不再使用
        """
        # 忽略 skills 参数，保留用于向后兼容
        _ = skills
        self.registry = get_registry()
        self.skills_prompt = self.registry.get_skill_descriptions()

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """将技能描述注入到系统消息中（同步版本）"""
        skills_addendum = (
            f"\n\n## 可用技能\n\n{self.skills_prompt}\n\n"
            "使用 load_skill 工具获取技能的详细信息。"
        )

        # 使用 content_blocks API（LangChain 1.0+）
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)

        return handler(request.override(system_message=new_system_message))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """将技能描述注入到系统消息中（异步版本）"""
        skills_addendum = (
            f"\n\n## 可用技能\n\n{self.skills_prompt}\n\n"
            "使用 load_skill 工具获取技能的详细信息。"
        )

        # 使用 content_blocks API（LangChain 1.0+）
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)

        return await handler(request.override(system_message=new_system_message))


__all__ = ["SkillMiddleware"]
