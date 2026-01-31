# RuralBrain（乡村智慧大脑）

![LangChain](https://img.shields.io/badge/LangChain-1%2E0-green?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-1%2E0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3%2E13-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0%2E115-green?style=flat-square)
![Next.js](https://img.shields.io/badge/Next%2Ejs-14-black?style=flat-square)
![PyTorch](https://img.shields.io/badge/PyTorch-2%2E0-red?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%2E0-blue?style=flat-square)

## 📋 项目简介

**RuralBrain（乡村智慧大脑）** 是一个基于 LangChain/LangGraph 的乡村决策系统，采用微服务架构，为乡村治理和发展提供智能化决策支持。

### 核心能力

- 🏘️ **智能规划咨询**：基于 RAG 知识库的乡村规划智能咨询服务
- 🔍 **AI 检测服务**：病虫害检测、大米品种识别、奶牛目标检测
- 💰 **智能定价分析**：农产品定价因素分析和建议
- 🤖 **Agent 系统**：使用 LangGraph 编排的智能体工作流

## 🏗️ 微服务架构

```
前端 (3000) → 后端服务 (8080) → 检测服务网关 (8001)
                            ↓           ├─ /detection/pest (病虫害)
                            ↓           ├─ /detection/rice (大米)
                            ↓           └─ /detection/cow (奶牛)
                       规划服务 (8003) ← RAG 知识库
```

## 🛠️ 技术栈

### 后端核心
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

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

#### 环境要求
- **[Docker](https://www.docker.com/get-started/)**：20.10+
- **[Docker Compose](https://docs.docker.com/compose/install/)**：1.29+
- **内存**：至少 8GB
- **磁盘空间**：至少 10GB

#### 部署步骤

**生产环境部署**：
```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain/docker

# 构建并启动所有服务
docker-compose -p ruralbrain up -d --build

# 查看服务状态
docker-compose -p ruralbrain ps

# 查看日志
docker-compose -p ruralbrain logs -f
```

**开发环境部署（支持热重载）**：
```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain/docker

# 构建并启动所有服务
docker-compose -f docker-compose.dev.yml -p ruralbrain up -d --build

# 查看服务状态
docker-compose -f docker-compose.dev.yml -p ruralbrain ps

# 查看日志
docker-compose -f docker-compose.dev.yml -p ruralbrain logs -f
```

**停止服务**：
```bash
# 生产环境
cd docker
docker-compose -p ruralbrain down

# 开发环境
docker-compose -f docker-compose.dev.yml -p ruralbrain down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml -p ruralbrain down -v
```

### 方式二：本地开发

#### 环境要求
- **[Python 3.13](https://www.python.org/downloads/)**：项目运行所需的 Python 版本
- **[uv](https://github.com/astral-sh/uv)**：Python 包管理工具
- **[Node.js 18+](https://nodejs.org/)**：前端运行环境

#### 安装依赖
```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 使用 uv 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

#### 运行服务
```bash
# 启动后端服务
uv run python run_server.py

# 在另一个终端启动前端服务（推荐方式）
uv run python run_frontend.py

# 或者手动启动前端
cd frontend
npm install
npm run dev
```

## 📊 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | Next.js 应用 |
| 后端 API | 8080 | FastAPI 主服务 |
| 检测服务网关 | 8001 | 统一检测服务（病虫害/大米/奶牛） |
| 规划咨询 | 8003 | RAG 服务 |

### 检测服务路由
所有检测服务整合在统一网关（8001），使用路由前缀区分：
- `/detection/pest/*` - 病虫害检测
- `/detection/rice/*` - 大米品种识别
- `/detection/cow/*` - 奶牛目标检测

## 📚 API 文档

- **后端 API**：http://localhost:8080/docs
- **检测服务网关**：http://localhost:8001/docs
- **规划咨询**：http://localhost:8003/docs

## 🎯 模型管理

RuralBrain 支持多个大语言模型供应商，可以灵活切换：

### 支持的模型
- **DeepSeek**：高性价比的国产大模型（默认）
- **智谱AI (GLM)**：国产领先的大语言模型

### 切换模型
在 `.env` 文件中设置 `MODEL_PROVIDER`：
```bash
# 使用 DeepSeek (默认)
MODEL_PROVIDER=deepseek

# 使用智谱AI
MODEL_PROVIDER=glm
```

详细的模型配置和使用方法，请参考 [模型管理文档](docs/model_management.md)。

## 📁 项目结构

```
RuralBrain/
├── service/                # FastAPI 主服务
├── src/                    # 核心代码
│   ├── agents/            # Agent 系统
│   ├── algorithms/        # 独立检测算法服务
│   └── rag/               # RAG 知识库系统
├── frontend/              # Next.js 前端应用
├── docker/                # Docker 配置
├── tests/                 # 测试文件
├── scripts/               # 脚本文件
└── docs/                  # 项目文档
```

## 📄 许可证

本项目采用 Apache License 2.0 开源协议。详见 [LICENSE](LICENSE) 文件。
