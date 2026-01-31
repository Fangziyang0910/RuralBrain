# RuralBrain - 乡村智慧决策系统

## 🌟 项目概述

RuralBrain 是一个基于 **LangChain/LangGraph** 的乡村智慧决策系统，采用微服务架构。系统集成了智能检测、规划咨询、智能定价等多种农业 AI 能力，为乡村治理和发展提供智能化决策支持。

### 核心特性

- **🤖 智能 Agent 系统**：基于 Skills 架构的 V2 Agent，支持渐进式披露
- **🔍 多模态检测**：病虫害、大米品种、奶牛目标检测
- **📚 RAG 知识库**：基于向量数据库的乡村规划咨询
- **🎯 智能定价**：农产品定价分析和建议
- **🌊 流式对话**：SSE 实时流式响应
- **🔀 智能路由**：自动识别用户意图并分发到相应服务

---

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      RuralBrain System                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   Frontend   │────▶│    Backend   │────▶│  Agent V2    │ │
│  │   Next.js    │     │   FastAPI    │     │ Orchestrator │ │
│  │    :3000     │     │    :8080     │     │  (Skills)    │ │
│  └──────────────┘     └──────────────┘     └──────┬───────┘ │
│       │                    │                      │         │
│       │                    ▼                      ▼         │
│       │         ┌──────────────────┐    ┌──────────────┐   │
│       │         │  Intent Router   │    │   Skills     │   │
│       │         │  (意图识别)       │    │   & Tools    │   │
│       │         └────────┬─────────┘    └──────────────┘   │
│       │                  │                                 │
│       ▼                  ▼                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              微服务层                                 │  │
│  ├──────────────────┬──────────────────┬───────────────┤  │
│  │ 检测服务网关     │  规划咨询服务   │  定价分析     │  │
│  │   :8001         │    :8003        │   (内置)       │  │
│  ├──────────────────┤                 │               │  │
│  │ • 病虫害检测    │  • RAG 知识库   │  • 营销策略   │  │
│  │ • 大米品种识别  │  • ChromaDB     │  • 农场检查   │  │
│  │ • 奶牛目标检测  │  • 规划 Agent   │               │  │
│  └─────────────────┴─────────────────┴───────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

#### 后端核心
- **Python 3.13+**：主要开发语言
- **FastAPI**：RESTful API 服务框架
- **LangChain/LangGraph 1.0+**：Agent 框架和工作流编排
- **LangSmith**：Agent 行为可观测性和调试
- **uv**：Python 包管理和环境管理

#### AI/ML 技术
- **PyTorch**：深度学习框架
- **Ultralytics YOLO**：目标检测模型
- **ChromaDB**：向量数据库（RAG）
- **sentence-transformers**：文本嵌入模型

#### 前端技术
- **Next.js 14**：React 框架
- **TypeScript**：类型安全
- **Tailwind CSS + Radix UI**：样式和组件库

#### 部署技术
- **Docker**：容器化部署
- **Docker Compose**：服务编排
- **SSE**：流式响应

---

## 📁 项目结构

