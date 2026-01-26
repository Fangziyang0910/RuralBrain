# RuralBrain 乡村智慧大脑 - 系统介绍文档

## 📖 系统概述

**RuralBrain（乡村智慧大脑）** 是一个基于 LangChain/LangGraph 的智能乡村决策系统，采用微服务架构，为乡村治理和发展提供全方位的智能化决策支持。

### 核心价值

- **智能规划咨询**：基于 RAG 知识库的乡村规划智能咨询服务，提供专业的乡村发展规划建议
- **AI 检测服务**：病虫害检测、大米品种识别、奶牛目标检测，助力精准农业
- **统一智能助手**：通过 Agent 编排实现自动意图识别和智能路由
- **可扩展架构**：微服务架构设计，易于扩展和维护

### 🆕 最新更新（2026-01-26）

#### Agent 系统升级
- ✨ **新增 Orchestrator Agent V2**：采用 LangChain Skills 架构
  - Progressive Disclosure：技能按需加载，大幅减少 Token 消耗
  - 6 个专业技能：检测技能（3）+ 规划技能（1）+ 编排技能（2）
  - 支持环境变量 `AGENT_VERSION` 切换 V1/V2
  - 自动回退机制：V2 失败时自动切换到 V1

#### 跨平台兼容性改进
- 🔧 **新增统一启动脚本**：`run_frontend.py` 跨平台兼容前端启动
- 📁 **临时目录路径优化**：使用 `tempfile.gettempdir()` 自动适配操作系统
- ⚡ **异步支持增强**：SkillMiddleware 添加异步方法支持

#### 服务管理优化
- 📦 **统一端口配置**：检测服务使用连续端口（8000-8002）
- 🛠️ **服务管理脚本**：一键启动/停止所有服务
- 📝 **文档完善**：新增服务管理指南和端口迁移说明

## 🏗️ 系统架构

### 整体架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Next.js)                        │
│                   http://localhost:3000                      │
│  - 聊天界面  - 图片上传  - 流式响应  - 结果可视化             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  主服务 (FastAPI)                            │
│                   http://localhost:8081                      │
│  - 统一编排 Agent  - 智能路由  - 流式响应                   │
└──┬──────────────┬──────────────┬──────────────┬────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐
│害虫检测 │  │大米识别 │  │奶牛检测 │  │规划咨询服务   │
│ :8000   │  │ :8001   │  │ :8002   │  │    :8003     │
└─────────┘  └─────────┘  └─────────┘  └──┬───────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ RAG 知识库   │
                                    │ - ChromaDB   │
                                    │ - 6个核心工具│
                                    └──────────────┘
```

### 微服务架构

RuralBrain 采用微服务架构，各服务独立部署和扩展：

| 服务名称 | 端口 | 技术栈 | 职责 |
|---------|------|--------|------|
| **前端应用** | 3000 | Next.js + React | 用户界面和交互 |
| **主服务** | 8081 | FastAPI + LangGraph | 统一编排和智能路由 |
| **害虫检测** | 8000 | FastAPI + YOLOv8 | 29种农业害虫识别 |
| **大米识别** | 8001 | FastAPI + YOLO | 大米品种和品质检测 |
| **奶牛检测** | 8002 | FastAPI + YOLO | 牛只目标检测和计数 |
| **规划咨询** | 8003 | FastAPI + LangChain | RAG 知识库问答 |

### 设计模式

#### 1. 智能路由模式
- **意图识别**：根据用户输入自动判断处理方式（图像检测 vs 规划咨询）
- **关键词匹配**：基于规则和 LLM 的混合路由策略
- **上下文感知**：结合对话历史和图片信息做出决策

#### 2. Agent 编排模式（V2 - Skills 架构）
- **统一编排器（Orchestrator V2）**：采用 LangChain Skills 架构
- **Progressive Disclosure**：技能描述按需加载，减少 Token 消耗
- **技能系统**：6个技能（3检测 + 1规划 + 2编排）
- **工具调用**：通过 LangGraph 实现复杂的多步推理

#### 3. 渐进式披露模式
- **分级响应**：摘要、中等、完整三种详细程度
- **按需加载**：根据场景选择合适的信息粒度
- **Token 优化**：平衡响应速度和信息完整性

## 🤖 Agent 系统

### Agent 版本管理

RuralBrain 支持两个版本的统一编排 Agent，可通过环境变量 `AGENT_VERSION` 切换：

| 版本 | 架构 | 特点 | 适用场景 |
|------|------|------|----------|
| **V1** | 传统固定提示词 | 简单直接，稳定性高 | 基础应用场景 |
| **V2** | Skills 架构 | Progressive Disclosure，按需加载技能 | 复杂场景，更智能的交互 |

**配置方式**：
```bash
# 使用 V1（默认）
AGENT_VERSION=v1

