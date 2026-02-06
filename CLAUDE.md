# CLAUDE.md

> **为 Claude Code 设计的项目导航文档**
> 本文档帮助 Claude Code 快速理解 RuralBrain 项目架构、关键约束和开发规范。

---

## 项目定位

**RuralBrain（乡村智慧大脑）** 是一个基于 **LangChain/LangGraph** 的乡村智慧决策系统，采用微服务架构。

**核心价值**：为乡村治理和发展提供智能化决策支持

**主要功能**：
- 🤖 **V2 Agent 系统**：基于 Skills 架构的智能体，支持多模态交互
- 🔍 **智能检测服务**：病虫害、大米品种、奶牛目标检测（统一网关）
- 📚 **RAG 规划咨询**：基于知识库的乡村规划智能问答
- 🎯 **智能定价分析**：农产品定价因素分析和建议

---

## 系统架构与逻辑关系

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户请求层                          │
│  (文本输入 + 图片上传)                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  前端 (Next.js)                         │
│              http://localhost:3001                     │
│  - 多模态输入（文本 + 图片）                             │
│  - 流式对话展示                                         │
│  - 工具调用可视化                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            后端主服务 (FastAPI)                        │
│             http://localhost:8081                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │  意图识别 (Intent Router)                         │ │
│  │   ├─ 有图片 + 检测关键词 → 检测流程               │ │
│  │   ├─ 规划关键词 → 规划咨询流程                    │ │
│  │   └─ 默认 → 通用对话                               │ │
│  └───────────────────────────────────────────────────┘ │
│                     │                                     │
│  ┌───────────────────────────────────────────────────┐ │
│  │      Orchestrator Agent V2 (LangGraph)           │ │
│  │  - Skills 架构（渐进式披露）                      │ │
│  │  - 工具系统（检测、定价、营销等）                   │ │
│  │  - 中间件（SkillMiddleware、ToolSelector）        │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌──────────────┴──────────────┐
        │                              │
        ▼                              ▼
┌──────────────────┐        ┌──────────────────┐
│  检测服务网关      │        │  规划咨询服务    │
│  :8001            │        │  :8003           │
│  (统一网关)       │        │  (RAG 知识库)    │
├──────────────────┤        ├──────────────────┤
│ • /detection/pest  │        │  • 7 个检索工具    │
│ • /detection/rice  │        │  • ChromaDB        │
│ • /detection/cow   │        │  • 向量检索        │
└──────────────────┘        └──────────────────┘
```

### 核心逻辑流程

#### 1. 用户请求 → 前端
- 用户输入文本 + 上传图片
- 前端发送 POST 请求到后端 `/chat` 端点
- 使用 SSE 流式接收响应

#### 2. 后端 → 意图识别
- 根据请求内容判断用户意图：
  - **有图片** → 检测流程
  - **规划关键词**（规划、发展、旅游等）→ 规划咨询流程
  - **默认** → 通用对话

#### 3. Agent V2 处理流程

**检测流程**（有图片）：
```
用户上传图片
    ↓
Orchestrator Agent V2 判断需要检测能力
    ↓
调用 load_skill("pest_detection") 获取完整指导
    ↓
调用 pest_detection_tool → 通过后端转发 → 检测服务网关 (8001)
    ↓
检测服务网关路由到具体检测服务
    ↓
YOLO 模型推理，返回检测结果
    ↓
Agent 基于结果生成专业建议（防治方案、危害分析等）
```

**规划咨询流程**（规划关键词）：
```
用户提出规划相关问题
    ↓
后端识别到规划关键词，转发到规划服务 (8003)
    ↓
Planning Agent 使用 RAG 工具查询知识库
    ↓
- 快速模式：摘要浏览 + 关键信息检索
- 深度模式：全文阅读 + 综合分析
    ↓
返回基于知识库的专业建议
```

**通用对话流程**（默认）：
```
用户提出一般性问题
    ↓
Orchestrator Agent V2 直接基于预训练知识回答
    ↓
可能调用定价工具、营销工具等辅助分析
    ↓
返回智能回复
```

#### 4. 工具调用链路

```
Agent 调用工具
    ↓
src/agents/tools/<tool>.py
    ↓
HTTP 请求到外部服务
    ↓
