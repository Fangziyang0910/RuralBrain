# 联网搜索功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Agent 添加联网搜索功能，让 Agent 能够自主获取实时网络信息，用户可通过前端开关控制。

**Architecture:** 复用现有知识库开关机制，在 DynamicToolMiddleware 中扩展 web_search 开关逻辑，开关开启时动态注册 web_search_tool，关闭时移除工具。

**Tech Stack:** Python, LangChain, Tavily Search API, TypeScript, Next.js

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `src/agents/tools/web_search_tool.py` | 网络搜索工具实现（调用 Tavily API） |
| `src/agents/tools/tool_loader.py` | 注册 web_search_tool 加载器 |
| `src/agents/tools/__init__.py` | 导出 web_search_tool |
| `src/agents/middleware/dynamic_tool_middleware.py` | 开关状态管理和工具动态注册 |
| `src/agents/context.py` | Agent 上下文字段 |
| `service/schemas.py` | API 请求参数定义 |
| `service/server.py` | 设置开关状态 |
| `frontend/src/app/page.tsx` | 前端开关 UI 和请求参数 |
| `.env.example` | 环境变量配置示例 |

---

## Chunk 1: 后端工具层（web_search_tool）

### Task 0: 安装依赖

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加 tavily-python 依赖**

Run: `uv add tavily-python`

- [ ] **Step 2: 验证依赖安装**

Run: `uv run python -c "from langchain_community.tools.tavily_search import TavilySearchResults; print('OK')"`
Expected: OK

- [ ] **Step 3: 提交**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: 添加 tavily-python 依赖

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 1: 实现 web_search_tool 工具

**Files:**
- Create: `src/agents/tools/web_search_tool.py`
- Test: `tests/unit/test_web_search_tool.py`

- [ ] **Step 1: 编写 web_search_tool 单元测试**

```python
# tests/unit/test_web_search_tool.py
"""web_search_tool 单元测试"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestWebSearchTool:
    """web_search_tool 测试类"""

    def test_web_search_tool_exists(self):
        """测试工具可以被导入"""
        from src.agents.tools.web_search_tool import web_search_tool
        assert web_search_tool is not None

    def test_web_search_tool_has_correct_name(self):
        """测试工具名称正确"""
        from src.agents.tools.web_search_tool import web_search_tool
        assert web_search_tool.name == "web_search_tool"

    def test_web_search_tool_description_contains_keywords(self):
        """测试工具描述包含关键词"""
        from src.agents.tools.web_search_tool import web_search_tool
        desc = web_search_tool.description.lower()
        assert "搜索" in desc or "search" in desc

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"})
    @patch("src.agents.tools.web_search_tool.TavilySearchResults")
    def test_web_search_tool_returns_results(self, mock_tavily):
        """测试工具返回搜索结果"""
        # 配置 mock
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = [
            {"title": "测试结果", "url": "https://example.com", "content": "测试内容"}
        ]
        mock_tavily.return_value = mock_instance

        from src.agents.tools.web_search_tool import web_search_tool

        result = web_search_tool.invoke({"query": "大米价格"})
        assert result is not None
        assert len(result) > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/unit/test_web_search_tool.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 web_search_tool**

```python
# src/agents/tools/web_search_tool.py
"""
联网搜索工具：通过 Tavily API 搜索实时网络信息

该工具让 Agent 能够获取实时市场信息、最新政策、新闻等。
"""
import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_MAX_RESULTS = 5
DEFAULT_SEARCH_DEPTH = "basic"


