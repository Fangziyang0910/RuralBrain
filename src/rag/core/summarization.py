"""
层次化摘要系统
为决策智能体提供多级摘要视图，实现从宏观到微观的渐进式文档理解

核心功能：
- 执行摘要（Executive Summary）- 200字
- 章节摘要（Chapter Summaries）- 每章300字
- 关键要点提取（Key Points）- 10-15条
"""
import re
from dataclasses import dataclass
from typing import Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.model_manager import ModelManager
from src.rag.config import DEFAULT_PROVIDER


# ==================== 数据结构 ====================

@dataclass
class ChapterSummary:
    """章节摘要数据结构"""
    title: str
    level: int
    summary: str
    key_points: list[str]
    start_index: int
    end_index: int


@dataclass
class DocumentSummary:
    """文档摘要数据结构"""
    source: str
    executive_summary: str
    chapter_summaries: list[ChapterSummary]
    key_points: list[str]


# ==================== 提示词模板 ====================

EXECUTIVE_SUMMARY_SYSTEM = """你是一个专业的文档摘要专家，擅长提炼乡村规划、政策文件的核心内容。

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
- 如果文档是PPT或非正式文档，重点关注其核心信息和数据"""


CHAPTER_SUMMARY_SYSTEM = """你是一个专业的文档分析专家，擅长提取章节的核心信息。

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
- 如果章节很短（少于100字），可以适当缩短摘要"""


KEY_POINTS_SYSTEM = """你是一个专业的信息提取专家，擅长从复杂文档中提取关键要点。

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
- 使用项目符号列表"""


