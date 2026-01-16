# RAG 知识库增强路线图（阶段2-3）

> 本文档记录决策智能体知识库的后续增强方向
> 创建时间：2026-01-15
> 状态：待规划

---

## 当前状态：阶段1已完成 ✅

**阶段1：全文上下文查询**
- ✅ DocumentContextManager 文档上下文管理器
- ✅ 增强的 Agent 工具集（4个新工具）
- ✅ 检索时自动返回前后上下文
- ✅ get_full_document - 获取完整文档
- ✅ get_chapter_by_header - 章节级查询
- ✅ 更新的 Planning Agent（决策导向）

---

## 阶段2：层次化摘要系统

### 目标
为决策智能体提供**多级摘要视图**，快速理解文档结构，按需深入细节。

### 核心思路

```
文档结构
├── 执行摘要（Executive Summary）- 200字
│   └── 快速了解文档核心内容
├── 章节摘要（Chapter Summaries）- 每章300字
│   ├── 第一章：背景与目标
│   ├── 第二章：空间布局
│   └── ...
└── 完整文档（Full Document）
    └── 深度阅读时使用
```

### 实现方案

#### 1. 摘要生成模块 `src/rag/summarization.py`

```python
class DocumentSummarizer:
    """文档摘要生成器"""

    def generate_executive_summary(self, document: Document) -> str:
        """生成执行摘要（200字）"""
        # 提取：目标、定位、关键指标
        pass

    def generate_chapter_summaries(self, document: Document) -> List[ChapterSummary]:
        """生成章节摘要（每章300字）"""
        # 按标题分割，逐章摘要
        pass

    def generate_key_points(self, document: Document) -> List[str]:
        """提取关键要点（10-15条）"""
        # 提取：目标、措施、项目、指标
        pass
```

#### 2. 摘要索引存储

在 `document_index.json` 中增加摘要字段：

```json
{
  "source": "plan.docx",
  "executive_summary": "本文档制定...",
  "chapter_summaries": [
    {
      "title": "第一章 总体目标",
      "summary": "...",
      "key_points": ["目标1", "目标2"]
    }
  ]
}
```

#### 3. 新增 Agent 工具

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `get_executive_summary` | 获取执行摘要 | 文档名 | 200字摘要 |
| `list_chapter_summaries` | 列出所有章节摘要 | 文档名 | 章节列表+摘要 |
| `get_chapter_summary` | 获取特定章节摘要 | 文档名+章节名 | 章节摘要+要点 |
| `search_key_points` | 搜索关键要点 | 关键词 | 匹配的要点列表 |

#### 4. Agent 工作流优化

```python
<workflow>
**快速模式**（需要快速了解文档）：
1. get_executive_summary → 了解核心内容
2. list_chapter_summaries → 浏览章节结构
3. 选择性深入：get_chapter_summary(感兴趣的章节)

**深度模式**（需要完整理解）：
1. get_executive_summary → 建立框架
2. get_chapter_summary(关键章节) → 理解重点
3. get_full_document → 验证细节
</workflow>
```

### 优势

- **效率提升**：Agent 可快速筛选文档，不需要全文阅读
- **Token 节省**：摘要比原文小 10-50 倍
- **结构清晰**：保持原文档的章节层级
- **渐进式理解**：从宏观到微观，按需深入

### 技术挑战

1. **摘要质量**：需要确保摘要包含关键信息
   - 解决方案：提取式 + 生成式混合
   - 使用关键词提取辅助

2. **章节分割**：PPT/TXT 可能没有明确标题
   - 解决方案：基于内容聚类、主题建模

3. **摘要一致性**：不同章节的摘要需要统一风格
   - 解决方案：结构化提示词

---

## 阶段3：结构化数据提取

### 目标
将非结构化文档转换为**结构化数据**，支持精确查询、对比分析、指标计算。

### 核心思路

```
原始文档 → 提取器 → 结构化数据（JSON）
                            ↓
                    可查询、可计算、可对比
```

### 提取的数据类型

#### 1. 发展目标（Development Goals）

```json
{
  "doc_id": "plan_001",
  "goals": [
    {
      "dimension": "经济发展",
      "target": "地区生产总值达到100亿",
      "baseline": "65.69亿",
      "target_year": 2030,
      "annual_growth": "7%"
    },
    {
      "dimension": "旅游发展",
      "target": "年接待游客100万人次",
      "baseline": "未知",
      "target_year": 2027,
      "annual_growth": "15%"
    }
  ]
}
```

#### 2. 重点项目（Key Projects）

```json
{
  "projects": [
    {
      "name": "罗浮山环线建设",
      "investment": "5亿元",
      "timeline": "2025-2027",
      "location": "罗浮山片区",
      "type": "基础设施",
      "status": "规划中"
    },
    {
      "name": "长宁高铁新城",
      "investment": "10亿元",
      "timeline": "2026-2030",
      "location": "长宁镇南部",
      "type": "平台建设",
      "status": "规划中"
    }
  ]
}
```

#### 3. 空间布局（Spatial Layout）

