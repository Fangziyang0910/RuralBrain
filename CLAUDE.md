# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**RuralBrain（乡村智慧大脑）** 是一个基于 LangChain/LangGraph 的乡村决策系统，采用微服务架构，为乡村治理和发展提供智能化决策支持。

### 核心能力
- **智能规划咨询**：基于 RAG 知识库的乡村规划智能咨询服务
- **AI 检测服务**：病虫害检测、大米品种识别、奶牛目标检测
- **智能定价分析**：农产品定价因素分析和建议
- **Agent 系统**：使用 LangGraph 编排的智能体工作流

## 常用命令

### 环境管理
```bash
# 安装依赖（使用 uv）
uv sync

# 运行 Python 代码（必须使用 uv）
uv run python <script>

# 运行测试
uv run pytest
```

### 服务启动

**Docker 部署（推荐）**：
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**本地开发**：
```bash
# 启动后端服务
uv run python run_server.py

# 启动前端（推荐方式，跨平台兼容）
uv run python run_frontend.py

# 或者手动启动前端
cd frontend/my-app
npm install
npm run dev
```

### 专项服务启动

```bash
# 启动规划咨询服务
uv run python src/rag/service/planning_service.py

# 启动病虫害检测服务
uv run python src/algorithms/pest_detection/start_service.py

# 启动大米识别服务
uv run python src/algorithms/rice_detection/start_service.py

# 启动奶牛检测服务
uv run python src/algorithms/cow_detection/start_service.py
```

### 知识库管理

```bash
# 构建知识库
uv run python scripts/dev/build_kb_auto.py
```

## 代码架构

### 微服务架构

```
前端 (3000) → 后端服务 (8080) → 检测服务 (8001/8002/8081)
                            ↓
                       规划服务 (8003) ← RAG 知识库
```

### 目录结构

- **[src/agents/](src/agents/)**：Agent 系统
  - `orchestrator_agent_v2.py`：统一编排 Agent（基于 LangGraph Skills 架构）
  - `tools/`：Agent 工具集（检测、定价等）
  - `skills/`：Skills 架构模块
  - `middleware/`：中间件

- **[src/algorithms/](src/algorithms/)**：独立检测算法服务
  - `pest_detection/`：病虫害检测服务
  - `rice_detection/`：大米品种识别服务
  - `cow_detection/`：奶牛目标检测服务
  - 每个服务都有独立的 `start_service.py` 启动脚本

- **[src/rag/](src/rag/)**：RAG 知识库系统（独立微服务）
  - `core/`：RAG 核心功能（工具、检索器、文档管理）
  - `service/`：RAG 服务实现
  - `docs/`：知识库文档

- **[service/](service/)**：FastAPI 主服务
  - `server.py`：主服务器入口
  - `settings.py`：服务配置

- **[frontend/my-app/](frontend/my-app/)**：Next.js 前端应用

### 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | Next.js 应用 |
| 后端 API | 8080 | FastAPI 主服务 |
| 病虫害检测 | 8001 | 独立检测服务 |
| 大米识别 | 8081 | 独立检测服务 |
| 奶牛检测 | 8002 | 独立检测服务 |
| 规划咨询 | 8003 | RAG 服务 |

## 技术栈

### 核心
- **Python 3.13+**：开发语言
- **LangChain/LangGraph 1.0+**：Agent 框架和工作流编排
- **LangSmith**：Agent 行为可观测性和调试
- **FastAPI**：RESTful API 服务
- **uv**：Python 包管理和环境管理

### AI/ML
- **PyTorch**：深度学习框架
- **Ultralytics YOLO**：目标检测模型
- **ChromaDB**：向量数据库（RAG）
- **sentence-transformers**：文本嵌入模型

### 前端
- **Next.js 14**：React 框架
- **TypeScript**：类型安全
- **Tailwind CSS + Radix UI**：样式和组件

## 重要约束

### 1. Python 环境管理
- **必须使用 `uv`** 运行所有 Python 代码
- 不使用 `pip` 或 `python` 直接运行

