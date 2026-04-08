# 联网搜索工具卡片可视化设计

> **设计日期**：2026-04-08
> **状态**：已批准，待实现

---

## 1. 背景与目标

### 1.1 问题陈述

当前联网搜索工具的可视化存在以下问题：

- **工具卡片内容空洞**：`tool_call` SSE 事件只传递工具名和状态，详细搜索结果通过 `content` 事件以纯文本流式输出
- **缺乏差异化特色**：用户无法直观看到搜索结果的结构化信息，体验与通用 AI 无异
- **信息展示不直观**：AI 摘要、来源类型、结果统计等关键信息无法在卡片中展示

### 1.2 设计目标

1. **增强可视化效果**：让联网搜索结果以结构化卡片形式展示，体现差异化特色
2. **提升用户体验**：用户可快速了解搜索结果的 AI 摘要、来源分布和关键内容
3. **保持简洁性**：卡片默认折叠，按需展开，不占用过多屏幕空间

---

## 2. 设计决策

### 2.1 用户选择记录

| 决策项 | 选项 | 理由 |
|--------|------|------|
| **卡片样式** | 摘要预览样式（方案 B） | AI 摘要 + 统计标签，平衡信息量与简洁度 |
| **展开内容** | 标题 + 链接 + 摘要片段 + 来源标签（标准版） | 用户无需跳转即可了解大致内容 |
| **结果数量** | 预览 3 条 + "查看全部"按钮 | 平衡信息量与简洁度 |
| **搜索参数** | 不展示 | 用户不关心技术参数，保持简洁 |
| **技术实现** | 后端返回结构化 JSON 数据 | 数据流清晰，改动集中 |

---

## 3. 架构设计

### 3.1 数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     数据流架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户请求 ──► Agent ──► web_search_tool                         │
│                              │                                  │
│                              ▼                                  │
│                    返回结构化 JSON 对象                          │
│                    {                                            │
│                      ai_summary: "...",                         │
│                      results: [{title, url, snippet, type}],    │
│                      stats: {total, news, web},                 │
│                      agent_text: "..."  # Agent 继续使用的文本   │
│                    }                                            │
│                              │                                  │
│                              ▼                                  │
│              SSE tool_call 事件携带 result_data                 │
│                              │                                  │
│                              ▼                                  │
│               前端 WebSearchCard 组件渲染                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 关键改动点

| 模块 | 改动内容 |
|------|---------|
| `web_search_tool.py` | 返回 JSON 对象，包含结构化数据和 Agent 文本 |
| `service/server.py` | SSE 事件增加 `result_data` 字段 |
| `WebSearchCard.tsx` | 新增联网搜索结果卡片组件 |
| `ChatMessageBubble.tsx` | 集成 WebSearchCard，按工具类型选择渲染器 |
| `tool-icons.ts` | 注册 web_search_tool 的卡片渲染器配置 |

---

## 4. 数据结构定义

### 4.1 后端返回结构

```python
{
    "ai_summary": str,        # Tavily API 返回的 answer 字段（AI 生成的摘要）
    "results": [              # 搜索结果列表
        {
            "title": str,     # 结果标题
            "url": str,       # 结果链接
            "snippet": str,   # 摘要片段（前 50 字）
            "type": str,      # 类型："news" 或 "web"
            "published_date": str | None  # 发布时间（可选）
        }
    ],
    "stats": {                # 统计信息
        "total": int,         # 总结果数
        "news": int,          # 新闻类型数量
        "web": int            # 网页类型数量
    },
    "agent_text": str         # Agent 继续使用的 Markdown 文本格式
}
```

### 4.2 前端接收结构

```typescript
interface WebSearchResult {
    title: string;
    url: string;
    snippet: string;
    type: 'news' | 'web';
    published_date?: string;
}

interface WebSearchData {
    ai_summary: string;
    results: WebSearchResult[];
    stats: {
        total: number;
        news: number;
        web: number;
    };
}

interface ToolCallEvent {
    type: 'tool_call';
    tool_name: string;
    status: '运行中' | '已完成';
    result_image?: string;
    result_data?: WebSearchData;  // 新增字段
}
```

