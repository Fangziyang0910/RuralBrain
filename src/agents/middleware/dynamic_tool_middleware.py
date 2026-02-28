"""
动态工具注册中间件

实现 Runtime tool registration，允许在运行时动态注册新工具。
初始时 Agent 只有 load_skill 工具，加载技能时动态注册该技能关联的工具。

基于 LangChain 官方文档的 Runtime tool registration 模式：
https://docs.langchain.com/oss/python/langchain/agents

会话级别工具管理：
- 每个 thread_id 独立管理工具集
- 工具注册后在同一 thread_id 的对话中永久生效
- 不同 thread_id 之间工具隔离
"""
import logging
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.tools import BaseTool
from langgraph.config import get_config

if TYPE_CHECKING:
    from ..tools.tool_loader import ToolLoader

logger = logging.getLogger(__name__)

# 全局中间件实例（用于单例模式）
_global_middleware: Optional["DynamicToolMiddleware"] = None

# 默认 thread_id，用于没有明确指定 thread_id 的场景
DEFAULT_THREAD_ID = "default"

# 知识库开关状态（thread_id -> enable_knowledge_base）
_kb_switch_state: Dict[str, Optional[bool]] = {}

def set_kb_switch_state(thread_id: str, enabled: Optional[bool]):
    """设置知识库开关状态"""
    # 确保 thread_id 是字符串类型
    thread_id = str(thread_id)
    _kb_switch_state[thread_id] = enabled
    logger.info(f"设置知识库开关: thread_id={thread_id}, enabled={enabled}")

def get_kb_switch_state(thread_id: str) -> Optional[bool]:
    """获取知识库开关状态"""
    return _kb_switch_state.get(thread_id)


