"""
技能中间件

实现 Progressive Disclosure（渐进式披露）核心机制：
1. 将技能描述注入到系统提示词中
2. 注册 load_skill 工具
3. Agent 按需加载技能完整内容
"""

from typing import Callable, List, Dict, Optional
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import tool
from langchain.messages import SystemMessage
from skills.base import Skill

# 全局技能存储（用于 load_skill 工具查询）
_AVAILABLE_SKILLS: Dict[str, "Skill"] = {}


@tool
def load_skill(skill_name: str) -> str:
    """
    加载技能的完整内容

    当需要详细了解如何处理特定类型的请求时使用此工具。
    这将提供全面的指导、策略和指南。

    Args:
        skill_name: 要加载的技能名称（例如 "pest_detection", "rural_planning"）

    Returns:
        技能的完整内容，包括系统提示词、约束、示例和工具说明
    """
    if skill_name not in _AVAILABLE_SKILLS:
        available = ", ".join(_AVAILABLE_SKILLS.keys())
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"

    skill = _AVAILABLE_SKILLS[skill_name]
    return f"已加载技能: {skill_name}\n\n{skill.get_full_content()}"


class SkillMiddleware(AgentMiddleware):
    """
    技能中间件

    实现 Progressive Disclosure 核心机制：
    1. 将技能描述列表注入到系统提示词中
    2. 注册 load_skill 工具供 Agent 按需调用
    3. 避免一次性加载所有技能内容，减少 Token 消耗

    Attributes:
        skills: 要注册的技能列表
        tools: 注册的工具（load_skill）
    """

    # 注册 load_skill 工具
    tools = [load_skill]

    def __init__(self, skills: Optional[List["Skill"]] = None):
        """
        初始化技能中间件

        Args:
            skills: 要注册的技能列表，如果为 None 则使用已注册的全局技能
        """
        global _AVAILABLE_SKILLS

        if skills is not None:
            # 使用提供的技能列表
            self.skills = skills
            # 更新全局技能存储
            _AVAILABLE_SKILLS.update({s.name: s for s in skills})
        else:
            # 使用全局技能存储中的技能
            self.skills = list(_AVAILABLE_SKILLS.values())

        # 构建技能提示词列表（只包含简短描述）
        skills_list = [skill.get_prompt_addendum() for skill in self.skills]
        self.skills_prompt = "\n".join(skills_list)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        将技能描述注入到系统提示词中

        这是 Progressive Disclosure 的核心：
        - 只在系统提示词中包含技能的简短描述
        - 完整内容通过 load_skill 工具按需加载
        """
        # 构建技能附加内容
        skills_addendum = (
            f"\n\n## 可用技能\n\n{self.skills_prompt}\n\n"
            "使用 load_skill 工具获取技能的详细信息、指导原则和示例。"
        )

        # 附加到系统消息
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)

        return handler(modified_request)


def register_skills(skills: List["Skill"]) -> None:
    """
    注册技能到全局存储

    Args:
        skills: 要注册的技能列表
    """
    global _AVAILABLE_SKILLS
    _AVAILABLE_SKILLS.update({s.name: s for s in skills})


def get_registered_skills() -> Dict[str, "Skill"]:
    """
    获取所有已注册的技能

    Returns:
        技能名称到技能对象的映射
    """
    return _AVAILABLE_SKILLS.copy()
