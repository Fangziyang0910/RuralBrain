# 前端模型选择功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现用户在前端页面选择大模型的功能，支持 DeepSeek、GLM-4、Qwen3.5-Plus 三种模型动态切换。

**Architecture:** 后端新增 `/models` API 提供模型列表，Agent 使用 LangChain Middleware + Runtime Context 模式实现动态模型切换，前端新增模型选择器 UI。

**Tech Stack:** FastAPI, LangChain, LangGraph, Next.js, TypeScript

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `src/agents/context.py` | Agent 运行时 Context 定义 |
| `src/agents/middleware/model_selection_middleware.py` | 模型选择中间件 |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/config.py` | 新增 `AVAILABLE_MODELS` 配置 |
| `service/schemas.py` | `ChatRequest` 新增 `model_id` 字段 |
| `service/server.py` | 新增 `/models` 接口，修改 `/chat/stream` |
| `src/agents/orchestrator_agent_v2.py` | 注册中间件和 Context |
| `frontend/src/app/page.tsx` | 新增模型选择器 UI 和逻辑 |

---

## Chunk 1: 后端配置与数据模型

### Task 1: 扩展模型配置

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: 添加 AVAILABLE_MODELS 配置**

在 `src/config.py` 末尾添加：

```python
# 用户可选的模型列表（扁平化）
AVAILABLE_MODELS = {
    "deepseek": {
        "name": "DeepSeek",
        "provider": "deepseek",
        "model_name": "deepseek-chat",
        "description": "DeepSeek 智能对话模型",
        "is_multimodal": False,
    },
    "glm-4": {
        "name": "GLM-4",
        "provider": "glm",
        "model_name": "glm-4",
        "description": "智谱AI GLM-4 大模型",
        "is_multimodal": False,
    },
    "qwen": {
        "name": "Qwen3.5-Plus",
        "provider": "qwen",
        "model_name": "qwen3.5-plus",
        "description": "通义千问多模态模型",
        "is_multimodal": True,
    },
}

DEFAULT_MODEL_ID = "deepseek"
```

- [ ] **Step 2: 验证配置语法**

```bash
uv run python -c "from src.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID; print(AVAILABLE_MODELS.keys())"
```

Expected: `dict_keys(['deepseek', 'glm-4', 'qwen'])`

- [ ] **Step 3: 提交**

```bash
git add src/config.py
git commit -m "feat(config): 添加 AVAILABLE_MODELS 模型列表配置"
```

---

### Task 2: 新增 ChatRequest model_id 字段

**Files:**
- Modify: `service/schemas.py`

- [ ] **Step 1: 添加 model_id 字段**

在 `ChatRequest` 类中添加 `model_id` 字段：

```python
class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    image_path: Optional[str] = Field(None, description="单图片路径（兼容旧版本）")
    image_paths: Optional[List[str]] = Field(None, description="多图片路径列表（新版本）")
    thread_id: Optional[str] = Field(None, description="对话线程ID")
    mode: Optional[str] = Field("auto", description="聊天模式: auto/detection/planning")
    work_mode: Optional[str] = Field("auto", description="规划咨询工作模式: auto/fast/deep")
    enable_knowledge_base: Optional[bool] = Field(None, description="是否启用知识库（规划咨询 skill）")
    model_id: Optional[str] = Field(None, description="模型ID: deepseek/glm-4/qwen")
```

- [ ] **Step 2: 验证 schema**

```bash
uv run python -c "from service.schemas import ChatRequest; print(ChatRequest.model_fields.keys())"
```

Expected: 包含 `model_id` 字段

- [ ] **Step 3: 提交**

```bash
git add service/schemas.py
git commit -m "feat(schemas): ChatRequest 新增 model_id 字段"
```

---

### Task 3: 新增 AgentContext

**Files:**
- Create: `src/agents/context.py`

- [ ] **Step 1: 创建 context.py**

```python
"""
Agent 运行时上下文定义

用于在 Agent 执行过程中传递用户配置（如模型选择）
"""
from dataclasses import dataclass


@dataclass
class AgentContext:
    """
    Agent 运行时上下文

    通过 LangChain create_agent 的 context_schema 参数注册，
    在 middleware 中通过 request.runtime.context 访问。

    Attributes:
        model_id: 用户选择的模型 ID，默认为 "deepseek"
    """
    model_id: str = "deepseek"
```

- [ ] **Step 2: 验证导入**

```bash
uv run python -c "from src.agents.context import AgentContext; ctx = AgentContext(model_id='qwen'); print(ctx.model_id)"
```

Expected: `qwen`

- [ ] **Step 3: 提交**

```bash
git add src/agents/context.py
git commit -m "feat(agents): 新增 AgentContext 运行时上下文"
```

---

## Chunk 2: 模型选择中间件

### Task 4: 创建模型选择中间件

**Files:**
- Create: `src/agents/middleware/model_selection_middleware.py`

- [ ] **Step 1: 创建中间件文件**

```python
"""
模型选择中间件

根据运行时 context 中的 model_id 动态选择 LLM 模型。
基于 LangChain 官方文档的 Middleware + Runtime Context 模式。
"""
import logging
from typing import Callable

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

