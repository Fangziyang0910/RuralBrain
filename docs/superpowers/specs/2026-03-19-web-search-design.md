# 联网搜索功能设计文档

> **设计日期**: 2026-03-19
> **设计状态**: 待实现
> **相关分支**: feat/web-search

---

## 1. 概述

### 1.1 背景

RuralBrain 当前依赖预训练知识和本地知识库（RAG）回答问题。但农业领域的许多信息具有时效性：
- 农产品市场价格波动
- 最新政策法规发布
- 实时天气、灾害信息
- 新闻事件动态

Agent 需要联网获取实时信息的能力，才能提供更准确、更有价值的决策支持。

### 1.2 目标

为 Agent 添加联网搜索功能，让 Agent 能够自主获取实时网络信息。

**核心需求**：
1. 用户可控的前端开关（类似 DeepSeek 联网搜索开关）
2. 支持同一会话内动态切换开关状态
3. 搜索结果直接返回给 Agent 进行理解和整合
4. 与现有知识库开关机制保持一致

### 1.3 范围

**包含**：
- Tavily Search API 集成
- web_search_tool 工具实现
- 开关状态管理（会话级别）
- 前端开关 UI
- 后端 API 参数传递

**不包含**：
- 搜索结果缓存（后续优化）
- 多搜索引擎切换
- 搜索历史记录

---

## 2. 技术决策

### 2.1 搜索 API 选择

**选择**: Tavily Search API

**理由**：
- 专为 AI Agent 设计，返回结构化结果
- LangChain 官方集成（`langchain-community`）
- 支持搜索深度控制（basic/advanced）
- 内置 AI 摘要功能
- 定价合理（免费额度 + 按量付费）

### 2.2 集成方式

**选择**: 核心工具 + 前端开关控制

**理由**：
- 联网搜索是通用能力，非特定场景技能
- 用户期望类似 DeepSeek 的"联网搜索"开关
- 与现有知识库开关机制一致

### 2.3 触发控制

**选择**: 开关开启时注册工具，Agent 自主判断调用

**理由**：
- 用户明确控制是否启用联网
- Agent 根据问题内容自主决定是否需要搜索
- 支持同一会话内动态切换

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Next.js)                          │
│  ┌─────────────────┐                                        │
│  │ 联网搜索开关     │  ← 用户切换，状态存于前端              │
│  └────────┬────────┘                                        │
└───────────┼─────────────────────────────────────────────────┘
            │ 每次请求携带 enable_web_search 参数
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ service/server.py                                    │   │
│  │ - 接收 enable_web_search 参数                        │   │
│  │ - 调用 set_web_search_switch_state(thread_id, bool) │   │
│  └─────────────────────────────────────────────────────┘   │
│            │                                                 │
│            ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ DynamicToolMiddleware                                │   │
│  │ - before_agent: 检查开关，注册/移除 web_search_tool │   │
│  │ - 开关开启 → 注册工具 (pinned=True)                  │   │
│  │ - 开关关闭 → 移除工具                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│            │                                                 │
│            ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Agent + web_search_tool                              │   │
│  │ - Agent 自主判断是否需要搜索                         │   │
│  │ - 调用 Tavily API 获取结果                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 请求流程

```
1. 用户切换前端开关 (enableWebSearch = true/false)
2. 用户发送消息
3. 前端携带 enable_web_search 参数发送请求
4. 后端设置开关状态: set_web_search_switch_state(thread_id, bool)
5. Agent 开始处理，触发 before_agent 钩子
6. DynamicToolMiddleware 检查开关，决定注册或移除 web_search_tool
7. Agent 根据问题内容自主决定是否调用搜索工具
8. 返回响应给用户
```

### 3.3 会话内动态切换

同一会话内，用户可以随时切换开关状态：

| 轮次 | 开关状态 | 工具状态 |
|------|---------|---------|
| 第1轮 | 开启 | web_search_tool 已注册 |
| 第2轮 | 关闭 | web_search_tool 已移除 |
| 第3轮 | 开启 | web_search_tool 重新注册 |

---

## 4. 详细设计

### 4.1 web_search_tool 工具

**文件**: `src/agents/tools/web_search_tool.py`