- 检测工具 → http://localhost:8001/detection/<type>/predict
- 定价工具 → 内置逻辑，不依赖外部服务
- 营销工具 → 内置逻辑，不依赖外部服务
```

---

## 目录结构（最新）

### 核心代码组织

```
RuralBrain/
│
├── service/                          # 【主服务】FastAPI 后端
│   ├── server.py                     # 主服务器入口（Agent 编排）
│   ├── settings.py                   # 服务配置（端口、CORS 等）
│   └── schemas.py                    # 请求/响应数据模型
│
├── src/                              # 【核心业务逻辑】
│   │
│   ├── agents/                        # Agent 系统（V2 Skills 架构）
│   │   ├── orchestrator_agent_v2.py  # ⭐ 统一编排 Agent
│   │   ├── skills/                    # Skills 架构模块
│   │   │   ├── detection_skills.py     # 检测技能
│   │   │   ├── planning_skills.py      # 规划技能
│   │   │   ├── pricing_skills.py       # 定价技能
│   │   │   └── orchestration_skills.py  # 编排技能
│   │   ├── tools/                     # Agent 工具集
│   │   │   ├── pest_detection_tool.py   # 病虫害检测
│   │   │   ├── rice_detection_tool.py   # 大米识别
│   │   │   ├── cow_detection_tool.py    # 奶牛检测
│   │   │   ├── pricing_tool.py          # 智能定价
│   │   │   ├── marketing_tool.py        # 营销策略
│   │   │   └── farm_inspection_tool.py  # 农场检查
│   │   └── middleware/                 # 中间件系统
│   │       ├── skill_middleware.py      # 技能中间件
│   │       └── tool_selector_middleware.py  # 工具选择中间件
│   │
│   ├── algorithms/                    # 【检测算法服务】
│   │   ├── api/                        # ⭐ 统一 API 网关（端口 8001）
│   │   │   └── main.py                 # FastAPI 检测服务网关
│   │   └── detection/                 # 检测算法实现
│   │       ├── pest_service.py          # 病虫害检测服务
│   │       ├── rice_service.py          # 大米品种识别服务
│   │       ├── cow_service.py           # 奶牛检测服务
│   │       └── models/                  # YOLO 模型文件
│   │
│   ├── rag/                           # 【RAG 知识库系统】
│   │   ├── core/                       # RAG 核心功能
│   │   │   ├── tools.py                # ⭐ 7 个核心检索工具
│   │   │   ├── context_manager.py      # 上下文管理
│   │   │   ├── cache.py                # 向量缓存
│   │   │   └── summarization.py        # 文档摘要
│   │   └── service/                    # RAG 服务实现
│   │       ├── main.py                 # FastAPI 服务入口（端口 8003）
│   │       └── config.py               # 服务配置
│   │
│   └── config.py                       # 全局配置（模型管理等）
│
├── frontend/                         # 【前端应用】Next.js
│   ├── src/
│   │   ├── app/                         # Next.js App Router
│   │   │   ├── api/                     # API 路由
│   │   │   └── page.tsx                 # 主页面
│   │   └── components/                  # React 组件
│   ├── package.json                     # 前端依赖
│   └── tailwind.config.ts               # Tailwind 配置
│
├── docker/                            # 【Docker 配置】
│   ├── docker-compose.yml              # 生产环境编排
│   └── docker-compose.dev.yml          # 开发环境（热重载）
│
├── tests/                             # 【测试代码】
├── scripts/                           # 【脚本工具】
│   ├── dev/                            # 开发脚本
│   │   ├── start_all_services.sh       # ⭐ 一键启动所有服务
│   │   ├── stop_all_services.sh        # 停止所有服务
│   │   └── check_services.sh          # 检查服务状态
│   └── deploy/                         # 部署脚本
│
└── docs/                              # 【项目文档】
    ├── README.md                       # 文档导航中心
    ├── CHANGELOG.md                    # 项目变更日志
    ├── overview/                       # 项目概览
    ├── guides/                         # 操作指南
    └── architecture/                   # 架构文档
```

### 关键文件说明

| 文件 | 作用 | 重要性 |
|------|------|--------|
| `service/server.py` | 后端主服务入口，Agent 编排 | ⭐⭐⭐ |
| `src/agents/orchestrator_agent_v2.py` | V2 统一编排 Agent（Skills 架构） | ⭐⭐⭐ |
| `src/algorithms/api/main.py` | 检测服务统一网关 | ⭐⭐⭐ |
| `src/rag/core/tools.py` | RAG 知识库的 7 个检索工具 | ⭐⭐⭐ |
| `src/config.py` | 全局配置（模型管理等） | ⭐⭐ |
| `run_server.py` | 后端启动脚本 | ⭐⭐ |
| `run_frontend.py` | 前端启动脚本 | ⭐⭐ |

---

## 服务端口分配（最新）

| 服务 | 端口 | 配置位置 | 说明 |
|------|------|----------|------|
| **前端** | 3000 | `frontend/package.json` | Next.js 应用 |
| **后端主服务** | 8081 | `service/settings.py` + `.env` | FastAPI + Orchestrator Agent V2 |
| **检测服务网关** | 8001 | `src/algorithms/api/main.py` | ⭐ 统一检测服务（所有检测类型） |
| **规划咨询服务** | 8003 | `src/rag/service/main.py` | RAG 知识库服务 |

### 检测服务路由

所有检测服务整合在统一网关（8001）：

```
http://localhost:8001
├── /detection/pest/predict    # 病虫害检测
├── /detection/rice/predict    # 大米品种识别
├── /detection/cow/predict     # 奶牛检测
└── /health                     # 健康检查
```

**重要**：检测服务不再有独立端口，全部通过网关 8001 访问。

---

## 常用命令（最新）

### 环境管理

```bash
# 必须使用 uv 运行 Python 代码
uv sync                              # 安装依赖
uv run python <script>              # 运行脚本
uv run pytest                       # 运行测试
```

### 服务启动

#### 开发环境（强制使用 Docker）

**所有开发工作必须使用 Docker 热重载模式进行**

```bash
cd docker