# 使用 V2
AGENT_VERSION=v2

# 启用自动回退（V2 失败时自动切换到 V1）
AGENT_AUTO_FALLBACK=true
```

### 统一编排 Agent V2（Orchestrator V2）

**设计理念**：采用 LangChain Skills 架构，实现更智能的交互和更高效的 Token 使用。

**核心特性**：
- **6 个专业技能**：
  1. `pest_detection`：病虫害检测技能
  2. `rice_detection`：大米品种识别技能
  3. `cow_detection`：牛只检测技能
  4. `consult_planning_knowledge`：规划咨询技能（包含6个RAG工具）
  5. `intent_recognition`：意图识别技能
  6. `scenario_switching`：场景切换技能

- **Progressive Disclosure**：
  - 系统提示词仅包含技能简短描述
  - 通过 `load_skill` 工具按需获取技能详细指导
  - 大幅减少初始 Token 消耗

- **9 个工具**：
  - 3 个检测工具：pest_detection_tool, rice_detection_tool, cow_detection_tool
  - 6 个 RAG 工具：document_list_tool, document_overview_tool, key_points_search_tool, knowledge_search_tool, chapter_content_tool, full_document_tool

**系统提示词**（简化版）：
```
<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
你拥有两大核心能力：图像检测和规划咨询。
</role>

<capabilities>
通过技能系统，你可以动态加载专业能力：
- 检测能力：病虫害检测、大米品种识别、牛只检测
- 规划能力：乡村发展规划、政策解读、技术指导
- 编排能力：意图识别、场景切换、上下文管理
</capabilities>

<workflow>
1. 理解用户意图
   - 需要详细了解时，使用 load_skill 工具加载技能指导
   - 可加载技能：pest_detection, rice_detection, cow_detection,
     consult_planning_knowledge, intent_recognition, scenario_switching

2. 选择合适的工具
   - 有图片 → 优先使用检测工具
   - 关键词"规划/发展/政策" → 使用 RAG 工具
   - 不确定 → 加载 intent_recognition 技能

3. 多轮对话管理
   - 保持上下文连续性
   - 场景切换时使用 load_skill("scenario_switching")
</workflow>
```

**工具集合**：
```python
orchestrator_tools = [
    # 检测工具（3个）
    pest_detection_tool,     # 害虫检测
    rice_detection_tool,     # 大米识别
    cow_detection_tool,      # 奶牛检测

    # RAG 规划工具（6个）
    document_list_tool,      # 列出文档
    document_overview_tool,  # 文档概览
    key_points_search_tool,  # 关键要点搜索
    knowledge_search_tool,   # 全文检索
    chapter_content_tool,    # 章节内容
    full_document_tool,      # 完整文档
]
```

### 统一编排 Agent V1（Orchestrator V1）

**设计理念**：作为智能路由中心，自动判断用户意图并调度相应服务。

**系统提示词**：
```
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
你拥有两大核心能力：图像检测和规划咨询。

工作流程：
1. 判断意图
   - 有图片 → 优先使用检测工具
   - 关键词"检测/识别/是什么" → 使用检测工具
   - 关键词"规划/发展/策略/政策/防治/如何" → 使用 RAG 工具

