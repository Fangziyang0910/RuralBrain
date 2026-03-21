"""
联网搜索工具：通过 Tavily API 搜索实时网络信息

该工具让 Agent 能够获取实时市场信息、最新政策、新闻等。

改进：
- 支持 time_range 参数提高时效性
- 支持 topic 参数区分普通搜索和新闻搜索
- 使用官方推荐的 langchain-tavily 包
"""
import logging
import os
from typing import Literal, Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_MAX_RESULTS = 5
DEFAULT_SEARCH_DEPTH = "basic"
DEFAULT_TIME_RANGE = "month"
DEFAULT_TOPIC = "general"


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
        # 尝试获取发布日期（如果有）
        published_date = result.get("published_date", "")

        output_lines.append(f"\n{i}. [{title}]({url})")
        if published_date:
            output_lines.append(f"   发布时间: {published_date}")
        output_lines.append(f"   摘要: {content}")

    return "\n".join(output_lines)


@tool
def web_search_tool(
    query: str,
    search_depth: Literal["basic", "advanced"] = DEFAULT_SEARCH_DEPTH,
    max_results: int = DEFAULT_MAX_RESULTS,
    time_range: Literal["day", "week", "month", "year"] = DEFAULT_TIME_RANGE,
    topic: Literal["general", "news"] = DEFAULT_TOPIC,
) -> str:
    """
    联网搜索实时信息，获取最新数据。

    适用场景：
    - 市场价格、行情趋势（建议使用 time_range="month"）
    - 最新政策法规（建议使用 topic="news"）
    - 实时新闻、事件（建议使用 time_range="day" 或 "week"）
    - Agent 知识库之外的信息

    Args:
        query: 搜索关键词或问题
        search_depth: 搜索深度
            - "basic": 快速搜索，适合简单查询
            - "advanced": 深度搜索，更全面但较慢
        max_results: 返回结果数量，默认 5 条
        time_range: 时间范围过滤，限制搜索结果的时间
            - "day": 最近一天
            - "week": 最近一周
            - "month": 最近一个月（默认）
            - "year": 最近一年
        topic: 搜索主题
            - "general": 通用搜索（默认）
            - "news": 新闻搜索，时效性更强

    Returns:
        结构化的搜索结果摘要
    """
    # 检查 API Key
    if not _check_api_key():
        return "联网搜索功能暂不可用，请检查 API 配置（TAVILY_API_KEY）。"

    try:
        logger.info(
            f"联网搜索: query={query}, depth={search_depth}, "
            f"max_results={max_results}, time_range={time_range}, topic={topic}"
        )

        # 使用官方推荐的 langchain-tavily 包
        try:
            from langchain_tavily import TavilySearch

            # 创建搜索工具实例
            search = TavilySearch(
                max_results=max_results,
                topic=topic,
                time_range=time_range,
                search_depth=search_depth,
                include_answer=True,
            )
        except ImportError:
            # 降级到旧版 API（兼容性）
            logger.warning("langchain-tavily 未安装，使用旧版 langchain-community")
            from langchain_community.tools.tavily_search import TavilySearchResults

            search = TavilySearchResults(
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
            )

        # 执行搜索
        results = search.invoke(query)

        # 处理返回结果格式差异
        # TavilySearch 返回 dict，TavilySearchResults 返回 list
        if isinstance(results, dict):
            # 新版 TavilySearch 返回格式
            result_list = results.get("results", [])
            answer = results.get("answer", "")
            formatted = _format_results(result_list)
            if answer:
                formatted = f"**AI 摘要**: {answer}\n\n{formatted}"
        else:
            # 旧版 TavilySearchResults 返回格式
            formatted = _format_results(results)

        result_count = len(results.get("results", results)) if isinstance(results, dict) else len(results)
        logger.info(f"搜索完成，返回 {result_count} 条结果")

        return formatted

    except ImportError:
        error_msg = "联网搜索依赖未安装，请运行: uv add langchain-tavily"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"搜索失败: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# 工具标签
web_search_tool.tags = ["web", "search", "realtime"]

__all__ = ["web_search_tool"]