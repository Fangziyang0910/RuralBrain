"""
技能加载工具

包含 load_skill 工具，用于按需加载技能完整内容和注册关联的工具。

动态工具注册机制：
1. 加载技能的完整内容到系统提示词
2. 动态注册该技能关联的工具（通过 tool_names 配置）
3. 工具在当前会话中永久生效（会话级别生命周期，按 thread_id 隔离）

注意：
- 使用 langgraph.config.get_config() 自动获取 thread_id
- 不需要手动传递 thread_id 参数
"""
import logging
from typing import Optional

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
    工具有生命周期（TTL），闲置工具会自动卸载，使用中的工具会续期。

    Args:
        skill_name: 要加载的技能名称
        config: RunnableConfig（自动注入，用于获取 thread_id 和 enable_knowledge_base）

    Returns:
        技能的完整内容和已注册的工具列表。如果技能名称不存在，将返回当前可用的技能名称列表。

    Examples:
        >>> load_skill("pest_detection")
        "已加载技能: pest_detection\\n\\n已注册工具: pest_detection_tool (TTL=5)\\n\\n[技能内容...]"
    """
    from ..middleware.dynamic_tool_middleware import get_dynamic_middleware, get_kb_switch_state
    from ..skills.registry import get_registry

    registry = get_registry()

    # 1. 检查技能是否存在
    skill = registry.get_skill(skill_name)
    if not skill:
        available = ", ".join(registry.list_skill_names())
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"

    # 2. 加载技能内容
    content = skill.content or f"# {skill.name}\n\n{skill.description}"

    # 3. 获取知识库开关（从全局状态）
    # 使用 langgraph.get_config() 获取当前 runnable 上下文的 config
    kb_enabled = None
    thread_id = None

    try:
        from langgraph.config import get_config as get_runnable_config
        current_config = get_runnable_config()
        if current_config:
            thread_id = current_config.get("configurable", {}).get("thread_id")
            # 确保 thread_id 是字符串类型（与中间件保持一致）
            if thread_id:
                thread_id = str(thread_id)
    except RuntimeError as e:
        logger.debug(f"无法获取 runnable config: {e}")
    except Exception as e:
        logger.warning(f"获取 thread_id 时出错: {e}")

    if thread_id:
        # 从中间件的全局状态获取知识库开关
        kb_enabled = get_kb_switch_state(thread_id)
        logger.info(f"知识库开关状态: thread_id={thread_id}, kb_enabled={kb_enabled}, skill_name={skill_name}")
    else:
        logger.warning(f"无法获取 thread_id，使用默认行为（启用知识库）")

    # 4. 获取 TTL 配置（仅在 TTL 启用时）
    ttl_config = None
    from ...config import ENABLE_TOOL_TTL
    if ENABLE_TOOL_TTL:
        ttl_config = skill.get_ttl_config()

    # 5. 注册关联的工具（动态工具注册）
    # 注意：register_tools_by_skill 会自动从调用上下文获取 thread_id
    registered_tools_info = ""

    # 规划技能特殊处理：受知识库开关控制
    if skill_name == "consult_planning_knowledge":
        if kb_enabled == False:
            # 知识库关闭：移除已注册的 RAG 工具
            rag_tools = [
                "document_list_tool",
                "document_overview_tool",
                "knowledge_search_tool",
                "key_points_search_tool"
            ]
            try:
                middleware = get_dynamic_middleware()
                removed = middleware.unregister_tools_by_names(rag_tools)
                registered_tools_info = f"\n\n⚠️ 知识库已关闭，移除 {removed} 个 RAG 工具，使用通用知识回答"
                logger.info(f"知识库关闭，移除 RAG 工具: {removed} 个")
            except RuntimeError as e:
                registered_tools_info = "\n\n⚠️ 知识库已关闭，使用通用知识回答"
                logger.warning(f"移除 RAG 工具失败: {e}")
        elif skill.tool_names:
            try:
                middleware = get_dynamic_middleware()

                # 注册工具到当前会话（thread_id 自动获取），传递 TTL 配置（None 当 TTL 禁用时）
                count = middleware.register_tools_by_skill(
                    skill_name,
                    skill.tool_names,
                    ttl_config=ttl_config
                    # thread_id 现在由 register_tools_by_skill 自动获取
                )

                if count > 0:
                    if ENABLE_TOOL_TTL and ttl_config:
                        ttl_info = f"TTL={ttl_config.base_ttl}" if not ttl_config.pinned else "已钉住"
                        registered_tools_info = f"\n\n✅ 已注册工具: {', '.join(skill.tool_names)} ({ttl_info})"
                        logger.info(f"技能 {skill_name} 注册了 {count} 个工具 ({ttl_info})")
                    else:
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
    elif skill.tool_names:
        # 非规划技能的正常工具注册流程
        try:
            middleware = get_dynamic_middleware()

            # 注册工具到当前会话（thread_id 自动获取），传递 TTL 配置（None 当 TTL 禁用时）
            count = middleware.register_tools_by_skill(
                skill_name,
                skill.tool_names,
                ttl_config=ttl_config
                # thread_id 现在由 register_tools_by_skill 自动获取
            )

            if count > 0:
                if ENABLE_TOOL_TTL and ttl_config:
                    ttl_info = f"TTL={ttl_config.base_ttl}" if not ttl_config.pinned else "已钉住"
                    registered_tools_info = f"\n\n✅ 已注册工具: {', '.join(skill.tool_names)} ({ttl_info})"
                    logger.info(f"技能 {skill_name} 注册了 {count} 个工具 ({ttl_info})")
                else:
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
