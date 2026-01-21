"""
知识库检索工具（优化版）
基于 references/agent_skills 最佳实践重构

核心改进：
1. 应用 Consolidation Principle - 从 10+ 个工具精简到 7 个核心工具
2. 优化工具描述 - 遵循"做什么、何时用、返回什么"原则
3. 统一参数格式 - 使用一致的设计模式
4. 支持渐进式披露 - 通过参数控制返回详细程度
"""
import os
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL_NAME,
)
from src.rag.core.context_manager import get_context_manager
from src.rag.core.cache import get_vector_cache


def get_vectorstore():
    """
    获取向量数据库（使用缓存）

    优化版本：使用 VectorStoreCache 替代懒加载全局变量
    - Embedding 模型自动缓存
    - 向量数据库连接自动缓存
    - 支持查询结果缓存（可选）
    """
    cache = get_vector_cache()
    return cache.get_vectorstore()


# ==================== 工具 1：列出可用文档 ====================

def list_available_documents(query: str = "") -> str:
    """
    列出知识库中所有可用文档

    **何时使用：**
    - 任务开始时，了解有哪些资料
    - 用户询问"你有什么知识库"、"你能做什么"时

    **返回：**
    - 文档名称、类型、切片数量、内容预览

    **示例：**
    - "你有什么文档？"
    - "知识库里有哪些资料？"
    """
    try:
        cm = get_context_manager()
        cm._ensure_loaded()

        if not cm.doc_index:
            return "⚠️  知识库中没有文档"

        output = ["【可用文档列表】\n"]

        for idx, (source, doc_idx) in enumerate(cm.doc_index.items(), 1):
            output.append(
                f"{idx}. {source}\n"
                f"   类型: {doc_idx.doc_type}\n"
                f"   切片数: {len(doc_idx.chunks_info)}\n"
                f"   预览: {doc_idx.chunks_info[0]['content_preview'] if doc_idx.chunks_info else 'N/A'}\n"
            )

        return "\n".join(output)

    except Exception as e:
        return f"❌ 列出文档时发生错误: {str(e)}"


# ==================== 工具 2：获取文档概览（新增）====================

def get_document_overview(source: str, include_chapters: bool = True) -> str:
    """
    获取文档概览（执行摘要 + 可选章节列表）

    **功能：**
    快速了解文档核心内容，包含 200 字执行摘要和可选的章节列表

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

    **示例：**
    - get_document_overview("罗浮-长宁山镇融合发展战略.pptx")
    - get_document_overview("plan.docx", include_chapters=False)

    **注意：**
    - 如果文档尚未生成摘要，会提示用户先运行知识库构建
    """
    try:
        cm = get_context_manager()
        result = cm.get_executive_summary(source)

        if "error" in result:
            return f"❌ {result['error']}"

        output = [
            f"【文档概览】\n",
            f"来源: {result['source']}\n",
            f"类型: {result['doc_type']}\n\n",
        ]

        # 添加执行摘要
        if result.get("executive_summary"):
            output.append(f"**执行摘要**\n{result['executive_summary']}\n")
        else:
            output.append(f"⚠️  该文档尚未生成摘要\n")

        # 添加章节列表
        if include_chapters:
            chapters_result = cm.list_chapter_summaries(source)
            if chapters_result.get("chapters"):
                output.append(f"\n**章节列表**\n")
                for idx, chapter in enumerate(chapters_result['chapters'], 1):
                    output.append(f"{idx}. {chapter['title']}\n")

        return "\n".join(output)

    except Exception as e:
        return f"❌ 获取文档概览时发生错误: {str(e)}"


# ==================== 工具 3：获取章节内容（新增）====================