---

## 5. 前端组件设计

### 5.1 WebSearchCard 组件结构

```
WebSearchCard
│
├── Header（折叠状态）
│   ├── 图标：🌐
│   ├── 标题：联网搜索
│   ├── 状态标签：✓ 已完成
│   └── 统计：找到 {stats.total} 条结果
│
├── AISummaryBox（AI 摘要区域）
│   └── 内容：💡 AI 摘要：{ai_summary}
│
├── StatsTags（统计标签）
│   ├── 新闻标签：📰 新闻 {stats.news}
│   └── 网页标签：📄 网页 {stats.web}
│
├── ExpandButton（展开按钮）
│   └── 文本：▼ 点击展开查看详细结果
│
└── ResultsList（展开后显示）
    ├── ResultItem（每条结果）
    │   ├── TypeBadge（来源标签）
    │   ├── TitleLink（标题链接）
    │   └── Snippet（摘要片段）
    │
    └── ViewAllButton（查看全部按钮，仅当 results.length > 3 时显示）
        └── 文本：查看全部 {results.length} 条结果
```

### 5.2 组件状态

| 状态 | 类型 | 说明 |
|------|------|------|
| `expanded` | `boolean` | 控制结果列表展开/折叠，默认 `false` |
| `showAll` | `boolean` | 控制显示全部结果，默认 `false`（只显示 3 条） |

### 5.3 样式设计

- **主题色**：紫色（`#7c3aed`），与现有联网搜索图标配色一致
- **背景**：渐变背景 `linear-gradient(135deg, #f3e8ff 0%, #fff 100%)`
- **来源标签**：
  - 新闻：黄色背景（`#fef3c7`），橙色文字（`#d97706`）
  - 网页：蓝色背景（`#dbeafe`），蓝色文字（`#2563eb`）
- **交互**：展开按钮点击后旋转图标（▼ → ▲），平滑展开结果列表

---

## 6. 后端改动设计

### 6.1 web_search_tool.py 改动

**当前实现**：
```python
@tool
def web_search_tool(query: str, ...) -> str:
    # 调用 Tavily API
    results = tavily_client.search(...)
    # 返回 Markdown 格式字符串
    return _format_results(results)
```

**改动后**：
```python
@tool
def web_search_tool(query: str, ...) -> str:
    # 调用 Tavily API
    response = tavily_client.search(...)
    results = response.get("results", [])
    answer = response.get("answer", "")

    # 构建结构化数据
    structured_data = {
        "ai_summary": answer,
        "results": _structure_results(results),
        "stats": _calculate_stats(results),
        "agent_text": _format_results(results)  # Agent 继续使用的文本
    }

    # 返回 JSON 字符串（Agent 可解析，前端可提取）
    return json.dumps(structured_data, ensure_ascii=False)

def _structure_results(results: list) -> list:
    """将 Tavily 结果转换为结构化格式"""
    return [
        {
            "title": r.get("title", "无标题"),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:50] + "...",
            "type": "news" if r.get("topic") == "news" else "web",
            "published_date": r.get("published_date")
        }
        for r in results
    ]

def _calculate_stats(results: list) -> dict:
    """计算结果统计"""
    news_count = sum(1 for r in results if r.get("topic") == "news")
    return {
        "total": len(results),
        "news": news_count,
        "web": len(results) - news_count
    }
```

### 6.2 SSE 事件改动

**当前实现**：
```python
tool_event = {
    "type": "tool_call",
    "tool_name": tool_name,
    "status": "已完成",
    "result_image": result_image,
}
```