```python
from langchain_community.tools.tavily_search import TavilySearchResults

@tool
def web_search_tool(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5
) -> str:
    """
    联网搜索实时信息，获取最新数据。

    适用场景：
    - 市场价格、行情趋势
    - 最新政策法规
    - 实时新闻、事件
    - Agent 知识库之外的信息

    Args:
        query: 搜索关键词或问题
        search_depth: 搜索深度 ("basic" 快速/"advanced" 深度)
        max_results: 返回结果数量，默认 5 条

    Returns:
        结构化的搜索结果摘要
    """
```

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | str | 是 | - | 搜索关键词或自然语言问题 |
| search_depth | str | 否 | "basic" | basic（快速）/ advanced（深度） |
| max_results | int | 否 | 5 | 返回结果数量 |

**返回格式**：

```
【联网搜索结果】
搜索: 大米市场价格 2024

1. [标题](URL)
   摘要: ...
   发布时间: ...

2. [标题](URL)
   摘要: ...

AI 摘要: 根据 X 月数据，大米市场均价...
```

### 4.2 中间件扩展

**文件**: `src/agents/middleware/dynamic_tool_middleware.py`

**新增状态存储**：

```python
# 常量定义
PINNED_TTL = 999  # 钉住工具的 TTL 值，表示永不过期

# Web 搜索开关状态（thread_id -> enable_web_search）
_web_search_switch_state: Dict[str, Optional[bool]] = {}

def set_web_search_switch_state(thread_id: str, enabled: Optional[bool]):
    """设置联网搜索开关状态"""
    thread_id = str(thread_id)
    _web_search_switch_state[thread_id] = enabled
    logger.info(f"设置联网搜索开关: thread_id={thread_id}, enabled={enabled}")

def get_web_search_switch_state(thread_id: str) -> Optional[bool]:
    """获取联网搜索开关状态"""
    return _web_search_switch_state.get(thread_id)
```

**before_agent 钩子扩展**：

```python
def before_agent(self, state, runtime):
    """Agent 执行前：TTL 衰减 + Web 搜索工具注册"""
    # ... 现有 TTL 逻辑 ...

    # Web 搜索工具注册逻辑
    thread_id = self._get_thread_id_from_runtime(runtime)
    web_search_enabled = get_web_search_switch_state(thread_id)

    if web_search_enabled:
        # 开关开启：注册工具（pinned=True）
        if "web_search_tool" not in self._registered_tools.get(thread_id, {}):
            self.register_tools(
                tool_names=["web_search_tool"],
                tools=[self._tool_loader.get_tool("web_search_tool")],
                skill_name="web_search",
                thread_id=thread_id,
                ttl_config=TTLConfig(base_ttl=PINNED_TTL, pinned=True)
            )
    else:
        # 开关关闭：移除工具
        self.unregister_tools_by_names(["web_search_tool"], thread_id)
```

**关键设计点**：
- `pinned=True`：工具不会被 TTL 机制移除
- 每轮对话检查开关状态，支持动态切换
- 开关关闭时立即移除工具

### 4.3 后端 API 集成

**文件**: `service/schemas.py`

```python
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    image_path: Optional[str] = None
    enable_knowledge_base: Optional[bool] = None
    enable_web_search: Optional[bool] = None  # 新增
```

**文件**: `service/server.py`

```python
from src.agents.middleware.dynamic_tool_middleware import (
    set_kb_switch_state,
    set_web_search_switch_state,  # 新增
)

@router.post("/chat")
async def chat(request: ChatRequest):
    thread_id = request.thread_id or generate_thread_id()

    # 知识库开关（现有）
    if request.enable_knowledge_base is not None:
        set_kb_switch_state(thread_id, request.enable_knowledge_base)

    # 联网搜索开关（新增）
    if request.enable_web_search is not None:
        set_web_search_switch_state(thread_id, request.enable_web_search)

    # ... 后续处理 ...
```

**文件**: `src/agents/context.py`

```python
class AgentContext(BaseModel):
    """Agent 上下文"""
    thread_id: Optional[str] = None
    enable_knowledge_base: Optional[bool] = None
    enable_web_search: Optional[bool] = None  # 新增
```

### 4.4 前端集成

