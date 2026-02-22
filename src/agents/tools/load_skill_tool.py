"""
技能加载工具

包含 load_skill 工具，用于按需加载技能完整内容和注册关联的工具。

动态工具注册机制：
1. 加载技能的完整内容到系统提示词
2. 动态注册该技能关联的工具（通过 tool_names 配置）
3. 工具在当前会话中永久生效（会话级别生命周期，按 thread_id 隔离）

注意：
- 使用 config 参数来获取 thread_id（从 RunnableConfig.configurable.thread_id）
- config 参数是 LangChain 工具的标准参数，会被自动注入
"""
import logging
from typing import Any, Optional

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LoadSkillInput(BaseModel):
    """加载技能的输入参数"""
    skill_name: str = Field(description="要加载的技能名称")


@tool(args_schema=LoadSkillInput)
def load_skill(
    skill_name: str,
    config: Optional[RunnableConfig] = None
) -> str:
    """加载技能的完整内容，并动态注册关联的工具。

    当需要详细了解如何处理特定类型的请求时，使用此工具获取专业技能的详细工作流程、输出格式和专业要求。

    **动态工具注册：**
    加载技能后，该技能关联的工具将自动注册到当前会话，Agent 可以直接调用这些工具。
    工具注册是会话级别的（按 thread_id 隔离），不同会话之间工具状态独立。

    Args:
        skill_name: 要加载的技能名称

    Returns:
        技能的完整内容和已注册的工具列表。如果技能名称不存在，将返回当前可用的技能名称列表。

    Examples:
        >>> load_skill("pest_detection")
        "已加载技能: pest_detection\\n\\n已注册工具: pest_detection_tool\\n\\n[技能内容...]"
    """
    from ..middleware.dynamic_tool_middleware import get_dynamic_middleware, DEFAULT_THREAD_ID
    from ..skills.registry import get_registry

    # 获取 thread_id（从 config.configurable.thread_id）
    thread_id = DEFAULT_THREAD_ID
    if config:
        try:
            configurable = config.get('configurable', {})
            thread_id = configurable.get('thread_id', DEFAULT_THREAD_ID)
            logger.debug(f"load_skill: 从 config 获取到 thread_id={thread_id}")
        except Exception as e:
            logger.debug(f"load_skill: 无法从 config 获取 thread_id: {e}")

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

            # 注册工具到指定会话
            count = middleware.register_tools_by_skill(
                skill_name,
                skill.tool_names,
                thread_id=thread_id
            )

            if count > 0:
                registered_tools_info = f"\n\n✅ 已注册工具: {', '.join(skill.tool_names)}"
                logger.info(f"技能 {skill_name} 注册了 {count} 个工具 (thread_id: {thread_id})")
            else:
                registered_tools_info = "\n\n⚠️ 工具已存在或加载失败"
                logger.warning(f"技能 {skill_name} 工具注册失败 (thread_id: {thread_id})")

        except RuntimeError as e:
            # DynamicToolMiddleware 未初始化（开发模式）
            logger.warning(f"DynamicToolMiddleware 未初始化，跳过工具注册: {e}")
            registered_tools_info = "\n\n⚠️ 工具注册暂时不可用（开发模式）"
        except Exception as e:
            logger.error(f"工具注册失败: {e}")
            registered_tools_info = f"\n\n❌ 工具注册失败: {e}"

    return f"已加载技能: {skill_name}{registered_tools_info}\n\n{content}"


__all__ = ["load_skill"]
