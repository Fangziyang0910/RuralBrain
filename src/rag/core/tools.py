"""
知识库检索工具（优化版）

基于 references/agent_skills 最佳实践重构：
1. 应用 Consolidation Principle - 4 个核心工具
2. 优化工具描述 - 遵循"做什么、何时用、返回什么"原则
3. 统一参数格式 - 使用一致的设计模式
4. 支持渐进式披露 - 通过参数控制返回详细程度

工具缩减说明：
- get_chapter_content 已删除 - 功能通过 search_knowledge 的 context_mode 实现
- get_full_document 已删除 - 功能通过 search_knowledge 的 expanded 模式实现
- retrieve_knowledge_detailed 已删除 - 冗余工具

优化版本更新：
- 添加评分过滤功能（使用 similarity_search_with_score）
- 支持多种检索策略（similarity、mmr、similarity_score_threshold）
- 与标准 Retriever 接口兼容
"""
import logging
from pathlib import Path
from typing import Optional, Literal

from langchain_core.documents import Document
from langchain_core.tools import Tool, tool

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import (
    DEFAULT_TOP_K,
    RETRIEVE_SCORE_THRESHOLD,
    RETRIEVE_SEARCH_TYPE,
)
from src.rag.core.context_manager import get_context_manager
from src.rag.core.cache import get_vector_cache

logger = logging.getLogger(__name__)

# 支持的检索策略
SearchType = Literal["similarity", "mmr", "similarity_score_threshold"]


# ==================== 辅助函数 ====================

def get_vectorstore():
    """获取向量数据库（使用缓存）"""
    return get_vector_cache().get_vectorstore()


def format_error(message: str, error: Exception) -> str:
    """格式化错误消息（记录完整堆栈）"""
    logger.error(f"{message}时发生错误: {error}", exc_info=True)
    return f"❌ {message}时发生错误: {error}"


# ==================== 工具函数 ====================

def list_available_documents(query: str = "") -> str:
    """
    列出知识库中所有可用文档

    **何时使用：**
    - 任务开始时，了解有哪些资料
    - 用户询问"你有什么知识库"、"你能做什么"时

    **返回：**
    - 文档名称、类型、切片数量、内容预览
    """
    try:
        cm = get_context_manager()
        cm._ensure_loaded()

        if not cm.doc_index:
            return "⚠️  知识库中没有文档"

        lines = ["【可用文档列表】\n"]

        for idx, (source, doc_idx) in enumerate(cm.doc_index.items(), 1):
            preview = doc_idx.chunks_info[0]['content_preview'] if doc_idx.chunks_info else 'N/A'
            lines.append(
                f"{idx}. {source}\n"
                f"   类型: {doc_idx.doc_type}\n"
                f"   切片数: {len(doc_idx.chunks_info)}\n"
                f"   预览: {preview}\n"
            )

        return "\n".join(lines)

    except Exception as e:
        return format_error("列出文档", e)


def get_document_overview(source: str, include_chapters: bool = True) -> str:
    """
    获取文档概览（执行摘要 + 可选章节列表）

    **何时使用：**
    - 快速了解文档核心内容
    - 决定是否需要深入阅读
    - 对比多个文档的主题

    **参数：**
    - source (str | required): 文档名称（文件名）
    - include_chapters (bool | optional): 是否包含章节列表，默认 True

    **返回：**
    - 执行摘要（200 字）
    - 章节标题列表（如果 include_chapters=True）
    """
    try:
        cm = get_context_manager()
        result = cm.get_executive_summary(source)

        if "error" in result:
            return f"❌ {result['error']}"

        lines = [
            f"【文档概览】\n",
            f"来源: {result['source']}\n",
            f"类型: {result.get('doc_type', '未知')}\n\n",
        ]

        if result.get("executive_summary"):
            lines.append(f"**执行摘要**\n{result['executive_summary']}\n")
        else:
            lines.append(f"⚠️  该文档尚未生成摘要\n")

        if include_chapters:
            chapters_result = cm.list_chapter_summaries(source)
            if chapters_result.get("chapters"):
                lines.append(f"\n**章节列表**\n")
                lines.extend(f"{idx}. {chapter['title']}\n" for idx, chapter in enumerate(chapters_result['chapters'], 1))

        return "\n".join(lines)

    except Exception as e:
        return format_error("获取文档概览", e)


