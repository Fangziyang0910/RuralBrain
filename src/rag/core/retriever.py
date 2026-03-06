"""
符合 LangChain 标准的自定义检索器

实现 BaseRetriever 接口，提供：
1. 标准检索接口（与 LangChain 生态兼容）
2. 评分过滤（使用 similarity_search_with_score）
3. 多种检索策略（相似度、MMR、混合检索）
4. 上下文管理（支持前后文扩展）

参考:官方文档 https://docs.langchain.com/oss/python/langchain/rag
"""
import logging
from typing import Literal, Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import (
    RETRIEVE_SCORE_THRESHOLD,
    MMR_LAMBDA_MULT,
)
from src.rag.core.context_manager import get_context_manager

logger = logging.getLogger(__name__)


# 定义支持的检索策略
SearchType = Literal["similarity", "mmr", "similarity_score_threshold"]


class RuralBrainRetriever(BaseRetriever):
    """
    符合 LangChain 标准的乡村知识库检索器

    功能：
    1. 实现标准 BaseRetriever 接口
    2. 支持多种检索策略
    3. 自动过滤低分结果
    4. 可选扩展上下文

    示例：
        from langchain_chroma import Chroma
        vectorstore = Chroma(...)

        retriever = RuralBrainRetriever(
            vectorstore=vectorstore,
            search_type="similarity_score_threshold",
            k=5,
            score_threshold=0.7
        )

        results = retriever.invoke("乡村规划的原则")
    """

    vectorstore: object
    """向量数据库实例（Chroma、FAISS 等）"""

    search_type: SearchType = "similarity_score_threshold"
    """检索策略类型"""

    k: int = 5
    """返回结果数量"""

    score_threshold: float = RETRIEVE_SCORE_THRESHOLD
    """相似度评分阈值（用于过滤低质量结果）"""

    fetch_k: int = 20
    """MMR 检索时先获取的候选数量（应大于 k）"""

    lambda_mult: float = MMR_LAMBDA_MULT
    """MMR 多样性权重（0-1，越高越多样化）"""

    enable_context: bool = True
    """是否启用上下文扩展"""

    context: int = 300
    """上下文扩展字符数"""

    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """
        标准检索方法（实现 BaseRetriever 接口）

        Args:
            query: 查询字符串
            run_manager: 回调管理器（用于追踪检索过程）

        Returns:
            相关文档列表（已过滤低分结果）
        """
        logger.info(f"执行检索: 查询='{query[:50]}...', 策略={self.search_type}, k={self.k}")

        if self.search_type == "similarity":
            return self._similarity_search(query, run_manager)
        elif self.search_type == "mmr":
            return self._mmr_search(query, run_manager)
        elif self.search_type == "similarity_score_threshold":
            return self._similarity_search_with_threshold(query, run_manager)
        else:
            logger.warning(f"未知的检索策略: {self.search_type}，使用默认 similarity")
            return self._similarity_search(query, run_manager)

    def _similarity_search(
        self,
        query: str,
        run: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> list[Document]:
        """
        基础相似度检索

        Args:
            query: 查询字符串
            run: 回调管理器

        Returns:
            相关文档列表
        """
        # 使用向量数据库的 similarity_search
        results = self.vectorstore.similarity_search(query, k=self.k)

        # 可选：扩展上下文
        if self.enable_context:
            results = self._expand_context(results)

        return results

    def _similarity_search_with_threshold(
        self,
        query: str,
        run: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> list[Document]:
        """
        带评分过滤的相似度检索（推荐）

        使用 similarity_search_with_score 获取带分数的结果，
        然后过滤低于分数阈值结果。

        Args:
            query: 查询字符串
            run: 回调管理器

        Returns:
            相关文档列表（已过滤低分结果）
        """
        # 使用 similarity_search_with_score 获取带分数的结果
        results_with_scores = self.vectorstore.similarity_search_with_score(
            query, k=self.k
        )

        # 过滤低分结果
        filtered_results = []
        for doc, score in results_with_scores:
            # 注意：Chroma 返回的距离分数是越小越相似
            # 我们需要检查是否在阈值内（距离 < (1 - threshold)）
            # 或者如果配置的是相似度，则需要进行转换
            # 这里假设分数是距离度量，需要转换成相似度
            similarity_score = 1.0 - score  # 假设 Cosine Distance，转换为相似度

            # 检查是否超过阈值
            if similarity_score >= self.score_threshold:
                # 将分数添加到元数据中
                doc.metadata["score"] = similarity_score
                filtered_results.append(doc)
                logger.debug(f"文档通过过滤: 相似度={similarity_score:.3f}, 阈值={self.score_threshold}")
            else:
                logger.debug(f"文档被过滤: 相似度={similarity_score:.3f}, 阈值={self.score_threshold}")

        logger.info(
            f"评分过滤完成: 原始 {len(results_with_scores)} 个结果，"
            f"过滤后 {len(filtered_results)} 个结果"
        )

        # 可选：扩展上下文
        if self.enable_context:
            filtered_results = self._expand_context(filtered_results)

        return filtered_results

    def _mmr_search(
        self,
        query: str,
        run: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> list[Document]:
        """
        最大边际相关性检索（MMR）

        MMR 平衡相关性和多样性，避免返回过于相似的文档。

        Args:
            query: 查询字符串
            run: 回调管理器

        Returns:
            相关文档列表（具有多样性）
        """
        # 使用向量数据库的 max_marginal_relevance_search
        results = self.vectorstore.max_marginal_relevance_search(
            query=query,
            k=self.k,
            fetch_k=self.fetch_k,  # 先获取更多候选，然后进行 MMR 选择
            lambda_mult=self.lambda_mult,
        )

        logger.info(f"MMR 检索完成: 返回 {len(results)} 个结果")

        # 可选：扩展上下文
        if self.enable_context:
            results = self._expand_context(results)

        return results

    def _expand_context(self, documents: list[Document]) -> list[Document]:
        """
        扩展文档上下文

        对于每个文档，从原文档中获取周围的内容，
        使返回结果更完整。

        Args:
            documents: 文档列表

        Returns:
            带扩展上下文的文档列表
        """
        if not documents:
            return documents

        try:
            cm = get_context_manager()
            cm._ensure_loaded()
        except Exception as e:
            logger.warning(f"无法获取上下文管理器: {e}")
            return documents

        expanded_documents = []

        for doc in documents:
            source = doc.metadata.get("source")
            start_index = doc.metadata.get("start_index")

            # 如果文档有位置信息，尝试扩展上下文
            if source and start_index is not None:
                try:
                    ctx = cm.get_context_around_chunk(source, start_index, self.context)

                    if "error" not in ctx:
                        # 创建扩展后的内容
                        parts = []

                        if ctx.get("before"):
                            parts.append(f"[前文] {ctx['before']}")

                        parts.append(f"[核心] {doc.page_content}")

                        if ctx.get("after"):
                            parts.append(f"[后文] {ctx['after']}")

                        # 创建新的文档对象
                        expanded_doc = Document(
                            page_content=" ".join(parts),
                            metadata={
                                **doc.metadata,
                                "context_expanded": True,
                                "context_chars": self.context,
                            }
                        )
                        expanded_documents.append(expanded_doc)
                        continue

                except Exception as e:
                    logger.debug(f"扩展上下文失败: {e}")

            # 如果扩展失败，返回原始文档
            expanded_documents.append(doc)

        return expanded_documents


def get_retriever(
    vectorstore: object,
    search_type: SearchType = "similarity_score_threshold",
    k: int = 5,
    score_threshold: Optional[float] = None,
    enable_context: bool = True,
    context: int = 300,
) -> RuralBrainRetriever:
    """
    便捷函数：创建标准检索器实例

    Args:
        vectorstore: 向量数据库实例
        search_type: 检索策略
        k: 返回结果数量
        score_threshold: 评分阈值（None 则使用默认值）
        enable_context: 是否启用上下文扩展
        context: 上下文扩展字符数

    Returns:
        RuralBrainRetriever 实例

    示例：
        from langchain_chroma import Chroma
        from src.rag.core.cache import get_vector_cache

        vectorstore = get_vector_cache().get_vectorstore()
        retriever = get_retriever(vectorstore, k=5)
        results = retriever.invoke("乡村规划")
    """
    return RuralBrainRetriever(
        vectorstore=vectorstore,
        search_type=search_type,
        k=k,
        score_threshold=score_threshold or RETRIEVE_SCORE_THRESHOLD,
        enable_context=enable_context,
        context=context,
    )


if __name__ == "__main__":
    # 测试代码
    print("测试 RuralBrainRetriever")

    # 初始化向量数据库
    from src.rag.core.cache import get_vector_cache

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 测试不同检索策略
    test_query = "乡村规划的基本原则"

    print(f"\n测试查询: {test_query}")

    # 1. 测试 similarity 检索
    print("\n1. similarity �检索:")
    retriever_sim = get_retriever(vectorstore, search_type="similarity", k=3)
    results_sim = retriever_sim.invoke(test_query)
    print(f"   返回 {len(results_sim)} 个结果")
    for i, doc in enumerate(results_sim, 1):
        print(f"   {i}. {doc.page_content[:100]}...")

    # 2. 测试 MMR 检索
    print("\n2. MMR 检索:")
    retriever_mmr = get_retriever(vectorstore, search_type="mmr", k=3)
    results_mmr = retriever_mmr.invoke(test_query)
    print(f"   返回 {len(results_mmr)} 个结果")
    for i, doc in enumerate(results_mmr, 1):
        print(f"   {i}. {doc.page_content[:100]}...")

    # 3. 测试带评分过滤的检索
    print("\n3. similarity_score_threshold 检索:")
    retriever_threshold = get_retriever(
        vectorstore,
        search_type="similarity_score_threshold",
        k=3,
        score_threshold=0.5,
    )
    results_threshold = retriever_threshold.invoke(test_query)
    print(f"   返回 {len(results_threshold)} 个结果")
    for i, doc in enumerate(results_threshold, 1):
        score = doc.metadata.get("score", "N/A")
        print(f"   {i}. [分数={score}] {doc.page_content[:100]}...")

    print("\n✅ 测试完成")