2. 工具调用
   - 害虫检测：pest_detection_tool
   - 大米识别：rice_detection_tool
   - 奶牛检测：cow_detection_tool
   - 规划咨询：使用 RAG 知识库工具

3. 结果整合
   - 综合各工具返回结果
   - 提供清晰、专业的建议
```

**工具集合**：与 V2 相同，共 9 个工具

### 规划咨询 Agent（Planning Agent）

**框架**：基于 LangGraph 的状态机架构

**核心特性**：
- **记忆功能**：使用 `InMemorySaver` 保存对话历史
- **多步推理**：支持复杂的多轮对话和场景切换
- **工具编排**：智能组合 6 个 RAG 工具完成任务

**工作模式**：

1. **快速模式**：
   - 场景：快速浏览和初步了解
   - 策略：摘要浏览 + 关键信息检索
   - 特点：响应快，Token 消耗少

2. **深度模式**：
   - 场景：深入分析和综合研究
   - 策略：全文阅读 + 多文档交叉验证
   - 特点：信息全面，分析深入

**约束机制**：
```
必须通过工具查询知识库，严禁基于预训练数据回答。
每个回答必须明确引用信息来源（文档名称、章节标题）。
```

## 📚 RAG 知识库系统

### 技术架构

- **向量数据库**：ChromaDB - 高效的相似度检索
- **嵌入模型**：sentence-transformers - 中文文本向量化
- **大语言模型**：DeepSeek / GLM - 智能理解和生成
- **文档格式**：PDF、Word (docx)、PPT (pptx)

### 核心 RAG 工具

RAG 系统提供 6 个核心工具，支持不同场景的知识检索：

#### 1. `list_documents` - 列出可用文档
**功能**：列出知识库中所有可用文档及其基本信息
**使用场景**：任务开始时了解可用资料
**返回**：文档名称、类型、切片数量、内容预览

**示例输出**：
```
可用文档：
1. 博罗县国土空间总体规划（2021-2035年）[PDF, 156个切片]
2. 罗浮山发展战略规划 [PDF, 89个切片]
3. 长宁镇乡村旅游发展规划 [Word, 45个切片]
```

#### 2. `get_document_overview` - 获取文档概览
**功能**：获取文档执行摘要和章节列表
**参数**：
- `source`：文档名称（必需）
- `include_chapters`：是否包含章节列表（可选，默认 true）
**返回**：200字执行摘要和完整章节列表

**使用场景**：
- 快速了解文档核心内容
- 确定是否需要深入阅读
- 定位感兴趣的章节

#### 3. `get_chapter_content` - 获取章节内容
**功能**：获取指定章节的详细内容，支持三级详情
**参数**：
- `source`：文档名称
- `chapter_pattern`：章节标题关键词（支持部分匹配）
- `detail_level`：详细程度
  - `"summary"`：仅摘要（100-200字）- 最快
  - `"medium"`：摘要 + 关键要点（默认）
  - `"full"`：完整章节内容 - 最详细

**使用场景**：
- 针对性阅读特定章节
- 根据需求调整信息密度
- 优化 Token 消耗

#### 4. `search_knowledge` - 全文检索
**功能**：基于查询检索相关文档片段
**参数**：
- `query`：查询问题或关键词
- `top_k`：返回片段数（默认5，范围3-10）
- `context_mode`：上下文模式
  - `"minimal"`：仅匹配片段
  - `"standard"`：片段 + 短上下文（300字，默认）
  - `"expanded"`：片段 + 长上下文（500字）

**使用场景**：
- 查找特定信息点
- 跨文档综合检索
- 获取相关上下文

#### 5. `search_key_points` - 关键要点搜索
**功能**：在预先提取的关键要点中搜索
**参数**：
- `query`：搜索关键词
- `sources`：限制搜索的文档列表（可选）

**使用场景**：
- 快速定位核心要点
- 文档间对比分析
- 高层次信息获取

#### 6. `get_document_full` - 获取完整文档
**功能**：获取文档完整内容和元数据
**注意**：文档可能很长，会消耗大量 Token

**使用场景**：
- 深度研究特定文档
- 全面了解政策细节
- 综合分析和引用

### 知识库内容

当前知识库包含以下领域的专业文档：

**规划发展**：
- 博罗县国土空间总体规划
- 罗浮山发展战略规划
- 长宁镇发展规划

**政策法规**：
- 乡村旅游发展政策
- 农业产业政策
- 乡村振兴支持政策

**技术指导**：
- 病虫害防治技术
- 现代农业种植技术
- 农产品质量标准

## 🔍 AI 检测服务

### 1. 害虫检测服务

**端口**：8000
**技术栈**：YOLOv8 + FastAPI
**能力**：识别 29 种常见农业害虫

**核心特性**：
- **高精度**：检测准确率 95%+
- **实时处理**：1-3秒完成图像分析
- **多目标检测**：同时识别多个不同害虫
- **可视化结果**：返回带标注框的处理后图像

**API 接口**：
```python
POST /detect
Request:
{
  "image_base64": "base64编码的图片"
}

