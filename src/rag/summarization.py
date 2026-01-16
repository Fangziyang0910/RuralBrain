"""
层次化摘要系统
为决策智能体提供多级摘要视图，实现从宏观到微观的渐进式文档理解

阶段2核心功能：
- 执行摘要（Executive Summary）- 200字
- 章节摘要（Chapter Summaries）- 每章300字
- 关键要点提取（Key Points）- 10-15条
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.model_manager import ModelManager
from src.config import DEFAULT_PROVIDER


@dataclass
class ChapterSummary:
    """章节摘要数据结构"""
    title: str  # 章节标题
    level: int  # 标题级别（1=#, 2=##, 3=###）
    summary: str  # 章节摘要（300字左右）
    key_points: List[str]  # 关键要点列表
    start_index: int  # 在原文档中的起始位置
    end_index: int  # 在原文档中的结束位置


@dataclass
class DocumentSummary:
    """文档摘要数据结构"""
    source: str  # 文档来源（文件名）
    executive_summary: str  # 执行摘要（200字）
    chapter_summaries: List[ChapterSummary]  # 章节摘要列表
    key_points: List[str]  # 全文关键要点（10-15条）


class DocumentSummarizer:
    """
    文档摘要生成器

    功能：
    1. 生成执行摘要（200字）- 快速了解文档核心
    2. 生成章节摘要（每章300字）- 结构化理解
    3. 提取关键要点（10-15条）- 精炼信息

    使用场景：
    - Agent 快速筛选文档
    - Token 节省（摘要比原文小 10-50 倍）
    - 渐进式理解（从宏观到微观）
    """

    def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        temperature: float = 0.3,  # 摘要生成使用较低温度
    ):
        """
        初始化摘要生成器

        Args:
            provider: 模型供应商（deepseek 或 glm）
            temperature: 温度参数，控制摘要的创造性
        """
        self.model_manager = ModelManager(provider=provider)
        self.llm = self.model_manager.get_chat_model(temperature=temperature)

        # 提示词模板
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""

        # 执行摘要提示词
        self.executive_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档摘要专家，擅长提炼乡村规划、政策文件的核心内容。

你的任务是从文档中提取最关键的信息，生成一份200字左右的执行摘要。

摘要必须包含以下要素：
1. 核心目标：文档要解决什么问题？达到什么目标？
2. 定位方向：主要的发展定位或战略方向
3. 关键指标：重要的量化指标（如有）
4. 重点措施：主要的实施措施或项目

要求：
- 简洁精炼，控制在200字左右
- 突出重点，不要面面俱到
- 使用专业但易懂的语言
- 保持客观，不要添加个人解读
- 如果文档是PPT或非正式文档，重点关注其核心信息和数据"""),
            ("human", "请为以下文档生成执行摘要：\n\n{content}")
        ])

        # 章节摘要提示词
        self.chapter_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档分析专家，擅长提取章节的核心信息。

你的任务是为文档的每个章节生成300字左右的摘要。

摘要结构：
1. **章节主题**（1句话概括本章核心内容）
2. **主要内容**（详细阐述本章讨论的主要问题、方案或措施）
3. **关键要点**（提取3-5条要点，使用项目符号列表）

