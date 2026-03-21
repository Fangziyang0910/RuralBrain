"""web_search_tool 单元测试"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestWebSearchTool:
    """web_search_tool 测试类"""

    def test_web_search_tool_exists(self):
        """测试工具可以被导入"""
        from src.agents.tools.web_search_tool import web_search_tool
        assert web_search_tool is not None

    def test_web_search_tool_has_correct_name(self):
        """测试工具名称正确"""
        from src.agents.tools.web_search_tool import web_search_tool
        assert web_search_tool.name == "web_search_tool"

    def test_web_search_tool_description_contains_keywords(self):
        """测试工具描述包含关键词"""
        from src.agents.tools.web_search_tool import web_search_tool
        desc = web_search_tool.description.lower()
        assert "搜索" in desc or "search" in desc

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    @patch("langchain_community.tools.tavily_search.TavilySearchResults")
    def test_web_search_tool_returns_results(self, mock_tavily):
        """测试工具返回搜索结果"""
        # 配置 mock
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = [
            {"title": "测试结果", "url": "https://example.com", "content": "测试内容"}
        ]
        mock_tavily.return_value = mock_instance

        from src.agents.tools.web_search_tool import web_search_tool

        result = web_search_tool.invoke({"query": "大米价格"})
        assert result is not None
        assert len(result) > 0