```json
{
  "spatial_structure": {
    "pattern": "一轴两带三片区",
    "zones": [
      {
        "name": "罗浮山生态保护区",
        "area": "120平方公里",
        "function": "生态保护、文化旅游",
        "constraints": ["严禁开发", "限制建设"]
      },
      {
        "name": "长宁镇中心区",
        "area": "50平方公里",
        "function": "综合服务、商业办公",
        "constraints": ["控制强度"]
      }
    ]
  }
}
```

#### 4. 产业体系（Industry System）

```json
{
  "industries": [
    {
      "category": "文化旅游",
      "sub_sectors": ["生态旅游", "文化旅游", "康养旅游"],
      "key_projects": ["罗浮山景区提升", "民宿集群"],
      "targets": [{"year": 2027, "value": "旅游收入20亿"}]
    },
    {
      "category": "现代农业",
      "sub_sectors": ["有机农业", "农产品加工"],
      "key_projects": ["现代农业产业园"],
      "targets": [{"year": 2030, "value": "农业产值10亿"}]
    }
  ]
}
```

### 实现方案

#### 1. 提取器模块 `src/rag/extractors.py`

```python
class StructuredDataExtractor:
    """结构化数据提取器"""

    def extract_goals(self, document: Document) -> List[Goal]:
        """提取发展目标"""
        # 使用正则 + LLM 提取
        pass

    def extract_projects(self, document: Document) -> List[Project]:
        """提取重点项目"""
        pass

    def extract_spatial_layout(self, document: Document) -> SpatialLayout:
        """提取空间布局"""
        pass

    def extract_industries(self, document: Document) -> List[Industry]:
        """提取产业体系"""
        pass
```

#### 2. Schema 定义 `src/rag/schemas.py`

```python
from pydantic import BaseModel
from typing import List, Optional

class Goal(BaseModel):
    dimension: str
    target: str
    baseline: Optional[str]
    target_year: int
    annual_growth: Optional[str]

class Project(BaseModel):
    name: str
    investment: str
    timeline: str
    location: str
    type: str
    status: str
```

#### 3. 查询工具

```python
# 新增 Agent 工具
query_goals_tool = Tool(
    name="query_development_goals",
    func=query_goals,
    description="查询发展目标，支持按维度、年份过滤"
)

query_projects_tool = Tool(
    name="query_key_projects",
    func=query_projects,
    description="查询重点项目，支持按类型、状态过滤"
)

compare_documents_tool = Tool(
    name="compare_documents",
    func=compare_documents,
    description="对比多个文档的目标、项目、指标"
)
```

#### 4. Agent 使用示例

```python
<example>
用户：长宁镇和石湾镇的旅游发展目标有什么区别？

Agent 工作流：
1. query_development_goals({"dimension": "旅游", "location": "长宁镇"})
2. query_development_goals({"dimension": "旅游", "location": "石湾镇"})
3. compare_documents([长宁镇目标, 石湾镇目标])
4. 输出对比表格+分析
</example>
```

### 优势

- **精确查询**：不再是模糊检索，而是精确过滤
- **对比分析**：可以横向对比不同文档
- **计算能力**：可以计算投资总额、项目数量等
- **可视化**：结构化数据易于可视化（表格、图表）

### 技术挑战

1. **提取准确性**：需要从非结构化文本中准确提取数据
   - 解决方案：
     - 使用 LLM + 人工校验
     - 设计结构化提示词
     - Pydantic Schema 强制类型约束

2. **数据一致性**：不同文档的表达方式不同
   - 解决方案：
     - 标准化 Schema
     - 数据清洗（单位统一、格式统一）

3. **更新维护**：文档更新后如何更新结构化数据
   - 解决方案：
     - 版本控制
     - 增量更新

---

## 优先级建议

### 推荐实施顺序

1. **阶段2：层次化摘要**（优先级：高）
   - 实现难度：中等
   - 价值：高（大幅提升 Agent 理解效率）
   - 时间估计：2-3天

2. **阶段3：结构化提取**（优先级：中）
   - 实现难度：高
   - 价值：高（支持精确查询和对比）
   - 时间估计：4-5天

### 为什么先做阶段2？

1. **快速见效**：摘要生成相对简单，效果立竿见影
2. **降低成本**：Agent 不需要频繁读取全文
3. **为阶段3铺垫**：摘要可以帮助理解结构，辅助结构化提取

---

## 其他可选方向（暂不考虑）

### 方案4：知识图谱（Knowledge Graph）

构建实体关系图谱，支持推理查询。

**优势**：可以发现隐含关联
**劣势**：构建复杂，维护成本高
**优先级**：低（当前需求可用关键词检索替代）

### 方案5：长上下文模型（Long Context）

直接使用 128k/200k token 的模型，不切分文档。

**优势**：保留完整上下文，无信息丢失
**劣势**：成本高，有 token 上限
**优先级**：低（当前文档量不大，传统 RAG 足够）

---

## 总结

| 阶段 | 核心功能 | 工具数量 | 实现难度 | 价值 |
|------|----------|----------|----------|------|
| 阶段1 ✅ | 全文上下文查询 | 4 | 低 | 中 |
| 阶段2 | 层次化摘要 | 4-5 | 中 | 高 |
| 阶段3 | 结构化提取 | 3-4 | 高 | 高 |

**当前建议**：先完成阶段2，验证效果后再决定是否做阶段3。

---

*文档结束*