### 2. LangChain/LangGraph 语法
- **涉及 LangChain/LangGraph 语法问题时，必须调用 docs-langchain MCP 获取官方文档**
- 不得仅凭预训练知识进行代码更改

### 3. 工作流程
- 对于所有任务，先逐步思考并拆解成一步一步的执行任务
- 给出修改计划，征求用户同意后再进行代码更改

### 4. 代码风格
- 遵守 Python 代码设计哲学（The Zen of Python）
- 使用 `uv run python` 运行所有 Python 脚本

### 5. 文件移动后的路径引用修复
当移动文件到新位置时，必须同时检查并修复文件内部的路径引用。

### 6. 库/API 文档查询
- **当需要库/API 文档、代码生成、设置或配置步骤时，始终使用 context7 mcp**
- 优先通过 context7 获取最新的官方文档和最佳实践

### 7. 前端开发
- **当涉及前端开发的时候，充分利用 playwright mcp 工具来进行错误排查和效果获取**
- 使用 playwright 进行页面截图、控制台日志检查、元素交互验证等

## 模型配置

项目支持多个大语言模型供应商，通过 `.env` 文件中的 `MODEL_PROVIDER` 切换：

- **DeepSeek**（默认）：`MODEL_PROVIDER=deepseek`
- **智谱AI (GLM)**：`MODEL_PROVIDER=glm`

模型配置定义在 [src/config.py](src/config.py)

## Agent 系统设计

### 智能定价工具

**定价工具**（[src/agents/tools/pricing_tool.py](src/agents/tools/pricing_tool.py)）为农产品定价提供结构化分析：

**功能**：
- 成本分析（基础成本、品质溢价空间）
- 市场分析（供需状况、季节性、价格趋势）
- 竞争分析（竞争对手价格区间）
- 定价策略建议（溢价、成本导向、市场导向、竞争导向）

**参数**：
- `product_name`：产品名称
- `product_category`：产品分类（粮食/蔬菜/水果/畜牧/水产）
- `cost_price`：成本价格
- `quality_grade`：品质等级（优等/一等/中等/三等）
- `market_data`：可选的市场数据 JSON（供需、竞争、季节等）

**返回**：结构化的定价因素分析报告

### Planning Agent 架构

规划咨询智能体（[src/agents/planning_agent.py](src/agents/planning_agent.py)）采用以下设计：

- **框架**：基于 LangGraph 的 Agent 工作流
- **工具**：集成 RAG 知识库的 6 个核心工具（[src/rag/core/tools.py](src/rag/core/tools.py)）
- **工作模式**：
  - 快速模式：摘要浏览 + 关键信息检索
  - 深度模式：全文阅读 + 综合分析
- **约束**：必须通过工具查询知识库，严禁基于预训练数据回答

### RAG 工具系统

RAG 工具定义在 [src/rag/core/tools.py](src/rag/core/tools.py)：

- `list_documents`：列出知识库可用文档
- `get_document_overview`：获取文档摘要
- `get_chapter_content`：获取指定章节内容
- `search_key_points`：搜索关键信息点
- `search_knowledge`：全文检索
- `get_document_full`：获取完整文档

## 知识库系统

RAG 知识库是一个独立的微服务，支持：

- **文档格式**：PDF、Word (docx)、PPT (pptx)
- **向量存储**：ChromaDB
- **嵌入模型**：sentence-transformers
- **服务端口**：8003

知识库构建脚本位于 `scripts/dev/build_kb_auto.py`

## 文件组织规范

详细的项目结构组织规范请参考 [docs/PROJECT_STRUCTURE_GUIDE.md](docs/PROJECT_STRUCTURE_GUIDE.md)

核心原则：
- 测试文件放在 `tests/` 目录
- 脚本文件放在 `scripts/` 目录
- 文档放在 `docs/` 目录
- 避免根目录堆满临时文件

## API 文档

- **后端 API**：http://localhost:8080/docs
- **规划咨询**：http://localhost:8003/docs
- **病虫害检测**：http://localhost:8001/docs
- **大米识别**：http://localhost:8081/docs
- **奶牛检测**：http://localhost:8002/docs
