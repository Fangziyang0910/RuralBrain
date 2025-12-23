# RuralBrain

![LangChain](https://img.shields.io/badge/LangChain-1.0%2B-green?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0%2B-blue?style=flat-square)
![LangSmith](https://img.shields.io/badge/LangSmith-0.4%2B-orange?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square)

## 📋 项目简介

**RuralBrain（乡村智慧大脑）** 是一个复杂的乡村决策系统，利用大语言模型 Agent 技术，为乡村治理和发展提供智能化决策支持。

### 核心能力

- 🔍 **智慧识别**：自动识别和分析乡村发展中的问题与机遇
- 🔬 **自主调研**：基于 Agent 的自主信息收集与分析能力
- 🧠 **复杂决策**：多维度综合评估，提供科学的决策建议

## 🛠️ 技术栈

- **LangChain**: 构建 LLM Agent的核心框架
- **LangGraph**: 实现复杂 Agent 工作流编排
- **LangSmith**: 提供 Agent 行为可观测性和调试能力
- **Python 3.13**: 开发语言

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

#### 环境要求
- **[Docker](https://www.docker.com/get-started/)**：20.10+
- **[Docker Compose](https://docs.docker.com/compose/install/)**：1.29+
- **内存**：至少 8GB
- **磁盘空间**：至少 10GB

#### 一键部署
```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 启动所有服务（前端 + 后端 + 所有检测算法服务）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 服务访问地址
- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8080
- **API 文档**: http://localhost:8080/docs
- **病虫害检测**: http://localhost:8001
- **大米识别**: http://localhost:8081
- **奶牛检测**: http://localhost:8002

#### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

### 方式二：本地开发

#### 环境要求

在开始之前，请确保你的系统已安装以下工具：

- **[Python 3.13](https://www.python.org/downloads/)**：项目运行所需的 Python 版本。如果未安装，uv 会自动下载所需版本
- **[uv](https://github.com/astral-sh/uv)**：Python 包管理工具，用于快速安装依赖和管理虚拟环境
- **[Git](https://git-scm.com/downloads)**：版本管理工具，用于克隆和同步代码仓库
- **[WSL](https://learn.microsoft.com/zh-cn/windows/wsl/install)（推荐）**：Windows 用户推荐使用 WSL（Windows Subsystem for Linux）以获得更好的开发体验

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git

# 进入项目目录
cd RuralBrain

# 使用 uv 安装依赖并创建虚拟环境
uv sync
```

### 配置环境变量

复制 `.env.example` 文件为 `.env`,并填入你的 API 密钥:

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件,填入你的 API 密钥
# 至少需要配置以下之一:
# - DEEPSEEK_API_KEY: DeepSeek API 密钥
# - ZHIPUAI_API_KEY: 智谱AI API 密钥
```

### 运行服务

```bash
# 启动后端服务
uv run python run_server.py

# 在另一个终端启动前端服务
cd frontend/my-app
npm install
npm run dev
```

前端将运行在 http://localhost:3000，后端 API 在 http://localhost:8080

## 📦 Docker 部署说明

### Docker 镜像说明
项目包含以下 Docker 镜像：
- **ruralbrain-frontend**: Next.js 前端应用
- **ruralbrain-backend**: FastAPI 后端服务（含 Agent 系统）
- **pest-detector**: 病虫害检测服务
- **rice-detector**: 大米识别服务
- **cow-detector**: 奶牛检测服务

### Docker Compose 配置
- **[docker-compose.yml](docker-compose.yml)**: 完整的服务编排（前端 + 后端 + 所有检测服务）
- **[docker-compose.all.yml](docker-compose.all.yml)**: 仅检测算法服务编排

### 生产环境部署建议
1. 设置环境变量 `ENVIRONMENT=production`
2. 配置适当的资源限制
3. 使用 secrets 管理敏感信息
4. 启用健康检查和自动重启
5. 配置日志收集和监控

## 🎯 模型管理

RuralBrain 支持多个大语言模型供应商,可以灵活切换:

### 支持的模型

- **DeepSeek**: 高性价比的国产大模型
- **智谱AI (GLM)**: 国产领先的大语言模型

### 切换模型

在 `.env` 文件中设置 `MODEL_PROVIDER`:

```bash
# 使用 DeepSeek (默认)
MODEL_PROVIDER=deepseek

# 使用智谱AI
MODEL_PROVIDER=glm
```

详细的模型配置和使用方法,请参考 [模型管理文档](docs/model_management.md)。