class DynamicToolMiddleware(AgentMiddleware):
    """
    动态工具注册中间件

    职责：
    1. 管理动态注册的工具实例（会话级别）
    2. 实现 wrap_model_call：将已注册的工具添加到请求中
    3. 实现 wrap_tool_call：处理动态工具的执行
    4. 提供 register_tools() 接口供 load_skill 调用

    工具生命周期：会话级别（按 thread_id 隔离）
    - 工具注册后在同一 thread_id 的会话中永久生效
    - 不同 thread_id 之间工具完全隔离
    - 避免 thread_id 内重复注册同一工具
    """

    def __init__(self, tool_loader: Optional["ToolLoader"] = None):
        """
        初始化动态工具注册中间件

        Args:
            tool_loader: 工具加载器实例（可选，延迟加载）
        """
        self._tool_loader = tool_loader
        # 嵌套字典：{thread_id: {tool_name: tool}}
        self._registered_tools: Dict[str, Dict[str, BaseTool]] = {}
        # 记录每个会话已注册的技能：{thread_id: [skill_names]}
        self._registered_skills: Dict[str, List[str]] = {}
        logger.info("DynamicToolMiddleware 初始化完成（会话级别工具管理）")

    def set_tool_loader(self, tool_loader: "ToolLoader"):
        """
        设置工具加载器

        Args:
            tool_loader: 工具加载器实例
        """
        self._tool_loader = tool_loader
        logger.debug("ToolLoader 已设置")

    def before_agent(self, state, runtime):
        """Agent 执行前的钩子（同步版本）"""
        return None

    async def abefore_agent(self, state, runtime):
        """Agent 执行前的钩子（异步版本）"""
        return None

    def _get_thread_id(self, request: ModelRequest) -> str:
        """
        从请求中提取 thread_id

        Args:
            request: 模型请求对象

        Returns:
            thread_id，如果无法获取则返回默认值
        """
        # 使用 langgraph 的 get_config() 获取 RunnableConfig
        # 这是在中间件中获取 thread_id 的正确方式
        try:
            config = get_config()
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                return str(thread_id)
        except RuntimeError:
            # 如果在 runnable 上下文外调用，使用默认值
            logger.debug("无法获取 config（不在 runnable 上下文中）")
        except Exception as e:
            logger.debug(f"获取 thread_id 时出错: {e}")

        # 如果无法获取，使用默认值
        return DEFAULT_THREAD_ID

    def register_tools(
        self,
        tool_names: List[str],
        tools: List[BaseTool],
        skill_name: str = "",
        thread_id: Optional[str] = None
    ):
        """
        注册工具到指定会话

        Args:
            tool_names: 工具名称列表
            tools: 工具实例列表
            skill_name: 关联的技能名称（可选，用于日志和跟踪）
            thread_id: 会话 ID，如果为 None 则自动从上下文获取
        """
        # 如果未指定 thread_id，尝试从调用上下文自动获取
        if thread_id is None:
            try:
                config = get_config()
                thread_id = config.get("configurable", {}).get("thread_id")
                if thread_id:
                    thread_id = str(thread_id)
                    logger.debug(f"从上下文自动获取 thread_id: {thread_id}")
            except (RuntimeError, KeyError) as e:
                logger.debug(f"无法从上下文获取 thread_id: {e}，使用默认值")

        # 如果仍然无法获取，使用默认值
        if thread_id is None:
            thread_id = DEFAULT_THREAD_ID

        # 确保该 thread_id 的工具字典存在
        if thread_id not in self._registered_tools:
            self._registered_tools[thread_id] = {}

        if thread_id not in self._registered_skills:
            self._registered_skills[thread_id] = []

        session_tools = self._registered_tools[thread_id]
        registered_count = 0

        for name, tool in zip(tool_names, tools):
            if name not in session_tools:
                session_tools[name] = tool
                registered_count += 1
                logger.debug(f"注册工具: {name} (技能: {skill_name or '未知'}, thread_id: {thread_id})")
            else:
                logger.debug(f"工具已存在，跳过: {name} (thread_id: {thread_id})")

        if skill_name and skill_name not in self._registered_skills[thread_id]:
            self._registered_skills[thread_id].append(skill_name)

        if registered_count > 0:
            logger.info(f"注册了 {registered_count} 个工具 (技能: {skill_name or '未知'}, thread_id: {thread_id})")

    def register_tools_by_skill(
        self,
        skill_name: str,
        tool_names: List[str],
        thread_id: Optional[str] = None
    ) -> int:
        """
        根据技能名称注册关联的工具

        Args:
            skill_name: 技能名称
            tool_names: 工具名称列表
            thread_id: 会话 ID，如果为 None 则自动从上下文获取

        Returns:
            成功注册的工具数量

        Raises:
            RuntimeError: 如果 ToolLoader 未设置
        """
        if self._tool_loader is None:
            raise RuntimeError("ToolLoader 未设置，无法加载工具")

        tools = self._tool_loader.load_tools_by_names(tool_names)

        # 如果未指定 thread_id，尝试从调用上下文自动获取
        if thread_id is None:
            try:
                config = get_config()
                thread_id = config.get("configurable", {}).get("thread_id")
                if thread_id:
                    thread_id = str(thread_id)
                    logger.debug(f"从上下文自动获取 thread_id: {thread_id}")
            except (RuntimeError, KeyError) as e:
                logger.debug(f"无法从上下文获取 thread_id: {e}，使用默认值")

        # 如果仍然无法获取，使用默认值
        if thread_id is None:
            thread_id = DEFAULT_THREAD_ID

        self.register_tools(tool_names, tools, skill_name, thread_id)

        # 返回该会话中成功注册的工具数量
        if thread_id in self._registered_tools:
            return len([name for name in tool_names if name in self._registered_tools[thread_id]])
        return 0

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        将动态注册的工具添加到模型调用请求中

        这是 LangChain Runtime tool registration 的核心钩子。
        """
        # 获取当前会话的 thread_id
        thread_id = self._get_thread_id(request)

        # 获取该会话已注册的工具
        session_tools = self._registered_tools.get(thread_id, {})
        if not session_tools:
            # 没有动态工具，直接调用
            return handler(request)

        # 将已注册的工具添加到请求中
        dynamic_tools = list(session_tools.values())
        updated = request.override(tools=[*request.tools, *dynamic_tools])

        logger.debug(
            f"wrap_model_call: thread_id={thread_id}, "
            f"静态工具 {len(request.tools)} 个, "
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

        # 获取当前会话的 thread_id（保持会话隔离）
        thread_id = self._get_thread_id(request)

        # 只在当前会话中查找该工具
        if tool_name and thread_id in self._registered_tools:
            session_tools = self._registered_tools[thread_id]
            if tool_name in session_tools:
                # 这是一个动态工具，提供正确的工具实例
                tool = session_tools[tool_name]
                logger.debug(f"wrap_tool_call: 执行动态工具 {tool_name} (thread_id: {thread_id})")
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
        # 获取当前会话的 thread_id
        thread_id = self._get_thread_id(request)

        # 获取该会话已注册的工具
        session_tools = self._registered_tools.get(thread_id, {})
        if not session_tools:
            # 没有动态工具，直接调用
            return await handler(request)

        # 将已注册的工具添加到请求中
        dynamic_tools = list(session_tools.values())
        updated = request.override(tools=[*request.tools, *dynamic_tools])

        logger.debug(
            f"awrap_model_call: thread_id={thread_id}, "
            f"静态工具 {len(request.tools)} 个, "
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

        # 获取当前会话的 thread_id（保持会话隔离）
        thread_id = self._get_thread_id(request)

        # 只在当前会话中查找该工具
        if tool_name and thread_id in self._registered_tools:
            session_tools = self._registered_tools[thread_id]
            if tool_name in session_tools:
                # 这是一个动态工具，提供正确的工具实例
                tool = session_tools[tool_name]
                logger.debug(f"awrap_tool_call: 执行动态工具 {tool_name} (thread_id: {thread_id})")
                return await handler(request.override(tool=tool))

        # 静态工具，直接调用（需要 await）
        return await handler(request)

    def get_registered_tools(self, thread_id: Optional[str] = None) -> Dict[str, BaseTool]:
        """
        获取已注册的工具列表

        Args:
            thread_id: 会话 ID，如果为 None 则返回第一个会话的工具

        Returns:
            工具名称到工具实例的映射
        """
        if thread_id is not None:
            return self._registered_tools.get(thread_id, {}).copy()
        # 如果没有指定 thread_id，返回第一个会话的工具（兼容旧行为）
        for session_tools in self._registered_tools.values():
            if session_tools:
                return session_tools.copy()
        return {}

    def get_registered_skills(self, thread_id: Optional[str] = None) -> List[str]:
        """
        获取已注册的技能列表

        Args:
            thread_id: 会话 ID，如果为 None 则返回第一个会话的技能

        Returns:
            技能名称列表
        """
        if thread_id is not None:
            return self._registered_skills.get(thread_id, []).copy()
        # 如果没有指定 thread_id，返回第一个会话的技能（兼容旧行为）
        for skills in self._registered_skills.values():
            if skills:
                return skills.copy()
        return []

    def clear_session_tools(self, thread_id: str):
        """
        清空指定会话的已注册工具

        Args:
            thread_id: 要清空的会话 ID
        """
        if thread_id in self._registered_tools:
            self._registered_tools[thread_id].clear()
        if thread_id in self._registered_skills:
            self._registered_skills[thread_id].clear()
        logger.info(f"已清空会话 {thread_id} 的所有动态注册工具")

    def clear_tools(self):
        """
        清空所有会话的已注册工具

        主要用于测试和重置
        """
        self._registered_tools.clear()
        self._registered_skills.clear()
        logger.info("已清空所有会话的动态注册工具")

    def is_tool_registered(self, tool_name: str, thread_id: Optional[str] = None) -> bool:
        """
        检查工具是否已注册

        Args:
            tool_name: 工具名称
            thread_id: 会话 ID，如果为 None 则检查所有会话

        Returns:
            如果工具已注册返回 True，否则返回 False
        """
        if thread_id is not None:
            return tool_name in self._registered_tools.get(thread_id, {})
        # 检查所有会话
        for session_tools in self._registered_tools.values():
            if tool_name in session_tools:
                return True
        return False


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
    "DEFAULT_THREAD_ID",
]