def search_knowledge(
    query: str,
    top_k: int = 5,
    context_mode: str = "standard",
    search_type: SearchType = RETRIEVE_SEARCH_TYPE,
    score_threshold: Optional[float] = None,
) -> str:
    """
    检索知识库（支持多种上下文模式和检索策略）

    **何时使用：**
    - 需要查找特定信息时
    - 获取相关片段的上下文
    - 探索知识库中的相关内容

    **参数：**
    - query (str | required): 查询问题或关键词
    - top_k (int | optional): 返回片段数，默认 5，范围 3-10
    - context_mode (str | optional): 上下文模式
      - "minimal": 仅匹配片段（最少 Token）- 最快
      - "standard": 片段 + 短上下文（300 字，默认）
      - "expanded": 片段 + 长上下文（500 字）- 最详细
    - search_type (SearchType | optional): 检索策略
      - "similarity": 基础相似度检索
      - "mmr": 最大边际相关性检索（增加多样性）
      - "similarity_score_threshold": 带评分过滤的检索（推荐）
    - score_threshold (float | optional): 相似度阈值（0-1），默认使用配置值

    **返回：**
    - 匹配的文档片段列表，包含来源、位置、内容
    """
    try:
        cache = get_vector_cache()

        # 检查缓存
        context_params = {"top_k": top_k, "context_mode": context_mode, "search_type": search_type}
        cached = cache.get_cached_query(query, context_params)
        if cached is not None:
            return cached

        db = get_vectorstore()
        context_chars_map = {"minimal": 0, "standard": 300, "expanded": 500}
        context_chars = context_chars_map.get(context_mode, 300)

        # 根据检索策略选择检索方法
        threshold = score_threshold or RETRIEVE_SCORE_THRESHOLD

        if search_type == "similarity_score_threshold":
            # 使用带评分过滤的检索
            results_with_scores = db.similarity_search_with_score(query, k=top_k)

            # 过滤低分结果
            # 注意：此公式仅适用于 Cosine Distance
            results = []
            for doc, score in results_with_scores:
                similarity_score = 1.0 - score

                if similarity_score >= threshold:
                    doc.metadata["score"] = similarity_score
                    results.append(doc)
                    logger.debug(f"文档通过过滤: 相似度={similarity_score:.3f}, 阈值={threshold}")
                else:
                    logger.debug(f"文档被过滤: 相似度={similarity_score:.3f}, 阈值={threshold}")

            logger.info(f"评分过滤: 原始 {len(results_with_scores)} 个，过滤后 {len(results)} 个")

            # Fallback: 如果过滤后结果为空，返回原始结果并添加警告
            if not results and results_with_scores:
                logger.warning(
                    f"所有结果都被过滤（阈值={threshold}），"
                    f"启用 fallback 机制返回原始结果"
                )
                for doc, score in results_with_scores:
                    similarity_score = 1.0 - score
                    doc.metadata["score"] = similarity_score
                    doc.metadata["low_similarity_warning"] = True
                    results.append(doc)

        elif search_type == "mmr":
            # 使用 MMR 检索（增加多样性）
            from src.rag.config import MMR_LAMBDA_MULT
            results = db.max_marginal_relevance_search(
                query=query,
                k=top_k,
                fetch_k=top_k * 3,  # 先获取更多候选
                lambda_mult=MMR_LAMBDA_MULT,
            )
            logger.info(f"MMR 检索: 返回 {len(results)} 个结果")

        else:  # similarity
            # 基础相似度检索
            results = db.similarity_search(query, k=top_k)

        if not results:
            return "⚠️  知识库中未找到相关信息。"

        # 格式化结果
        fragments = []

        for idx, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", doc.metadata.get("paragraph", "未知"))
            doc_type = doc.metadata.get("type", "未知类型")
            start_index = doc.metadata.get("start_index", 0)
            score = doc.metadata.get("score")

            fragment = [f"【知识片段 {idx}】", f"来源: {source}", f"位置: 第{page} {doc_type}"]

            # 显示评分（如果有）
            if score is not None:
                fragment.append(f"相似度: {score:.3f}")

            # 显示低相似度警告
            if doc.metadata.get("low_similarity_warning"):
                fragment.append("⚠️ 注意: 相似度较低，结果仅供参考")

            if context_mode == "minimal":
                fragment.append(f"内容: {doc.page_content}")
            elif context_chars > 0 and start_index > 0:
                try:
                    cm = get_context_manager()
                    ctx = cm.get_context_around_chunk(source, start_index, context_chars)

                    if "error" not in ctx and (ctx.get('before') or ctx.get('after')):
                        if ctx['before']:
                            fragment.append(f"\n前文:\n{ctx['before'][:200]}...")
                        fragment.append(f"\n核心内容:\n{doc.page_content}")
                        if ctx['after']:
                            fragment.append(f"\n后文:\n{ctx['after'][:200]}...")
                    else:
                        fragment.append(f"\n内容:\n{doc.page_content}")
                except Exception:
                    fragment.append(f"\n内容:\n{doc.page_content}")
            else:
                fragment.append(f"\n内容:\n{doc.page_content}")

            fragments.append("\n".join(fragment))

        result = "\n\n".join(fragments)

        # 缓存结果
        cache.cache_query_result(query, result, context_params)

        return result

    except Exception as e:
        return format_error("查询知识库", e)


