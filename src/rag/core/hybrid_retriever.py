"""
混合检索器：向量检索 + BM25 关键词检索

实现混合检索策略：
1. 向量检索：语义相似度（ChromaDB）
2. BM25 检索：关键词匹配
3. RRF 融合排序：结合两种检索结果

参考：
- LangChain EnsembleRetriever
- RRF (Reciprocal Rank Fusion) 算法
"""
import logging
import threading
from typing import List, Optional, Tuple

from langchain_core.documents import Document

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.config import (
    DEFAULT_TOP_K,
    RETRIEVE_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)

# BM25 相关导入
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None
    logger.warning("rank-bm25 未安装，混合检索不可用。请运行: uv add rank-bm25")


class HybridRetriever:
    """
    混合检索器：向量检索 + BM25 关键词检索

    功能：
    1. 向量检索：语义相似度
    2. BM25 检索：关键词精确匹配
    3. RRF 融合排序：结合两种检索结果

    使用场景：
    - 用户查询包含明确关键词
    - 语义检索可能遗漏精确匹配的内容
    - 需要提高召回率

    示例：
        retriever = HybridRetriever(vectorstore)
        results = retriever.retrieve("耕地保护政策", k=5)
    """

    def __init__(
        self,
        vectorstore,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rrf_k: int = 60,  # RRF 算法参数
    ):
        """
        初始化混合检索器

        Args:
            vectorstore: 向量数据库实例（Chroma）
            vector_weight: 向量检索权重（0-1）
            bm25_weight: BM25 检索权重（0-1）
            rrf_k: RRF 算法的 k 参数，用于平滑排名
        """
        if not BM25_AVAILABLE:
            raise ImportError("rank-bm25 未安装，请运行: uv add rank-bm25")

        self.vectorstore = vectorstore
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

        # BM25 索引（延迟加载）
        self._bm25 = None
        self._bm25_documents: List[Document] = []
        self._bm25_loaded = False  # 标记是否已尝试加载
        self._bm25_empty = False  # 标记知识库是否为空
        self._bm25_lock = threading.Lock()

        logger.info(
            f"HybridRetriever 初始化: vector_weight={vector_weight}, "
            f"bm25_weight={bm25_weight}, rrf_k={rrf_k}"
        )

    def _ensure_bm25_loaded(self):
        """确保 BM25 索引已加载（延迟加载）"""
        if self._bm25_loaded:
            return

        with self._bm25_lock:
            if self._bm25_loaded:
                return

            logger.info("正在构建 BM25 索引...")
            self._load_documents_for_bm25()
            self._bm25_loaded = True

    def _load_documents_for_bm25(self):
        """从 ChromaDB 加载所有文档用于 BM25 索引"""
        try:
            # 获取 ChromaDB 的底层 collection
            chroma_collection = self.vectorstore._collection

            # 获取所有文档
            result = chroma_collection.get(include=["documents", "metadatas"])

            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])

            if not documents:
                logger.warning("向量数据库中没有文档，BM25 索引为空，将仅使用向量检索")
                self._bm25_empty = True
                self._bm25 = None
                return

            # 构建 Document 对象列表
            self._bm25_documents = []
            for doc_content, metadata in zip(documents, metadatas):
                self._bm25_documents.append(Document(
                    page_content=doc_content,
                    metadata=metadata or {}
                ))

            # 中文分词：使用简单的字符分割 + jieba（如果可用）
            tokenized_docs = [self._tokenize(doc) for doc in documents]

            # 构建 BM25 索引
            self._bm25 = BM25Okapi(tokenized_docs)

            logger.info(f"BM25 索引构建完成: {len(documents)} 个文档")

        except Exception as e:
            logger.error(f"构建 BM25 索引失败: {e}", exc_info=True)
            self._bm25_empty = True
            self._bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        """
        中文分词

        优先使用 jieba，如果不可用则使用简单的字符分割

        Args:
            text: 待分词的文本

        Returns:
            分词结果列表
        """
        # 尝试使用 jieba
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # jieba 不可用，使用简单的字符分割
            # 将文本按字符分割，过滤空白字符
            return [c for c in text if c.strip()]

    def retrieve(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = None,
    ) -> List[Tuple[Document, float]]:
        """
        混合检索

        Args:
            query: 查询字符串
            k: 返回结果数量
            score_threshold: 相似度阈值（仅用于向量检索）

        Returns:
            (Document, score) 元组列表
        """
        self._ensure_bm25_loaded()

        threshold = score_threshold or RETRIEVE_SCORE_THRESHOLD

        # 1. 向量检索
        vector_results = self._vector_search(query, k * 2, threshold)
        logger.debug(f"向量检索返回 {len(vector_results)} 个结果")

        # 2. BM25 检索（如果知识库不为空）
        bm25_results = []
        if not self._bm25_empty and self._bm25 is not None:
            bm25_results = self._bm25_search(query, k * 2)
            logger.debug(f"BM25 检索返回 {len(bm25_results)} 个结果")
        else:
            logger.debug("BM25 索引为空，跳过 BM25 检索")

        # 3. RRF 融合排序
        # 如果 BM25 没有结果，直接返回向量检索结果
        if not bm25_results:
            logger.debug("BM25 无结果，返回向量检索结果")
            return vector_results[:k]

        combined_results = self._rrf_fusion(vector_results, bm25_results, k)

        return combined_results

    def _vector_search(
        self,
        query: str,
        k: int,
        score_threshold: float,
    ) -> List[Tuple[Document, float]]:
        """
        向量检索

        Args:
            query: 查询字符串
            k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            (Document, score) 元组列表
        """
        try:
            results_with_scores = self.vectorstore.similarity_search_with_score(
                query, k=k
            )

            # 转换分数并过滤
            filtered_results = []
            for doc, score in results_with_scores:
                # Cosine Distance 转 Similarity
                similarity_score = 1.0 - score

                # 不在这里过滤，让 RRF 融合后再决定
                filtered_results.append((doc, similarity_score))

            return filtered_results

        except Exception as e:
            logger.error(f"向量检索失败: {e}", exc_info=True)
            return []

    def _bm25_search(
        self,
        query: str,
        k: int,
    ) -> List[Tuple[Document, float]]:
        """
        BM25 关键词检索

        Args:
            query: 查询字符串
            k: 返回结果数量

        Returns:
            (Document, score) 元组列表
        """
        if not self._bm25_documents:
            return []

        try:
            # 分词
            tokenized_query = self._tokenize(query)

            # 获取 BM25 分数
            scores = self._bm25.get_scores(tokenized_query)

            # 获取 top-k 索引
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:k]

            # 构建结果
            results = []
            for idx in top_indices:
                if idx < len(self._bm25_documents) and scores[idx] > 0:
                    doc = self._bm25_documents[idx]
                    # 归一化 BM25 分数（简单归一化到 0-1）
                    normalized_score = min(scores[idx] / 10.0, 1.0)
                    results.append((doc, normalized_score))

            return results

        except Exception as e:
            logger.error(f"BM25 检索失败: {e}", exc_info=True)
            return []

    def _rrf_fusion(
        self,
        vector_results: List[Tuple[Document, float]],
        bm25_results: List[Tuple[Document, float]],
        k: int,
    ) -> List[Tuple[Document, float]]:
        """
        RRF (Reciprocal Rank Fusion) 融合排序

        RRF 公式: score(d) = Σ (1 / (k + rank(d)))

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            k: 返回结果数量

        Returns:
            融合后的 (Document, score) 元组列表
        """
        # 文档 ID 到文档对象的映射
        doc_map = {}

        # 计算向量检索的 RRF 分数
        vector_rrf_scores = {}
        for rank, (doc, _) in enumerate(vector_results, 1):
            doc_id = self._get_doc_id(doc)
            doc_map[doc_id] = doc
            vector_rrf_scores[doc_id] = self.vector_weight / (self.rrf_k + rank)

        # 计算 BM25 检索的 RRF 分数
        bm25_rrf_scores = {}
        for rank, (doc, _) in enumerate(bm25_results, 1):
            doc_id = self._get_doc_id(doc)
            doc_map[doc_id] = doc
            bm25_rrf_scores[doc_id] = self.bm25_weight / (self.rrf_k + rank)

        # 合并所有文档 ID
        all_doc_ids = set(vector_rrf_scores.keys()) | set(bm25_rrf_scores.keys())

        # 计算最终 RRF 分数
        combined_scores = {}
        for doc_id in all_doc_ids:
            v_score = vector_rrf_scores.get(doc_id, 0)
            b_score = bm25_rrf_scores.get(doc_id, 0)
            combined_scores[doc_id] = v_score + b_score

        # 按分数排序
        sorted_doc_ids = sorted(
            combined_scores.keys(),
            key=lambda x: combined_scores[x],
            reverse=True
        )[:k]

        # 构建最终结果
        results = []
        for doc_id in sorted_doc_ids:
            doc = doc_map[doc_id]
            score = combined_scores[doc_id]
            # 将 RRF 分数记录到 metadata
            doc.metadata["hybrid_score"] = score
            doc.metadata["vector_score"] = vector_rrf_scores.get(doc_id, 0)
            doc.metadata["bm25_score"] = bm25_rrf_scores.get(doc_id, 0)
            results.append((doc, score))

        return results

    def _get_doc_id(self, doc: Document) -> str:
        """
        获取文档的唯一标识

        使用内容哈希作为 ID，确保相同内容的文档被视为同一个

        Args:
            doc: Document 对象

        Returns:
            文档 ID 字符串
        """
        # 优先使用 metadata 中的 ID
        if "id" in doc.metadata:
            return str(doc.metadata["id"])

        # 使用 source + start_index 作为 ID
        source = doc.metadata.get("source", "")
        start_index = doc.metadata.get("start_index", "")

        if source and start_index != "":
            return f"{source}_{start_index}"

        # 最后使用内容哈希
        import hashlib
        content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()[:16]
        return content_hash


