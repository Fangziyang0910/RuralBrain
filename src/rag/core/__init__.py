"""
RAG 核心模块

包含：
- context_manager: 文档上下文管理器
- summarization: 层次化摘要系统
- tools: Agent 工具集
"""

from src.rag.core.context_manager import (
    DocumentContextManager,
    DocumentIndex,
    get_context_manager,
)

from src.rag.core.summarization import (
    DocumentSummarizer,
    DocumentSummary,
    ChapterSummary,
    summarize_document,
)

from src.rag.core.tools import (
    planning_knowledge_tool,
    full_document_tool,
    chapter_context_tool,
    document_list_tool,
    context_around_tool,
    executive_summary_tool,
    chapter_summaries_list_tool,
    chapter_summary_tool,
    key_points_search_tool,
)

__all__ = [
    # Context Manager
    "DocumentContextManager",
    "DocumentIndex",
    "get_context_manager",
    # Summarization
    "DocumentSummarizer",
    "DocumentSummary",
    "ChapterSummary",
    "summarize_document",
    # Tools (阶段1)
    "planning_knowledge_tool",
    "full_document_tool",
    "chapter_context_tool",
    "document_list_tool",
    "context_around_tool",
    # Tools (阶段2)
    "executive_summary_tool",
    "chapter_summaries_list_tool",
    "chapter_summary_tool",
    "key_points_search_tool",
]
