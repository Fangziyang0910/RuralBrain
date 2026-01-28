"""
工具选择中间件

实现动态工具选择：根据标签动态选择工具子集，减少工具列表长度。
"""

from typing import Callable, List, Optional

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import BaseTool


class ToolSelectorMiddleware(AgentMiddleware):
    """工具选择中间件 - 根据标签动态选择工具子集"""

    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        tags: Optional[List[str]] = None,
        match_all: bool = False,
    ):
        """初始化工具选择中间件

        Args:
            tools: 可用的工具列表
            tags: 工具标签列表，用于筛选工具
            match_all: 是否要求工具匹配所有标签
        """
        self.available_tools = tools or []
        self.tags = tags or []
        self.match_all = match_all
        self.selected_tools = self._select_tools_by_tags()

    def _select_tools_by_tags(self) -> List[BaseTool]:
        """根据标签选择工具"""
        if not self.tags:
            return self.available_tools

        selected = []
        for tool in self.available_tools:
            tool_tags = getattr(tool, "tags", None) or []

            if self.match_all:
                if set(self.tags).issubset(set(tool_tags)):
                    selected.append(tool)
            else:
                if any(tag in tool_tags for tag in self.tags):
                    selected.append(tool)

        return selected

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """使用筛选后的工具列表"""
        return handler(request.override(tools=self.selected_tools))

    def update_tools(self, tools: List[BaseTool]) -> None:
        """更新可用工具列表并重新筛选"""
        self.available_tools = tools
        self.selected_tools = self._select_tools_by_tags()
