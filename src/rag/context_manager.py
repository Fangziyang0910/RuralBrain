"""
文档上下文管理器
用于在检索时提供完整的章节上下文，而非孤立切片
支持决策智能体深度理解文档结构
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict as asdict

from langchain_core.documents import Document
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.rag.config import CHROMA_PERSIST_DIR


@dataclass
class DocumentIndex:
    """原文档索引条目"""
    source: str  # 文件名
    doc_type: str  # 文档类型 (pdf/docx/pptx等)
    full_content: str  # 完整内容
    metadata: dict  # 原始元数据
    chunks_info: List[dict]  # 该文档的所有切片信息
    # 阶段2新增：摘要字段
    executive_summary: Optional[str] = None  # 执行摘要（200字）
    chapter_summaries: Optional[List[dict]] = None  # 章节摘要列表
    key_points: Optional[List[str]] = None  # 全文关键要点


class DocumentContextManager:
    """
    文档上下文管理器

    功能：
    1. 保存原文档完整内容和切片映射
    2. 根据切片位置获取周围上下文
    3. 获取完整章节内容
    4. 跨切片上下文拼接

    使用场景：
    - Agentic RAG：Agent 需要阅读完整章节而非孤立片段
    - 复杂决策：需要理解文档的前后逻辑
    - 精确引用：提供准确的上下文范围
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        初始化上下文管理器

        Args:
            index_path: 索引文件路径，默认使用 CHROMA_PERSIST_DIR/document_index.json
        """
        if index_path is None:
            index_path = CHROMA_PERSIST_DIR / "document_index.json"

        self.index_path = Path(index_path)
        self.doc_index: Dict[str, DocumentIndex] = {}
        self._loaded = False

    def build_index(self, documents: List[Document], splits: List[Document]) -> None:
        """
        从原始文档和切片构建索引

        Args:
            documents: 原始文档列表（加载后、切分前）
            splits: 切分后的文档列表
        """
        # 按来源分组原始文档
        original_docs: Dict[str, Document] = {}
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            original_docs[source] = doc

        # 按来源分组切片
        splits_by_source: Dict[str, List[Document]] = {}
        for split in splits:
            source = split.metadata.get("source", "unknown")
            if source not in splits_by_source:
                splits_by_source[source] = []
            splits_by_source[source].append(split)

        # 构建索引
        self.doc_index = {}
        for source, orig_doc in original_docs.items():
            source_splits = splits_by_source.get(source, [])

            # 收集切片信息
            chunks_info = []
            for split in source_splits:
                chunks_info.append({
                    "start_index": split.metadata.get("start_index", 0),
                    "content_preview": split.page_content[:100] + "..." if len(split.page_content) > 100 else split.page_content,
                    "metadata": split.metadata
                })

            # 创建索引条目
            self.doc_index[source] = DocumentIndex(
                source=source,
                doc_type=orig_doc.metadata.get("type", "unknown"),
                full_content=orig_doc.page_content,
                metadata=orig_doc.metadata,
                chunks_info=chunks_info
            )

        self._loaded = True

    def save(self) -> None:
        """保存索引到磁盘"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化的格式
        from dataclasses import asdict
        serializable_index = {
            source: asdict(index) for source, index in self.doc_index.items()
        }

        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_index, f, ensure_ascii=False, indent=2)

        print(f"✅ 文档索引已保存到: {self.index_path}")

    def load(self) -> None:
        """从磁盘加载索引"""
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"文档索引不存在: {self.index_path}\n"
                f"请先运行 build.py 构建知识库"
            )

        with open(self.index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 重建 DocumentIndex 对象（兼容旧格式）
        self.doc_index = {}
        for source, item in data.items():
            # 确保新字段存在（兼容旧版本）
            if 'executive_summary' not in item:
                item['executive_summary'] = None
            if 'chapter_summaries' not in item:
                item['chapter_summaries'] = None
            if 'key_points' not in item:
                item['key_points'] = None

            self.doc_index[source] = DocumentIndex(**item)

        self._loaded = True
        print(f"✅ 文档索引已加载，共 {len(self.doc_index)} 个文档")

    def _ensure_loaded(self) -> None:
        """确保索引已加载"""
        if not self._loaded:
            self.load()

    def get_context_around_chunk(
        self,
        source: str,
        chunk_start_index: int,
        context_chars: int = 500
    ) -> dict:
        """
        获取切片周围的上下文

        Args:
            source: 文档来源（文件名）
            chunk_start_index: 切片的起始字符位置
            context_chars: 前后上下文字符数

        Returns:
            包含前文、当前切片、后文的字典
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]
        full_content = doc_index.full_content

        # 计算上下文范围
        start = max(0, chunk_start_index - context_chars)
        end = min(len(full_content), chunk_start_index + context_chars)

        # 提取上下文
        before = full_content[start:chunk_start_index].strip()
        after = full_content[chunk_start_index + context_chars:end].strip()

        # 获取当前切片内容（近似）
        current_end = min(len(full_content), chunk_start_index + context_chars)
        current = full_content[chunk_start_index:current_end]

        return {
            "source": source,
            "before": before,
            "current": current,
            "after": after,
            "context_range": f"{start}-{end}"
        }

    def get_full_document(self, source: str) -> dict:
        """
        获取完整文档内容

        Args:
            source: 文档来源（文件名）

        Returns:
            包含完整内容和元数据的字典
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]

        return {
            "source": source,
            "doc_type": doc_index.doc_type,
            "content": doc_index.full_content,
            "metadata": doc_index.metadata,
            "total_chunks": len(doc_index.chunks_info)
        }

    def get_chapter_by_header(
        self,
        source: str,
        header_pattern: str
    ) -> dict:
        """
        根据标题模式获取章节内容

        Args:
            source: 文档来源
            header_pattern: 标题模式（支持部分匹配）

        Returns:
            章节内容和上下文
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]
        full_content = doc_index.full_content

        # 查找标题位置
        lines = full_content.split('\n')
        chapter_start = None
        chapter_end = None

        for i, line in enumerate(lines):
            if header_pattern.lower() in line.lower():
                chapter_start = i
                # 查找章节结束（下一个同级或更高级标题）
                for j in range(i + 1, len(lines)):
                    # 检测下一行是否是标题
                    next_line = lines[j].strip()
                    if next_line.startswith('#') and j > i + 1:
                        chapter_end = j
                        break
                break

        if chapter_start is None:
            return {"error": f"未找到包含 '{header_pattern}' 的章节"}

        # 提取章节内容
        if chapter_end is None:
            chapter_content = '\n'.join(lines[chapter_start:])
        else:
            chapter_content = '\n'.join(lines[chapter_start:chapter_end])

        return {
            "source": source,
            "chapter_title": lines[chapter_start].strip(),
            "content": chapter_content,
            "line_range": f"{chapter_start}-{chapter_end if chapter_end else 'end'}"
        }

    def search_across_contexts(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        context_chars: int = 300
    ) -> List[dict]:
        """
        跨文档搜索并返回上下文

        Args:
            query: 搜索关键词
            sources: 限制搜索的文档列表，None 表示搜索所有
            context_chars: 上下文字符数

        Returns:
            匹配结果列表，每个结果包含上下文
        """
        self._ensure_loaded()

        results = []

        # 确定要搜索的文档
        search_docs = sources if sources else list(self.doc_index.keys())

        for source in search_docs:
            if source not in self.doc_index:
                continue

            doc_index = self.doc_index[source]
            full_content = doc_index.full_content

            # 查找所有匹配位置
            pos = 0
            while True:
                pos = full_content.lower().find(query.lower(), pos)
                if pos == -1:
                    break

                # 提取上下文
                start = max(0, pos - context_chars)
                end = min(len(full_content), pos + len(query) + context_chars)

                context = full_content[start:end]

                results.append({
                    "source": source,
                    "match_position": pos,
                    "context": context,
                    "snippet": full_content[pos:pos + len(query)]
                })

                pos += len(query)

        return results

    # ==================== 阶段2：摘要查询方法 ====================

    def get_executive_summary(self, source: str) -> dict:
        """
        获取文档的执行摘要

        Args:
            source: 文档来源（文件名）

        Returns:
            包含执行摘要的字典
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]

        if not doc_index.executive_summary:
            return {
                "source": source,
                "executive_summary": None,
                "message": "该文档尚未生成摘要，请先运行知识库构建流程"
            }

        return {
            "source": source,
            "doc_type": doc_index.doc_type,
            "executive_summary": doc_index.executive_summary
        }

    def list_chapter_summaries(self, source: str) -> dict:
        """
        列出文档的所有章节摘要

        Args:
            source: 文档来源（文件名）

        Returns:
            包含章节摘要列表的字典
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]

        if not doc_index.chapter_summaries:
            return {
                "source": source,
                "chapters": [],
                "message": "该文档尚未生成章节摘要，请先运行知识库构建流程"
            }

        chapters = []
        for chapter in doc_index.chapter_summaries:
            chapters.append({
                "title": chapter.get("title"),
                "level": chapter.get("level"),
                "summary": chapter.get("summary"),
                "key_points": chapter.get("key_points", [])
            })

        return {
            "source": source,
            "total_chapters": len(chapters),
            "chapters": chapters
        }

    def get_chapter_summary(self, source: str, chapter_pattern: str) -> dict:
        """
        获取特定章节的摘要

        Args:
            source: 文档来源（文件名）
            chapter_pattern: 章节标题关键词（支持部分匹配）

        Returns:
            包含章节摘要的字典
        """
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]

        if not doc_index.chapter_summaries:
            return {
                "error": "该文档尚未生成章节摘要，请先运行知识库构建流程"
            }

        # 搜索匹配的章节
        for chapter in doc_index.chapter_summaries:
            title = chapter.get("title", "")
            if chapter_pattern.lower() in title.lower():
                return {
                    "source": source,
                    "chapter_title": title,
                    "level": chapter.get("level"),
                    "summary": chapter.get("summary"),
                    "key_points": chapter.get("key_points", []),
                    "position": f"{chapter.get('start_index')}-{chapter.get('end_index')}"
                }

        return {"error": f"未找到包含 '{chapter_pattern}' 的章节"}

    def search_key_points(self, query: str, sources: Optional[List[str]] = None) -> dict:
        """
        在关键要点中搜索关键词

        Args:
            query: 搜索关键词
            sources: 限制搜索的文档列表，None 表示搜索所有

        Returns:
            匹配的要点列表
        """
        self._ensure_loaded()

        results = []

        # 确定要搜索的文档
        search_docs = sources if sources else list(self.doc_index.keys())

        for source in search_docs:
            if source not in self.doc_index:
                continue

            doc_index = self.doc_index[source]

            if not doc_index.key_points:
                continue

            # 在该文档的要点中搜索
            for point in doc_index.key_points:
                if query.lower() in point.lower():
                    results.append({
                        "source": source,
                        "point": point
                    })

        return {
            "query": query,
            "total_matches": len(results),
            "matches": results
        }


# 全局单例（懒加载）
_context_manager: Optional[DocumentContextManager] = None


def get_context_manager() -> DocumentContextManager:
    """获取全局上下文管理器实例"""
    global _context_manager

    if _context_manager is None:
        _context_manager = DocumentContextManager()
        # 自动尝试加载
        if _context_manager.index_path.exists():
            _context_manager.load()

    return _context_manager


if __name__ == "__main__":
    # 测试代码
    print("测试 DocumentContextManager")
    cm = DocumentContextManager()

    # 尝试加载已有索引
    try:
        cm.load()
        print(f"\n索引中的文档: {list(cm.doc_index.keys())}")

        # 测试获取完整文档
        if cm.doc_index:
            first_source = list(cm.doc_index.keys())[0]
            print(f"\n获取完整文档: {first_source}")
            doc = cm.get_full_document(first_source)
            print(f"文档类型: {doc['doc_type']}")
            print(f"总切片数: {doc['total_chunks']}")
            print(f"内容长度: {len(doc['content'])} 字符")

    except FileNotFoundError as e:
        print(f"索引文件不存在: {e}")
