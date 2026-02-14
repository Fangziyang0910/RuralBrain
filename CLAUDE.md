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

## 系统架构

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

**1. 用户请求 → 意图识别 → Agent 处理**

- **有图片** → 检测流程（Agent 调用检测工具 → 网关 8001 → YOLO 推理）
- **规划关键词** → 规划咨询流程（转发到 8003 → RAG 工具查询知识库）
- **默认** → 通用对话（Agent 直接基于预训练知识回答，可能调用定价/营销工具）

**2. 工具调用链路**

```
Agent 调用工具
    ↓
src/agents/tools/<tool>.py
    ↓
HTTP 请求到外部服务
    ↓
- 检测工具 → http://localhost:8001/detection/<type>/predict
- 定价工具 → 内置逻辑
- 营销工具 → 内置逻辑
```

---

## 服务端口与 API 文档

| 服务 | 端口 | 配置位置 | API 文档 |
|------|------|----------|----------|
| **前端** | 3001 | `frontend/package.json` | http://localhost:3001 |
| **后端主服务** | 8081 | `service/settings.py` + `.env` | http://localhost:8081/docs |
| **检测服务网关** | 8001 | `src/algorithms/api/main.py` | http://localhost:8001/docs |
| **规划咨询服务** | 8003 | `src/rag/service/main.py` | http://localhost:8003/docs |

### 检测服务路由（统一网关 8001）

```
/detection/pest/predict    # 病虫害检测
/detection/rice/predict    # 大米品种识别
/detection/cow/predict     # 奶牛检测
/health                     # 健康检查
```

---

## 目录结构

```
RuralBrain/
│
├── service/                     # FastAPI 后端主服务
│   ├── server.py              # 主服务器入口（Agent 编排）
│   ├── settings.py            # 服务配置
│   └── schemas.py             # 数据模型
│
├── src/                        # 核心业务逻辑
│   ├── agents/                 # Agent 系统（V2 Skills 架构）
│   │   ├── orchestrator_agent_v2.py   # ⭐ 统一编排 Agent
│   │   ├── skills/            # Skills 架构模块
│   │   ├── tools/             # Agent 工具集
│   │   └── middleware/        # 中间件系统
│   │
│   ├── algorithms/            # 检测算法服务
│   │   ├── api/               # ⭐ 统一 API 网关（端口 8001）
│   │   └── detection/        # 检测算法实现 + YOLO 模型
│   │
│   ├── rag/                   # RAG 知识库系统
│   │   ├── core/              # 7 个核心检索工具
│   │   └── service/           # FastAPI 服务入口（端口 8003）
│   │
│   └── config.py              # 全局配置
│
├── frontend/                  # Next.js 前端应用
├── docker/                   # Docker 配置（ONNX 轻量级镜像）
├── tests/                    # 测试代码
├── scripts/                  # 脚本工具
│   └── dev/                  # 开发脚本（健康检查、测试、环境切换）
└── docs/                     # 项目文档
```

---

## 常用命令

### 环境管理

```bash
# 必须使用 uv 运行 Python 代码
uv sync                              # 安装依赖
uv run python <script>              # 运行脚本
uv run pytest                       # 运行测试
```

### Docker ONNX 部署（推荐）⭐

**优势**：镜像体积减少 60-75%（~10GB），构建时间缩短 50%（3-5分钟）

```bash
# 1. 构建镜像（首次）
.\scripts\dev\build-onnx-images.ps1       # Windows
bash scripts/dev/build-onnx-images.sh    # Linux/macOS

# 2. 启动开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 3. 查看状态/日志
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs -f
```

### 服务启动（非 Docker）

```bash
uv run python run_server.py      # 后端
uv run python run_frontend.py    # 前端
```

### 健康检查与测试

```bash
# 健康检查
bash scripts/dev/health_check.sh                 # 完整检查
bash scripts/dev/health_check.sh --quick         # 快速检查

# 功能测试（分级）
bash scripts/dev/test_services.sh --fast         # 快速测试 (< 30秒)
bash scripts/dev/test_services.sh --normal       # 正常测试 (< 2分钟)
bash scripts/dev/test_services.sh --full         # 完整测试 (< 5分钟)
```

### 知识库构建

```bash
uv run python scripts/dev/build_kb_auto.py
```

**详细命令参考**：[docs/commands.md](docs/commands.md) | **快速开始**：[docs/guides/getting-started.md](docs/guides/getting-started.md)

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

### 8. 开发测试验证 ⭐⭐⭐

**重要**：每次代码更改后必须进行测试验证

```
代码更改 → 热重载（1-3秒） → 健康检查 → 功能测试
```

**验证流程**：
```bash
# 1. 等待热重载完成（自动，1-3秒）

# 2. 快速健康检查
bash scripts/dev/health_check.sh --quick

# 3. 运行相关功能测试
bash scripts/dev/test_services.sh --fast

# 4. 如果测试通过，继续开发
#    如果测试失败，修复问题
```

**部署前验证**：
```bash
# 1. 完整功能测试
bash scripts/dev/test_services.sh --full

# 2. 切换到生产模式
bash scripts/dev/switch_to_production.sh

# 3. 生产环境测试
bash scripts/dev/test_production.sh

# 4. 如果所有测试通过，可以部署
```

