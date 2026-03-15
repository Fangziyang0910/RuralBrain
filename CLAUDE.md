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
- 📚 **RAG 规划咨询**：基于知识库的乡村规划智能问答（作为 Skill 集成到主 Agent）
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
│  - 知识库开关（启用/禁用）                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            后端主服务 (FastAPI)                        │
│             http://localhost:8081                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │  意图识别 (Intent Router)                         │ │
│  │   ├─ 有图片 + 检测关键词 → 检测流程               │ │
│  │   └─ 默认 → 统一 Agent 处理                      │ │
│  └───────────────────────────────────────────────────┘ │
│                     │                                     │
│  ┌───────────────────────────────────────────────────┐ │
│  │      Orchestrator Agent V2 (LangGraph)           │ │
│  │  - Skills 架构（渐进式披露）                      │ │
│  │  - 工具系统（检测、定价、营销、RAG 等）            │ │
│  │  - 中间件（SkillMiddleware、DynamicTool + TTL）   │ │
│ 100%  知识库开关控制 RAG 工具可用性                   │ │
│  │  - 工具生命周期管理（TTL、自动卸载）              │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  检测服务网关      │        │  RAG 知识库        │
│  :8001            │        │  (ChromaDB)        │
│  (统一网关)       │        │  - 4 个检索工具      │
├──────────────────┤        └──────────────────┘
│ • /detection/pest  │        注意：RAG 工具由主 Agent 直接调用
│ • /detection/rice  │
│ • /detection/cow   │
└──────────────────┘
```

### 核心逻辑流程

**1. 用户请求 → 意图识别 → Agent 处理**

- **有图片** → 检测流程（Agent 调用检测工具 → 网关 8001 → YOLO 推理）
- **默认** → 通用对话（Agent 自主决定调用哪些技能和工具）

**2. 工具调用链路**

```
Agent 调用工具
    ↓
src/agents/tools/<tool>.py
    ↓
- 检测工具 → HTTP 请求到 8001 网关
- RAG 工具 → 直接调用 ChromaDB（知识库检索）
- 定价/营销工具 → 内置逻辑
```

**3. 知识库开关控制**

- **前端开关**：用户可在前端界面开启/关闭知识库
- **后端传递**：`enable_knowledge_base` 参数通过 config 传递给 Agent
- **load_skill 内部判断**：
  - 开启（True）→ 注册 RAG 检索工具供 Agent 调用
  - 关闭（False）→ 不注册 RAG 工具，Agent 用通用知识回答
  - 未设置（None）→ 默认行为，注册 RAG 工具
- **规划技能统一接口**：`consult_planning_knowledge` 对外只有一个入口，内部自动处理知识库开关逻辑

**4. 工具生命周期管理（TTL）**

- **TTL 机制**：工具注册后拥有生命周期（TTL），闲置工具自动卸载
- **轮次衰减**：每轮对话开始时，所有已注册工具 TTL - 1
- **使用续期**：工具被调用时 TTL 续期（base_ttl + extension）
- **钉住工具**：支持设置 `pinned: true`，关键工具永不卸载
- **配置方式**：
  - 全局配置：环境变量 `DEFAULT_TOOL_TTL`、`DEFAULT_TOOL_EXTENSION`
  - 技能配置：YAML 中 `ttl_config` 字段
  - 开关控制：`ENABLE_TOOL_TTL` 环境变量

---

## 服务端口与 API 文档

| 服务 | 端口 | 配置位置 | API 文档 |
|------|------|----------|----------|
| **前端** | 3001 | `frontend/package.json` | http://localhost:3001 |
| **后端主服务** | 8081 | `service/settings.py` + `.env` | http://localhost:8081/docs |
| **检测服务网关** | 8001 | `src/algorithms/api/main.py` | http://localhost:8001/docs |

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
│   │   │   ├── configs/       # YAML 技能配置文件
│   │   │   ├── registry.py    # 技能注册中心
│   │   │   └── base.py        # Skill 数据模型
│   │   ├── tools/             # Agent 工具集（包含 RAG 工具）
│   │   └── middleware/        # 中间件系统
│   │       ├── dynamic_tool_middleware.py  # 动态工具注册中间件
│   │       └── tool_lifecycle.py           # 工具生命周期 TTL 管理
│   │
│   ├── algorithms/            # 检测算法服务
│   │   ├── api/               # ⭐ 统一 API 网关（端口 8001）
│   │   └── detection/        # 检测算法实现 + YOLO 模型
│   │
│   ├── rag/                   # RAG 知识库系统
│   │   ├── core/              # 4 个核心检索工具
│   │   └── config.py          # RAG 配置
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
# 必须使用 uv 运行aring Python 代码
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
# 统一检查脚本（合并了健康检查和功能测试）
bash scripts/dev/check.sh --health                # 健康检查
bash scripts/dev/check.sh --quick                 # 快速检查

# 功能测试（分级）
bash scripts/dev/check.sh --test fast             # 快速测试 (< 30秒)
bash scripts/dev/check.sh --test normal           # 正常测试 (< 2分钟)
bash scripts/dev/check.sh --test full             # 完整测试 (< 5分钟)
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
bash scripts/dev/check.sh --quick

# 3. 运行相关功能测试
bash scripts/dev/check.sh --test fast

# 4. 如果测试通过，继续开发
#    如果测试失败，修复问题
```