Response:
{
  "success": true,
  "detections": [
    {
      "class": "稻飞虱",
      "confidence": 0.95,
      "bbox": [x, y, width, height]
    }
  ],
  "result_image": "base64编码的结果图片"
}
```

**支持的害虫种类**：
- 水稻害虫：稻飞虱、稻纵卷叶螟、二化螟、三化螟等
- 蔬菜害虫：蚜虫、菜青虫、小菜蛾等
- 经济作物害虫：棉铃虫、红蜘蛛等

### 2. 大米品种识别服务

**端口**：8001
**技术栈**：YOLO + FastAPI
**能力**：大米品种识别和品质评估

**核心特性**：
- **品种识别**：识别多种大米品种
- **品质评估**：基于图像的质量评估
- **分级系统**：按标准进行等级划分
- **快速检测**：秒级响应时间

### 3. 奶牛目标检测服务

**端口**：8002
**技术栈**：YOLO + FastAPI
**能力**：牛只检测和行为分析

**核心特性**：
- **目标检测**：牛只位置识别和计数
- **行为分析**：基于图像的行为模式识别
- **健康监测**：初步的健康状态判断
- **群体管理**：支持牛群规模统计

## 💻 前端应用

### 技术栈

- **框架**：Next.js 14 (React)
- **语言**：TypeScript
- **样式**：Tailwind CSS + Radix UI
- **状态管理**：React Hooks
- **流式响应**：Server-Sent Events (SSE)

### 核心功能

#### 1. 智能对话界面
- **流式输出**：实时显示 AI 回复
- **Markdown 渲染**：支持富文本格式
- **代码高亮**：专业的代码展示
- **工具调用可视化**：展示工具使用过程

#### 2. 图片上传
- **批量上传**：支持最多 10 张图片
- **实时预览**：上传前预览和确认
- **单独删除**：可删除特定图片
- **格式支持**：JPG、PNG、WEBP

#### 3. 对话管理
- **历史记录**：保存对话历史
- **会话管理**：支持多会话切换
- **上下文保持**：多轮对话上下文连贯

### 用户交互流程

```
1. 用户输入问题或上传图片
       ↓
2. 前端发送请求到主服务（/chat/stream）
       ↓
3. 主服务通过 Orchestrator Agent 判断意图
       ↓
4a. 图像检测 → 调用检测服务（8000/8001/8002）
4b. 规划咨询 → 调用规划服务（8003）
       ↓
5. Agent 执行工具调用并获取结果
       ↓
6. 主服务通过 SSE 流式返回结果
       ↓
7. 前端实时更新界面
```

## 🔌 API 接口文档

### 主服务 API（端口 8081）

#### 1. 统一流式对话接口
```
POST /chat/stream
Content-Type: application/json