要求：
- 摘要长度控制在300字左右
- 保持原文的逻辑结构
- 突出数据、指标、措施等具体信息
- 使用项目符号列表呈现关键要点
- 如果章节很短（少于100字），可以适当缩短摘要"""),
            ("human", "请为以下章节生成摘要：\n\n章节标题：{title}\n\n章节内容：\n{content}")
        ])

        # 关键要点提取提示词
        self.key_points_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的信息提取专家，擅长从复杂文档中提取关键要点。

你的任务是从文档中提取10-15条最关键的要点。

要点类型：
1. **发展目标**：具体的、可量化的目标
2. **重要措施**：主要的行动方案或策略
3. **关键项目**：重点建设工程或项目
4. **重要指标**：量化的绩效指标
5. **时间节点**：重要的时间安排

要求：
- 提取10-15条要点
- 每条要点使用简洁的陈述句
- 按重要性排序
- 尽可能包含具体数据和指标
- 使用项目符号列表"""),
            ("human", "请从以下文档中提取关键要点：\n\n{content}")
        ])

    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        根据标题分割文档

        Args:
            content: 文档内容

        Returns:
            章节列表，每个元素包含 {title, level, content, start_index, end_index}
        """
        chapters = []
        lines = content.split('\n')

        current_chapter = {
            "title": "文档开头",
            "level": 0,
            "content": [],
            "start_index": 0,
        }

        title_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        for i, line in enumerate(lines):
            match = title_pattern.match(line.strip())

            if match:
                # 保存上一个章节
                if current_chapter["content"]:
                    end_index = sum(len(l) + 1 for l in lines[:i])
                    current_chapter["end_index"] = end_index
                    current_chapter["content"] = "\n".join(current_chapter["content"])
                    chapters.append(current_chapter.copy())

                # 开始新章节
                level = len(match.group(1))
                title = match.group(2).strip()
                start_index = sum(len(l) + 1 for l in lines[:i+1])

                current_chapter = {
                    "title": title,
                    "level": level,
                    "content": [],
                    "start_index": start_index,
                }
            else:
                current_chapter["content"].append(line)

        # 保存最后一个章节
        if current_chapter["content"]:
            end_index = len(content)
            current_chapter["end_index"] = end_index
            current_chapter["content"] = "\n".join(current_chapter["content"])
            chapters.append(current_chapter)

        return chapters

    def _split_by_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        """
        按段落分割文档（用于没有明确标题的文档）

        Args:
            content: 文档内容

        Returns:
            段落列表
        """
        paragraphs = []
        lines = content.split('\n')

        current_para = {
            "title": f"段落 {len(paragraphs) + 1}",
            "level": 1,
            "content": [],
            "start_index": 0,
        }

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 空行表示段落结束
            if not stripped:
                if current_para["content"]:
                    end_index = sum(len(l) + 1 for l in lines[:i])
                    current_para["end_index"] = end_index
                    current_para["content"] = "\n".join(current_para["content"])
                    paragraphs.append(current_para.copy())

                    start_index = sum(len(l) + 1 for l in lines[:i+1])
                    current_para = {
                        "title": f"段落 {len(paragraphs) + 1}",
                        "level": 1,
                        "content": [],
                        "start_index": start_index,
                    }
            else:
                current_para["content"].append(line)

        # 保存最后一个段落
        if current_para["content"]:
            end_index = len(content)
            current_para["end_index"] = end_index
            current_para["content"] = "\n".join(current_para["content"])
            paragraphs.append(current_para)

        return paragraphs

    def generate_executive_summary(self, document: Document) -> str:
        """
        生成执行摘要（200字）

        Args:
            document: 文档对象

        Returns:
            执行摘要文本
        """
        content = document.page_content

        # 如果文档太长，截取前5000字（LLM上下文限制）
        if len(content) > 5000:
            content = content[:5000] + "\n...(文档过长，已截断)"

        try:
            chain = self.executive_summary_prompt | self.llm
            result = chain.invoke({"content": content})
            summary = result.content.strip()

            # 清理多余的markdown格式
            summary = re.sub(r'^#+\s*', '', summary)
            summary = re.sub(r'\n#+\s*', '\n', summary)

            return summary

        except Exception as e:
            return f"⚠️ 执行摘要生成失败: {str(e)}"

    def generate_chapter_summaries(
        self,
        document: Document,
        max_chapters: int = 20
    ) -> List[ChapterSummary]:
        """
        生成章节摘要（每章300字）

        Args:
            document: 文档对象
            max_chapters: 最多处理章节数（避免过长）

        Returns:
            章节摘要列表
        """
        content = document.page_content

        # 尝试按标题分割
        chapters = self._split_by_headers(content)

        # 如果没有找到标题，按段落分割
        if len(chapters) <= 1:
            chapters = self._split_by_paragraphs(content)

        # 限制章节数
        if len(chapters) > max_chapters:
            print(f"⚠️  文档章节数过多({len(chapters)})，仅处理前{max_chapters}个")
            chapters = chapters[:max_chapters]

        chapter_summaries = []

        for chapter in chapters:
            title = chapter["title"]
            chapter_content = chapter["content"]

            # 跳过太短的章节
            if len(chapter_content.strip()) < 50:
                continue

            try:
                chain = self.chapter_summary_prompt | self.llm
                result = chain.invoke({
                    "title": title,
                    "content": chapter_content[:3000]  # 限制长度
                })

                summary_text = result.content.strip()

                # 提取关键要点（查找项目符号列表）
                key_points = []
                lines = summary_text.split('\n')
                current_section = "summary"
                summary_lines = []

                for line in lines:
                    stripped = line.strip()

                    # 检测项目符号
                    if re.match(r'^[\*\-\•]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                        point = re.sub(r'^[\*\-\•]\s+|^\d+\.\s+', '', stripped).strip()
                        if point:
                            key_points.append(point)
                    else:
                        summary_lines.append(stripped)

                summary = "\n".join(summary_lines).strip()

                # 如果没有提取到要点，使用简单分割
                if not key_points:
                    key_points = self._extract_simple_points(summary_text)

                chapter_summaries.append(ChapterSummary(
                    title=title,
                    level=chapter["level"],
                    summary=summary,
                    key_points=key_points[:5],  # 每章最多5个要点
                    start_index=chapter["start_index"],
                    end_index=chapter["end_index"]
                ))

            except Exception as e:
                print(f"⚠️  章节 '{title}' 摘要生成失败: {str(e)}")
                # 添加失败回退
                chapter_summaries.append(ChapterSummary(
                    title=title,
                    level=chapter["level"],
                    summary=f"（摘要生成失败: {str(e)}）",
                    key_points=[],
                    start_index=chapter["start_index"],
                    end_index=chapter["end_index"]
                ))

        return chapter_summaries

    def _extract_simple_points(self, text: str) -> List[str]:
        """从文本中简单提取要点"""
        points = []

        # 按句号分割
        sentences = re.split(r'[。；；\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:
                points.append(sentence)
                if len(points) >= 5:
                    break

        return points

    def generate_key_points(self, document: Document) -> List[str]:
        """
        提取关键要点（10-15条）

        Args:
            document: 文档对象

        Returns:
            关键要点列表
        """
        content = document.page_content

        # 如果文档太长，截取前8000字
        if len(content) > 8000:
            content = content[:8000] + "\n...(文档过长，已截断)"

        try:
            chain = self.key_points_prompt | self.llm
            result = chain.invoke({"content": content})
            points_text = result.content.strip()

            # 提取项目符号列表
            points = []
            lines = points_text.split('\n')

            for line in lines:
                stripped = line.strip()

                # 匹配各种项目符号格式
                if re.match(r'^[\*\-\•]\s+', stripped):
                    point = re.sub(r'^[\*\-\•]\s+', '', stripped).strip()
                elif re.match(r'^\d+\.\s+', stripped):
                    point = re.sub(r'^\d+\.\s+', '', stripped).strip()
                elif stripped and not stripped.startswith('#'):
                    point = stripped
                else:
                    continue

                if point and len(point) > 5:
                    points.append(point)

            return points[:15]  # 最多15条

        except Exception as e:
            print(f"⚠️  关键要点提取失败: {str(e)}")
            # 回退到简单提取
            return self._extract_simple_points(content)[:15]

    def generate_summary(self, document: Document) -> DocumentSummary:
        """
        生成完整的文档摘要（包含所有层次）

        Args:
            document: 文档对象

        Returns:
            完整文档摘要
        """
        source = document.metadata.get("source", "unknown")

        print(f"📝 正在生成文档摘要: {source}")
        print(f"   文档长度: {len(document.page_content)} 字符")

        # 生成执行摘要
        print("   1/3 生成执行摘要...")
        executive_summary = self.generate_executive_summary(document)

        # 生成章节摘要
        print("   2/3 生成章节摘要...")
        chapter_summaries = self.generate_chapter_summaries(document)

        # 提取关键要点
        print("   3/3 提取关键要点...")
        key_points = self.generate_key_points(document)

        print(f"✅ 摘要生成完成: {len(chapter_summaries)} 个章节, {len(key_points)} 个要点")

        return DocumentSummary(
            source=source,
            executive_summary=executive_summary,
            chapter_summaries=chapter_summaries,
            key_points=key_points
        )

    def summarize_batch(self, documents: List[Document]) -> List[DocumentSummary]:
        """
        批量生成摘要

        Args:
            documents: 文档列表

        Returns:
            摘要列表
        """
        summaries = []

        for doc in documents:
            try:
                summary = self.generate_summary(doc)
                summaries.append(summary)
            except Exception as e:
                print(f"❌ 文档 {doc.metadata.get('source', 'unknown')} 摘要生成失败: {str(e)}")

        return summaries


# 便捷函数
def summarize_document(
    document: Document,
    provider: str = DEFAULT_PROVIDER
) -> DocumentSummary:
    """
    为单个文档生成摘要的便捷函数

    Args:
        document: 文档对象
        provider: 模型供应商

    Returns:
        文档摘要
    """
    summarizer = DocumentSummarizer(provider=provider)
    return summarizer.generate_summary(document)


if __name__ == "__main__":
    # 测试代码
    from langchain_core.documents import Document

    # 创建测试文档
    test_doc = Document(
        page_content="""