def _check_api_key() -> bool:
    """检查 TAVILY_API_KEY 是否配置"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY 未配置，联网搜索功能不可用")
        return False
    return True


def _format_results(results: list) -> str:
    """
    格式化搜索结果为可读文本

    Args:
        results: Tavily API 返回的结果列表

    Returns:
        格式化后的文本
    """
    if not results:
        return "未找到相关搜索结果。"

    output_lines = ["【联网搜索结果】"]

    for i, result in enumerate(results, 1):
        title = result.get("title", "无标题")
        url = result.get("url", "")
        content = result.get("content", "无摘要")

        output_lines.append(f"\n{i}. [{title}]({url})")
        output_lines.append(f"   摘要: {content}")

    return "\n".join(output_lines)


@tool
def web_search_tool(
    query: str,
    search_depth: str = DEFAULT_SEARCH_DEPTH,
    max_results: int = DEFAULT_MAX_RESULTS
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
        search_depth: 搜索深度 ("basic" 快速/"advanced" 深度)，默认 "basic"
        max_results: 返回结果数量，默认 5 条

    Returns:
        结构化的搜索结果摘要
    """
    # 检查 API Key
    if not _check_api_key():
        return "联网搜索功能暂不可用，请检查 API 配置（TAVILY_API_KEY）。"

    try:
        logger.info(f"联网搜索: query={query}, depth={search_depth}, max_results={max_results}")

        # 延迟导入，避免未安装依赖时报错
        from langchain_community.tools.tavily_search import TavilySearchResults

        # 创建搜索工具实例
        search = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
        )

        # 执行搜索
        results = search.invoke(query)

        # 格式化输出
        formatted = _format_results(results)
        logger.info(f"搜索完成，返回 {len(results) if results else 0} 条结果")

        return formatted

    except ImportError:
        error_msg = "联网搜索依赖未安装，请运行: uv add langchain-community"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"搜索失败: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# 工具标签
web_search_tool.tags = ["web", "search", "realtime"]

__all__ = ["web_search_tool"]
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/unit/test_web_search_tool.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/agents/tools/web_search_tool.py tests/unit/test_web_search_tool.py
git commit -m "feat: 添加 web_search_tool 联网搜索工具

- 基于 Tavily Search API 实现
- 支持搜索深度和结果数量控制
- 包含 API Key 检查和错误处理

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 注册工具到 ToolLoader

**Files:**
- Modify: `src/agents/tools/tool_loader.py`
- Modify: `src/agents/tools/__init__.py`

- [ ] **Step 1: 在 ToolLoader 中注册 web_search_tool**

在 `src/agents/tools/tool_loader.py` 中添加：

```python
# 在 _register_all_tools 方法中添加（约第 49 行后）

    # ==================== 网络搜索工具 ====================
    self._tool_factories.update({
        "web_search_tool": self._load_web_search_tool,
    })
```

```python
# 添加加载器方法（文件末尾，公共接口前）

    def _load_web_search_tool(self) -> BaseTool:
        from .web_search_tool import web_search_tool
        return web_search_tool
```

- [ ] **Step 2: 在 __init__.py 中导出**

在 `src/agents/tools/__init__.py` 中添加：

```python
# 导入
from .web_search_tool import web_search_tool

# __all__ 列表
__all__ = [
    # ... 现有导出 ...
    "web_search_tool",
]
```

- [ ] **Step 3: 验证工具可加载**

Run: `uv run python -c "from src.agents.tools.tool_loader import get_tool_loader; loader = get_tool_loader(); print('web_search_tool' in loader.get_available_tool_names())"`
Expected: True

- [ ] **Step 4: 提交**

```bash
git add src/agents/tools/tool_loader.py src/agents/tools/__init__.py
git commit -m "feat: 注册 web_search_tool 到 ToolLoader

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: 中间件层（开关状态管理）

### Task 3: 扩展 DynamicToolMiddleware 支持联网搜索开关

**Files:**
- Modify: `src/agents/middleware/dynamic_tool_middleware.py`
- Test: `tests/unit/test_web_search_switch.py`

- [ ] **Step 1: 编写开关状态管理测试**

```python
# tests/unit/test_web_search_switch.py
"""联网搜索开关状态管理测试"""
import pytest