**部署前验证**：
```bash
# 1. 完整功能测试
bash scripts/dev/check.sh --test full

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
- **YAML 配置驱动**：技能定义使用 YAML 配置文件，支持热重载
- **技能注册中心**：集中管理所有技能配置，提供统一加载接口
- **中间件系统**：SkillMiddleware（技能渐进式披露）

### 技能配置系统

技能定义位于 `src/agents/skills/configs/`：
- `detection.yaml` - 检测技能（病虫害、大米品种、牛只检测）
- `planning.yaml` - 规划技能（乡村规划咨询，直接引用 RAG 工具）
- `pricing.yaml` - 定价技能（农产品定价分析）
- `marketing.yaml` - 营销技能（营销策略建议）
- `inspection.yaml` - 巡检技能（农场检查）
- `disease_prediction.yaml` - 疾病预测技能

### 工具系统

**检测工具**（通过网关 8001）：
- `pest_detection_tool` - 病虫害检测
- `rice_detection_tool` - 大米品种识别
- `cow_detection_tool` - 奶牛检测

**RAG 工具**（知识库检索）：
- `document_list` - 列出可用文档
- `document_overview` - 获取文档摘要
- `knowledge_search` - 全文检索
- `key_points_search` - 搜索关键要点

**内置工具**：
- `pricing_tool` - 智能定价分析
- `marketing_tool` - 营销策略
- `farm_inspection_tool` - 农场检查
- `disease_prediction_tool` - 疾病预测
- `load_skill` - 技能加载工具（按需加载技能完整内容）

### 技能注册中心

- 文件：`src/agents/skills/registry.py`
- 功能：从 YAML 配置文件加载所有技能，提供统一的技能查询接口
- 支持热重载：可通过 `SKILL_RELOAD_STRATEGY` 配置重新加载策略

### 工具生命周期管理（TTL）

- **文件**：`src/agents/middleware/tool_lifecycle.py`
- **功能**：实现工具自适应 TTL（Time To Live）机制

**核心机制**：
1. **工具注册**：赋予初始 TTL（默认 3 轮）
2. **轮次衰减**：每轮对话所有工具 TTL - 1
3. **使用续期**：工具被调用时续期（base_ttl + extension）
4. **自动卸载**：TTL 过期的工具自动移除
5. **钉住保护**：关键工具可设置 `pinned: true` 永不卸载

**配置方式**：
- **全局配置**（环境变量）：
  - `DEFAULT_TOOL_TTL=3` - 默认工具生命周期（轮数）
  - `DEFAULT_TOOL_EXTENSION=2` - 默认续期增量（轮数）
  - `ENABLE_TOOL_TTL=true` - 是否启用 TTL 机制
- **技能配置**（YAML）：
  ```yaml
  pest_detection:
    ttl_config:
      base_ttl: 2      # 基础生命周期
      extension: 1      # 使用后续期
      pinned: false    # 是否钉住
  ```

---

## RAG 知识库系统

- **集成方式**：作为 Skill 集成到主 Agent（独立端口 8003 已废弃）
- **向量数据库**：ChromaDB（使用 cosine 距离）
- **嵌入模型**：阿里云百炼 text-embedding-v4（优先），本地模型 BAAI/bge-small-zh-v1.5（降级）
- **知识库位置**：`knowledge_base/chroma_db/`

**标准检索器**（[src/rag/core/retriever.py](src/rag/core/retriever.py)）：
- `RuralBrainRetriever` - 符合 LangChain `BaseRetriever` 接口
- 支持检索策略：similarity、mmr、similarity_score_threshold
- 评分过滤：自动过滤低相似度结果

**4 个检索工具**（[src/rag/core/tools.py](src/rag/core/tools.py)）：
1. `list_documents` - 列出可用文档
2. `get_document_overview` - 获取文档摘要
3. `search_knowledge` - 全文检索（支持多种检索策略）
4. `search_key_points` - 搜索关键要点

**知识库开关控制**：
- 前端开关 → 后端参数 `enable_knowledge_base` → Agent 系统提示词
- 开启：Agent 可调用 RAG 检索工具
- 关闭：Agent 仅用预训练知识回答
- 未设置：Agent 自主判断

**关键配置**：
```bash
CHROMA_DISTANCE_METRIC=cosine           # 距离度量
RETRIEVE_SCORE_THRESHOLD=0.7            # 相似度阈值
RETRIEVE_SEARCH_TYPE=similarity_score_threshold  # 检索策略
```

---

## 模型管理

### 支持的模型供应商

- **DeepSeek**（默认）：`MODEL_PROVIDER=deepseek`
- **智谱AI (GLM)**：`MODEL_PROVIDER=glm`

### 配置位置

- **环境变量**：`.env` 文件
- **模型配置**：`src/config.py`
- **TTL 配置**：`src/config.py` + 技能 YAML 文件

**环境变量配置项**：
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEFAULT_TOOL_TTL` | 3 | 工具默认生命周期（轮数） |
| `DEFAULT_TOOL_EXTENSION` | 2 | 工具使用后续期增量（轮数） |
| `ENABLE_TOOL_TTL` | true | 是否启用 TTL 机制 |