---

## Agent V2 系统（Skills 架构）

### 架构特点

- **渐进式披露**：初始只提供技能描述，按需加载完整内容
- **模块化技能配置**：每个技能专注一个特定领域
- **中间件系统**：SkillMiddleware、ToolSelectorMiddleware

### 工具系统

**检测工具**（通过网关 8001）：
- `pest_detection_tool` - 病虫害检测
- `rice_detection_tool` - 大米品种识别
- `cow_detection_tool` - 奶牛检测

**内置工具**：
- `pricing_tool` - 智能定价分析
- `marketing_tool` - 营销策略
- `farm_inspection_tool` - 农场检查
- `disease_prediction_tool` - 疾病预测

### 技能文件

位于 `src/agents/skills/`：
- `detection_skills.py` - 检测技能
- `planning_skills.py` - 规划技能
- `pricing_skills.py` - 定价技能
- `marketing_skills.py` - 营销技能
- `orchestration_skills.py` - 编排技能

---

## RAG 知识库系统

- **端口**：8003
- **向量数据库**：ChromaDB
- **嵌入模型**：sentence-transformers
- **知识库位置**：`knowledge_base/chroma_db/`

**7 个检索工具**（[src/rag/core/tools.py](src/rag/core/tools.py)）：
1. `list_documents` - 列出可用文档
2. `get_document_overview` - 获取文档摘要
3. `get_chapter_content` - 获取章节内容
4. `search_key_points` - 搜索关键信息
5. `search_knowledge` - 全文检索
6. `get_document_full` - 获取完整文档
7. `load_skill` - 加载技能（V2 特有）

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

## 开发最佳实践

### 添加新功能时

1. **确定功能类型**：
   - Agent 功能 → `src/agents/`
   - 检测功能 → `src/algorithms/detection/`
   - RAG 功能 → `src/rag/`

2. **遵循现有模式**：
   - 查看同类功能的实现方式
   - 遵循相同的代码组织结构和命名规范

3. **添加测试**：
   - 单元测试 → `tests/unit/`
   - 集成测试 → `tests/integration/`

4. **更新文档**：
   - API 变更 → 更新 API 文档
   - 架构变更 → 更新架构文档

### 修改 Agent 时

1. 优先修改 Skills 定义：`src/agents/skills/`
2. 更新工具注册：在 `orchestrator_agent_v2.py` 中注册
3. 测试工具调用
4. 同步更新相关文档

### 添加新检测服务时

1. 在 `src/algorithms/detection/` 创建服务文件
2. 在 `src/algorithms/api/main.py` 添加路由
3. 在 `src/agents/tools/` 添加对应工具
4. 更新文档

---

## 关键文件速查表

| 文件 | 作用 | 优先级 |
|------|------|--------|
| [service/server.py](service/server.py) | 后端主服务入口，Agent 编排 | ⭐⭐⭐ |
| [src/agents/orchestrator_agent_v2.py](src/agents/orchestrator_agent_v2.py) | V2 统一编排 Agent | ⭐⭐⭐ |
| [src/algorithms/api/main.py](src/algorithms/api/main.py) | 检测服务统一网关 | ⭐⭐⭐ |
| [src/rag/core/tools.py](src/rag/core/tools.py) | RAG 知识库的 7 个检索工具 | ⭐⭐⭐ |
| [src/config.py](src/config.py) | 全局配置（模型管理等） | ⭐⭐ |
| [.env](.env) | 环境变量配置 | ⭐⭐⭐ |

---

## 常见问题速查（快速索引）

| 问题 | 答案位置 |
|------|----------|
| 如何启动项目？ | [常用命令 › 服务启动](#常用命令) |
| 检测服务在哪个端口？ | [服务端口与 API 文档](#服务端口与-api-文档) |
| 如何切换 Agent 版本？ | [模型管理 › Agent 版本切换](#模型管理) |
| RAG 服务如何启动？ | [常用命令 › 知识库构建](#常用命令) |
| 检测服务如何调用？ | [服务端口与 API 文档 › 检测服务路由](#服务端口与-api-文档) |
| Docker ONNX 部署说明 | [常用命令 › Docker ONNX 部署](#常用命令) |
| 日常开发流程？ | [开发最佳实践](#开发最佳实践) |

---

## 更新日志

**最后更新**: 2026-02-14 | **版本**: v3.1

**v3.1 主要变更**（本次精简）：
- 删除重复的端口信息说明（统一到"服务端口与 API 文档"）
- 删除重复的命令说明（合并到"常用命令"）
- 删除独立的"检测服务架构"和"RAG 知识库系统"章节（已在系统架构中说明）
- 简化"常见问题"为快速索引风格
- 文档从 ~500 行精简至 ~350 行（-30%）

**v3.0 主要变更**：
- 文档结构重构：新增 `docs/decisions/`、`docs/architecture/`、`docs/guides/`
- 删除 8 个冗余/过时文档

**v2.2 变更**：
- 新增 ONNX Runtime 轻量级 Docker 部署方案

---

**相关文档**：[docs/README.md](docs/README.md) | [docs/commands.md](docs/commands.md)
