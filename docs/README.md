# RuralBrain 文档中心

欢迎来到 RuralBrain 项目文档中心。本文档帮助您快速找到所需信息。

---

## 📚 快速导航

### 新手入门
- [项目概览](overview/PROJECT_OVERVIEW.md) - 了解 RuralBrain 是什么
- [快速开始](#快速开始) - 5 分钟上手

### 操作指南
- [部署指南](guides/deployment.md) - Docker 和本地部署
- [服务管理](guides/service-management.md) - 服务启动和配置
- [前端开发](guides/frontend.md) - Next.js 前端开发指南
- [项目结构](guides/project-structure.md) - 代码组织规范
- [多图上传](guides/multi-image-upload.md) - 批量图片上传功能
- [模型管理](guides/model-management.md) - 模型配置和切换

### 架构设计
- [V2 Agent 架构](architecture/v2-agent-upgrade.md) - Agent V2 架构详解

### 项目记录
- [变更日志](CHANGELOG.md) - 功能迭代和配置变更记录

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.13+
- **Node.js**: 20+
- **Docker**: 20.10+（可选，用于容器化部署）
- **uv**: Python 包管理器

### 一键启动（Docker）

```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 访问前端
open http://localhost:3001
```

### 本地开发

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，配置 API Keys

# 3. 启动后端
uv run python service/server.py

# 4. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3001 | Web 用户界面 |
| 后端 API | http://localhost:8081 | FastAPI 服务 |
| API 文档 | http://localhost:8081/docs | Swagger 文档 |
| 病虫害检测 | http://localhost:8000 | 检测服务 |
| 大米识别 | http://localhost:8001 | 检测服务 |
| 奶牛检测 | http://localhost:8002 | 检测服务 |

---

## 📂 文档结构

```
docs/
├── README.md                          # 📑 文档导航（本文件）
├── CHANGELOG.md                       # 📜 项目变更日志
│
├── guides/                            # 📚 操作指南
│   ├── deployment.md                  # 部署指南（Docker + 本地）
│   ├── service-management.md          # 服务管理和配置
│   ├── frontend.md                    # 前端开发指南
│   ├── project-structure.md           # 项目结构规范
│   ├── model-management.md            # 模型配置和管理
│   └── multi-image-upload.md          # 多图上传功能
│
├── architecture/                      # 🏗️ 架构文档
│   └── v2-agent-upgrade.md            # V2 Agent 架构详解
│
└── overview/                          # 项目概览
    └── PROJECT_OVERVIEW.md            # 项目总体介绍
```

---

## 🔍 按场景查找

### 我想...

#### 部署项目
👉 [部署指南](guides/deployment.md)

#### 了解服务架构
👉 [项目概览](overview/PROJECT_OVERVIEW.md) | [V2 Agent 架构](architecture/v2-agent-upgrade.md)

#### 启动和配置服务
👉 [服务管理指南](guides/service-management.md)

#### 开发前端功能
👉 [前端开发指南](guides/frontend.md)

#### 切换 AI 模型
👉 [模型管理指南](guides/model-management.md)

#### 查看项目更新
👉 [变更日志](CHANGELOG.md)

#### 了解代码组织
👉 [项目结构指南](guides/project-structure.md)

---

## 🛠️ 常用命令

### 服务管理

```bash
# 启动所有服务（Docker）
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart
```

### 本地开发

```bash
# 同步 Python 依赖
uv sync

# 运行 Python 代码
uv run python <script>

# 启动后端服务
uv run python service/server.py

# 启动前端服务
cd frontend && npm run dev
```

### 知识库管理

```bash
# 构建知识库
uv run python scripts/dev/build_kb_auto.py

# 启动规划服务
uv run python src/rag/service/planning_service.py
```

---

## 🎯 核心功能

### 智能检测
- **病虫害检测** - 农作物病虫害识别和防治建议
- **大米品种识别** - 大米品种识别和品质分析
- **奶牛目标检测** - 牛只识别和计数

### 智能规划
- **规划咨询** - 基于知识库的乡村规划问答
- **快速浏览** - 使用摘要快速了解文档
- **深度分析** - 完整阅读进行深度理解

### Agent 系统
- **V2 Agent** - 基于 Skills 架构的新一代 Agent
- **多模态交互** - 支持图片、文本输入
- **流式输出** - 实时返回响应结果

---

## 📖 关键概念

### Agent Skills 架构

RuralBrain V2 Agent 采用**渐进式披露（Progressive Disclosure）**设计：

- 初始只提供技能描述，Token 消耗减少 50%+
- Agent 按需加载完整技能指导
- 模块化配置，易于扩展

详细文档：[V2 Agent 架构](architecture/v2-agent-upgrade.md)

### 微服务架构

```
前端 (3000)
    ↓
后端主服务 (8081) - Orchestrator Agent
    ↓
    ├─→ 病虫害检测服务 (8000)
    ├─→ 大米识别服务 (8001)
    └─→ 奶牛检测服务 (8002)
```

### 模型管理

支持多个大语言模型供应商：

- **DeepSeek**（默认）
- **智谱AI (GLM)**

通过 `MODEL_PROVIDER` 环境变量切换。

---

## ❓ 常见问题

### Q: 服务启动失败？

**A**: 检查端口占用、环境变量配置、API Keys 是否正确。

```bash
# 检查端口占用
lsof -i :8081

# 检查配置
cat .env
```

详细解决方案：[服务管理指南 - 常见问题](guides/service-management.md#常见问题)

### Q: 如何切换 AI 模型？

**A**: 编辑 `.env` 文件，修改 `MODEL_PROVIDER`：

```bash
# 使用 DeepSeek
MODEL_PROVIDER=deepseek

# 使用智谱AI
MODEL_PROVIDER=glm
```

详细指南：[模型管理](guides/model-management.md)

### Q: Docker 部署和本地开发如何选择？

**A**:
- **Docker 部署**：适合快速体验、生产环境
- **本地开发**：适合代码修改、功能开发

### Q: 检测服务必须启动吗？

**A**: 不是。后端主服务可以独立运行（提供规划咨询功能），检测服务是可选的。

---

## 🔗 相关资源

### 项目链接
- **GitHub**: https://github.com/Fangziyang0910/RuralBrain
- **问题反馈**: https://github.com/Fangziyang0910/RuralBrain/issues

### 技术栈
- **后端**: FastAPI + LangChain + LangGraph
- **前端**: Next.js 14 + TypeScript
- **AI**: PyTorch + Ultralytics YOLO
- **向量数据库**: ChromaDB

### 参考资料
- [LangChain 官方文档](https://docs.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 💡 贡献指南

欢迎改进文档！

### 添加新文档

请遵循以下分类：

- **架构设计** → `docs/architecture/`
- **操作指南** → `docs/guides/`
- **测试报告** → `docs/reports/`
- **API 文档** → `docs/api/`

### 文档模板

```markdown
# 标题

> **版本**: v1.0
> **更新日期**: YYYY-MM-DD

## 概述

[简要说明文档目的]

## 内容

[详细内容]

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | YYYY-MM-DD | 初始版本 |
```

### 注意事项

1. **项目结构规范**: 在添加新文件前，请先阅读 [项目结构指南](guides/project-structure.md)
2. **文档同步**: 代码变更时同步更新相关文档
3. **格式统一**: 使用 Markdown 格式，保持排版整洁

---

**最后更新**: 2026-01-31
**文档版本**: v2.0
**维护者**: RuralBrain Team