# 构建并启动所有服务（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

**热重载工作流程**：
1. 启动服务后，修改本地代码文件
2. 容器自动检测变更并重启服务（1-3秒）
3. 通过浏览器或 API 测试更改

详细说明请参阅：[Docker 使用指南](docker/README.md)

#### 生产环境部署

```bash
cd docker

# 启动生产环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 知识库构建

```bash
# 构建或更新 RAG 知识库
uv run python scripts/dev/build_kb_auto.py
```

---

## 核心约束与规范

### 1. Python 环境管理 ⭐⭐⭐

```bash
# ✅ 正确：使用 uv
uv run python script.py

# ❌ 错误：直接使用 python
python script.py
pip install package
```

**原因**：项目使用 uv 管理依赖，必须使用 uv 运行 Python 代码。

### 2. LangChain/LangGraph 语法 ⭐⭐⭐

**重要**：涉及 LangChain/LangGraph 语法问题时：
- **必须**调用 `docs-langchain` MCP 获取官方文档
- **不得**仅凭预训练知识进行代码更改

### 3. 工作流程

```
接受任务 → 理解需求 → 拆解步骤 → 征求同意 → 执行修改 → 验证结果
```

- 对于所有任务，先逐步思考并拆解成一步一步的执行任务
- 给出修改计划，征求用户同意后再进行代码更改

### 4. 代码风格

- 遵守 Python 代码设计哲学（The Zen of Python）
- 使用 `uv run python` 运行所有 Python 脚本
- 避免过度工程化，保持简单实用

### 5. 文件移动后的路径引用修复

当移动文件到新位置时：
- **必须**同时检查并修复文件内部的路径引用
- 使用绝对导入优先于相对导入
- 验证所有导入路径的正确性

### 6. 库/API 文档查询

当需要库/API 文档、代码生成、设置或配置步骤时：
- **始终**使用 `context7` mcp 获取最新的官方文档和最佳实践
- 优先通过 context7 获取权威信息

### 7. 前端开发

- **充分利用** playwright mcp 工具进行错误排查和效果获取
- 使用 playwright 进行页面截图、控制台日志检查、元素交互验证

---

## Agent 系统（V2 Skills 架构）

### 架构特点

- **渐进式披露（Progressive Disclosure）**：初始只提供技能描述，按需加载完整内容
- **模块化技能配置**：每个技能专注一个特定领域
- **中间件系统**：SkillMiddleware、ToolSelectorMiddleware

### 工具系统

**检测工具**（通过网关调用）：
- `pest_detection_tool` - 病虫害检测
- `rice_detection_tool` - 大米品种识别
- `cow_detection_tool` - 奶牛检测

**内置工具**：
- `pricing_tool` - 智能定价分析
- `marketing_tool` - 营销策略
- `farm_inspection_tool` - 农场检查

### 技能系统

位于 `src/agents/skills/`：
- `detection_skills.py` - 检测技能
- `planning_skills.py` - 规划技能
- `pricing_skills.py` - 定价技能
- `orchestration_skills.py` - 编排技能

---

## RAG 知识库系统

### 核心组件

**7 个检索工具**（`src/rag/core/tools.py`）：
1. `list_documents` - 列出可用文档
2. `get_document_overview` - 获取文档摘要
3. `get_chapter_content` - 获取章节内容
4. `search_key_points` - 搜索关键信息
5. `search_knowledge` - 全文检索
6. `get_document_full` - 获取完整文档
7. `load_skill` - 加载技能（V2 特有）

### 服务配置

- **端口**：8003
- **向量数据库**：ChromaDB
- **嵌入模型**：sentence-transformers
- **知识库位置**：`knowledge_base/chroma_db/`

---

## 检测服务架构

### 统一网关模式

**重要**：所有检测服务已整合到统一网关 `src/algorithms/api/main.py`（端口 8001）

**服务路由**：
- `/detection/pest/*` - 病虫害检测
- `/detection/rice/*` - 大米品种识别
- `/detection/cow/*` - 奶牛检测

**检测算法实现**：
- `pest_service.py` - 病虫害检测服务
- `rice_service.py` - 大米品种识别服务
- `cow_service.py` - 奶牛检测服务

**模型文件**：
- `models/pest/` - 病虫害检测模型
- `models/rice/` - 大米识别模型
- `models/cow/` - 奶牛检测模型

---

## 模型管理

### 支持的模型供应商

- **DeepSeek**（默认）：`MODEL_PROVIDER=deepseek`
- **智谱AI (GLM)**：`MODEL_PROVIDER=glm`

### 配置位置

- 环境变量：`.env` 文件
- 模型配置：`src/config.py`

### Agent 版本切换

- **V1**（传统架构）：固定提示词，所有工具始终加载
- **V2**（Skills 架构）：渐进式披露，按需加载技能（推荐）

配置：`AGENT_VERSION=v2`（在 `.env` 文件中）

---

## API 文档地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **后端 API** | http://localhost:8081/docs | FastAPI 主服务文档 |
| **检测服务网关** | http://localhost:8001/docs | 统一检测服务文档 |
| **规划咨询服务** | http://localhost:8003/docs | RAG 服务文档 |
| **前端界面** | http://localhost:3001 | Next.js 应用 |

---

## 开发最佳实践

### 添加新功能时

1. **确定功能类型**：
   - Agent 功能 → `src/agents/`
   - 检测功能 → `src/algorithms/detection/`
   - RAG 功能 → `src/rag/`

2. **遵循现有模式**：
   - 查看同类功能的实现方式
   - 遵循相同的代码组织结构
   - 使用相同的命名规范

3. **添加测试**：
   - 单元测试 → `tests/unit/`
   - 集成测试 → `tests/integration/`

4. **更新文档**：
   - API 变更 → 更新 API 文档
   - 架构变更 → 更新架构文档
   - 新功能 → 添加操作指南

### 修改 Agent 时

1. **优先修改 Skills 定义**：`src/agents/skills/`
2. **更新工具注册**：在 `orchestrator_agent_v2.py` 中注册
3. **测试工具调用**：确保工具能正常调用
4. **更新文档**：同步更新相关文档

### 添加新检测服务时

1. 在 `src/algorithms/detection/` 创建服务文件
2. 在 `src/algorithms/api/main.py` 添加路由
3. 在 `src/agents/tools/` 添加对应工具
4. 更新文档

---

## 关键文件速查表

| 文件 | 作用 | 优先级 |
|------|------|--------|
| `service/server.py` | 后端主服务入口，Agent 编排 | ⭐⭐⭐ |
| `src/agents/orchestrator_agent_v2.py` | V2 统一编排 Agent | ⭐⭐⭐ |
| `src/algorithms/api/main.py` | 检测服务统一网关 | ⭐⭐⭐ |
| `src/rag/core/tools.py` | RAG 知识库工具 | ⭐⭐⭐ |
| `src/config.py` | 全局配置 | ⭐⭐ |
| `run_server.py` | 后端启动脚本 | ⭐⭐ |
| `run_frontend.py` | 前端启动脚本 | ⭐⭐ |
| `.env` | 环境变量配置 | ⭐⭐⭐ |

---

## 常见问题速查

### Q: 如何启动项目？

**A**:
```bash
# 快速启动
uv run python run_server.py      # 后端
uv run python run_frontend.py    # 前端
```

### Q: 检测服务在哪个端口？

**A**: 统一网关端口 **8001**

### Q: 如何切换 Agent 版本？

**A**: 编辑 `.env` 文件：`AGENT_VERSION=v2`

### Q: RAG 服务如何启动？

**A**:
```bash
# 1. 构建知识库
uv run python scripts/dev/build_kb_auto.py

# 2. 启动服务
uv run python src/rag/service/main.py
```

### Q: 检测服务如何调用？

**A**: 通过统一网关：
```bash
# 病虫害检测
curl -X POST "http://localhost:8001/detection/pest/predict" \
  -F "file=@image.jpg"
```

### Q: 如何查看 API 文档？

**A**:
- 后端：http://localhost:8081/docs
- 检测：http://localhost:8001/docs
- 规划：http://localhost:8003/docs

---

## 更新日志

**最后更新**: 2026-01-31
**版本**: v2.0

**主要变更**：
- 更新为 V2 Agent Skills 架构说明
- 修正端口分配（后端 8081，检测网关 8001，规划 8003）
- 更新目录结构（反映最新的代码组织）
- 修正服务启动命令
- 添加各部分逻辑关系的详细说明
