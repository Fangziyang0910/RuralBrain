"""
知识库检索工具（适配 Planning Agent）
使用 Agentic RAG 模式，让 LLM 自主决定何时检索
支持整体层面知识读取，更适合复杂决策场景
"""
import os
from pathlib import Path
from typing import List

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
from src.rag.context_manager import get_context_manager

# 全局变量（懒加载）
_embedding_model = None
_vectorstore = None


def get_vectorstore():
    """
    懒加载向量数据库
    避免每次调用都重新加载模型
    """
    global _embedding_model, _vectorstore

    if _vectorstore is None:
        print("📥 正在加载知识库...")

        # 初始化 Embedding 模型
        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            encode_kwargs={"normalize_embeddings": True},
        )

        # 加载向量数据库
        if not CHROMA_PERSIST_DIR.exists():
            raise FileNotFoundError(
                f"知识库不存在: {CHROMA_PERSIST_DIR}\n"
                f"请先运行: python src/rag/build.py"
            )

        _vectorstore = Chroma(
            persist_directory=str(CHROMA_PERSIST_DIR),
            embedding_function=_embedding_model,
            collection_name=CHROMA_COLLECTION_NAME,
        )

        print(f"✅ 知识库加载完成（集合: {CHROMA_COLLECTION_NAME}）")

    return _vectorstore


def retrieve_planning_knowledge(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    with_context: bool = True,
    context_chars: int = 300
) -> str:
    """
    检索乡村规划相关知识（适配 Planning Agent）

    Args:
        query: 查询问题
        top_k: 返回的切片数量（Planning Agent 需要更多上下文）
        with_context: 是否包含周围上下文（阶段1新增功能）
        context_chars: 上下文字符数（仅在 with_context=True 时生效）

    Returns:
        格式化的检索结果，包含上下文信息
    """
    try:
        db = get_vectorstore()

        # 使用更高的 k 值获取更多上下文（适合 Planning Agent）
        results: List[Document] = db.similarity_search(query, k=top_k)

        if not results:
            return "⚠️  知识库中未找到相关信息。"

        # 格式化结果，提供更丰富的上下文信息
        context_parts = []

        for idx, doc in enumerate(results, 1):
            # 提取元数据
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", doc.metadata.get("paragraph", "未知"))
            doc_type = doc.metadata.get("type", "未知类型")
            start_index = doc.metadata.get("start_index", 0)

            # 构建基础上下文片段
            context_part = [
                f"【知识片段 {idx}】",
                f"来源: {source}",
                f"位置: 第{page}{doc_type}",
            ]

            # 如果启用了上下文功能，尝试获取周围内容
            if with_context and start_index > 0:
                try:
                    cm = get_context_manager()
                    ctx = cm.get_context_around_chunk(source, start_index, context_chars)

                    if "error" not in ctx:
                        # 添加上下文信息
                        if ctx['before']:
                            context_part.append(f"\n前文:\n{ctx['before'][:200]}...")

                        context_part.append(f"\n核心内容:\n{doc.page_content}")

                        if ctx['after']:
                            context_part.append(f"\n后文:\n{ctx['after'][:200]}...")

                        context_part.append(f"\n💡 提示: 使用 get_full_document('{source}') 查看完整文档")
                    else:
                        # 回退到原始格式
                        context_part.append(f"\n内容:\n{doc.page_content}")

                except Exception as e:
                    # 上下文获取失败，回退到原始格式
                    context_part.append(f"\n内容:\n{doc.page_content}")
            else:
                # 不使用上下文，使用原始格式
                context_part.append(f"\n内容:\n{doc.page_content}")

            context_parts.append("\n".join(context_part))

        return "\n\n".join(context_parts)

    except Exception as e:
        return f"❌ 查询知识库时发生错误: {str(e)}"


def retrieve_with_metadata(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    source_filter: str | None = None,
):
    """
    带元数据过滤的检索（高级用法）

    Args:
        query: 查询问题
        top_k: 返回的切片数量
        source_filter: 按来源过滤（例如："luofu_strategy.pptx"）

    Returns:
        文档列表（包含完整元数据）
    """
    try:
        db = get_vectorstore()

        # 构建过滤条件
        if source_filter:
            # 使用元数据过滤
            results = db.similarity_search(
                query,
                k=top_k,
                filter={"source": source_filter},
            )
        else:
            results = db.similarity_search(query, k=top_k)

        return results

    except Exception as e:
        print(f"❌ 检索失败: {e}")
        return []


