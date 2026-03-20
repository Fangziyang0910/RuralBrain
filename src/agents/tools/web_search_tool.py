"""
联网搜索工具：通过 Tavily API 搜索实时网络信息

该工具让 Agent 能够获取实时市场信息、最新政策、新闻等。
"""
import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_MAX_RESULTS = 5
DEFAULT_SEARCH_DEPTH = "basic"


def _check_api_key() -> bool:
    """检查 TAVILY_API_KEY 是否配置"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY 未配置，联网搜索功能不可用")
        return False
    return True


def _format_results(results: list) -> str:
    """
    格式化搜索结果为可读文本

    Args:
        results: Tavily API 返回的结果列表

    Returns:
        格式化后的文本
    """
    if not results:
        return "未找到相关搜索结果。"

    output_lines = ["【联网搜索结果】"]

    for i, result in enumerate(results, 1):
        title = result.get("title", "无标题")
        url = result.get("url", "")
        content = result.get("content", "无摘要")

        output_lines.append(f"\n{i}. [{title}]({url})")
        output_lines.append(f"   摘要: {content}")

    return "\n".join(output_lines)


@tool
def web_search_tool(
    query: str,
    search_depth: str = DEFAULT_SEARCH_DEPTH,
    max_results: int = DEFAULT_MAX_RESULTS
) -> str:
    """
    联网搜索实时信息，获取最新数据。

    适用场景：
    - 市场价格、行情趋势
    - 最新政策法规
    - 实时新闻、事件
    - Agent 知识库之外的信息

    Args:
        query: 搜索关键词或问题
        search_depth: 搜索深度 ("basic" 快速/"advanced" 深度)，默认 "basic"
        max_results: 返回结果数量，默认 5 条

    Returns:
        结构化的搜索结果摘要
    """
    # 检查 API Key
    if not _check_api_key():
        return "联网搜索功能暂不可用，请检查 API 配置（TAVILY_API_KEY）。"

    try:
        logger.info(f"联网搜索: query={query}, depth={search_depth}, max_results={max_results}")

        # 延迟导入，避免未安装依赖时报错
        from langchain_community.tools.tavily_search import TavilySearchResults

        # 创建搜索工具实例
        search = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
        )

        # 执行搜索
        results = search.invoke(query)

        # 格式化输出
        formatted = _format_results(results)
        logger.info(f"搜索完成，返回 {len(results) if results else 0} 条结果")

        return formatted

    except ImportError:
        error_msg = "联网搜索依赖未安装，请运行: uv add langchain-community"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"搜索失败: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# 工具标签
web_search_tool.tags = ["web", "search", "realtime"]

__all__ = ["web_search_tool"]