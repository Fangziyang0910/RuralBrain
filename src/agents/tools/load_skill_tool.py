"""
技能加载工具

包含 load_skill 工具，用于按需加载技能完整内容。
"""
from langchain_core.tools import tool


@tool
def load_skill(skill_name: str) -> str:
    """加载技能的完整内容

    当需要详细了解如何处理特定类型的请求时使用此工具。

    Args:
        skill_name: 要加载的技能名称（例如 "pest_detection", "rural_planning"）

    Returns:
        技能的完整内容
    """
    from ..skills.registry import get_registry
    registry = get_registry()

    try:
        content = registry.load_content(skill_name)
        return f"已加载技能: {skill_name}\n\n{content}"
    except ValueError:
        available = ", ".join(registry.list_skill_names())
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"


__all__ = ["load_skill"]