def get_chapter_content(source: str, chapter_pattern: str, detail_level: str = "medium") -> str:
    """
    获取章节内容（支持三级详情）

    **功能：**
    根据需求获取不同详细程度的章节内容，从摘要到完整内容

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
    - detail_level="summary": 章节摘要
    - detail_level="medium": 章节摘要 + 关键要点
    - detail_level="full": 完整章节内容

    **示例：**
    - 快速浏览：get_chapter_content("plan.docx", "第一章", "summary")
    - 中等深度：get_chapter_content("plan.docx", "产业", "medium")
    - 深度阅读：get_chapter_content("plan.docx", "投资", "full")

    **注意：**
    - 支持标题的部分匹配，不必输入完整标题
    - "full" 模式可能返回较长内容，谨慎使用
    """
    try:
        cm = get_context_manager()

        # 根据详细程度选择不同的方法
        if detail_level == "summary":
            # 仅返回摘要
            result = cm.get_chapter_summary(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"

            output = [
                f"【章节摘要】\n",
                f"来源: {result['source']}\n",
                f"章节: {result['chapter_title']}\n\n",
                f"{result['summary']}"
            ]
            return "\n".join(output)

        elif detail_level == "medium":
            # 返回摘要 + 要点
            result = cm.get_chapter_summary(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"

            output = [
                f"【章节内容（中等详细）】\n",
                f"来源: {result['source']}\n",
                f"章节: {result['chapter_title']}\n\n",
                f"**摘要**\n{result['summary']}\n\n",
                f"**关键要点**\n"
            ]

            for point in result.get('key_points', []):
                output.append(f"  • {point}")

            return "\n".join(output)

        elif detail_level == "full":
            # 返回完整章节
            result = cm.get_chapter_by_header(source, chapter_pattern)
            if "error" in result:
                return f"❌ {result['error']}"

            output = [
                f"【章节完整内容】\n",
                f"来源: {result['source']}\n",
                f"章节: {result['chapter_title']}\n",
                f"行范围: {result['line_range']}\n\n",
                f"{result['content']}"
            ]
            return "\n".join(output)

        else:
            return f"❌ 无效的 detail_level: {detail_level}。请使用 'summary', 'medium', 或 'full'"

    except Exception as e:
        return f"❌ 获取章节内容时发生错误: {str(e)}"


# ==================== 工具 4：检索知识库（优化）====================

def search_knowledge(
    query: str,
    top_k: int = 5,
    context_mode: str = "standard"
) -> str:
    """
    检索知识库（支持多种上下文模式）

    **功能：**
    基于查询检索相关文档片段，支持不同详细程度的上下文

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
    - 匹配的文档片段列表
    - 每个片段包含来源、位置、内容

    **示例：**
    - search_knowledge("旅游发展目标")
    - search_knowledge("投资政策", top_k=3, context_mode="minimal")
    - search_knowledge("产业布局", context_mode="expanded")

    **注意：**
    - "minimal" 模式适合快速查找
    - "expanded" 模式提供更多上下文，但 Token 消耗更多
    - top_k 过大可能导致返回内容过长
    """
    try:
        db = get_vectorstore()

        # 根据上下文模式设置参数
        context_chars_map = {
            "minimal": 0,
            "standard": 300,
            "expanded": 500
        }

        context_chars = context_chars_map.get(context_mode, 300)

        # 使用更高的 k 值获取更多上下文（适合 Planning Agent）
        results: List[Document] = db.similarity_search(query, k=top_k)

        if not results:
            return "⚠️  知识库中未找到相关信息。"

        # 格式化结果
        context_parts = []

        for idx, doc in enumerate(results, 1):
            # 提取元数据
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", doc.metadata.get("paragraph", "未知"))
            doc_type = doc.metadata.get("type", "未知类型")
            start_index = doc.metadata.get("start_index", 0)

            # 构建基础上下文片段
            if context_mode == "minimal":
                # minimal 模式：仅返回核心内容
                context_part = [
                    f"【片段 {idx}】",
                    f"来源: {source}",
                    f"位置: 第{page}{doc_type}",
                    f"内容: {doc.page_content}"
                ]
            else:
                # standard 和 expanded 模式：包含上下文
                context_part = [
                    f"【片段 {idx}】",
                    f"来源: {source}",
                    f"位置: 第{page}{doc_type}",
                ]

                # 尝试获取上下文
                if context_chars > 0 and start_index > 0:
                    try:
                        cm = get_context_manager()
                        ctx = cm.get_context_around_chunk(source, start_index, context_chars)

                        if "error" not in ctx and ctx.get('before') or ctx.get('after'):
                            # 添加上下文信息
                            if ctx['before']:
                                context_part.append(f"\n前文:\n{ctx['before'][:200]}...")

                            context_part.append(f"\n核心内容:\n{doc.page_content}")

                            if ctx['after']:
                                context_part.append(f"\n后文:\n{ctx['after'][:200]}...")
                        else:
                            # 回退到原始格式
                            context_part.append(f"\n内容:\n{doc.page_content}")

                    except Exception:
                        # 上下文获取失败，回退到原始格式
                        context_part.append(f"\n内容:\n{doc.page_content}")
                else:
                    # 不使用上下文
                    context_part.append(f"\n内容:\n{doc.page_content}")

            context_parts.append("\n".join(context_part))

        return "\n\n".join(context_parts)

    except Exception as e:
        return f"❌ 查询知识库时发生错误: {str(e)}"


# ==================== 工具 5：搜索关键要点（保留，优化描述）====================

def search_key_points(query: str, sources: Optional[List[str]] = None) -> str:
    """
    搜索关键要点（预先提取的核心信息）

    **功能：**
    在所有文档的关键要点中搜索关键词，要点是预先提取的 10-15 条核心信息

    **何时使用：**
    - 快速查找关键信息（比全文检索更精确）
    - 需要"要点式"答案时
    - 探索文档的核心观点

    **参数：**
    - query (str | required): 搜索关键词
    - sources (list[str] | optional): 限制搜索的文档列表，默认搜索所有文档

    **返回：**
    - 匹配的要点列表
    - 每个要点包含来源文档和具体内容

    **示例：**
    - search_key_points({"query": "旅游"})
    - search_key_points({"query": "目标", "sources": ["plan.docx"]})
    - search_key_points({"query": "投资", "sources": ["plan1.docx", "plan2.docx"]})

    **注意：**
    - 关键要点是预先提取的，比全文检索更快、更精确
    - 仅搜索要点，不搜索完整文档内容
    - 如果没有匹配的要点，会返回空结果
    """
    try:
        # 兼容旧的调用方式（JSON 字符串或字典）
        if isinstance(query, dict):
            query = query.get("query", "")
            sources = query.get("sources")

        cm = get_context_manager()

        # 处理 sources 参数
        sources_list = None
        if sources:
            if isinstance(sources, str):
                sources_list = [sources]
            elif isinstance(sources, list):
                sources_list = sources

        result = cm.search_key_points(query, sources_list)

        if result['total_matches'] == 0:
            return f"⚠️  未找到包含 '{query}' 的要点"

        output = [
            f"【关键要点搜索结果】",
            f"查询: {result['query']}",
            f"匹配数量: {result['total_matches']}\n"
        ]

        for match in result['matches']:
            output.append(
                f"📄 {match['source']}\n"
                f"   {match['point']}\n"
            )

        return "\n".join(output)

    except Exception as e:
        return f"❌ 搜索要点时发生错误: {str(e)}"


# ==================== 工具 6：获取完整文档（保留）====================

def get_full_document(source: str) -> str:
    """
    获取完整文档内容

    **功能：**
    获取文档的完整内容和元数据

    **何时使用：**
    - 需要深度理解完整规划时
    - 需要查看文档的整体结构和全貌
    - 需要引用完整文档内容时

    **参数：**
    - source (str | required): 文档名称（文件名）

    **返回：**
    - 完整文档内容
    - 元数据（类型、切片数、内容长度等）

    **示例：**
    - get_full_document("罗浮-长宁山镇融合发展战略.pptx")
    - get_full_document("plan.docx")

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
        return f"❌ 获取文档时发生错误: {str(e)}"


# ==================== LangChain Tools 定义 ====================
# 这些 Tool 对象可以直接集成到 Agent 中

document_list_tool = Tool(
    name="list_documents",
    func=list_available_documents,
    description=(
        "列出知识库中所有可用的文档及其基本信息。"
        "在使用其他文档工具前，建议先使用此工具查看有哪些文档可用。"
        "\n\n"
        "**何时使用：**"
        "- 任务开始时，了解有哪些资料"
        "- 用户询问'你有什么知识库'、'你能做什么'时"
        "\n\n"
        "**返回：**"
        "- 文档名称、类型、切片数量、内容预览"
    ),
)

document_overview_tool = Tool(
    name="get_document_overview",
    func=lambda params: get_document_overview(**params) if isinstance(params, dict) else get_document_overview(params),
    description=(
        "获取文档概览（执行摘要 + 可选章节列表）。"
        "快速了解文档核心内容，包含 200 字执行摘要和可选的章节列表。"
        "\n\n"
        "**何时使用：**"
        "- 快速了解文档核心内容"
        "- 决定是否需要深入阅读"
        "- 对比多个文档的主题"
        "\n\n"
        "**参数（JSON 格式）：**"
        '- source: 文档名称（文件名，必需）'
        '- include_chapters: 是否包含章节列表（可选，默认 true）'
        "\n\n"
        "**示例：**"
        '- {"source": "罗浮-长宁山镇融合发展战略.pptx"}'
        '- {"source": "plan.docx", "include_chapters": false}'
    ),
)

chapter_content_tool = Tool(
    name="get_chapter_content",
    func=lambda params: get_chapter_content(**params) if isinstance(params, dict) else get_chapter_content(params, ""),
    description=(
        "获取章节内容（支持三级详情）。"
        "根据需求获取不同详细程度的章节内容，从摘要到完整内容。"
        "\n\n"
        "**何时使用：**"
        "- 了解特定章节内容时"
        "- 根据信息需求选择合适的详细程度"
        "- 快速浏览或深度阅读特定章节"
        "\n\n"
        "**参数（JSON 格式）：**"
        '- source: 文档名称（文件名，必需）'
        '- chapter_pattern: 章节标题关键词（必需，支持部分匹配）'
        '- detail_level: 详细程度（可选，默认 "medium"）'
        '  * "summary": 仅摘要（100-200 字）- 最快'
        '  * "medium": 摘要 + 关键要点（默认）'
        '  * "full": 完整章节内容 - 最详细'
        "\n\n"
        "**示例：**"
        '- 快速浏览: {"source": "plan.docx", "chapter_pattern": "第一章", "detail_level": "summary"}'
        '- 中等深度: {"source": "plan.docx", "chapter_pattern": "产业", "detail_level": "medium"}'
        '- 深度阅读: {"source": "plan.docx", "chapter_pattern": "投资", "detail_level": "full"}'
    ),
)

knowledge_search_tool = Tool(
    name="search_knowledge",
    func=lambda params: search_knowledge(**params) if isinstance(params, dict) else search_knowledge(params),
    description=(
        "检索知识库（支持多种上下文模式）。"
        "基于查询检索相关文档片段，支持不同详细程度的上下文。"
        "\n\n"
        "**何时使用：**"
        "- 需要查找特定信息时"
        "- 获取相关片段的上下文"
        "- 探索知识库中的相关内容"
        "\n\n"
        "**参数（JSON 格式）：**"
        '- query: 查询问题或关键词（必需）'
        '- top_k: 返回片段数（可选，默认 5，范围 3-10）'
        '- context_mode: 上下文模式（可选，默认 "standard"）'
        '  * "minimal": 仅匹配片段（最少 Token）- 最快'
        '  * "standard": 片段 + 短上下文（300 字，默认）'
        '  * "expanded": 片段 + 长上下文（500 字）- 最详细'
        "\n\n"
        "**示例：**"
        '- search_knowledge({"query": "旅游发展目标"})'
        '- search_knowledge({"query": "投资政策", "top_k": 3, "context_mode": "minimal"})'
        '- search_knowledge({"query": "产业布局", "context_mode": "expanded"})'
    ),
)

key_points_search_tool = Tool(
    name="search_key_points",
    func=search_key_points,
    description=(
        "搜索关键要点（预先提取的核心信息）。"
        "在所有文档的关键要点中搜索关键词，要点是预先提取的 10-15 条核心信息。"
        "\n\n"
        "**何时使用：**"
        "- 快速查找关键信息（比全文检索更精确）"
        "- 需要'要点式'答案时"
        "- 探索文档的核心观点"
        "\n\n"
        "**参数（JSON 格式）：**"
        '- query: 搜索关键词（必需）'
        '- sources: 限制搜索的文档列表（可选，可以是字符串或列表）'
        "\n\n"
        "**示例：**"
        '- {"query": "旅游"}'
        '- {"query": "目标", "sources": "plan.docx"}'
        '- {"query": "投资", "sources": ["plan1.docx", "plan2.docx"]}'
        "\n\n"
        "**注意：**"
        "关键要点是预先提取的，比全文检索更快、更精确。"
    ),
)

full_document_tool = Tool(
    name="get_document_full",
    func=get_full_document,
    description=(
        "获取完整文档内容。"
        "获取文档的完整内容和元数据。"
        "\n\n"
        "**何时使用：**"
        "- 需要深度理解完整规划时"
        "- 需要查看文档的整体结构和全貌"
        "- 需要引用完整文档内容时"
        "\n\n"
        "**参数：**"
        '- source: 文档名称（文件名，必需）'
        "\n\n"
        "**示例：**"
        '- {"source": "罗浮-长宁山镇融合发展战略.pptx"}'
        '- {"source": "plan.docx"}'
        "\n\n"
        "**注意：**"
        "文档可能很长（数万字），会消耗大量 Token。"
        "谨慎使用，优先考虑 get_document_overview 或 get_chapter_content。"
    ),
)


# ==================== 导出工具列表 ====================

# 核心工具集（7 个工具）
PLANNING_TOOLS = [
    # 基础工具
    document_list_tool,

    # 快速模式工具
    document_overview_tool,
    key_points_search_tool,

    # 深度模式工具
    knowledge_search_tool,
    chapter_content_tool,
    full_document_tool,
]

# 向后兼容：保留旧的工具名称
planning_knowledge_tool = knowledge_search_tool  # 别名
executive_summary_tool = document_overview_tool  # 别名
chapter_summaries_list_tool = document_overview_tool  # 别名
chapter_summary_tool = chapter_content_tool  # 别名
chapter_context_tool = chapter_content_tool  # 别名
context_around_tool = knowledge_search_tool  # 别名


# ==================== 旧版工具（兼容性）====================

# 保留旧的 retrieve_planning_knowledge 函数以兼容现有代码
def retrieve_planning_knowledge(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    with_context: bool = True,
    context_chars: int = 300
) -> str:
    """
    检索乡村规划相关知识（兼容旧版）

    **注意：** 这是一个兼容性函数，建议使用新的 search_knowledge 工具
    """
    # 根据旧参数映射到新的 context_mode
    if not with_context or context_chars == 0:
        context_mode = "minimal"
    elif context_chars >= 500:
        context_mode = "expanded"
    else:
        context_mode = "standard"

    return search_knowledge(query, top_k, context_mode)


# 旧的 Agentic RAG 模式工具（兼容性）
from langchain_core.tools import tool

@tool(response_format="content_and_artifact")
def retrieve_knowledge_detailed(query: str) -> tuple[str, List[Document]]:
    """
    检索知识（Agentic RAG 模式，兼容旧版）
    返回格式化文本 + 原始文档对象

    **注意：** 这是一个兼容性函数，建议使用新的 search_knowledge 工具
    """
    db = get_vectorstore()
    retrieved_docs = db.similarity_search(query, k=DEFAULT_TOP_K)

    # 格式化内容
    serialized = "\n\n".join(
        f"来源: {doc.metadata.get('source', '未知')}\n"
        f"位置: {doc.metadata.get('page', doc.metadata.get('paragraph', '未知'))}\n"
        f"内容: {doc.page_content}"
        for doc in retrieved_docs
    )

    return serialized, retrieved_docs