class TestWebSearchSwitch:
    """联网搜索开关测试"""

    def test_set_web_search_switch_state(self):
        """测试设置开关状态"""
        from src.agents.middleware.dynamic_tool_middleware import (
            set_web_search_switch_state,
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        # 清理状态
        _web_search_switch_state.clear()

        set_web_search_switch_state("test-thread-1", True)
        assert get_web_search_switch_state("test-thread-1") is True

        set_web_search_switch_state("test-thread-1", False)
        assert get_web_search_switch_state("test-thread-1") is False

    def test_get_web_search_switch_state_default(self):
        """测试未设置时返回 None"""
        from src.agents.middleware.dynamic_tool_middleware import (
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        _web_search_switch_state.clear()
        result = get_web_search_switch_state("non-existent-thread")
        assert result is None

    def test_web_search_switch_isolation(self):
        """测试不同 thread_id 的开关状态隔离"""
        from src.agents.middleware.dynamic_tool_middleware import (
            set_web_search_switch_state,
            get_web_search_switch_state,
            _web_search_switch_state,
        )

        _web_search_switch_state.clear()

        set_web_search_switch_state("thread-A", True)
        set_web_search_switch_state("thread-B", False)

        assert get_web_search_switch_state("thread-A") is True
        assert get_web_search_switch_state("thread-B") is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/unit/test_web_search_switch.py -v`
Expected: FAIL - ImportError (函数不存在)

- [ ] **Step 3: 实现开关状态管理函数**

在 `src/agents/middleware/dynamic_tool_middleware.py` 中添加（约第 40 行后，知识库开关函数后）：

```python
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

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/unit/test_web_search_switch.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/agents/middleware/dynamic_tool_middleware.py tests/unit/test_web_search_switch.py
git commit -m "feat: 添加联网搜索开关状态管理

- 新增 set_web_search_switch_state / get_web_search_switch_state 函数
- 支持会话级别的开关状态隔离

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 实现 before_agent 钩子中的工具注册逻辑

**Files:**
- Modify: `src/agents/middleware/dynamic_tool_middleware.py`

- [ ] **Step 1: 在 before_agent 中添加 web_search 工具注册逻辑**

**重要**：Web 搜索工具注册必须在 TTL 检查之前执行，否则当 TTL 未启用时会提前返回。

将现有的 `before_agent` 方法（约 177-198 行）替换为：

```python
def before_agent(self, state, runtime):
    """
    Agent 执行前的钩子（同步版本）

    1. Web 搜索工具动态注册（始终执行）
    2. TTL 衰减（仅在 TTL 启用时执行）
    """
    # ==================== Web 搜索工具动态注册 ====================
    # 必须在 TTL 检查之前执行，否则 TTL 未启用时会提前返回
    self._handle_web_search_tool_registration()

    # TTL 衰减（仅在 TTL 启用时执行）
    if ENABLE_TOOL_TTL:
        try:
            config = get_config()
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                thread_id = str(thread_id)
                # 增加轮次
                self._increment_round(thread_id)
                # TTL 衰减
                self._decrement_all_tools(thread_id)
        except (RuntimeError, KeyError):
            pass

    return None
```

在类中添加辅助方法（在 `before_agent` 方法后）：

**注意**：`TTLConfig` 已在文件顶部（第 27 行）导入：
```python
from .tool_lifecycle import TTLConfig, ToolLifecycle
```

```python
def _handle_web_search_tool_registration(self):
    """处理 Web 搜索工具的动态注册/移除"""
    try:
        config = get_config()
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            thread_id = str(thread_id)
            web_search_enabled = get_web_search_switch_state(thread_id)

            if web_search_enabled:
                # 开关开启：注册工具
                if "web_search_tool" not in self._registered_tools.get(thread_id, {}):
                    tool = self._tool_loader.get_tool("web_search_tool")
                    if tool:
                        self.register_tools(
                            tool_names=["web_search_tool"],
                            tools=[tool],
                            skill_name="web_search",
                            thread_id=thread_id,
                            ttl_config=TTLConfig(base_ttl=999, pinned=True)
                        )
                        logger.info(f"联网搜索工具已注册: thread_id={thread_id}")
            else:
                # 开关关闭或未设置：移除工具
                if "web_search_tool" in self._registered_tools.get(thread_id, {}):
                    self.unregister_tools_by_names(["web_search_tool"], thread_id)
                    logger.info(f"联网搜索工具已移除: thread_id={thread_id}")
    except (RuntimeError, KeyError) as e:
        logger.debug(f"Web 搜索工具注册检查失败: {e}")
```

- [ ] **Step 2: 同样修改 abefore_agent 异步版本**

**同样注意**：Web 搜索工具注册必须在 TTL 检查之前执行。

将现有的 `abefore_agent` 方法（约 200-221 行）替换为：

```python
async def abefore_agent(self, state, runtime):
    """
    Agent 执行前的钩子（异步版本）

    1. Web 搜索工具动态注册（始终执行）
    2. TTL 衰减（仅在 TTL 启用时执行）
    """
    # ==================== Web 搜索工具动态注册 ====================
    # 必须在 TTL 检查之前执行，否则 TTL 未启用时会提前返回
    self._handle_web_search_tool_registration()

    # TTL 衰减（仅在 TTL 启用时执行）
    if ENABLE_TOOL_TTL:
        try:
            config = get_config()
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                thread_id = str(thread_id)
                # 增加轮次
                self._increment_round(thread_id)
                # TTL 衰减
                self._decrement_all_tools(thread_id)
        except (RuntimeError, KeyError):
            pass

    return None
```

- [ ] **Step 3: 更新 __all__ 导出**

在文件末尾的 `__all__` 列表中更新（补充遗漏的知识库开关函数导出）：

```python
__all__ = [
    "DynamicToolMiddleware",
    "get_dynamic_middleware",
    "set_dynamic_middleware",
    "reset_dynamic_middleware",
    "DEFAULT_THREAD_ID",
    "set_kb_switch_state",           # 补充遗漏
    "get_kb_switch_state",           # 补充遗漏
    "set_web_search_switch_state",   # 新增
    "get_web_search_switch_state",   # 新增
]
```

- [ ] **Step 4: 提交**

```bash
git add src/agents/middleware/dynamic_tool_middleware.py
git commit -m "feat: 在 before_agent 中实现 web_search_tool 动态注册

- 开关开启时注册工具（pinned=True）
- 开关关闭时移除工具
- 支持会话内动态切换
- 同步和异步版本都已实现

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: 后端 API 层

### Task 5: 扩展 API 请求参数

**Files:**
- Modify: `service/schemas.py`
- Modify: `src/agents/context.py`

- [ ] **Step 1: 在 ChatRequest 中添加 enable_web_search 字段**

在 `service/schemas.py` 的 `ChatRequest` 类中添加：

```python
class ChatRequest(BaseModel):
    # ... 现有字段 ...
    enable_web_search: Optional[bool] = Field(None, description="是否启用联网搜索")
```

- [ ] **Step 2: 在 AgentContext 中添加字段**

在 `src/agents/context.py` 中添加：

```python
@dataclass
class AgentContext:
    """Agent 运行时上下文"""
    model_id: str = "deepseek"
    enable_web_search: Optional[bool] = None
```

- [ ] **Step 3: 提交**

```bash
git add service/schemas.py src/agents/context.py
git commit -m "feat: 添加 enable_web_search API 参数

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 在 server.py 中设置开关状态

**Files:**
- Modify: `service/server.py`

- [ ] **Step 1: 导入 set_web_search_switch_state**

在 `service/server.py` 约 33 行修改导入：

```python
from src.agents.middleware.dynamic_tool_middleware import (
    set_kb_switch_state,
    set_web_search_switch_state,
)
```

- [ ] **Step 2: 在 chat 端点中设置开关状态**

在处理 `enable_knowledge_base` 的代码后添加：

```python
# 联网搜索开关（新增）
if request.enable_web_search is not None:
    set_web_search_switch_state(thread_id, request.enable_web_search)
```

- [ ] **Step 3: 提交**

```bash
git add service/server.py
git commit -m "feat: 在 chat 端点设置联网搜索开关状态

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: 前端集成

### Task 7: 添加联网搜索开关 UI

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: 添加 enableWebSearch 状态**

在 `frontend/src/app/page.tsx` 约 66 行后添加：

```tsx
const [enableWebSearch, setEnableWebSearch] = useState<boolean>(false);
```

- [ ] **Step 2: 在请求中传递参数**

修改 sendMessage 函数中的 fetch body（约 349 行）：

```tsx
body: JSON.stringify({
  message,
  image_paths: imagePaths,
  thread_id: threadId,
  enable_knowledge_base: enableKnowledgeBase,
  enable_web_search: enableWebSearch,
  model_id: selectedModelId,
}),
```

- [ ] **Step 3: 添加开关按钮 UI**

在知识库开关按钮后（约 666 行后）添加联网搜索开关：

```tsx
{/* 联网搜索开关 */}
<button
  type="button"
  onClick={() => setEnableWebSearch(!enableWebSearch)}
  disabled={loading}
  className={`px-4 py-2 rounded-full text-sm font-medium transition-all border-2 shadow-sm hover:shadow-md ${
    enableWebSearch
      ? "bg-blue-50 border-blue-500 text-blue-700"
      : "bg-white border-stone-300 text-stone-600"
  }`}
>
  联网搜索 {enableWebSearch ? "✓" : ""}
</button>
```

- [ ] **Step 4: 更新 useCallback 依赖**

在 sendMessage 的 useCallback 依赖数组中添加 `enableWebSearch`（约 507 行）：

```tsx
[threadId, enableKnowledgeBase, enableWebSearch, selectedModelId]
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: 添加联网搜索前端开关

- 新增 enableWebSearch 状态
- 在请求中传递 enable_web_search 参数
- 添加开关按钮 UI

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: 配置与文档

### Task 8: 更新配置文件

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: 添加 TAVILY_API_KEY 配置示例**

在 `.env.example` 中添加：

```bash
# Tavily API 配置（联网搜索功能）
TAVILY_API_KEY=tvly-xxxxx  # 从 https://tavily.com 获取
```

- [ ] **Step 2: 提交**

```bash
git add .env.example
git commit -m "docs: 添加 TAVILY_API_KEY 配置示例

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 验证与集成测试

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动开发环境**

Run: `docker-compose -f docker-compose.dev.yml up -d`

- [ ] **Step 2: 健康检查**

Run: `bash scripts/dev/check.sh --quick`

- [ ] **Step 3: 手动测试场景**

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 开关默认关闭 | 刷新页面 | "联网搜索" 按钮无 ✓ 标记 |
| 开启开关发送消息 | 点击开关 → 发送 "今天大米价格" | Agent 调用 web_search_tool |
| 关闭开关发送消息 | 点击开关关闭 → 发送消息 | Agent 不调用搜索工具 |
| 会话内切换 | 开启 → 发送 → 关闭 → 发送 | 工具状态随开关变化 |

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: 完成联网搜索功能实现

- 基于 Tavily Search API
- 前端开关控制，支持会话内动态切换
- 复用现有知识库开关机制

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 总结

| 任务 | 文件 | 状态 |
|------|------|------|
| Task 0 | pyproject.toml | 待执行 |
| Task 1 | web_search_tool.py, test_web_search_tool.py | 待执行 |
| Task 2 | tool_loader.py, __init__.py | 待执行 |
| Task 3 | dynamic_tool_middleware.py, test_web_search_switch.py | 待执行 |
| Task 4 | dynamic_tool_middleware.py | 待执行 |
| Task 5 | schemas.py, context.py | 待执行 |
| Task 6 | server.py | 待执行 |
| Task 7 | page.tsx | 待执行 |
| Task 8 | .env.example | 待执行 |
| Task 9 | 集成测试 | 待执行 |