### Agent 架构

当前采用 **V2 Skills 架构**：
- 渐进式披露（Progressive Disclosure）
- YAML 配置驱动
- 技能按需加载
- 中间件系统支持

---

## 开发最佳实践

### ⭐⭐⭐ 日常开发工作流（必读）

**重要**：所有开发都应该遵循 Docker 热重载开发工作流。

**日常开发指南**：[docs/guides/development.md](docs/guides/development.md)

**核心原则**：
1. **所有开发使用 Docker 热重载模式** - 不推荐本地直接运行
2. **每次代码更改后必须验证** - 健康检查 + 功能测试
3. **重要功能完成后切换到生产模式测试** - 确保生产环境可用
4. **验证通过后才能提交代码** - 保持代码库健康

**快速启动**：
```bash
# 启动开发环境（热重载模式）
docker-compose -f docker-compose.dev.yml up -d

# 验证服务健康
bash scripts/dev/check.sh --quick

# 每次代码修改后
bash scripts/dev/check.sh --quick
bash scripts/dev/check.sh --test fast
```

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
| [src/agents/middleware/tool_lifecycle.py](src/agents/middleware/tool_lifecycle.py) | 工具生命周期 TTL 管理 | ⭐⭐ |
| [src/agents/middleware/dynamic_tool_middleware.py](src/agents/middleware/dynamic_tool_middleware.py) | 动态工具注册中间件 | ⭐⭐⭐ |
| [src/algorithms/api/main.py](src/algorithms/api/main.py) | 检测服务统一网关 | ⭐⭐⭐ |
| [src/rag/core/retriever.py](src/rag/core/retriever.py) | LangChain 标准检索器 | ⭐⭐ |
| [src/rag/core/tools.py](src/rag/core/tools.py) | RAG 知识库的 4 个检索工具 | ⭐⭐ |
| [src/rag/config.py](src/rag/config.py) | RAG 配置（距离度量、检索策略） | ⭐⭐ |
| [src/config.py](src/config.py) | 全局配置（模型管理等） | ⭐⭐ |
| [.env](.env) | 环境变量配置 | ⭐⭐⭐ |