# ==================== LangChain Tool 定义 ====================
# 这个 Tool 可以直接集成到 Agent 中

planning_knowledge_tool = Tool(
    name="search_rural_planning_knowledge",
    func=retrieve_planning_knowledge,
    description=(
        "【乡村规划知识库】"
        "当用户询问关于乡村规划、农业发展、产业布局、历史文化、"
        "旅游开发、政策解读等需要宏观决策的问题时，使用此工具。"
        "该工具会返回相关的知识片段，帮助你做出更全面的规划和决策。"
        "\n\n"
        "使用场景示例："
        '- "博罗古城的发展定位是什么？"'
        '- "如何规划乡村旅游产业？"'
        '- "当地有哪些历史文化资源？"'
    ),
)

# 也可以使用 response_format="content_and_artifact" 模式（Agentic RAG）
# 让 LLM 能够看到原始文档对象
from langchain_core.tools import tool

@tool(response_format="content_and_artifact")
def retrieve_knowledge_detailed(query: str) -> tuple[str, List[Document]]:
    """
    检索知识（Agentic RAG 模式）
    返回格式化文本 + 原始文档对象
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


# ==================== 上下文查询工具（阶段1新增）====================

def get_full_document(source: str) -> str:
    """
    获取完整文档内容（用于深度理解）

    Args:
        source: 文档来源（文件名）

    Returns:
        完整文档内容
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


def get_chapter_by_header(source: str, header_pattern: str) -> str:
    """
    根据标题获取章节内容

    Args:
        source: 文档来源（文件名）
        header_pattern: 标题关键词（如"第一章"、"产业发展"等）

    Returns:
        章节内容
    """
    try:
        cm = get_context_manager()
        result = cm.get_chapter_by_header(source, header_pattern)

        if "error" in result:
            return f"❌ {result['error']}"

        return (
            f"【章节内容】\n"
            f"来源: {result['source']}\n"
            f"章节: {result['chapter_title']}\n"
            f"行范围: {result['line_range']}\n\n"
            f"内容:\n{result['content']}"
        )

    except Exception as e:
        return f"❌ 获取章节时发生错误: {str(e)}"


