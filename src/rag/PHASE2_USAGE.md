# RAG 阶段2：层次化摘要系统 - 使用指南

## 概述

阶段2为 RAG 知识库系统添加了层次化摘要功能，提供多级摘要视图，实现从宏观到微观的渐进式文档理解。

## 核心功能

### 1. 执行摘要（Executive Summary）
- **长度**：200字左右
- **用途**：快速了解文档核心内容
- **包含**：目标、定位、关键指标、重点措施

### 2. 章节摘要（Chapter Summaries）
- **长度**：每章300字左右
- **用途**：结构化理解文档内容
- **包含**：章节主题、主要内容、关键要点

### 3. 关键要点（Key Points）
- **数量**：10-15条
- **用途**：精炼信息提取
- **类型**：发展目标、重要措施、关键项目、重要指标、时间节点

## 使用方式

### 方式1：通过 Python API

```python
from src.rag.context_manager import get_context_manager

# 获取上下文管理器
cm = get_context_manager()

# 1. 获取执行摘要
result = cm.get_executive_summary("plan.docx")
print(result["executive_summary"])

# 2. 列出所有章节摘要
result = cm.list_chapter_summaries("plan.docx")
for chapter in result["chapters"]:
    print(f"{chapter['title']}: {chapter['summary']}")

# 3. 获取特定章节摘要
result = cm.get_chapter_summary("plan.docx", "产业发展")
print(result["summary"])
print(result["key_points"])

# 4. 搜索关键要点
result = cm.search_key_points("旅游")
for match in result["matches"]:
    print(f"{match['source']}: {match['point']}")
```

### 方式2：通过 LangChain Tools

```python
from src.rag.tool import (
    executive_summary_tool,
    chapter_summaries_list_tool,
    chapter_summary_tool,
    key_points_search_tool
)

# 在 Agent 中使用
# 1. 获取执行摘要
result = executive_summary_tool.run("plan.docx")

# 2. 列出章节摘要
result = chapter_summaries_list_tool.run("plan.docx")

# 3. 获取特定章节摘要
result = chapter_summary_tool.run({
    "source": "plan.docx",
    "chapter_pattern": "产业发展"
})

# 4. 搜索关键要点
result = key_points_search_tool.run({"query": "旅游"})
```

### 方式3：集成到 Planning Agent

```python
from src.rag.tool import (
    planning_knowledge_tool,
    executive_summary_tool,
    chapter_summaries_list_tool,
    full_document_tool
)

# 将新工具添加到 Agent
tools = [
    planning_knowledge_tool,        # 基础检索
    executive_summary_tool,          # 执行摘要（阶段2）
    chapter_summaries_list_tool,     # 章节摘要列表（阶段2）
    full_document_tool,              # 完整文档（深度阅读）
]

# Agent 工作流
# 1. 快速模式：执行摘要 → 章节列表 → 选择性深入
# 2. 深度模式：执行摘要 → 关键章节 → 完整文档
```

## 构建/更新知识库

### 首次构建

```bash
python src/rag/build.py
```

构建过程中会询问是否生成摘要：
- 选择 `y`（推荐）：为所有文档生成摘要（需要几分钟）
- 选择 `n`：跳过摘要生成，可稍后重新构建

### 重新生成摘要

如果之前跳过了摘要生成，需要重新运行：

```bash
python src/rag/build.py
```

选择生成摘要，系统会为所有文档生成摘要并更新索引。

## 测试

运行测试脚本验证功能：

```bash
python src/rag/test_summarization.py
```

测试包括：
1. 基本摘要生成功能
2. 文档上下文管理器集成
3. 工具函数测试
4. 真实文档测试（可选）

## 数据结构

### DocumentIndex（扩展）

```python
@dataclass
class DocumentIndex:
    source: str                              # 文件名
    doc_type: str                            # 文档类型
    full_content: str                        # 完整内容
    metadata: dict                           # 原始元数据
    chunks_info: List[dict]                  # 切片信息

    # 阶段2新增
    executive_summary: Optional[str]         # 执行摘要（200字）
    chapter_summaries: Optional[List[dict]]  # 章节摘要列表
    key_points: Optional[List[str]]          # 全文关键要点
```

### 章节摘要结构

```python
@dataclass
class ChapterSummary:
    title: str                # 章节标题
    level: int                # 标题级别（1=#, 2=##, 3=###）
    summary: str              # 章节摘要（300字）
    key_points: List[str]     # 关键要点列表
    start_index: int          # 起始位置
    end_index: int            # 结束位置
```

## 优势

### 效率提升
- Agent 可快速筛选文档，不需要全文阅读
- Token 节省：摘要比原文小 10-50 倍

### 结构清晰
- 保持原文档的章节层级
- 渐进式理解：从宏观到微观

### 灵活性
- 支持快速浏览和深度阅读两种模式
- 可按需深入细节

## 注意事项

### LLM API 调用
- 摘要生成需要调用 LLM API（DeepSeek 或 GLM）
- 生成时间取决于文档数量和长度
- 请确保已设置相应的 API 密钥

### 兼容性
- 系统向后兼容，没有摘要的文档仍可正常使用
- 旧格式索引会自动升级

### 性能建议
- 对于大量文档，建议分批生成摘要
- 可以先跳过摘要生成，稍后按需生成

## 文件结构

```
src/rag/
├── summarization.py         # 摘要生成模块（阶段2新增）
├── context_manager.py       # 文档上下文管理器（已扩展）
├── tool.py                  # Agent 工具（已扩展）
├── build.py                 # 知识库构建脚本（已扩展）
├── test_summarization.py    # 摘要功能测试（阶段2新增）
├── PHASE2_USAGE.md          # 本文档
└── ROADMAP_PHASE2_PHASE3.md # 路线图
```

## 下一步

### 阶段3：结构化数据提取
- 从非结构化文档中提取结构化数据
- 支持精确查询、对比分析、指标计算
- 预计开发时间：4-5天

## 常见问题

**Q: 如何查看文档是否有摘要？**
```python
cm = get_context_manager()
doc = cm.doc_index["文件名"]
print(doc.executive_summary)  # None 表示未生成
```

**Q: 可以为单个文档生成摘要吗？**
```python
from src.rag.summarization import summarize_document
from langchain_core.documents import Document

doc = Document(page_content="...", metadata={"source": "test.docx"})
summary = summarize_document(doc)
```

**Q: 摘要生成失败怎么办？**
- 检查 API 密钥是否正确设置
- 查看错误日志，可能是网络或 API 问题
- 文档可以正常使用，只是没有摘要

**Q: 如何更新已有摘要？**
- 重新运行 `build.py` 并选择生成摘要
- 会覆盖已有的摘要数据