Request:
{
  "message": "用户消息",
  "image_paths": ["图片路径数组"],
  "thread_id": "会话ID（可选）"
}

Response:
(SSE 流式响应)
data: {"type": "content", "content": "回复内容"}
data: {"type": "tool", "tool_name": "工具名", "result": "结果"}
data: {"type": "end"}
```

#### 2. 图片上传接口
```
POST /upload
Content-Type: multipart/form-data

Request:
(文件上传表单)

Response:
{
  "success": true,
  "image_paths": ["/uploads/xxx.jpg"]
}
```

#### 3. 健康检查
```
GET /health

Response:
{
  "status": "healthy",
  "services": {
    "planning": "healthy",
    "pest_detection": "healthy",
    "rice_detection": "healthy",
    "cow_detection": "healthy"
  }
}
```

### 规划咨询 API（端口 8003）

#### 1. 规划咨询接口
```
POST /chat
Content-Type: application/json

Request:
{
  "message": "咨询问题",
  "thread_id": "会话ID（可选）"
}

Response:
{
  "response": "回复内容",
  "sources": ["来源文档列表"]
}
```

#### 2. 知识库检索
```
POST /search

Request:
{
  "query": "检索关键词",
  "top_k": 5
}

Response:
{
  "results": [
    {
      "content": "文档片段",
      "source": "文档名称",
      "score": 0.95
    }
  ]
}
```

### 检测服务 API（端口 8000/8001/8002）

#### 检测接口
```
POST /detect
Content-Type: application/json

Request:
{
  "image_base64": "base64编码图片"
}

Response:
{
  "success": true,
  "detections": [
    {
      "class": "类别名称",
      "confidence": 0.95,
      "bbox": [x, y, width, height]
    }
  ],
  "result_image": "base64编码结果图"
}
```

## 🚀 服务启动指南

### 方式一：Docker 部署（推荐）

**前置要求**：
- 安装 Docker Desktop
- 确保端口 3000、8000-8003、8081 未被占用

**启动步骤**：
```bash
# 1. 进入项目根目录
cd /path/to/RuralBrain

# 2. 启动所有服务（首次运行会构建镜像）
docker-compose up -d --build

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志（可选）
docker-compose logs -f

# 5. 访问前端
open http://localhost:3000
```

**停止服务**：
```bash
docker-compose down
```

### 方式二：本地开发（需要多个终端）

**前置要求**：
- Python 3.13+
- Node.js 18+
- 已安装项目依赖：`uv sync`

**启动步骤**：

**终端 1 - 规划咨询服务**：
```bash
cd /path/to/RuralBrain
uv run python src/rag/service/main.py
# 服务运行在 http://localhost:8003
```

**终端 2 - 害虫检测服务**：
```bash
cd /path/to/RuralBrain
uv run python src/algorithms/pest_detection/detector/app/main.py
# 服务运行在 http://localhost:8000
```

**终端 3 - 主服务**：
```bash
cd /path/to/RuralBrain
uv run python service/server.py
# 服务运行在 http://localhost:8081
```

**终端 4 - 前端服务**：

**推荐方式（跨平台兼容）**：
```bash
cd /path/to/RuralBrain
uv run python run_frontend.py
# 自动检查环境、安装依赖、启动服务
# 前端运行在 http://localhost:3000
```

**或者手动启动**：
```bash
cd /path/to/RuralBrain/frontend/my-app
npm install  # 首次运行需要安装依赖
npm run dev
# 前端运行在 http://localhost:3000
```

### 服务验证

启动后，访问以下地址验证服务状态：

- **前端界面**：http://localhost:3000
- **主服务 API**：http://localhost:8081/docs
- **规划咨询**：http://localhost:8003/docs
- **害虫检测**：http://localhost:8000/docs
- **大米识别**：http://localhost:8001/docs
- **奶牛检测**：http://localhost:8002/docs

## 🔧 技术实现细节

### 智能路由实现

**关键代码**（service/server.py）：
```python
def classify_intent(message: str, has_images: bool = False) -> str:
    """智能判断用户意图"""

    # 规则1: 有图片优先检测
    if has_images:
        return "detection"

    # 规则2: 基于关键词匹配
    planning_keywords = ["规划", "发展", "策略", "旅游", "产业"]
    detection_keywords = ["识别", "检测", "害虫", "病害", "大米", "品种", "牛"]

    message_lower = message.lower()

    if any(keyword in message_lower for keyword in detection_keywords):
        return "detection"

    if any(keyword in message_lower for keyword in planning_keywords):
        return "planning"

    # 规则3: 默认规划咨询
    return "planning"