def search_key_points(query: str, sources: Optional[list[str]] = None) -> str:
    """
    搜索关键要点（预先提取的核心信息）

    **何时使用：**
    - 快速查找关键信息（比全文检索更精确）
    - 需要"要点式"答案时
    - 探索文档的核心观点

    **参数：**
    - query (str | required):: 搜索关键词
    - sources (list[str] | optional): 限制搜索的文档列表，默认搜索所有文档

    **返回：**
    - 匹配的要点列表，包含来源文档和具体内容
    """
    try:
        cm = get_context_manager()

        sources_list = None
        if sources:
            sources_list = [sources] if isinstance(sources, str) else sources

        result = cm.search_key_points(query, sources_list)

        if result['total_matches'] == 0:
            return f"⚠️  未找到包含 '{query}' 的要点"

        lines = [
            f"【关键要点搜索结果】",
            f"查询: {result['query']}",
            f"匹配数量: {result['total_matches']}\n"
        ]

        for match in result['matches']:
            lines.append(f"📄 {match['source']}\n   {match['point']}\n")

        return "\n".join(lines)

    except Exception as e:
        return format_error("搜索要点", e)


# ==================== LangChain Tools 定义 ====================

@tool
def document_list_tool() -> str:
    """
    列出知识库中所有可用的文档及其基本信息。

    在使用其他文档工具前，建议先使用此工具查看有哪些文档可用。
    """
    return list_available_documents()

@tool
def document_overview_tool(source: str, include_chapters: bool = True) -> str:
    """
    获取文档概览（执行摘要 + 可选章节列表）。

    快速了解文档核心内容，包含 200 字执行摘要和可选的章节列表。

    Args:
        source: 文档名称（文件名，必需）
        include_chapters: 是否包含章节列表（可选，默认 true）

    Returns:
        执行摘要和可选的章节列表
    """
    return get_document_overview(source, include_chapters)

@tool
def knowledge_search_tool(
    query: str,
    top_k: int = 5,
    context_mode: str = "standard",
    search_type: str = RETRIEVE_SEARCH_TYPE,
) -> str:
    """
    检索知识库（支持多种上下文模式和检索策略）。

    基于查询检索相关文档片段，支持不同详细程度的上下文和多种检索策略。

    Args:
        query: 查询问题或关键词（必需）
        top_k: 返回片段数（可选，默认 5，范围 3-10）
        context_mode: 上下文模式（可选，默认 "standard"）
            - "minimal": 仅匹配片段（最少 Token）
            - "standard": 片段 + 短上下文（300 字，默认）
            - "expanded": 片段 + 长上下文（500 字，用于深度检索）
        search_type: 检索策略（可选，默认 "similarity_score_threshold"）
            - "similarity": 基础相似度检索
            - "mmr": 最大边际相关性检索（增加结果多样性）
            - "similarity_score_threshold": 带评分过滤的检索（推荐）

    Returns:
        匹配的文档片段列表，包含来源、位置、内容
    """
    return search_knowledge(query, top_k, context_mode, search_type)

@tool
def key_points_search_tool(query: str, sources: Optional[str] = None) -> str:
    """
    搜索关键要点（预先提取的核心信息）。

    在所有文档的关键要点中搜索关键词，比全文检索更精确。

    Args:
        query: 搜索关键词（必需）
        sources: 限制搜索的文档列表（可选，可以是单个文档名或用逗号分隔的多个文档名）

    Returns:
        匹配的要点列表，包含来源文档和具体内容
    """
    # 处理 sources 参数：将逗号分隔的字符串转换为列表
    sources_list = None
    if sources:
        sources_list = [s.strip() for s in sources.split(",") if s.strip()]

    return search_key_points(query, sources_list)


# ==================== 工具列表 ====================

PLANNING_TOOLS = [
    document_list_tool,
    document_overview_tool,
    key_points_search_tool,
    knowledge_search_tool,
]
