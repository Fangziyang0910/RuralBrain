"""
文档上下文管理器
用于在检索时提供完整的章节上下文，而非孤立切片
支持决策智能体深度理解文档结构
"""
import json
from pathlib import Path
from dataclasses import dataclass

from langchain_core.documents import Document

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.rag.config import CHROMA_PERSIST_DIR


# ==================== 数据结构 ====================

@dataclass
class DocumentIndex:
    """原文档索引条目"""
    source: str
    doc_type: str
    full_content: str
    metadata: dict
    chunks_info: list[dict]
    executive_summary: str | None = None
    chapter_summaries: list[dict] | None = None
    key_points: list[str] | None = None


# ==================== 文档上下文管理器 ====================

class DocumentContextManager:
    """
    文档上下文管理器

    功能：
    1. 保存原文档完整内容和切片映射
    2. 根据切片位置获取周围上下文
    3. 获取完整章节内容
    4. 跨切片上下文拼接
    """

    def __init__(self, index_path: Path | None = None):
        self.index_path = Path(index_path or CHROMA_PERSIST_DIR / "document_index.json")
        self.doc_index: dict[str, DocumentIndex] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """确保索引已加载"""
        if not self._loaded:
            self.load()

    # ==================== 索引管理 ====================

    def build_index(self, documents: list[Document], splits: list[Document]) -> None:
        """从原始文档和切片构建索引"""
        # 按来源分组
        original_docs = {doc.metadata.get("source", "unknown"): doc for doc in documents}
        splits_by_source: dict[str, list[Document]] = {}

        for split in splits:
            source = split.metadata.get("source", "unknown")
            splits_by_source.setdefault(source, []).append(split)

        # 构建索引
        self.doc_index = {}

        for source, orig_doc in original_docs.items():
            source_splits = splits_by_source.get(source, [])

            chunks_info = [
                {
                    "start_index": split.metadata.get("start_index", 0),
                    "content_preview": split.page_content[:100] + "..." if len(split.page_content) > 100 else split.page_content,
                    "metadata": split.metadata
                }
                for split in source_splits
            ]

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
        from dataclasses import asdict

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

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
            # 确保新字段存在
            item.setdefault('executive_summary', None)
            item.setdefault('chapter_summaries', None)
            item.setdefault('key_points', None)

            self.doc_index[source] = DocumentIndex(**item)

        self._loaded = True
        print(f"✅ 文档索引已加载，共 {len(self.doc_index)} 个文档")

    # ==================== 上下文查询 ====================

    def get_context_around_chunk(
        self,
        source: str,
        chunk_start_index: int,
        context_chars: int = 500
    ) -> dict:
        """获取切片周围的上下文"""
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]
        full_content = doc_index.full_content

        start = max(0, chunk_start_index - context_chars)
        end = min(len(full_content), chunk_start_index + context_chars)

        return {
            "source": source,
            "before": full_content[start:chunk_start_index].strip(),
            "current": full_content[chunk_start_index:min(len(full_content), chunk_start_index + context_chars)],
            "after": full_content[chunk_start_index + context_chars:end].strip(),
            "context_range": f"{start}-{end}"
        }

    def get_full_document(self, source: str) -> dict:
        """获取完整文档内容"""
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

    def get_chapter_by_header(self, source: str, header_pattern: str) -> dict:
        """根据标题模式获取章节内容"""
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]
        full_content = doc_index.full_content
        lines = full_content.split('\n')

        # 查找标题位置
        chapter_start = None
        chapter_end = None

        for i, line in enumerate(lines):
            if header_pattern.lower() in line.lower():
                chapter_start = i

                # 查找章节结束
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('#') and j > i + 1:
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
        sources: list[str] | None = None,
        context_chars: int = 300
    ) -> list[dict]:
        """跨文档搜索并返回上下文"""
        self._ensure_loaded()

        results = []
        search_docs = sources or list(self.doc_index.keys())

        for source in search_docs:
            if source not in self.doc_index:
                continue

            doc_index = self.doc_index[source]
            full_content = doc_index.full_content

            # 查找所有匹配位置
            pos = 0
            query_lower = query.lower()

            while True:
                pos = full_content.lower().find(query_lower, pos)
                if pos == -1:
                    break

                start = max(0, pos - context_chars)
                end = min(len(full_content), pos + len(query) + context_chars)

                results.append({
                    "source": source,
                    "match_position": pos,
                    "context": full_content[start:end],
                    "snippet": full_content[pos:pos + len(query)]
                })

                pos += len(query)

        return results

    # ==================== 摘要查询方法 ====================

    def get_executive_summary(self, source: str) -> dict:
        """获取文档的执行摘要"""
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
        """列出文档的所有章节摘要"""
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

        chapters = [
            {
                "title": chapter.get("title"),
                "level": chapter.get("level"),
                "summary": chapter.get("summary"),
                "key_points": chapter.get("key_points", [])
            }
            for chapter in doc_index.chapter_summaries
        ]

        return {
            "source": source,
            "total_chapters": len(chapters),
            "chapters": chapters
        }

    def get_chapter_summary(self, source: str, chapter_pattern: str) -> dict:
        """获取特定章节的摘要"""
        self._ensure_loaded()

        if source not in self.doc_index:
            return {"error": f"未找到文档: {source}"}

        doc_index = self.doc_index[source]

        if not doc_index.chapter_summaries:
            return {"error": "该文档尚未生成章节摘要，请先运行知识库构建流程"}

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

    def search_key_points(self, query: str, sources: list[str] | None = None) -> dict:
        """在关键要点中搜索关键词"""
        self._ensure_loaded()

        results = []
        search_docs = sources or list(self.doc_index.keys())

        for source in search_docs:
            if source not in self.doc_index:
                continue

            doc_index = self.doc_index[source]

            if not doc_index.key_points:
                continue

            # 在该文档的要点中搜索
            for point in doc_index.key_points:
                if query.lower() in point.lower():
                    results.append({"source": source, "point": point})

        return {
            "query": query,
            "total_matches": len(results),
            "matches": results
        }


# ==================== 全局单例 ====================

_context_manager = None


def get_context_manager() -> DocumentContextManager:
    """获取全局上下文管理器实例"""
    global _context_manager

    if _context_manager is None:
        _context_manager = DocumentContextManager()
        if _context_manager.index_path.exists():
            _context_manager.load()

    return _context_manager


if __name__ == "__main__":
    print("测试 DocumentContextManager")
    cm = DocumentContextManager()

    try:
        cm.load()
        print(f"\n索引中的文档: {list(cm.doc_index.keys())}")

        if cm.doc_index:
            first_source = list(cm.doc_index.keys())[0]
            print(f"\n获取完整文档: {first_source}")
            doc = cm.get_full_document(first_source)
            print(f"文档类型: {doc['doc_type']}")
            print(f"总切片数: {doc['total_chunks']}")
            print(f"内容长度: {len(doc['content'])} 字符")

    except FileNotFoundError as e:
        print(f"索引文件不存在: {e}")