```
RuralBrain/
├── service/                          # FastAPI 主服务
│   ├── server.py                     # 主服务器入口（Agent 编排）
│   ├── settings.py                   # 服务配置
│   └── schemas.py                    # 数据模型
│
├── src/                              # 核心代码
│   ├── agents/                       # Agent 系统
│   │   ├── orchestrator_agent_v2.py  # V2 统一编排 Agent（基于 Skills）
│   │   ├── tools/                    # Agent 工具集
│   │   │   ├── pest_detection_tool.py    # 病虫害检测
│   │   │   ├── rice_detection_tool.py    # 大米品种识别
│   │   │   ├── cow_detection_tool.py     # 奶牛检测
│   │   │   ├── pricing_tool.py           # 智能定价
│   │   │   ├── marketing_tool.py         # 营销策略
│   │   │   └── farm_inspection_tool.py   # 农场检查
│   │   ├── skills/                   # Skills 架构模块
│   │   │   ├── detection_skills.py      # 检测技能
│   │   │   ├── planning_skills.py       # 规划技能
│   │   │   ├── pricing_skills.py        # 定价技能
│   │   │   └── orchestration_skills.py   # 编排技能
│   │   └── middleware/               # 中间件系统
│   │       ├── skill_middleware.py      # 技能中间件
│   │       └── tool_selector_middleware.py  # 工具选择中间件
│   │
│   ├── algorithms/                   # 检测算法服务
│   │   ├── api/                      # 统一 API 网关（端口 8001）
│   │   │   └── main.py               # FastAPI 检测服务网关
│   │   └── detection/                # 检测算法实现
│   │       ├── pest_service.py       # 病虫害检测服务
│   │       ├── rice_service.py       # 大米品种识别服务
│   │       ├── cow_service.py        # 奶牛检测服务
│   │       └── models/               # YOLO 模型文件
│   │
│   └── rag/                          # RAG 知识库系统（独立微服务）
│       ├── core/                     # RAG 核心功能
│       │   ├── tools.py              # 7 个核心检索工具
│       │   ├── context_manager.py    # 上下文管理
│       │   ├── cache.py              # 向量缓存
│       │   └── summarization.py      # 文档摘要
│       ├── service/                  # RAG 服务实现
│       │   ├── main.py               # FastAPI 服务入口（端口 8003）
│       │   └── config.py             # 配置管理
│       └── docs/                     # 知识库文档
│
├── frontend/                         # Next.js 前端应用
│   ├── src/                          # 前端源代码
│   │   ├── app/                      # Next.js 14 App Router
│   │   └── components/               # React 组件
│   └── package.json                  # 前端依赖
│
├── docker/                           # Docker 配置
│   ├── docker-compose.yml            # 生产环境部署
│   └── docker-compose.dev.yml        # 开发环境部署（热重载）
│
├── tests/                            # 测试文件
├── scripts/                          # 脚本文件
├── docs/                             # 项目文档
└── CLAUDE.md                         # 项目级配置
```

---

## 🔧 服务配置

### 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| **前端** | 3000 | Next.js 应用 |
| **后端主服务** | 8080 | FastAPI + Orchestrator Agent |
| **检测服务网关** | 8001 | 统一检测服务（所有检测类型） |
| **规划咨询服务** | 8003 | RAG 知识库服务 |

### 检测服务路由

所有检测服务整合在统一网关（8001），使用路由前缀区分：

```
http://localhost:8001
├── /detection/pest/*    # 病虫害检测
├── /detection/rice/*    # 大米品种识别
└── /detection/cow/*     # 奶牛目标检测
```

### 核心服务

#### 1. 后端主服务（FastAPI + Orchestrator Agent）
- **位置**: `service/server.py`
- **端口**: 8080
- **主要功能**:
  - API 网关和统一入口
  - V2 Orchestrator Agent（基于 Skills 架构）
  - 意图识别和智能路由
  - 流式 SSE 响应
- **API 文档**: http://localhost:8080/docs

#### 2. 检测服务网关
- **位置**: `src/algorithms/api/main.py`
- **端口**: 8001
- **主要功能**:
  - 统一所有检测服务的路由
  - 病虫害检测（瓜实蝇、斜纹夜蛾等）
  - 大米品种识别（5种大米品种）
  - 奶牛目标检测（识别和计数）
- **API 文档**: http://localhost:8001/docs

#### 3. 规划咨询服务（RAG）
- **位置**: `src/rag/service/main.py`
- **端口**: 8003
- **主要功能**:
  - 基于知识库的乡村规划咨询
  - 支持快速浏览和深度分析模式
  - 7 个核心检索工具
  - ChromaDB 向量数据库
- **API 文档**: http://localhost:8003/docs

#### 4. 前端应用
- **位置**: `frontend/`
- **端口**: 3000
- **技术栈**: Next.js 14 + TypeScript + Tailwind CSS
- **主要功能**:
  - Web 用户界面
  - 多模态输入（文本 + 图片）
  - 流式对话展示
  - 工具调用可视化

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.13+
- **Node.js**: 20+
- **Docker**: 20.10+（可选，用于容器化部署）
- **uv**: Python 包管理器

### Docker 部署（推荐）

#### 一键启动所有服务

```bash
# 进入 docker 目录
cd docker

# 启动所有服务（生产环境）
docker-compose up -d

# 或启动开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | Web 用户界面 |
| 后端 API | http://localhost:8080 | FastAPI 主服务 |
| API 文档 | http://localhost:8080/docs | Swagger 文档 |
| 检测服务 | http://localhost:8001 | 统一检测服务网关 |
| 规划咨询 | http://localhost:8003 | RAG 知识库服务 |

### 本地开发

#### 1. 安装依赖

```bash
# 使用 uv 同步依赖
uv sync

