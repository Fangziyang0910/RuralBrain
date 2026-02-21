"""
动态工具注册中间件

实现 Runtime tool registration，允许在运行时动态注册新工具。
初始时 Agent 只有 load_skill 工具，加载技能时动态注册该技能关联的工具。

基于 LangChain 官方文档的 Runtime tool registration 模式：
https://docs.langchain.com/oss/python/langchain/agents
"""
import logging
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse, ToolCallRequest
from langchain_core.tools import BaseTool

if TYPE_CHECKING:
    from ..tools.tool_loader import ToolLoader

logger = logging.getLogger(__name__)

# 全局中间件实例（用于单例模式）
_global_middleware: Optional["DynamicToolMiddleware"] = None


class DynamicToolMiddleware(AgentMiddleware):
    """
    动态工具注册中间件

    职责：
    1. 管理动态注册的工具实例（会话级别）
    2. 实现 wrap_model_call：将已注册的工具添加到请求中
    3. 实现 wrap_tool_call：处理动态工具的执行
    4. 提供 register_tools() 接口供 load_skill 调用

    工具生命周期：会话级别
    - 工具注册后在当前会话永久生效
    - 避免重复注册同一工具
    """

    def __init__(self, tool_loader: Optional["ToolLoader"] = None):
        """
        初始化动态工具注册中间件

        Args:
            tool_loader: 工具加载器实例（可选，延迟加载）
        """
        self._tool_loader = tool_loader
        self._registered_tools: Dict[str, BaseTool] = {}
        self._registered_skills: List[str] = []  # 记录已注册的技能
        logger.info("DynamicToolMiddleware 初始化完成")

    def set_tool_loader(self, tool_loader: "ToolLoader"):
        """
        设置工具加载器

        Args:
            tool_loader: 工具加载器实例
        """
        self._tool_loader = tool_loader
        logger.debug("ToolLoader 已设置")

    def register_tools(self, tool_names: List[str], tools: List[BaseTool], skill_name: str = ""):
        """
        注册工具到会话

        Args:
            tool_names: 工具名称列表
            tools: 工具实例列表
            skill_name: 关联的技能名称（可选，用于日志和跟踪）
        """
        registered_count = 0
        for name, tool in zip(tool_names, tools):
            if name not in self._registered_tools:
                self._registered_tools[name] = tool
                registered_count += 1
                logger.debug(f"注册工具: {name} (技能: {skill_name or '未知'})")
            else:
                logger.debug(f"工具已存在，跳过: {name}")

        if skill_name and skill_name not in self._registered_skills:
            self._registered_skills.append(skill_name)

        if registered_count > 0:
            logger.info(f"注册了 {registered_count} 个工具 (技能: {skill_name or '未知'})")

    def register_tools_by_skill(self, skill_name: str, tool_names: List[str]) -> int:
        """
        根据技能名称注册关联的工具

        Args:
            skill_name: 技能名称
            tool_names: 工具名称列表

        Returns:
            成功注册的工具数量

        Raises:
            RuntimeError: 如果 ToolLoader 未设置
        """
        if self._tool_loader is None:
            raise RuntimeError("ToolLoader 未设置，无法加载工具")

        tools = self._tool_loader.load_tools_by_names(tool_names)
        self.register_tools(tool_names, tools, skill_name)
        return len([name for name in tool_names if name in self._registered_tools])

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        将动态注册的工具添加到模型调用请求中

        这是 LangChain Runtime tool registration 的核心钩子。
        """
        if not self._registered_tools:
            # 没有动态工具，直接调用
            return handler(request)

        # 将已注册的工具添加到请求中
        dynamic_tools = list(self._registered_tools.values())
        updated = request.override(tools=[*request.tools, *dynamic_tools])

        logger.debug(
            f"wrap_model_call: 静态工具 {len(request.tools)} 个, "
            f"动态工具 {len(dynamic_tools)} 个"
        )

        return handler(updated)

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ModelResponse],
    ) -> ModelResponse:
        """
        处理动态工具的执行（同步版本）

        这是 LangChain Runtime tool registration 的第二个关键钩子。
        如果调用的工具是动态注册的，需要提供正确的工具实例。
        """
        tool_name = request.tool_call.get("name")

        if tool_name and tool_name in self._registered_tools:
            # 这是一个动态工具，提供正确的工具实例
            tool = self._registered_tools[tool_name]
            logger.debug(f"wrap_tool_call: 执行动态工具 {tool_name}")
            return handler(request.override(tool=tool))

        # 静态工具，直接调用
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        将动态注册的工具添加到模型调用请求中（异步版本）

        用于异步调用上下文（如 astream()、ainvoke()）。
        """
        if not self._registered_tools:
            # 没有动态工具，直接调用
            return await handler(request)

        # 将已注册的工具添加到请求中
        dynamic_tools = list(self._registered_tools.values())
        updated = request.override(tools=[*request.tools, *dynamic_tools])

        logger.debug(
            f"awrap_model_call: 静态工具 {len(request.tools)} 个, "
            f"动态工具 {len(dynamic_tools)} 个"
        )

        return await handler(updated)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ModelResponse],
    ) -> ModelResponse:
        """
        处理动态工具的执行（异步版本）

        用于异步调用上下文。
        """
        tool_name = request.tool_call.get("name")

        if tool_name and tool_name in self._registered_tools:
            # 这是一个动态工具，提供正确的工具实例
            tool = self._registered_tools[tool_name]
            logger.debug(f"awrap_tool_call: 执行动态工具 {tool_name}")
            return await handler(request.override(tool=tool))

        # 静态工具，直接调用
        return await handler(request)

    def get_registered_tools(self) -> Dict[str, BaseTool]:
        """
        获取已注册的工具列表

        Returns:
            工具名称到工具实例的映射
        """
        return self._registered_tools.copy()

    def get_registered_skills(self) -> List[str]:
        """
        获取已注册的技能列表

        Returns:
            技能名称列表
        """
        return self._registered_skills.copy()

    def clear_tools(self):
        """
        清空所有已注册的工具

        主要用于测试和重置会话
        """
        self._registered_tools.clear()
        self._registered_skills.clear()
        logger.info("已清空所有动态注册的工具")

    def is_tool_registered(self, tool_name: str) -> bool:
        """
        检查工具是否已注册

        Args:
            tool_name: 工具名称

        Returns:
            如果工具已注册返回 True，否则返回 False
        """
        return tool_name in self._registered_tools


# --- 单例模式函数 ---

def get_dynamic_middleware() -> DynamicToolMiddleware:
    """
    获取全局动态工具注册中间件实例

    Returns:
        DynamicToolMiddleware 实例

    Raises:
        RuntimeError: 如果中间件未初始化
    """
    global _global_middleware
    if _global_middleware is None:
        raise RuntimeError(
            "DynamicToolMiddleware 未初始化。"
            "请先调用 set_dynamic_middleware() 设置实例。"
        )
    return _global_middleware


def set_dynamic_middleware(middleware: DynamicToolMiddleware):
    """
    设置全局动态工具注册中间件实例

    Args:
        middleware: DynamicToolMiddleware 实例
    """
    global _global_middleware
    _global_middleware = middleware
    logger.info("全局 DynamicToolMiddleware 实例已设置")


def reset_dynamic_middleware():
    """
    重置全局动态工具注册中间件实例

    主要用于测试
    """
    global _global_middleware
    _global_middleware = None


__all__ = [
    "DynamicToolMiddleware",
    "get_dynamic_middleware",
    "set_dynamic_middleware",
    "reset_dynamic_middleware",
]