def get_context_around(source: str, position: int, context_chars: int = 500) -> str:
    """
    获取指定位置周围的上下文

    Args:
        source: 文档来源（文件名）
        position: 字符位置
        context_chars: 前后上下文字符数

    Returns:
        包含前文、当前位置、后文的字符串
    """
    try:
        cm = get_context_manager()
        result = cm.get_context_around_chunk(source, position, context_chars)

        if "error" in result:
            return f"❌ {result['error']}"

        output = [
            f"【上下文片段】",
            f"来源: {result['source']}",
            f"范围: {result['context_range']}",
        ]

        if result['before']:
            output.append(f"\n前文:\n{result['before']}")

        output.append(f"\n当前位置:\n{result['current']}")

        if result['after']:
            output.append(f"\n后文:\n{result['after']}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ 获取上下文时发生错误: {str(e)}"


def list_available_documents(query: str = "") -> str:
    """
    列出所有可用的文档

    Returns:
        文档列表
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


# ==================== 新增的 LangChain Tools ====================

full_document_tool = Tool(
    name="get_full_document",
    func=get_full_document,
    description=(
        "【获取完整文档】"
        "当你需要阅读整个文档来理解完整的规划背景、政策细节或方案全貌时使用此工具。"
        "这比检索片段更适合理解宏观结构和完整逻辑。\n\n"
        "参数说明："
        '- source: 文档来源（文件名），如 "plan.docx" 或 "strategy.pdf"'
        "\n\n"
        "使用场景示例："
        '- "我要了解罗浮山发展战略的完整内容"'
        '- "查看博罗古城规划的所有章节"'
        "\n\n"
        "提示：可以使用 list_available_documents 先查看所有可用文档。"
    ),
)

chapter_context_tool = Tool(
    name="get_chapter_by_header",
    func=lambda params: get_chapter_by_header(**params),
    description=(
        "【获取章节内容】"
        "根据标题关键词获取特定章节的完整内容。适合查看文档中的某个主题章节。\n\n"
        "参数说明（JSON格式）："
        '- source: 文档来源（文件名）'
        '- header_pattern: 标题关键词（如"第一章"、"产业发展"、"环境保护"等）'
        "\n\n"
        "使用场景示例："
        '- 查看第一章: {"source": "plan.docx", "header_pattern": "第一章"}'
        '- 查看产业规划: {"source": "strategy.pdf", "header_pattern": "产业"}'
        "\n\n"
        "提示：支持标题的部分匹配，不必输入完整标题。"
    ),
)

document_list_tool = Tool(
    name="list_available_documents",
    func=list_available_documents,
    description=(
        "【列出可用文档】"
        "列出知识库中所有可用的文档及其基本信息。"
        "在使用其他文档工具前，建议先使用此工具查看有哪些文档可用。"
    ),
)

context_around_tool = Tool(
    name="get_context_around",
    func=lambda params: get_context_around(**params),
    description=(
        "【获取上下文】"
        "获取文档中特定位置周围的上下文（前文+当前位置+后文）。"
        "用于理解某个观点或段落的完整语境。\n\n"
        "参数说明（JSON格式）："
        '- source: 文档来源（文件名）'
        '- position: 字符位置（从切片的 start_index 元数据获取）'
        '- context_chars: 上下文字符数（可选，默认500）'
        "\n\n"
        "使用场景："
        "需要理解某个检索结果的前后逻辑时使用。"
    ),
)


# ==================== 阶段2：摘要查询工具 ====================

def get_executive_summary_tool_func(source: str) -> str:
    """
    获取文档的执行摘要（200字）

    Args:
        source: 文档来源（文件名）

    Returns:
        执行摘要
    """
    try:
        cm = get_context_manager()
        result = cm.get_executive_summary(source)

        if "error" in result:
            return f"❌ {result['error']}"

        if not result.get("executive_summary"):
            return f"⚠️  {result.get('message', '该文档暂无执行摘要')}"

        return (
            f"【执行摘要】\n"
            f"来源: {result['source']}\n"
            f"类型: {result['doc_type']}\n\n"
            f"{result['executive_summary']}"
        )

    except Exception as e:
        return f"❌ 获取执行摘要时发生错误: {str(e)}"


def list_chapter_summaries_tool_func(source: str) -> str:
    """
    列出文档的所有章节摘要

    Args:
        source: 文档来源（文件名）

    Returns:
        章节摘要列表
    """
    try:
        cm = get_context_manager()
        result = cm.list_chapter_summaries(source)

        if "error" in result:
            return f"❌ {result['error']}"

        if not result.get("chapters"):
            return f"⚠️  {result.get('message', '该文档暂无章节摘要')}"

        output = [
            f"【章节摘要列表】",
            f"来源: {result['source']}",
            f"总章节数: {result['total_chapters']}\n"
        ]

        for idx, chapter in enumerate(result['chapters'], 1):
            output.append(
                f"\n{idx}. {chapter['title']}\n"
                f"   摘要: {chapter['summary']}\n"
                f"   要点: {'; '.join(chapter.get('key_points', [])[:3])}"
            )

        return "\n".join(output)

    except Exception as e:
        return f"❌ 获取章节摘要时发生错误: {str(e)}"


def get_chapter_summary_tool_func(params: dict) -> str:
    """
    获取特定章节的摘要

    Args:
        params: 包含 source 和 chapter_pattern 的字典

    Returns:
        章节摘要
    """
    try:
        source = params.get("source")
        chapter_pattern = params.get("chapter_pattern")

        if not source or not chapter_pattern:
            return "❌ 缺少必要参数：source 和 chapter_pattern"

        cm = get_context_manager()
        result = cm.get_chapter_summary(source, chapter_pattern)

        if "error" in result:
            return f"❌ {result['error']}"

        output = [
            f"【章节摘要】",
            f"来源: {result['source']}",
            f"章节: {result['chapter_title']}",
            f"级别: {result['level']}",
            f"位置: {result['position']}\n",
            f"摘要:\n{result['summary']}\n",
            f"关键要点:"
        ]

        for point in result.get('key_points', []):
            output.append(f"  • {point}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ 获取章节摘要时发生错误: {str(e)}"


def search_key_points_tool_func(params: dict) -> str:
    """
    在关键要点中搜索关键词

    Args:
        params: 包含 query 和可选 sources 的字典

    Returns:
        匹配的要点列表
    """
    try:
        query = params.get("query")
        sources = params.get("sources")  # 可选

        if not query:
            return "❌ 缺少必要参数：query"

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
            f"【关键要点搜索】",
            f"查询: {result['query']}",
            f"匹配数量: {result['total_matches']}\n"
        ]

        for match in result['matches']:
            output.append(
                f"来源: {match['source']}\n"
                f"要点: {match['point']}\n"
            )

        return "\n".join(output)

    except Exception as e:
        return f"❌ 搜索要点时发生错误: {str(e)}"


# ==================== 新增的 LangChain Tools（阶段2）====================

executive_summary_tool = Tool(
    name="get_executive_summary",
    func=get_executive_summary_tool_func,
    description=(
        "【获取执行摘要】"
        "快速了解文档的核心内容（200字左右摘要）。"
        "适合在时间有限或需要快速浏览文档时使用。\n\n"
        "参数说明："
        '- source: 文档来源（文件名）'
        "\n\n"
        "使用场景示例："
        '- "这个规划文档的核心目标是什么？"'
        '- "快速了解这个政策的主要内容"'
        "\n\n"
        "提示：执行摘要包含目标、定位、关键指标和重点措施。"
    ),
)

chapter_summaries_list_tool = Tool(
    name="list_chapter_summaries",
    func=list_chapter_summaries_tool_func,
    description=(
        "【列出章节摘要】"
        "列出文档的所有章节摘要，浏览文档结构。"
        "每个章节包含摘要和关键要点。\n\n"
        "参数说明："
        '- source: 文档来源（文件名）'
        "\n\n"
        "使用场景示例："
        '- "这个规划文档有哪些章节？"'
        '- "浏览文档的结构和主要内容"'
        "\n\n"
        "提示：与 get_chapter_by_header 不同，此工具只返回摘要，不返回完整内容。"
    ),
)

chapter_summary_tool = Tool(
    name="get_chapter_summary",
    func=get_chapter_summary_tool_func,
    description=(
        "【获取章节摘要】"
        "获取特定章节的摘要和关键要点（不返回完整内容）。"
        "比 get_chapter_by_header 更简洁，只返回摘要版本。\n\n"
        "参数说明（JSON格式）："
        '- source: 文档来源（文件名）'
        '- chapter_pattern: 章节标题关键词（如"第一章"、"产业发展"等）'
        "\n\n"
        "使用场景示例："
        '- 获取第一章摘要: {"source": "plan.docx", "chapter_pattern": "第一章"}'
        '- 获取产业章节摘要: {"source": "strategy.pdf", "chapter_pattern": "产业"}'
        "\n\n"
        "提示：支持标题的部分匹配，返回摘要+要点，不返回完整内容。"
    ),
)

key_points_search_tool = Tool(
    name="search_key_points",
    func=search_key_points_tool_func,
    description=(
        "【搜索关键要点】"
        "在所有文档的关键要点中搜索关键词。"
        "要点是从文档中提取的10-15条核心信息。\n\n"
        "参数说明（JSON格式）："
        '- query: 搜索关键词（必需）'
        '- sources: 限制搜索的文档列表（可选，可以是字符串或列表）'
        "\n\n"
        "使用场景示例："
        '- 搜索旅游相关: {"query": "旅游"}'
        '- 搜索特定文档: {"query": "目标", "sources": "plan.docx"}'
        '- 搜索多个文档: {"query": "投资", "sources": ["plan1.docx", "plan2.docx"]}'
        "\n\n"
        "提示：关键要点是预先提取的，比全文检索更精确、更快速。"
    ),
)