# 前端依赖
cd frontend
npm install
cd ..
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置 API Keys
# 必需：DEEPSEEK_API_KEY 或 ZHIPUAI_API_KEY
```

#### 3. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
# 启动后端服务
uv run python run_server.py

# 启动前端服务（新终端）
uv run python run_frontend.py
```

**方式二：手动启动**

```bash
# 启动后端（端口 8080）
uv run python service/server.py

# 启动检测服务网关（端口 8001）
uv run python src/algorithms/api/main.py

# 启动规划服务（端口 8003）
uv run python src/rag/service/main.py

# 启动前端（端口 3000）
cd frontend
npm run dev
```

#### 4. 构建知识库（可选，用于规划咨询）

```bash
# 自动构建知识库
uv run python scripts/dev/build_kb_auto.py
```

---

## 🎯 核心功能

### 1. 智能 Agent 系统（V2 Skills 架构）

基于 LangChain 官方 **Skills 模式**和**渐进式披露（Progressive Disclosure）**设计：

**核心优势**：
- ✅ Token 消耗减少 50%+（按需加载技能）
- ✅ 提示词长度从 82 行减少到 20 行
- ✅ 模块化技能配置，易于扩展
- ✅ 支持版本切换（V1/V2）和自动降级

**组件**：
- **中间件系统**：SkillMiddleware、ToolSelectorMiddleware
- **技能系统**：检测、规划、定价、营销等技能
- **工具系统**：病虫害检测、大米识别、奶牛检测、定价等工具

详细文档：[V2 Agent 架构](../architecture/v2-agent-upgrade.md)

### 2. 多模态智能检测

#### 病虫害检测
- 识别农作物病虫害（瓜实蝇、斜纹夜蛾、稻飞虱等）
- 分析危害程度和影响
- 提供综合防治方案（化学、生物、物理防治）

#### 大米品种识别
- 支持 5 种大米品种识别
  - 糯米 (nuomi)
  - 珍珠大米 (zhenzhudami)
  - 五常糯米 (wuchangnuomi)
  - 丝苗米 (simiaomi)
  - 泰国香米 (taiguoxiangmi)
- 品质分析和特点说明

#### 奶牛目标检测
- 牛只识别和计数
- 品种识别（本地黄牛、杂交肉牛等）
- 养殖管理建议

### 3. RAG 知识库系统

基于 ChromaDB 的乡村规划咨询服务：

**核心工具**（7 个）：
1. `list_documents` - 列出可用文档
2. `get_document_overview` - 获取文档摘要
3. `get_chapter_content` - 获取章节内容
4. `search_key_points` - 搜索关键信息
5. `search_knowledge` - 全文检索
6. `get_document_full` - 获取完整文档
7. `load_skill` - 加载技能（V2 特有）

**工作模式**：
- `auto` - AI 自动选择
- `fast` - 快速浏览（摘要模式）
- `deep` - 深度分析（全文模式）

### 4. 智能定价分析

为农产品定价提供结构化分析：
- 成本分析（基础成本、品质溢价空间）
- 市场分析（供需状况、季节性、价格趋势）
- 竞争分析（竞争对手价格区间）
- 定价策略建议

### 5. 其他功能

- **营销策略** - 农产品营销方案
- **农场检查** - 农场运营检查和建议
- **流式对话** - SSE 实时响应
- **意图识别** - 自动判断用户需求类型

---

## 🧪 测试

### 健康检查

```bash
# 后端服务
curl http://localhost:8080/health

# 检测服务网关
curl http://localhost:8001/health

# 规划咨询服务
curl http://localhost:8003/health
```

### 功能测试

```bash
# 病虫害检测
curl -X POST "http://localhost:8001/detection/pest/predict" \
  -F "file=@path/to/image.jpg"

# 大米品种识别
curl -X POST "http://localhost:8001/detection/rice/predict" \
  -F "file=@path/to/image.jpg"

# 奶牛检测
curl -X POST "http://localhost:8001/detection/cow/predict" \
  -F "file=@path/to/image.jpg"

# 规划咨询
curl -X POST "http://localhost:8080/chat/planning" \
  -H "Content-Type: application/json" \
  -d '{"message": "长宁镇的旅游发展目标是什么？", "mode": "auto"}'
```

---

## 📊 模型信息