---

## 常见问题速查（快速索引）

| 问题 | 答案位置 |
|------|----------|
| 如何启动项目？ | [常用命令 › 服务启动](#常用命令) |
| **日常开发流程？** | **[开发最佳实践](#开发最佳实践)** ⭐ |
| **Docker 热重载开发？** | **[docs/guides/development.md](docs/guides/development.md)** ⭐ |
| 检测服务在哪个端口？ | [服务端口与 API 文档](#服务端口与-api-文档) |
| 如何切换 Agent 版本？ | [模型管理 › Agent 版本切换](#模型管理) |
| RAG 服务如何启动？ | RAG 已集成到主 Agent，无需独立启动 |
| 检测服务如何调用？ | [服务端口与 API 文档 › 检测服务路由](#服务端口与-api-文档) |
| Docker ONNX 部署说明 | [常用命令 › Docker ONNX 部署](#常用命令) |

---

**相关文档**：[docs/README.md](docs/README.md) | [docs/commands.md](docs/commands.md) | [docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## Superpowers Skills（开发工作流）

> 来源：[obra/superpowers](https://github.com/obra/superpowers)

### 可用技能

| 技能 | 触发场景 | 功能 |
|------|---------|------|
| **brainstorming** | 开始新功能开发前 | 通过对话提炼需求，生成设计文档 |
| **writing-plans** | 设计文档批准后 | 生成详细实现计划 |
| **test-driven-development** | 编写代码时 | RED-GREEN-REFACTOR 循环 |
| **systematic-debugging** | 遇到 bug 时 | 4 阶段根因分析流程 |
| **verification-before-completion** | 任务完成前 | 确保问题真正修复 |
| **executing-plans** | 批量执行任务 | 带检查点的计划执行 |
| **subagent-driven-development** | 复杂任务 | 两阶段审查快速迭代 |

---

## PUA Skills（抗放弃引擎）

> 来源：[tanweai/pua](https://github.com/tanweai/pua)
> 让 AI 不敢摆烂，穷尽所有方案才允许放弃。

### 核心能力

| 能力 | 说明 |
|------|------|
| **PUA 话术** | 让 AI 不敢放弃 |
| **调试方法论** | 5 步调试法，让 AI 有能力不放弃 |
| **能动性鞭策** | 让 AI 主动出击而非被动等待 |

### 三条铁律

1. **穷尽一切** — 没有穷尽所有方案前，禁止说"我无法解决"
2. **先做后问** — 向用户提问前，必须先用工具自行排查
3. **主动出击** — 不要只做到"刚好够用"，要端到端交付结果

### 触发条件

- 任务连续失败 2 次以上
- 即将说"我无法解决" / 建议用户手动操作
- 被动等待 — 不搜索、不读源码、只等指示
- 用户不满："try harder" / "换个方法" / "你再试试"

### 压力升级机制

| 失败次数 | 等级 | 强制动作 |
|---------|------|---------|
| L1 | 温和失望 | 切换到本质不同的方案 |
| L2 | 灵魂拷问 | 搜索完整错误 + 读源码 + 列出 3 个假设 |
| L3 | 361 考核 | 完成 7 项检查清单 |
| L4 | 毕业警告 | 最小 PoC + 隔离环境 + 不同技术栈 |

### 可用技能

| 技能 | 说明 |
|------|------|
| **pua** | 中文版 PUA 激励引擎 |
| **pua-en** | 英文版 PIP 绩效改进计划 |
| **high-agency** | v2 演进版，增加自我驱动引擎 |

---

技能定义位置：`.claude/skills/`
