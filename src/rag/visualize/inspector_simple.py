"""
切片可视化工具（简化版 - 不使用 Rich 库）
避免终端乱码问题
"""
import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document


class SimpleSliceInspector:
    """
    切片检查器（简化版）
    使用纯文本输出，避免终端乱码
    """

    def __init__(self, documents: List[Document]):
        self.documents = documents
        self.stats = self._calculate_stats()

    def _calculate_stats(self) -> dict:
        """计算切片统计信息"""
        total_chunks = len(self.documents)
        total_chars = sum(len(doc.page_content) for doc in self.documents)
        avg_chars = total_chars / total_chunks if total_chunks > 0 else 0

        # 统计元数据
        sources = {}
        types = {}
        for doc in self.documents:
            source = doc.metadata.get("source", "unknown")
            doc_type = doc.metadata.get("type", "unknown")
            sources[source] = sources.get(source, 0) + 1
            types[doc_type] = types.get(doc_type, 0) + 1

        return {
            "total_chunks": total_chunks,
            "total_chars": total_chars,
            "avg_chars": avg_chars,
            "sources": sources,
            "types": types,
        }

    def print_summary(self) -> None:
        """打印统计摘要（纯文本）"""
        print("\n" + "="*60)
        print("切片统计摘要")
        print("="*60 + "\n")

        print(f"总切片数: {self.stats['total_chunks']:,}")
        print(f"总字符数: {self.stats['total_chars']:,}")
        print(f"平均字符数: {self.stats['avg_chars']:.0f}\n")

        if self.stats['sources']:
            print("按文档来源分布:")
            for source, count in sorted(
                self.stats['sources'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  - {source}: {count} 个切片")
            print()

    def print_slice_details(
        self,
        start_idx: int = 0,
        end_idx: int = None,
        show_content: bool = True,
    ) -> None:
        """打印切片详细信息（纯文本）"""
        if end_idx is None:
            end_idx = min(start_idx + 5, len(self.documents))

        print("\n" + "="*60)
        print(f"切片详情 (索引 {start_idx}-{end_idx-1})")
        print("="*60 + "\n")

        for idx in range(start_idx, min(end_idx, len(self.documents))):
            doc = self.documents[idx]

            print(f"--- 切片 #{idx} ---")
            print("元数据:")
            for key, value in doc.metadata.items():
                print(f"  {key}: {value}")

            content = doc.page_content
            print(f"字符数: {len(content)}")

            if show_content:
                # 截断过长的内容
                preview = content if len(content) <= 500 else content[:500] + "..."
                print(f"内容:\n{preview}\n")

    def find_potential_issues(self) -> List[dict]:
        """查找潜在的切片问题"""
        issues = []

        for idx, doc in enumerate(self.documents):
            content = doc.page_content

            # 检查 1: 空切片或过短切片
            if len(content.strip()) < 50:
                issues.append({
                    "type": "过短切片",
                    "index": idx,
                    "description": f"切片内容过短（{len(content)} 字符），可能是垃圾信息",
                    "content": content,
                })

            # 检查 2: 重复内容
            words = content.split()
            if len(words) > 10:
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.3:
                    issues.append({
                        "type": "重复内容",
                        "index": idx,
                        "description": f"内容重复率过高（唯一率: {unique_ratio:.1%}）",
                        "content": content,
                    })

            # 检查 3: 特殊字符过多
            special_char_ratio = sum(
                1 for c in content if not c.isalnum() and not c.isspace()
            ) / max(len(content), 1)
            if special_char_ratio > 0.3:
                issues.append({
                    "type": "特殊字符过多",
                    "index": idx,
                    "description": f"特殊字符比例过高（{special_char_ratio:.1%}）",
                    "content": content,
                })

        return issues

    def print_issues(self, max_issues: int = 20) -> None:
        """打印发现的问题（纯文本）"""
        issues = self.find_potential_issues()

        if not issues:
            print("\n未发现明显问题！\n")
            return

        print(f"\n发现 {len(issues)} 个潜在问题（显示前 {min(max_issues, len(issues))} 个）:\n")

        for issue in issues[:max_issues]:
            print(f"[问题 #{issue['index']}] {issue['type']}")
            print(f"  描述: {issue['description']}")
            print(f"  内容: {issue['content'][:100]}...\n")

    def export_to_json(self, output_path: str | Path) -> None:
        """导出切片数据到 JSON 文件"""
        output_path = Path(output_path)

        export_data = {
            "statistics": self.stats,
            "slices": [
                {
                    "index": idx,
                    "metadata": doc.metadata,
                    "content": doc.page_content,
                    "char_count": len(doc.page_content),
                }
                for idx, doc in enumerate(self.documents)
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"\n切片数据已导出到: {output_path}\n")


def inspect_documents(documents: List[Document]) -> SimpleSliceInspector:
    """便捷函数：创建并返回切片检查器"""
    inspector = SimpleSliceInspector(documents)
    return inspector