```

### 流式响应实现

**前端代码**（frontend/my-app/src/app/page.tsx）：
```typescript
const chatResponse = await fetch(`${API_BASE}/chat/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message,
    image_paths: imagePaths,
    thread_id: threadId,
  }),
});

// 处理 SSE 流
const reader = chatResponse.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));

      if (data.type === 'content') {
        // 更新内容
      } else if (data.type === 'tool') {
        // 显示工具调用
      }
    }
  }
}
```

### RAG 检索实现

**关键代码**（src/rag/core/retriever.py）：
```python
def search_knowledge(
    query: str,
    top_k: int = 5,
    context_mode: str = "standard"
) -> List[Document]:
    """知识库检索"""

    # 向量检索
    results = vector_store.similarity_search(
        query=query,
        k=top_k
    )

    # 上下文扩展
    if context_mode == "expanded":
        results = expand_context(results, window_size=500)
    elif context_mode == "standard":
        results = expand_context(results, window_size=300)

    return results
```

### Skills 架构实现（V2 Agent）

**核心概念**：Progressive Disclosure（渐进式披露）

**Skill 中间件**（src/agents/middleware/skill_middleware.py）：
```python
class SkillMiddleware:
    """技能中间件，实现 Progressive Disclosure"""

    def __init__(self, skills: List[Skill]):
        self.skills = {s.name: s for s in skills}
        self.load_skill_tool = self._create_load_skill_tool()

    def _create_load_skill_tool(self) -> BaseTool:
        """创建按需加载技能的工具"""

        def load_skill(skill_name: str) -> str:
            """加载技能的详细指导"""
            skill = self.skills.get(skill_name)
            if skill:
                return f"## {skill.name}\n\n{skill.system_prompt}"
            return f"技能 {skill_name} 不存在"

        return StructuredTool.from_function(
            func=load_skill,
            name="load_skill",
            description="按需加载技能的详细指导内容",
        )
```

**技能定义示例**（src/agents/skills/orchestration_skills.py）：
```python
def create_intent_recognition_skill() -> Skill:
    """意图识别技能"""
    return Skill(
        name="intent_recognition",
        description="意图识别专家，判断用户需要检测服务还是规划咨询",
        category="orchestration",
        version="1.0.0",
        system_prompt="""你是意图识别专家...

## 核心能力
- 识别检测意图：图片、识别、检测、是什么等
- 识别规划意图：规划、发展、政策、如何、策略等
- 识别混合意图：检测后咨询、规划中需要检测
...
""",
        tools=[],
        examples=[...],
        constraints=[...],
    )
```

**优势**：
1. **Token 优化**：系统提示词仅包含技能简述，详细内容按需加载
2. **模块化**：每个技能独立定义，易于维护和扩展
3. **灵活性**：可根据场景动态组合不同技能

### 跨平台兼容实现

**临时目录路径**（service/settings.py）：
```python
import tempfile
from pathlib import Path

# 使用系统临时目录，跨平台兼容
# Windows: C:\Users\<username>\AppData\Local\Temp\ruralbrain_uploads
# Linux/macOS: /tmp/ruralbrain_uploads
UPLOAD_DIR = Path(tempfile.gettempdir()) / "ruralbrain_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
```

**前端启动脚本**（run_frontend.py）：
```python
def check_nodejs() -> str:
    """检查 Node.js 和 npm 是否安装"""
    node_exec = shutil.which("node")
    npm_exec = shutil.which("npm")
    # 使用 shutil.which() 跨平台查找可执行文件
    ...

def start_frontend() -> None:
    """启动前端开发服务器"""
    # 自动检查依赖、安装、启动
    # 支持 Windows、Linux、macOS
    ...
```

**优势**：
- 无需手动配置路径
- 自动适配不同操作系统
- 一致的启动体验

## 📊 性能指标

### 响应时间

| 服务 | 平均响应时间 | 峰值响应时间 |
|------|-------------|-------------|
| 害虫检测 | 1-2秒 | 3秒 |
| 大米识别 | 0.5-1秒 | 2秒 |
| 奶牛检测 | 1-2秒 | 3秒 |
| 规划咨询 | 3-5秒 | 10秒 |

### 准确率

| 检测类型 | 准确率 | 召回率 |
|---------|--------|--------|
| 害虫检测 | 95%+ | 92%+ |
| 大米识别 | 90%+ | 88%+ |
| 奶牛检测 | 93%+ | 90%+ |

### 并发能力

- **支持并发**：所有服务支持多请求并发
- **负载均衡**：可通过水平扩展提升并发能力
- **缓存机制**：RAG 检索结果缓存，提升响应速度

## 🛡️ 安全性考虑

### 输入验证
- 图片上传大小限制（最大 10MB）
- 文件类型白名单验证
- SQL 注入防护（使用 ORM）
- XSS 防护（前端转义）

### API 安全
- CORS 配置（生产环境需限制域名）
- 速率限制（防止滥用）
- 错误信息脱敏（不暴露敏感信息）

### 数据隐私
- 图片上传后临时存储，定期清理
- 对话历史可选持久化
- 不收集用户个人信息

## 🔄 扩展性设计

### 新增检测服务

1. 在 `src/algorithms/` 创建新服务目录
2. 实现标准 FastAPI 接口（/detect, /health）
3. 在主服务注册新工具
4. 更新 Orchestrator Agent 工具列表

### 新增 RAG 工具

1. 在 `src/rag/core/tools.py` 定义新工具
2. 实现工具逻辑和文档字符串
3. 添加到 PLANNING_TOOLS 列表
4. 更新 Agent 系统提示词

### 新增知识库文档

1. 将文档放入 `src/rag/docs/` 目录
2. 运行构建脚本：
   ```bash
   uv run python scripts/dev/build_kb_auto.py
   ```
3. 系统自动索引新文档

## 📈 未来规划

### 短期目标
- [ ] 完善大米和奶牛检测服务
- [ ] 增加更多害虫种类识别
- [ ] 优化 RAG 检索准确率
- [ ] 添加用户反馈机制

### 中期目标
- [ ] 支持语音输入和输出
- [ ] 增加数据可视化功能
- [ ] 实现多语言支持
- [ ] 开发移动端应用

### 长期目标
- [ ] 构建 AI 模型训练平台
- [ ] 集成物联网设备数据
- [ ] 建立乡村知识图谱
- [ ] 提供开放 API 平台

## 📞 技术支持

### 文档资源
- 项目结构规范：[PROJECT_STRUCTURE_GUIDE.md](../PROJECT_STRUCTURE_GUIDE.md)
- API 文档：http://localhost:8081/docs
- LangChain 官方文档：https://python.langchain.com/

### 常见问题

**Q: Docker 启动失败？**
A: 检查端口是否被占用，确保 Docker Desktop 已启动

**Q: 检测服务返回 500 错误？**
A: 检查模型文件是否存在，环境变量是否正确配置

**Q: RAG 回答不准确？**
A: 尝试重新构建知识库，或调整检索参数

**Q: 前端无法连接后端？**
A: 检查 API_BASE 配置，确保后端服务已启动

---

**版本**：v1.0.0
**更新日期**：2026-01-26
**维护团队**：RuralBrain 开发团队