from ...config import AVAILABLE_MODELS, DEFAULT_MODEL_ID
from ...utils import ModelManager

logger = logging.getLogger(__name__)

# 预初始化所有模型实例（避免每次请求都创建）
MODEL_INSTANCES: dict = {}


def _initialize_models():
    """初始化所有模型实例"""
    global MODEL_INSTANCES
    if MODEL_INSTANCES:
        return  # 已初始化

    for model_id, config in AVAILABLE_MODELS.items():
        try:
            manager = ModelManager(provider=config["provider"])
            MODEL_INSTANCES[model_id] = manager.get_chat_model(model=config["model_name"])
            logger.info(f"模型实例初始化成功: {model_id} ({config['model_name']})")
        except Exception as e:
            logger.error(f"模型实例初始化失败: {model_id} - {e}")


@wrap_model_call
def model_selection_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """
    根据运行时 context 动态选择模型

    从 request.runtime.context 获取用户选择的 model_id，
    然后覆盖请求中的模型实例。

    Args:
        request: 模型请求对象
        handler: 下一个处理器

    Returns:
        模型响应
    """
    # 确保模型已初始化
    _initialize_models()

    # 从 context 获取用户选择的 model_id
    model_id = DEFAULT_MODEL_ID
    if request.runtime and request.runtime.context:
        model_id = getattr(request.runtime.context, "model_id", DEFAULT_MODEL_ID)

    # 获取对应的模型实例
    model = MODEL_INSTANCES.get(model_id)
    if model is None:
        logger.warning(f"未找到模型 {model_id}，使用默认模型 {DEFAULT_MODEL_ID}")
        model = MODEL_INSTANCES.get(DEFAULT_MODEL_ID)

    if model is None:
        raise RuntimeError(f"无法获取模型实例: {model_id}")

    logger.debug(f"模型选择: {model_id}")

    # 覆盖请求中的模型
    return handler(request.override(model=model))
```

- [ ] **Step 2: 验证中间件导入**

```bash
uv run python -c "from src.agents.middleware.model_selection_middleware import model_selection_middleware; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add src/agents/middleware/model_selection_middleware.py
git commit -m "feat(middleware): 新增模型选择中间件"
```

---

### Task 5: 注册中间件到 Agent

**Files:**
- Modify: `src/agents/orchestrator_agent_v2.py`

- [ ] **Step 1: 添加导入**

在文件顶部添加导入：

```python
from .context import AgentContext
from .middleware.model_selection_middleware import model_selection_middleware
```

- [ ] **Step 2: 修改 middleware 列表**

将 `middleware` 列表修改为：

```python
middleware = [
    model_selection_middleware,  # 模型选择中间件（放最前面）
    dynamic_tool_middleware,
    skill_middleware,
    summarization_middleware,
]
```

- [ ] **Step 3: 注册 context_schema**

修改 `create_agent` 调用，添加 `context_schema` 参数：

```python
agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
    context_schema=AgentContext,  # 注册 Context
)
```

- [ ] **Step 4: 验证 Agent 创建**

```bash
uv run python -c "from src.agents.orchestrator_agent_v2 import agent; print('Agent created successfully')"
```

Expected: `Agent created successfully`

- [ ] **Step 5: 提交**

```bash
git add src/agents/orchestrator_agent_v2.py
git commit -m "feat(agent): 注册模型选择中间件和 AgentContext"
```

---

## Chunk 3: 后端 API 实现

### Task 6: 新增 /models API

**Files:**
- Modify: `service/server.py`

- [ ] **Step 1: 添加导入**

在文件顶部添加：

```python
from src.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID
```

- [ ] **Step 2: 添加 /models 路由**

在 `/health` 路由后添加：

```python
@app.get("/models")
async def get_models():
    """
    获取可用模型列表

    Returns:
        models: 模型列表
        default_model: 默认模型 ID
    """
    models = []
    for model_id, config in AVAILABLE_MODELS.items():
        models.append({
            "id": model_id,
            "name": config["name"],
            "description": config["description"],
            "is_multimodal": config["is_multimodal"],
        })

    return {
        "models": models,
        "default_model": DEFAULT_MODEL_ID,
    }
