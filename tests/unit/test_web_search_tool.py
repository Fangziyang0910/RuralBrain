"""web_search_tool 单元测试"""
import json
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
    def test_web_search_tool_returns_json(self, mock_tavily):
        """测试工具返回 JSON 格式结果"""
        # 配置 mock（使用旧版 TavilySearchResults 返回 list 格式）
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = [
            {"title": "测试结果", "url": "https://example.com", "content": "测试内容"}
        ]
        mock_tavily.return_value = mock_instance

        from src.agents.tools.web_search_tool import web_search_tool

        result = web_search_tool.invoke({"query": "大米价格"})
        assert result is not None
        assert result.startswith("{")  # 返回 JSON 字符串

        # 解析 JSON 验证结构
        parsed = json.loads(result)
        assert "agent_text" in parsed
        assert "results" in parsed
        assert "stats" in parsed

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    @patch("langchain_tavily.TavilySearch")
    def test_web_search_tool_agent_text_is_markdown(self, mock_tavily):
        """测试 agent_text 字段包含可读 Markdown 文本"""
        # 配置 mock（使用新版 TavilySearch 返回 dict 格式）
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = {
            "results": [
                {"title": "大米价格", "url": "https://example.com", "content": "测试内容"}
            ],
            "answer": "AI 摘要内容"
        }
        mock_tavily.return_value = mock_instance

        from src.agents.tools.web_search_tool import web_search_tool

        result = web_search_tool.invoke({"query": "大米价格"})
        parsed = json.loads(result)
        agent_text = parsed.get("agent_text", "")

        # agent_text 应包含 Markdown 格式的搜索结果
        assert "【联网搜索结果】" in agent_text