# ==================== 全局实例管理 ====================

_hybrid_retriever_instances = {}
_hybrid_retriever_lock = threading.Lock()


def get_hybrid_retriever(
    vectorstore,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> HybridRetriever:
    """
    获取混合检索器实例（单例模式）

    Args:
        vectorstore: 向量数据库实例
        vector_weight: 向量检索权重
        bm25_weight: BM25 检索权重

    Returns:
        HybridRetriever 实例
    """
    # 使用 vectorstore 的 id 作为缓存键
    cache_key = id(vectorstore)

    with _hybrid_retriever_lock:
        if cache_key not in _hybrid_retriever_instances:
            _hybrid_retriever_instances[cache_key] = HybridRetriever(
                vectorstore=vectorstore,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
            )
        return _hybrid_retriever_instances[cache_key]


if __name__ == "__main__":
    # 测试代码
    print("测试 HybridRetriever")

    from src.rag.core.cache import get_vector_cache

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    retriever = HybridRetriever(vectorstore)

    # 测试检索
    test_query = "耕地保护政策"
    print(f"\n测试查询: {test_query}")

    results = retriever.retrieve(test_query, k=5)

    print(f"\n返回 {len(results)} 个结果:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n{i}. [分数={score:.4f}]")
        print(f"   向量分数: {doc.metadata.get('vector_score', 0):.4f}")
        print(f"   BM25分数: {doc.metadata.get('bm25_score', 0):.4f}")
        print(f"   来源: {doc.metadata.get('source', 'N/A')}")
        print(f"   内容: {doc.page_content[:100]}...")