**文件**: `frontend/src/components/ChatInput.tsx`

```tsx
// 状态管理
const [enableWebSearch, setEnableWebSearch] = useState(false);

// 开关 UI
<div className="flex items-center gap-2">
  <Switch
    checked={enableWebSearch}
    onCheckedChange={setEnableWebSearch}
  />
  <Label>联网搜索</Label>
</div>

// 请求参数
const sendMessage = async (message: string) => {
  await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      thread_id,
      enable_knowledge_base: enableKnowledgeBase,
      enable_web_search: enableWebSearch,
    }),
  });
};
```

---

## 5. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `src/agents/tools/web_search_tool.py` | 新建 | 网络搜索工具实现 |
| `src/agents/tools/tool_loader.py` | 修改 | 注册 web_search_tool |
| `src/agents/tools/__init__.py` | 修改 | 导出 web_search_tool |
| `src/agents/middleware/dynamic_tool_middleware.py` | 修改 | 添加开关状态管理和注册逻辑 |
| `src/agents/context.py` | 修改 | 添加 enable_web_search 字段 |
| `service/schemas.py` | 修改 | 添加 enable_web_search 字段 |
| `service/server.py` | 修改 | 设置开关状态 |
| `frontend/src/components/ChatInput.tsx` | 修改 | 添加联网搜索开关 UI |
| `.env.example` | 修改 | 添加 TAVILY_API_KEY 配置说明 |

### 5.1 tool_loader.py 注册详情

```python
# src/agents/tools/tool_loader.py

def _register_all_tools(self):
    # ... 现有工具注册 ...

    # ==================== 网络搜索工具 ====================
    self._tool_factories.update({
        "web_search_tool": self._load_web_search_tool,
    })

def _load_web_search_tool(self) -> BaseTool:
    from .web_search_tool import web_search_tool
    return web_search_tool
```

---

## 6. 配置项

### 6.1 环境变量

```bash
# .env
TAVILY_API_KEY=tvly-xxxxx  # Tavily API 密钥
```

**API Key 验证行为**：
- 如果 `TAVILY_API_KEY` 未配置或无效，工具返回友好错误提示："联网搜索功能暂不可用，请检查 API 配置"
- 工具不会因 API Key 问题而崩溃，确保用户体验不受影响
- 服务启动时检查 API Key 配置，记录警告日志（不阻塞启动）

### 6.2 工具参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `search_depth` | basic | 默认使用快速搜索 |
| `max_results` | 5 | 默认返回 5 条结果 |
| `include_answer` | true | 启用 AI 摘要 |

---

## 7. 测试计划

### 7.1 单元测试

- `web_search_tool` 工具功能测试
- 开关状态管理测试
- 工具注册/移除逻辑测试

### 7.2 集成测试

- 端到端流程测试：前端开关 → 后端处理 → 工具调用
- 会话内动态切换测试
- 与知识库开关共存测试

### 7.3 手动测试场景

| 场景 | 预期结果 |
|------|---------|
| 开关关闭时发送消息 | Agent 无法调用搜索工具 |
| 开关开启时询问市场价格 | Agent 调用搜索工具返回实时信息 |
| 会话内切换开关 | 工具状态立即生效 |
| 开关开启但问题不需要搜索 | Agent 自主决定不调用搜索 |

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Tavily API 限流 | 搜索失败 | 添加重试机制和错误提示 |
| 搜索结果质量不佳 | 信息不准确 | Agent 应交叉验证信息 |
| Token 消耗增加 | 成本上升 | 控制返回结果数量 |
| 用户隐私 | 搜索内容泄露 | 明确告知用户搜索行为 |

---

## 9. 后续优化

1. **搜索结果缓存** — 相同查询复用结果，减少 API 调用
2. **搜索历史** — 记录用户搜索历史，提供参考
3. **多引擎支持** — 支持 Google/Bing 等多搜索引擎
4. **搜索结果过滤** — 过滤低质量或不相关结果

---

## 10. 参考资料

- [Tavily API 文档](https://docs.tavily.com/)
- [LangChain Tavily 集成](https://python.langchain.com/docs/integrations/tools/tavily_search/)
- 项目知识库开关实现：`src/agents/middleware/dynamic_tool_middleware.py`