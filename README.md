# RuralBrain（乡村智慧大脑）

![LangChain](https://img.shields.io/badge/LangChain-1%2E0-green?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-1%2E0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3%2E13-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0%2E115-green?style=flat-square)
![Next.js](https://img.shields.io/badge/Next%2Ejs-14-black?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%2E0-blue?style=flat-square)

## 项目简介

**RuralBrain（乡村智慧大脑）** 是一个基于 LangChain/LangGraph 的乡村决策系统，采用微服务架构，为乡村治理和发展提供智能化决策支持。

### 核心能力

- 🏘️ **智能规划咨询**：基于 RAG 知识库的乡村规划智能咨询服务
- 🔍 **AI 检测服务**：病虫害检测、大米品种识别、奶牛目标检测
- 💰 **智能定价分析**：农产品定价因素分析和建议
- 🤖 **Agent 系统**：V2 Skills 架构，渐进式披露，按需加载能力

## 架构概览

```
前端 (3001) → 后端服务 (8081) → 检测服务网关 (8001)
                            ↓           ├─ /detection/pest (病虫害)
                            ↓           ├─ /detection/rice (大米)
                            ↓           └─ /detection/cow (奶牛)
                       RAG 知识库 (集成到主 Agent)
```

## 技术栈

### 后端核心
- **Python 3.13+**：开发语言
- **LangChain/LangGraph 1.0+**：Agent 框架和工作流编排
- **FastAPI**：RESTful API 服务
- **uv**：Python 包管理

### AI/ML
- **ONNX Runtime**：轻量级推理引擎
- **Ultralytics YOLO**：目标检测模型
- **ChromaDB**：向量数据库（RAG）

### 前端
- **Next.js 14**：React 框架
- **TypeScript**：类型安全
- **Tailwind CSS + Radix UI**：样式和组件

## 快速开始

### Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 启动开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

### 本地开发（受限模式）

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Keys

# 启动核心服务
uv run python run_server.py      # 后端
uv run python run_frontend.py    # 前端
```

> ⚠️ **注意**: 以上仅启动核心服务。完整功能（规划咨询、图像检测）需要额外启动检测服务（8001）。详见 [快速开始指南](docs/guides/getting-started.md)。

> 📖 **详细命令**：查看 [统一命令参考](docs/commands.md) 获取完整的部署、测试和故障排查命令。

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3001 | Next.js 应用 |
| 后端 API | 8081 | FastAPI 主服务（包含 RAG 知识库） |
| 检测服务网关 | 8001 | 统一检测服务（病虫害/大米/奶牛） |

> 📍 **完整端口配置**：详见 [统一命令参考 - 服务端口分配](docs/commands.md#附录服务端口分配)

## API 文档

- **后端 API**：http://localhost:8081/docs（包含 RAG 知识库功能）
- **检测服务网关**：http://localhost:8001/docs

## 模型管理

RuralBrain 支持多个大语言模型供应商：

```bash
# .env 配置
MODEL_PROVIDER=deepseek  # 或 glm
DEEPSEEK_API_KEY=your_key_here
```

支持：**DeepSeek**（默认）、**智谱AI (GLM)**

## 项目结构

```
RuralBrain/
├── service/           # FastAPI 主服务
├── src/              # 核心代码
│   ├── agents/      # Agent 系统（V2 Skills 架构）
│   ├── algorithms/  # 检测算法服务
│   └── rag/         # RAG 知识库系统
├── frontend/         # Next.js 前端应用
├── docker/          # Docker 配置
└── docs/            # 项目文档
```

## 文档导航

### 📚 按场景查找

| 我想... | 查看文档 |
|---------|----------|
| 快速开始项目 | [快速开始指南](docs/guides/getting-started.md) |
| 了解系统设计 | [系统架构设计](docs/architecture/system-design.md) |
| 了解 V2 Agent | [V2 Agent 架构设计](docs/architecture/v2-agent-architecture.md) |
| 查看所有命令 | [统一命令参考](docs/commands.md) |
| 排查问题 | [故障排查指南](docs/guides/troubleshooting.md) |
| 了解重要决策 | [架构决策记录](docs/decisions/) |

### 🏗️ 架构设计文档

- [系统架构设计](docs/architecture/system-design.md) - 整体架构设计理念
- [V2 Agent 架构设计](docs/architecture/v2-agent-architecture.md) - Progressive Disclosure 设计
- [微服务架构设计](docs/architecture/microservices.md) - 微服务拆分和通信

### 💡 重要决策记录

- [检测服务网关化决策](docs/decisions/detection-gateway.md) - 为什么统一检测服务
- [Agent V2 迁移决策](docs/decisions/agent-v2-migration.md) - V2 架构升级背景
- [端口统一决策](docs/decisions/port-unification.md) - 端口规范说明

### 📖 操作指南

- [快速开始](docs/guides/getting-started.md) - Docker 和本地部署
- [开发工作流](docs/guides/development.md) - 热重载和测试流程
- [故障排查](docs/guides/troubleshooting.md) - 常见问题解决

## 变更日志

查看 [CHANGELOG.md](docs/CHANGELOG.md) 了解版本更新和架构变更。

## 许可证

本项目采用 Apache License 2.0 开源协议。详见 [LICENSE](LICENSE) 文件。
