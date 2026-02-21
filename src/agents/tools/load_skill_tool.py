"""
技能加载工具

包含 load_skill 工具，用于按需加载技能完整内容和注册关联的工具。

动态工具注册机制：
1. 加载技能的完整内容到系统提示词
2. 动态注册该技能关联的工具（通过 tool_names 配置）
3. 工具在当前会话中永久生效（会话级别生命周期）
"""
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def load_skill(skill_name: str) -> str:
    """加载技能的完整内容，并动态注册关联的工具。

    当需要详细了解如何处理特定类型的请求时，使用此工具获取专业技能的详细工作流程、输出格式和专业要求。

    **动态工具注册：**
    加载技能后，该技能关联的工具将自动注册到当前会话，Agent 可以直接调用这些工具。

    Args:
        skill_name: 要加载的技能名称

    Returns:
        技能的完整内容和已注册的工具列表。如果技能名称不存在，将返回当前可用的技能名称列表。

    Examples:
        >>> load_skill("pest_detection")
        "已加载技能: pest_detection\n\n已注册工具: pest_detection_tool\n\n[技能内容...]"
    """
    from ..skills.registry import get_registry
    from ..middleware.dynamic_tool_middleware import get_dynamic_middleware
    from ..tools.tool_loader import get_tool_loader

    registry = get_registry()

    # 1. 检查技能是否存在
    skill = registry.get_skill(skill_name)
    if not skill:
        available = ", ".join(registry.list_skill_names())
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"

    # 2. 加载技能内容
    content = skill.content or f"# {skill.name}\n\n{skill.description}"

    # 3. 注册关联的工具（动态工具注册）
    registered_tools_info = ""
    if skill.tool_names:
        try:
            middleware = get_dynamic_middleware()
            tool_loader = get_tool_loader()

            # 注册工具
            count = middleware.register_tools_by_skill(skill_name, skill.tool_names)

            if count > 0:
                registered_tools_info = f"\n\n✅ 已注册工具: {', '.join(skill.tool_names)}"
                logger.info(f"技能 {skill_name} 注册了 {count} 个工具")
            else:
                registered_tools_info = "\n\n⚠️ 工具已存在或加载失败"
                logger.warning(f"技能 {skill_name} 工具注册失败")

        except RuntimeError as e:
            # DynamicToolMiddleware 未初始化（开发模式）
            logger.warning(f"DynamicToolMiddleware 未初始化，跳过工具注册: {e}")
            registered_tools_info = "\n\n⚠️ 工具注册暂时不可用（开发模式）"
        except Exception as e:
            logger.error(f"工具注册失败: {e}")
            registered_tools_info = f"\n\n❌ 工具注册失败: {e}"

    return f"已加载技能: {skill_name}{registered_tools_info}\n\n{content}"


__all__ = ["load_skill"]
