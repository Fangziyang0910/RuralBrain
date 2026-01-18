"""
切片可视化工具
用于检查知识文件被切片后的具体内容，发现冗余和垃圾信息
"""
import json
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint

# 初始化 Rich Console
console = Console()


class SliceInspector:
    """
    切片检查器
    可视化展示文档切片后的内容和统计信息
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
        """打印统计摘要"""
        console.print("\n[bold cyan]📊 切片统计摘要[/bold cyan]\n")

        # 基本统计表格
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("指标", style="cyan")
        table.add_column("数值", justify="right")
        table.add_column("说明", style="dim")

        table.add_row(
            "总切片数",
            f"{self.stats['total_chunks']:,}",
            "文档被切分成的片段总数"
        )
        table.add_row(
            "总字符数",
            f"{self.stats['total_chars']:,}",
            "所有切片的字符总数"
        )
        table.add_row(
            "平均字符数",
            f"{self.stats['avg_chars']:.0f}",
            "每个切片的平均字符数"
        )

        console.print(table)

        # 按来源分布
        if self.stats['sources']:
            console.print("\n[bold yellow]📁 按文档来源分布:[/bold yellow]")
            for source, count in sorted(
                self.stats['sources'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                console.print(f"  • {source}: {count} 个切片")

        # 按类型分布
        if self.stats['types']:
            console.print("\n[bold green]📋 按文档类型分布:[/bold green]")
            for doc_type, count in sorted(
                self.stats['types'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                console.print(f"  • {doc_type}: {count} 个切片")

    def print_slice_details(
        self,
        start_idx: int = 0,
        end_idx: Optional[int] = None,
        show_content: bool = True,
    ) -> None:
        """
        打印切片详细信息

        Args:
            start_idx: 起始索引（从 0 开始）
            end_idx: 结束索引（不包含），None 表示到最后
            show_content: 是否显示切片内容
        """
        if end_idx is None:
            end_idx = min(start_idx + 5, len(self.documents))

        console.print(
            f"\n[bold cyan]📄 切片详情 (索引 {start_idx}-{end_idx-1})[/bold cyan]\n"
        )

        for idx in range(start_idx, min(end_idx, len(self.documents))):
            doc = self.documents[idx]

            # 显示元数据
            console.print(f"[bold yellow]切片 #{idx}[/bold yellow]")

            # 元数据表格
            meta_table = Table(show_header=False, box=None, padding=0)
            meta_table.add_column("Key", style="cyan")
            meta_table.add_column("Value", style="green")

            for key, value in doc.metadata.items():
                meta_table.add_row(f"  {key}:", str(value))

            console.print(meta_table)

            # 显示字符数统计
            content = doc.page_content
            char_count = len(content)
            console.print(f"  [dim]字符数: {char_count}[/dim]")

            # 显示内容
            if show_content:
                # 截断过长的内容
                preview = content if len(content) <= 500 else content[:500] + "..."
                console.print(Panel(
                    preview,
                    title="[bold]内容预览[/bold]",
                    border_style="blue",
                    expand=False,
                ))

            console.print()  # 空行分隔

    def find_potential_issues(self) -> List[dict]:
        """
        查找潜在的切片问题

        Returns:
            问题列表，每个问题包含类型、索引和描述
        """
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

            # 检查 2: 重复内容（简单判断）
            # 如果切片内容重复出现的词组比例过高
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
            special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / max(len(content), 1)
            if special_char_ratio > 0.3:
                issues.append({
                    "type": "特殊字符过多",
                    "index": idx,
                    "description": f"特殊字符比例过高（{special_char_ratio:.1%}），可能包含格式信息",
                    "content": content,
                })

            # 检查 4: 可能的页眉页脚
            footer_patterns = ["第", "页", "Page", "保密", "机密"]
            if any(pattern in content for pattern in footer_patterns) and len(content) < 100:
                issues.append({
                    "type": "可能的页眉页脚",
                    "index": idx,
                    "description": "可能是页眉页脚或模板占位符",
                    "content": content,
                })

        return issues

    def print_issues(self, max_issues: int = 20) -> None:
        """
        打印发现的问题

        Args:
            max_issues: 最多显示的问题数量
        """
        issues = self.find_potential_issues()

        if not issues:
            console.print("\n✅ [bold green]未发现明显问题！[/bold green]\n")
            return

        console.print(
            f"\n⚠️  [bold yellow]发现 {len(issues)} 个潜在问题"
            f"（显示前 {min(max_issues, len(issues))} 个）:[/bold yellow]\n"
        )

        for issue in issues[:max_issues]:
            console.print(f"[bold red]问题 #{issue['index']}[/bold red]: {issue['type']}")
            console.print(f"  [dim]{issue['description']}[/dim]")
            console.print(f"  [cyan]内容:[/cyan] {issue['content'][:100]}...")
            console.print()

    def export_to_json(self, output_path: str | Path) -> None:
        """
        导出切片数据到 JSON 文件

        Args:
            output_path: 输出文件路径
        """
        output_path = Path(output_path)

        # 准备数据
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

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        console.print(
            f"\n✅ [bold green]切片数据已导出到: {output_path}[/bold green]\n"
        )


def inspect_documents(documents: List[Document]) -> SliceInspector:
    """
    便捷函数：创建并返回切片检查器

    Args:
        documents: 文档列表

    Returns:
        SliceInspector 实例
    """
    inspector = SliceInspector(documents)
    return inspector
