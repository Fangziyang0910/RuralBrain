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


def retrieve_planning_knowledge(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    检索乡村规划相关知识（适配 Planning Agent）

    Args:
        query: 查询问题
        top_k: 返回的切片数量（Planning Agent 需要更多上下文）

    Returns:
        格式化的检索结果
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

            # 构建上下文片段
            context_part = (
                f"【知识片段 {idx}】\n"
                f"来源: {source}\n"
                f"位置: 第{page}{doc_type}\n"
                f"内容:\n{doc.page_content}"
            )
            context_parts.append(context_part)

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