**改动后**：
```python
# 解析工具输出
result_data = None
if tool_name == "web_search_tool":
    try:
        parsed_output = json.loads(tool_output)
        # 提取结构化数据给前端
        result_data = {
            "ai_summary": parsed_output.get("ai_summary"),
            "results": parsed_output.get("results"),
            "stats": parsed_output.get("stats")
        }
        # Agent 继续使用的文本（已在 parsed_output 中）
        # 后续 content 事件继续流式输出 agent_text
    except json.JSONDecodeError:
        pass  # 保持原有行为

tool_event = {
    "type": "tool_call",
    "tool_name": tool_name,
    "status": "已完成",
    "result_image": result_image,
    "result_data": result_data,  # 新增字段
}
```

---

## 7. 测试策略

### 7.1 单元测试

- **test_web_search_tool.py**：测试工具返回结构化 JSON 格式
  - 测试 `_structure_results()` 函数正确转换 Tavily 结果
  - 测试 `_calculate_stats()` 函数正确计算统计信息
  - 测试返回的 JSON 可被正确解析

### 7.2 集成测试

- **test_sse_events.py**：测试 SSE 事件包含 `result_data` 字段
  - 测试 `web_search_tool` 调用后 SSE 事件格式正确
  - 测试 `result_data` 字段包含完整的结构化数据

### 7.3 前端测试

- **WebSearchCard.test.tsx**：
  - 测试组件正确渲染 AI 摘要、统计标签
  - 测试展开/折叠交互逻辑
  - 测试结果列表正确显示标题、链接、摘要片段

### 7.4 手动验证

1. 启动开发环境：`docker-compose -f docker-compose.dev.yml up -d`
2. 发送联网搜索请求，观察工具卡片展示效果
3. 验证 AI 摘要、统计标签、来源标签正确显示
4. 测试展开/折叠交互流畅性
5. 验证标题链接可点击跳转

---

## 8. 文件改动清单

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `src/agents/tools/web_search_tool.py` | 修改 | 返回结构化 JSON 对象，保留 agent_text |
| `service/server.py` | 修改 | SSE 事件增加 `result_data` 字段解析 |
| `frontend/src/components/WebSearchCard.tsx` | 新增 | 联网搜索结果卡片组件 |
| `frontend/src/components/ChatMessageBubble.tsx` | 修改 | 集成 WebSearchCard，按工具类型选择渲染器 |
| `frontend/src/config/tool-icons.ts` | 修改 | 注册 web_search_tool 的卡片渲染配置 |
| `frontend/src/types/tool.ts` | 新增 | WebSearchData 类型定义 |
| `tests/unit/tools/test_web_search_tool.py` | 新增 | 工具结构化输出单元测试 |

---

## 9. 实现顺序建议

1. **后端改动**（优先）：修改 `web_search_tool.py` 返回结构化数据
2. **SSE 事件改动**：修改 `server.py` 传递 `result_data`
3. **前端类型定义**：添加 `WebSearchData` 类型
4. **组件开发**：实现 `WebSearchCard` 组件
5. **集成**：在 `ChatMessageBubble.tsx` 中集成新组件
6. **测试验证**：运行测试和手动验证

---

## 10. 附录：Visual Mockup

设计方案通过 Visual Companion 工具与用户进行可视化讨论，最终确定的 UI 样式如下：

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐 联网搜索  ✓ 已完成                    找到 5 条结果          │
├─────────────────────────────────────────────────────────────────┤
│  💡 AI 摘要：根据搜索结果，2024年农产品电商市场规模预计达到...   │
├─────────────────────────────────────────────────────────────────┤
│  📰 新闻 3  |  📄 网页 2                                          │
├─────────────────────────────────────────────────────────────────┤
│  ▼ 点击展开查看详细结果                                          │
├─────────────────────────────────────────────────────────────────┤
│  （展开后）                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 新闻 | 农产品电商发展趋势报告                                 ││
│  │       2024年市场规模预计突破万亿...                           ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 网页 | 乡村振兴政策解读                                       ││
│  │       最新政策支持农村电商发展...                             ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 新闻 | 农产品定价策略分析                                     ││
│  │       市场波动因素及应对建议...                               ││
│  └─────────────────────────────────────────────────────────────┘│
│  查看全部 5 条结果                                               │
└─────────────────────────────────────────────────────────────────┘
```