# 前端模型选择功能设计文档

> 创建时间：2026-03-17
> 完成时间：2026-03-19
> 状态：已完成

## 概述

允许用户在前端页面选择大模型，实现模型动态切换功能。

## 需求确认

| 项目 | 决策 |
|------|------|
| **UI 位置** | 输入区域，和"知识库开关"并排 |
| **模型列表** | 预设扁平列表（DeepSeek、GLM-4、Qwen3.5-Plus） |
| **持久化** | 会话级，刷新后恢复默认模型 |
| **对话历史** | 切换模型后保持对话，新消息用新模型回答 |
| **模型列表来源** | 后端 API 提供 `/models` 接口 |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Next.js)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 输入区域                                                 ││
│  │  [知识库 ✓] [DeepSeek ▼]  ← 两个开关并排                ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │ 文本输入框...                                       │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ POST /chat/stream { model_id: "deepseek" }
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ /models → 返回可用模型列表                               ││
│  │ /chat/stream → 接收 model_id，传递给 Agent              ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ModelMiddleware (wrap_model_call)                       ││
│  │  - 从 configurable 读取 model_id                         ││
│  │  - 根据 model_id 选择对应的模型实例                      ││
│  │  - request.override(model=selected_model)               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 详细设计

### 一、后端 API 设计

#### 1. 模型列表 API

**新增接口** `GET /models`

```python
# 响应结构
{
    "models": [
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "description": "DeepSeek 智能对话模型",
            "is_multimodal": false
        },
        {
            "id": "glm-4",
            "name": "GLM-4",
            "description": "智谱AI GLM-4 大模型",
            "is_multimodal": false
        },
        {
            "id": "qwen",
            "name": "Qwen3.5-Plus",
            "description": "通义千问多模态模型",
            "is_multimodal": true
        }
    ],
    "default_model": "deepseek"
}
```

#### 2. 聊天接口修改

**修改** `POST /chat/stream` 的请求参数：

```python
# service/schemas.py
class ChatRequest(BaseModel):
    message: str
    image_paths: Optional[List[str]] = None
    thread_id: Optional[str] = None
    enable_knowledge_base: Optional[bool] = None
    model_id: Optional[str] = None  # 新增：模型选择
```

#### 3. 模型映射配置

扩展 `src/config.py`：

```python
# 扁平化模型列表（用户可见）
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
```

### 二、Agent 模型切换机制

基于 LangChain 官方文档，使用 **Middleware + Runtime Context** 模式实现动态模型切换。

#### 1. Context 定义

新建 `src/agents/context.py`：

```python
from dataclasses import dataclass

@dataclass
class AgentContext:
    """Agent 运行时上下文"""
    model_id: str = "deepseek"  # 用户选择的模型 ID
```

#### 2. 模型选择中间件

新建 `src/agents/middleware/model_selection_middleware.py`：

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from ...config import AVAILABLE_MODELS
from ...utils import ModelManager

# 预初始化所有模型实例（避免每次请求都创建）
MODEL_INSTANCES = {}
for model_id, config in AVAILABLE_MODELS.items():
    manager = ModelManager(provider=config["provider"])
    MODEL_INSTANCES[model_id] = manager.get_chat_model(model=config["model_name"])

@wrap_model_call
def model_selection_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """根据运行时 context 动态选择模型"""
    # 从 context 获取用户选择的 model_id
    model_id = request.runtime.context.model_id if request.runtime else "deepseek"

    # 获取对应的模型实例
    model = MODEL_INSTANCES.get(model_id, MODEL_INSTANCES["deepseek"])

    # 覆盖请求中的模型
    return handler(request.override(model=model))
```

#### 3. Agent 创建时注册中间件

修改 `src/agents/orchestrator_agent_v2.py`：

```python
from langchain.agents import create_agent
from .middleware.model_selection_middleware import model_selection_middleware
from .context import AgentContext

middleware = [
    model_selection_middleware,  # 模型选择中间件（放最前面）
    dynamic_tool_middleware,
    skill_middleware,
    summarization_middleware,
]

agent = create_agent(
    model=model,  # 默认模型
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
    context_schema=AgentContext,  # 注册 Context
)
```

#### 4. Server 端调用时传递 model_id

修改 `service/server.py`：

```python
from src.agents.context import AgentContext

config = {
    "configurable": {
        "thread_id": thread_id,
        "enable_knowledge_base": request.enable_knowledge_base,
    },
    "context": AgentContext(model_id=request.model_id or "deepseek"),  # 传递模型选择
}
```

### 三、前端设计

#### 1. 类型定义

```typescript
// frontend/src/types/model.ts
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

#### 2. 主页面修改

修改 `frontend/src/app/page.tsx`：

```tsx
// 新增状态
const [models, setModels] = useState<Model[]>([]);
const [selectedModelId, setSelectedModelId] = useState<string>("deepseek");

// 启动时获取模型列表
useEffect(() => {
  fetch(`${API_BASE}/models`)
    .then(res => res.json())
    .then(data => {
      setModels(data.models);
      setSelectedModelId(data.default_model);
    });
}, []);

// 发送消息时传递 model_id
body: JSON.stringify({
  message,
  image_paths: imagePaths,
  thread_id: threadId,
  enable_knowledge_base: enableKnowledgeBase,
  model_id: selectedModelId,  // 新增
}),
```

#### 3. UI 布局

```tsx
{/* 输入区域 - 开关行 */}
<div className="flex items-center gap-3 mb-3">
  {/* 知识库开关 */}
  <button
    type="button"
    onClick={() => setEnableKnowledgeBase(!enableKnowledgeBase)}
    className={`px-4 py-2 rounded-full text-sm font-medium transition-all border-2 ...`}
  >
    知识库 {enableKnowledgeBase ? "✓" : ""}
  </button>

  {/* 模型选择器 */}
  <select
    value={selectedModelId}
    onChange={(e) => setSelectedModelId(e.target.value)}
    disabled={loading}
    className="px-4 py-2 rounded-full text-sm font-medium border-2 border-stone-200 bg-white ..."
  >
    {models.map(model => (
      <option key={model.id} value={model.id}>
        {model.name}
      </option>
    ))}
  </select>

  {/* 多模态提示 */}
  {models.find(m => m.id === selectedModelId)?.is_multimodal && (
    <span className="text-xs text-green-600">支持图片识别</span>
  )}
</div>
```

## 文件变更清单

### 后端新增文件

| 文件 | 说明 |
|------|------|
| `src/agents/context.py` | Agent Context 定义 |
| `src/agents/middleware/model_selection_middleware.py` | 模型选择中间件 |

### 后端修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/config.py` | 新增 `AVAILABLE_MODELS` 配置 |
| `service/schemas.py` | `ChatRequest` 新增 `model_id` 字段 |
| `service/server.py` | 新增 `/models` 接口，修改 `/chat/stream` |
| `src/agents/orchestrator_agent_v2.py` | 注册中间件和 Context |

### 前端修改文件

| 文件 | 修改内容 |
|------|---------|
| `frontend/src/app/page.tsx` | 新增模型选择器 UI 和逻辑 |
| `frontend/src/types/model.ts` | 新增类型定义（可选） |

## 注意事项

1. **LangChain/LangGraph 语法**：本设计基于 LangChain 官方文档的 Middleware + Runtime Context 模式
2. **模型实例预初始化**：避免每次请求都创建模型实例，提高性能
3. **向后兼容**：`model_id` 参数可选，不传时使用默认模型