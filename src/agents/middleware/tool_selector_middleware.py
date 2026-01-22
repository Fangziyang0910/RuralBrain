"""
工具选择中间件

实现动态工具选择：
1. 根据标签或分类动态选择工具子集
2. 减少工具列表长度，提高 Agent 决策准确性
3. 支持灵活的工具分组和过滤
"""

from typing import Callable, List, Optional, Set
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import BaseTool


class ToolSelectorMiddleware(AgentMiddleware):
    """
    工具选择中间件

    功能：
    1. 根据标签动态选择工具子集
    2. 减少工具列表长度，提高 Agent 决策准确性
    3. 支持基于标签的工具分组

    Attributes:
        selected_tools: 根据标签筛选后的工具列表
    """

    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        tags: Optional[List[str]] = None,
        match_all: bool = False,
    ):
        """
        初始化工具选择中间件

        Args:
            tools: 可用的工具列表，如果为 None 则需要从外部提供
            tags: 工具标签列表，用于筛选工具
            match_all: 是否要求工具匹配所有标签（False 表示匹配任一标签即可）
        """
        self.available_tools = tools or []
        self.tags = tags or []
        self.match_all = match_all

        # 根据标签筛选工具
        self.selected_tools = self._select_tools_by_tags()

    def _select_tools_by_tags(self) -> List[BaseTool]:
        """
        根据标签选择工具

        Returns:
            筛选后的工具列表
        """
        if not self.tags:
            # 没有标签限制，返回所有工具
            return self.available_tools

        selected = []

        for tool in self.available_tools:
            # 获取工具的标签（假设工具有 tags 属性）
            tool_tags = getattr(tool, "tags", None) or []

            if self.match_all:
                # 需要匹配所有标签
                if set(self.tags).issubset(set(tool_tags)):
                    selected.append(tool)
            else:
                # 匹配任一标签即可
                if any(tag in tool_tags for tag in self.tags):
                    selected.append(tool)

        return selected

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        动态选择工具子集

        使用筛选后的工具列表替换默认的工具列表
        """
        # 使用选定的工具子集
        modified_request = request.override(tools=self.selected_tools)

        return handler(modified_request)

    def update_tools(self, tools: List[BaseTool]) -> None:
        """
        更新可用工具列表并重新筛选

        Args:
            tools: 新的工具列表
        """
        self.available_tools = tools
        self.selected_tools = self._select_tools_by_tags()