```

- [ ] **Step 3: 测试 API**

```bash
curl http://localhost:8081/models
```

Expected: 返回包含 models 列表和 default_model 的 JSON

- [ ] **Step 4: 提交**

```bash
git add service/server.py
git commit -m "feat(api): 新增 /models 接口返回可用模型列表"
```

---

### Task 7: 修改 /chat/stream 传递 model_id

**Files:**
- Modify: `service/server.py`

- [ ] **Step 1: 添加 AgentContext 导入**

在文件顶部添加：

```python
from src.agents.context import AgentContext
```

- [ ] **Step 2: 修改 config 配置**

在 `chat_stream` 函数中，修改 `config` 变量：

```python
config = {
    "configurable": {
        "thread_id": thread_id,
        "enable_knowledge_base": request.enable_knowledge_base,
    },
    "context": AgentContext(model_id=request.model_id or DEFAULT_MODEL_ID),
    "recursion_limit": 50,
}
```

- [ ] **Step 3: 验证修改**

```bash
uv run python -c "from service.server import app; print('Server module OK')"
```

Expected: `Server module OK`

- [ ] **Step 4: 提交**

```bash
git add service/server.py
git commit -m "feat(api): /chat/stream 支持 model_id 参数传递给 Agent"
```

---

## Chunk 4: 前端实现

### Task 8: 前端添加模型选择器

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: 添加类型定义**

在文件顶部 `const API_BASE` 后添加：

```typescript
// 模型类型定义
interface Model {
  id: string;
  name: string;
  description: string;
  is_multimodal: boolean;
}

interface ModelsResponse {
  models: Model[];
  default_model: string;
}
```

- [ ] **Step 2: 添加状态变量**

在现有状态变量后添加：

```typescript
const [models, setModels] = useState<Model[]>([]);
const [selectedModelId, setSelectedModelId] = useState<string>("deepseek");
```

- [ ] **Step 3: 添加获取模型列表的 useEffect**

在现有 `useEffect` 后添加：

```typescript
// 获取可用模型列表
useEffect(() => {
  fetch(`${API_BASE}/models`)
    .then(res => res.json())
    .then(data => {
      setModels(data.models);
      setSelectedModelId(data.default_model);
    })
    .catch(err => {
      console.error("获取模型列表失败:", err);
    });
}, []);
```

- [ ] **Step 4: 修改 handleSendMessage 传递 model_id**

在 `handleSendMessage` 函数的 `body: JSON.stringify` 中添加 `model_id`：

```typescript
body: JSON.stringify({
  message,
  image_paths: imagePaths,
  thread_id: threadId,
  enable_knowledge_base: enableKnowledgeBase,
  model_id: selectedModelId,
}),
```

- [ ] **Step 5: 添加模型选择器 UI**

在 `<form onSubmit={handleSubmit} className="space-y-3">` 内，知识库开关按钮后添加：

```tsx
{/* 模型选择器 */}
<select
  value={selectedModelId}
  onChange={(e) => setSelectedModelId(e.target.value)}
  disabled={loading}
  className="px-4 py-2 rounded-full text-sm font-medium border-2 border-stone-200 bg-white text-stone-700 hover:border-stone-300 focus:outline-none focus:border-paddy-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
>
  {models.map(model => (
    <option key={model.id} value={model.id}>
      {model.name}
    </option>
  ))}
</select>

{/* 多模态提示 */}
{models.find(m => m.id === selectedModelId)?.is_multimodal && (
  <span className="text-xs text-green-600 font-medium">支持图片识别</span>
)}
```

- [ ] **Step 6: 验证前端编译**

```bash
cd frontend && npm run build
```

Expected: 编译成功，无错误

- [ ] **Step 7: 提交**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat(frontend): 新增模型选择器 UI"
```

---

## Chunk 5: 集成测试与验证

### Task 9: 端到端测试

- [ ] **Step 1: 启动后端服务**

```bash
uv run python run_server.py
```

- [ ] **Step 2: 测试 /models API**

```bash
curl http://localhost:8081/models | jq
```

Expected:
```json
{
  "models": [
    {"id": "deepseek", "name": "DeepSeek", ...},
    {"id": "glm-4", "name": "GLM-4", ...},
    {"id": "qwen", "name": "Qwen3.5-Plus", ...}
  ],
  "default_model": "deepseek"
}
```

- [ ] **Step 3: 启动前端服务**

```bash
uv run python run_frontend.py
```

- [ ] **Step 4: 浏览器测试**

1. 打开 http://localhost:3001
2. 验证模型选择器显示在输入区域
3. 切换模型，发送消息
4. 验证对话正常，模型切换生效

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "feat: 完成前端模型选择功能"
```

---

## 注意事项

1. **LangChain/LangGraph 语法**：本实现基于 LangChain 官方文档的 Middleware + Runtime Context 模式
2. **模型实例预初始化**：中间件在首次调用时初始化所有模型实例，避免每次请求都创建
3. **向后兼容**：`model_id` 参数可选，不传时使用默认模型 `deepseek`
4. **错误处理**：如果请求的模型不存在，自动回退到默认模型