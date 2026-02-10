"""
知识库检索工具（优化版）

基于 references/agent_skills 最佳实践重构：
1. 应用 Consolidation Principle - 7 个核心工具
2. 优化工具描述 - 遵循"做什么、何时用、返回什么"原则
3. 统一参数格式 - 使用一致的设计模式
4. 支持渐进式披露 - 通过参数控制返回详细程度
"""
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.tools import Tool, tool

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import DEFAULT_TOP_K
from src.rag.core.context_manager import get_context_manager
from src.rag.core.cache import get_vector_cache


# ==================== 辅助函数 ====================

def get_vectorstore():
    """获取向量数据库（使用缓存）"""
    return get_vector_cache().get_vectorstore()


def format_error(message: str, error: Exception) -> str:
    """格式化错误消息"""
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


def get_chapter_content(source: str, chapter_pattern: str, detail_level: str = "medium") -> str:
    """
    获取章节内容（支持三级详情）

    **何时使用：**
    - 了解特定章节内容时
    - 根据信息需求选择合适的详细程度
    - 快速浏览或深度阅读特定章节

    **参数：**
    - source (str | required): 文档名称（文件名）
    - chapter_pattern (str | required): 章节标题关键词（支持部分匹配）
    - detail_level (str | optional): 详细程度
      - "summary": 仅摘要（100-200 字）- 最快
      - "medium": 摘要 + 关键要点（默认）
      - "full": 完整章节内容 - 最详细

    **返回：**
    - 根据 detail_level 返回不同详细程度的章节内容
    """
    try:
        cm = get_context_manager()

        if detail_level == "summary":
            result = cm.get_chapter_summary(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"
            return f"【知识片段 1】\n来源: {result['source']}\n位置: 第1 页\n内容:\n{result['summary']}"

        elif detail_level == "medium":
            result = cm.get_chapter_summary(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"

            lines = [
                f"【知识片段 1】\n",
                f"来源: {result['source']}\n",
                f"位置: 第1 页\n",
                f"内容:\n**摘要**\n{result['summary']}\n\n",
                f"**关键要点**\n"
            ]
            lines.extend(f"  • {point}" for point in result.get('key_points', []))
            return "\n".join(lines)

        elif detail_level == "full":
            result = cm.get_chapter_by_header(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"
            return f"【知识片段 1】\n来源: {result['source']}\n位置: 第1 页\n内容:\n{result['content']}"

        else:
            return f"❌ 无效的 detail_level: {detail_level}。请使用 'summary', 'medium', 或 'full'"

    except Exception as e:
        return format_error("获取章节内容", e)


def search_knowledge(query: str, top_k: int = 5, context_mode: str = "standard") -> str:
    """
    检索知识库（支持多种上下文模式）

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

    **返回：**
    - 匹配的文档片段列表，包含来源、位置、内容
    """
    try:
        db = get_vectorstore()
        context_chars_map = {"minimal": 0, "standard": 300, "expanded": 500}
        context_chars = context_chars_map.get(context_mode, 300)

        results: list[Document] = db.similarity_search(query, k=top_k)

        if not results:
            return "⚠️  知识库中未找到相关信息。"

        fragments = []

        for idx, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", doc.metadata.get("paragraph", "未知"))
            doc_type = doc.metadata.get("type", "未知类型")
            start_index = doc.metadata.get("start_index", 0)

            fragment = [f"【知识片段 {idx}】", f"来源: {source}", f"位置: 第{page} {doc_type}"]

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

        return "\n\n".join(fragments)

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
    - query (str | required): 搜索关键词
    - sources (list[str] | optional): 限制搜索的文档列表，默认搜索所有文档

    **返回：**
    - 匹配的要点列表，包含来源文档和具体内容
    """
    try:
        # 兼容旧的调用方式
        if isinstance(query, dict):
            query = query.get("query", "")
            sources = query.get("sources")

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


def get_full_document(source: str) -> str:
    """
    获取完整文档内容

    **何时使用：**
    - 需要深度理解完整规划时
    - 需要查看文档的整体结构和全貌
    - 需要引用完整文档内容时

    **参数：**
    - source (str | required): 文档名称（文件名）

    **返回：**
    - 完整文档内容和元数据（类型、切片数、内容长度等）

    **注意：**
    - 文档可能很长（数万字），会消耗大量 Token
    - 谨慎使用，优先考虑 get_document_overview 或 get_chapter_content
    """
    try:
        cm = get_context_manager()
        result = cm.get_full_document(source)

        if "error" in result:
            return f"❌ {result['error']}"

        return (
            f"【完整文档】\n"
            f"来源: {result['source']}\n"
            f"类型: {result['doc_type']}\n"
            f"总切片数: {result['total_chunks']}\n"
            f"内容长度: {len(result['content'])} 字符\n\n"
            f"内容:\n{result['content']}"
        )

    except Exception as e:
        return format_error("获取文档", e)


# ==================== LangChain Tools 定义 ====================

def create_tool(name: str, func, description_template: str) -> Tool:
    """创建工具的辅助函数"""
    return Tool(name=name, func=func, description=description_template)


document_list_tool = Tool(
    name="list_documents",
    func=list_available_documents,
    description="列出知识库中所有可用的文档及其基本信息。在使用其他文档工具前，建议先使用此工具查看有哪些文档可用。",
)

# 使用 @tool 装饰器重新定义工具（修复参数传递问题）
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
def chapter_content_tool(source: str, chapter_pattern: str, detail_level: str = "medium") -> str:
    """
    获取章节内容（支持三级详情）。

    根据需求获取不同详细程度的章节内容，从摘要到完整内容。

    Args:
        source: 文档名称（文件名，必需）
        chapter_pattern: 章节标题关键词（必需，支持部分匹配）
        detail_level: 详细程度（可选，默认 "medium"）
            - "summary": 仅摘要（100-200 字）
            - "medium": 摘要 + 关键要点（默认）
            - "full": 完整章节内容

    Returns:
        根据 detail_level 返回不同详细程度的章节内容
    """
    return get_chapter_content(source, chapter_pattern, detail_level)

@tool
def knowledge_search_tool(query: str, top_k: int = 5, context_mode: str = "standard") -> str:
    """
    检索知识库（支持多种上下文模式）。

    基于查询检索相关文档片段，支持不同详细程度的上下文。

    Args:
        query: 查询问题或关键词（必需）
        top_k: 返回片段数（可选，默认 5，范围 3-10）
        context_mode: 上下文模式（可选，默认 "standard"）
            - "minimal": 仅匹配片段（最少 Token）
            - "standard": 片段 + 短上下文（300 字，默认）
            - "expanded": 片段 + 长上下文（500 字）

    Returns:
        匹配的文档片段列表，包含来源、位置、内容
    """
    return search_knowledge(query, top_k, context_mode)

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

    # 直接调用原始函数，传递解析后的参数
    cm = get_context_manager()
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

@tool
def full_document_tool(source: str) -> str:
    """
    获取完整文档内容。

    获取文档的完整内容和元数据。

    Args:
        source: 文档名称（文件名，必需）

    Returns:
        完整文档内容和元数据（类型、切片数、内容长度等）

    注意：
        文档可能很长（数万字），会消耗大量 Token。谨慎使用，优先考虑 get_document_overview 或 get_chapter_content。
    """
    return get_full_document(source)


# ==================== 工具列表 ====================

PLANNING_TOOLS = [
    document_list_tool,
    document_overview_tool,
    key_points_search_tool,
    knowledge_search_tool,
    chapter_content_tool,
    full_document_tool,
]

# 向后兼容：别名
planning_knowledge_tool = knowledge_search_tool
executive_summary_tool = document_overview_tool
chapter_summaries_list_tool = document_overview_tool
chapter_summary_tool = chapter_content_tool
chapter_context_tool = chapter_content_tool
context_around_tool = knowledge_search_tool


# ==================== 旧版工具（兼容性）====================

def retrieve_planning_knowledge(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    with_context: bool = True,
    context_chars: int = 300
) -> str:
    """检索乡村规划相关知识（兼容旧版）"""
    if not with_context or context_chars == 0:
        context_mode = "minimal"
    elif context_chars >= 500:
        context_mode = "expanded"
    else:
        context_mode = "standard"

    return search_knowledge(query, top_k, context_mode)


from langchain_core.tools import tool


@tool(response_format="content_and_artifact")
def retrieve_knowledge_detailed(query: str) -> tuple[str, list[Document]]:
    """检索知识（Agentic RAG 模式，兼容旧版）"""
    db = get_vectorstore()
    retrieved_docs = db.similarity_search(query, k=DEFAULT_TOP_K)

    serialized = "\n\n".join(
        f"来源: {doc.metadata.get('source', '未知')}\n"
        f"位置: {doc.metadata.get('page', doc.metadata.get('paragraph', '未知'))}\n"
        f"内容: {doc.page_content}"
        for doc in retrieved_docs
    )

    return serialized, retrieved_docs