# 博罗县乡村发展规划

## 一、总体目标

到2030年，博罗县将建设成为粤港澳大湾区生态宜居示范区。

### 主要指标
- 地区生产总值达到100亿元
- 年接待游客500万人次
- 森林覆盖率达到70%

## 二、产业发展

重点发展文化旅游、现代农业、康养产业三大主导产业。

### 文化旅游
依托罗浮山文化资源，打造5A级旅游景区。
投资5亿元建设罗浮山环线。

### 现代农业
建设现代农业产业园，发展有机农业。
目标：农业产值达到20亿元。

## 三、空间布局

构建"一轴两带三片区"的空间发展格局。
""",
        metadata={"source": "test_plan.md", "type": "md"}
    )

    # 生成摘要
    summarizer = DocumentSummarizer()
    summary = summarizer.generate_summary(test_doc)

    print("\n" + "="*60)
    print("【执行摘要】")
    print(summary.executive_summary)
    print("\n" + "="*60)
    print("【章节摘要】")
    for chapter in summary.chapter_summaries:
        print(f"\n章节: {chapter.title}")
        print(f"摘要: {chapter.summary}")
        print(f"要点: {chapter.key_points}")
    print("\n" + "="*60)
    print("【关键要点】")
    for i, point in enumerate(summary.key_points, 1):
        print(f"{i}. {point}")