### 病虫害检测模型
- **模型文件**: `src/algorithms/detection/models/pest/`
- **架构**: YOLOv8
- **支持类别**: 多种农作物病虫害

### 大米识别模型
- **模型文件**: `src/algorithms/detection/models/rice/`
- **架构**: YOLOv8
- **支持品种**: 5 种大米品种

### 奶牛检测模型
- **模型文件**: `src/algorithms/detection/models/cow/`
- **架构**: YOLOv8n
- **支持类别**: 牛只识别和计数

---

## 🔧 配置选项

### 环境变量

```bash
# 后端服务配置
PORT=8080                          # 后端端口
HOST=127.0.0.1                     # 监听地址
ALLOWED_ORIGINS=http://localhost:3000  # CORS 配置

# Agent 配置
MODEL_PROVIDER=deepseek             # 模型供应商（deepseek/glm）
AGENT_VERSION=v2                   # Agent 版本（v1/v2）
MODEL_TEMPERATURE=0                # 模型温度

# API Keys（配置一个即可）
DEEPSEEK_API_KEY=your_key_here
ZHIPUAI_API_KEY=your_key_here

# LangSmith 可观测性（可选）
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
```

### 模型管理

支持多个大语言模型供应商：

- **DeepSeek**（默认）
- **智谱AI (GLM)**

通过 `MODEL_PROVIDER` 环境变量切换。

详细文档：[模型管理指南](../guides/model-management.md)

---

## 🛠️ 开发指南

### Python 环境

项目使用 `uv` 包管理器：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 运行 Python 代码
uv run python <script>

# 运行测试
uv run pytest
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（热重载）
npm run dev

# 生产构建
npm run build

# 生产模式
npm start
```

### 添加新技能

1. 在 `src/agents/skills/` 创建新技能文件
2. 在 `src/agents/tools/` 创建对应工具
3. 在 `orchestrator_agent_v2.py` 中注册技能
4. 更新文档

详细指南：[项目结构指南](../guides/project-structure.md)

---

## 📈 性能优化

### 生产环境建议

1. **GPU 加速**：使用 GPU 版本的 PyTorch
2. **负载均衡**：配置 Nginx 反向代理
3. **资源限制**：设置适当的内存和 CPU 限制
4. **监控告警**：添加服务监控和 LangSmith 追踪
5. **日志管理**：配置集中式日志收集

### Agent 性能

V2 Agent 相比 V1：
- Token 消耗减少 **50%+**
- 提示词长度减少 **75%**
- 响应延迟增加 **<10%**

---

## 🔒 安全建议

1. **访问控制**：生产环境应添加身份验证
2. **HTTPS**：使用 SSL/TLS 加密通信
3. **输入验证**：严格验证用户上传的图片和输入
4. **API Key 保护**：不要在代码中硬编码 API Keys
5. **CORS 配置**：限制允许的来源
6. **速率限制**：防止 API 滥用

---

## 📚 相关文档

- [文档中心](../README.md) - 文档导航
- [变更日志](../CHANGELOG.md) - 功能迭代记录
- [部署指南](../guides/deployment.md) - Docker 和本地部署
- [服务管理](../guides/service-management.md) - 服务启动和配置
- [V2 Agent 架构](../architecture/v2-agent-upgrade.md) - Agent V2 架构详解
- [项目结构](../guides/project-structure.md) - 代码组织规范

---

## 🆘 故障排除

### 常见问题

**Q: 服务启动失败？**

A: 检查以下项：
- 端口是否被占用（`lsof -i :8080`）
- API Keys 是否配置正确
- 依赖是否安装完整（`uv sync`）

**Q: 检测服务无法连接？**

A: 确认检测服务网关已启动（端口 8001）

**Q: RAG 查询无结果？**

A: 确认知识库已构建：
```bash
uv run python scripts/dev/build_kb_auto.py
```

**Q: 如何切换 Agent 版本？**

A: 编辑 `.env` 文件：
```bash
AGENT_VERSION=v1  # 或 v2
```

### 获取帮助

- 查看 API 文档：http://localhost:8080/docs
- 查看服务日志：`docker-compose logs -f`
- 提交 Issue 到项目仓库

---

## 📞 联系方式

- **GitHub**: https://github.com/Fangziyang0910/RuralBrain
- **问题反馈**: https://github.com/Fangziyang0910/RuralBrain/issues

---

**最后更新**: 2026-01-31
**版本**: v2.0
**维护者**: RuralBrain Team