# ==================== 文档摘要生成器 ====================

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
        temperature: float = 0.3,
    ):
        self.model_manager = ModelManager(provider=provider)
        self.llm = self.model_manager.get_chat_model(temperature=temperature)
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.executive_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", EXECUTIVE_SUMMARY_SYSTEM),
            ("human", "请为以下文档生成执行摘要：\n\n{content}")
        ])

        self.chapter_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", CHAPTER_SUMMARY_SYSTEM),
            ("human", "请为以下章节生成摘要：\n\n章节标题：{title}\n\n章节内容：\n{content}")
        ])

        self.key_points_prompt = ChatPromptTemplate.from_messages([
            ("system", KEY_POINTS_SYSTEM),
            ("human", "请从以下文档中提取关键要点：\n\n{content}")
        ])

    def _split_by_headers(self, content: str) -> list[dict[str, Any]]:
        """根据标题分割文档"""
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
                if current_chapter["content"]:
                    end_index = sum(len(l) + 1 for l in lines[:i])
                    current_chapter["end_index"] = end_index
                    current_chapter["content"] = "\n".join(current_chapter["content"])
                    chapters.append(current_chapter.copy())

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

        if current_chapter["content"]:
            current_chapter["end_index"] = len(content)
            current_chapter["content"] = "\n".join(current_chapter["content"])
            chapters.append(current_chapter)

        return chapters

    def _split_by_paragraphs(self, content: str) -> list[dict[str, Any]]:
        """按段落分割文档"""
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

        if current_para["content"]:
            current_para["end_index"] = len(content)
            current_para["content"] = "\n".join(current_para["content"])
            paragraphs.append(current_para)

        return paragraphs

    def _clean_markdown(self, text: str) -> str:
        """清理多余的markdown格式"""
        text = re.sub(r'^#+\s*', '', text)
        text = re.sub(r'\n#+\s*', '\n', text)
        return text

    def _extract_bullet_points(self, text: str) -> list[str]:
        """从文本中提取项目符号列表"""
        points = []
        lines = text.split('\n')

        for line in lines:
            stripped = line.strip()

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

        return points

    def _extract_simple_points(self, text: str, max_points: int = 15) -> list[str]:
        """从文本中简单提取要点"""
        points = []
        sentences = re.split(r'[。；；\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if 10 < len(sentence) < 100:
                points.append(sentence)
                if len(points) >= max_points:
                    break

        return points

    def generate_executive_summary(self, document: Document) -> str:
        """生成执行摘要（200字）"""
        content = document.page_content

        if len(content) > 5000:
            content = content[:5000] + "\n...(文档过长，已截断)"

        try:
            chain = self.executive_summary_prompt | self.llm
            result = chain.invoke({"content": content})
            summary = self._clean_markdown(result.content.strip())
            return summary

        except Exception as e:
            return f"⚠️ 执行摘要生成失败: {str(e)}"

    def generate_chapter_summaries(
        self,
        document: Document,
        max_chapters: int = 20
    ) -> list[ChapterSummary]:
        """生成章节摘要（每章300字）"""
        content = document.page_content

        chapters = self._split_by_headers(content)

        if len(chapters) <= 1:
            chapters = self._split_by_paragraphs(content)

        if len(chapters) > max_chapters:
            print(f"⚠️  文档章节数过多({len(chapters)})，仅处理前{max_chapters}个")
            chapters = chapters[:max_chapters]

        chapter_summaries = []

        for chapter in chapters:
            title = chapter["title"]
            chapter_content = chapter["content"]

            if len(chapter_content.strip()) < 50:
                continue

            try:
                chain = self.chapter_summary_prompt | self.llm
                result = chain.invoke({
                    "title": title,
                    "content": chapter_content[:3000]
                })

                summary_text = result.content.strip()

                # 提取关键要点
                key_points = self._extract_bullet_points(summary_text)

                # 如果没有提取到要点，使用简单分割
                if not key_points:
                    key_points = self._extract_simple_points(summary_text, 5)

                # 分离摘要和要点
                summary_lines = []
                for line in summary_text.split('\n'):
                    stripped = line.strip()
                    if not re.match(r'^[\*\-\•]\s+', stripped) and not re.match(r'^\d+\.\s+', stripped):
                        summary_lines.append(stripped)

                summary = "\n".join(summary_lines).strip()

                chapter_summaries.append(ChapterSummary(
                    title=title,
                    level=chapter["level"],
                    summary=summary,
                    key_points=key_points[:5],
                    start_index=chapter["start_index"],
                    end_index=chapter["end_index"]
                ))

            except Exception as e:
                print(f"⚠️  章节 '{title}' 摘要生成失败: {str(e)}")
                chapter_summaries.append(ChapterSummary(
                    title=title,
                    level=chapter["level"],
                    summary=f"（摘要生成失败: {str(e)}）",
                    key_points=[],
                    start_index=chapter["start_index"],
                    end_index=chapter["end_index"]
                ))

        return chapter_summaries

    def generate_key_points(self, document: Document) -> list[str]:
        """提取关键要点（10-15条）"""
        content = document.page_content

        if len(content) > 8000:
            content = content[:8000] + "\n...(文档过长，已截断)"

        try:
            chain = self.key_points_prompt | self.llm
            result = chain.invoke({"content": content})
            points_text = result.content.strip()

            points = self._extract_bullet_points(points_text)

            return points[:15]

        except Exception as e:
            print(f"⚠️  关键要点提取失败: {str(e)}")
            return self._extract_simple_points(content, 15)

    def generate_summary(self, document: Document) -> DocumentSummary:
        """生成完整的文档摘要（包含所有层次）"""
        source = document.metadata.get("source", "unknown")

        print(f"📝 正在生成文档摘要: {source}")
        print(f"   文档长度: {len(document.page_content)} 字符")

        print("   1/3 生成执行摘要...")
        executive_summary = self.generate_executive_summary(document)

        print("   2/3 生成章节摘要...")
        chapter_summaries = self.generate_chapter_summaries(document)

        print("   3/3 提取关键要点...")
        key_points = self.generate_key_points(document)

        print(f"✅ 摘要生成完成: {len(chapter_summaries)} 个章节, {len(key_points)} 个要点")

        return DocumentSummary(
            source=source,
            executive_summary=executive_summary,
            chapter_summaries=chapter_summaries,
            key_points=key_points
        )

    def summarize_batch(self, documents: list[Document]) -> list[DocumentSummary]:
        """批量生成摘要"""
        summaries = []

        for doc in documents:
            try:
                summary = self.generate_summary(doc)
                summaries.append(summary)
            except Exception as e:
                print(f"❌ 文档 {doc.metadata.get('source', 'unknown')} 摘要生成失败: {str(e)}")

        return summaries


# ==================== 便捷函数 ====================

def summarize_document(
    document: Document,
    provider: str = DEFAULT_PROVIDER
) -> DocumentSummary:
    """为单个文档生成摘要的便捷函数"""
    summarizer = DocumentSummarizer(provider=provider)
    return summarizer.generate_summary(document)


if __name__ == "__main__":
    from langchain_core.documents import Document

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
