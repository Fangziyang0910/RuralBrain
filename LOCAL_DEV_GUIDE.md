# RuralBrain 本地开发部署指南

> 完整的本地开发环境搭建和启动指南

## 目录

- [环境准备](#环境准备)
- [服务架构说明](#服务架构说明)
- [启动步骤](#启动步骤)
- [验证部署](#验证部署)
- [常见问题](#常见问题)

---

## 环境准备

### 必需软件

| 软件 | 版本要求 | 用途 | 下载地址 |
|------|----------|------|----------|
| **Python** | 3.13+ | 后端运行环境 | https://www.python.org/downloads/ |
| **uv** | 最新版 | Python 包管理工具 | https://github.com/astral-sh/uv |
| **Node.js** | 18+ | 前端运行环境 | https://nodejs.org/ |

### 检查环境

```powershell
# 检查 Python 版本
python --version

# 检查 uv 是否安装
uv --version

# 检查 Node.js 版本
node --version
npm --version
```

### 安装依赖

```powershell
# 克隆项目（如果还没有）
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 安装 Python 依赖
uv sync

# 安装前端依赖（首次运行时自动安装，也可手动安装）
cd frontend
npm install
cd ..
```

### 配置环境变量

```powershell
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置以下必需配置：
# MODEL_PROVIDER=deepseek  # 或 glm
# API_KEY=sk-xxxxx         # 你的 API 密钥（必需）
# AGENT_VERSION=v2         # 推荐使用 V2
```

**获取 API Key**：
- DeepSeek: https://platform.deepseek.com/
- 智谱AI: https://open.bigmodel.cn/

---

## 服务架构说明

RuralBrain 采用微服务架构，本地开发需要启动 **4 个独立服务**：

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (Next.js)                      │
│                  端口: 3001                             │
│  用户界面 - 多模态输入、流式对话、工具调用可视化          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              后端主服务 (FastAPI)                       │
│                  端口: 8081                             │
│  Orchestrator Agent V2 - 意图识别、Agent 编排            │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  检测服务网关     │    │  规划咨询服务     │
│  端口: 8001      │    │  端口: 8003      │
│  (统一网关)      │    │  (RAG 知识库)    │
│ • 病虫害检测      │    │  • 7 个检索工具  │
│ • 大米品种识别    │    │  • ChromaDB      │
│ • 奶牛目标检测    │    │  • 向量检索      │
└──────────────────┘    └──────────────────┘
```

### 服务清单

| # | 服务名称 | 端口 | 启动命令 | 作用 | 是否必需 |
|---|----------|------|----------|------|----------|
| ① | **检测服务网关** | 8001 | `uv run python src/algorithms/api/main.py` | AI 检测服务（病虫害/大米/奶牛） | 检测功能必需 |
| ② | **规划咨询服务** | 8003 | `uv run python src/rag/service/main.py` | RAG 知识库服务（规划咨询） | 规划咨询必需 |
| ③ | **后端主服务** | 8081 | `uv run python run_server.py` | Agent 编排服务（核心） | ✅ 必需 |
| ④ | **前端** | 3001 | `uv run python run_frontend.py` | Web 用户界面 | ✅ 必需 |

**最小化部署**：如果只测试基础对话功能，可以只启动 ③ 和 ④，但检测和规划功能将不可用。

---

## 启动步骤

### 方式一：手动启动（推荐新手）

需要打开 **4 个独立的终端窗口**，按以下顺序启动：

#### Windows (PowerShell)

**终端 1 - 检测服务网关**
```powershell
cd D:\src\RuralBrain
uv run python src/algorithms/api/main.py
```

**终端 2 - 规划咨询服务**
```powershell
cd D:\src\RuralBrain
uv run python src/rag/service/main.py
```

**终端 3 - 后端主服务**
```powershell
cd D:\src\RuralBrain
uv run python run_server.py
```

**终端 4 - 前端**
```powershell
cd D:\src\RuralBrain
uv run python run_frontend.py
```

#### macOS / Linux

**终端 1 - 检测服务网关**
```bash
cd /path/to/RuralBrain
uv run python src/algorithms/api/main.py
```

**终端 2 - 规划咨询服务**
```bash
cd /path/to/RuralBrain
uv run python src/rag/service/main.py
```

**终端 3 - 后端主服务**
```bash
cd /path/to/RuralBrain
uv run python run_server.py
```

**终端 4 - 前端**
```bash
cd /path/to/RuralBrain
uv run python run_frontend.py
```

---

### 方式二：一键启动脚本

#### Windows

```powershell
# 在项目根目录运行
.\scripts\dev\start_all_dev.ps1
```

这会自动打开 4 个终端窗口并启动所有服务。

#### macOS / Linux

```bash
# 在项目根目录运行
bash scripts/dev/start_all_services.sh
```

---

### 方式三：后台运行（高级用户）

#### macOS / Linux

```bash
# 启动所有服务（后台运行）
bash scripts/dev/start_all_services.sh

# 查看日志
tail -f logs/*.log

# 停止所有服务
bash scripts/dev/stop_all_services.sh
```

---

## 验证部署

所有服务启动完成后，访问以下地址验证：

### 服务健康检查

| 服务 | 健康检查地址 | 说明 |
|------|-------------|------|
| 前端 | http://localhost:3001 | 用户界面 |
| 后端 API | http://localhost:8081/docs | API 文档 |
| 检测服务 | http://localhost:8001/docs | 检测 API 文档 |
| 规划服务 | http://localhost:8003/docs | 规划 API 文档 |

### 功能测试

**1. 基础对话测试**
- 访问 http://localhost:3001
- 输入："你好"
- 应该收到 Agent 的回复

**2. 检测功能测试**
- 上传一张农作物图片
- 输入："这是什么病虫害？"
- 应该返回检测结果和专业建议

**3. 规划咨询测试**
- 输入："乡村旅游如何规划？"
- 应该返回基于知识库的专业建议

---

## 常见问题

### Q1: 端口被占用怎么办？

**错误信息**：`Address already in use`

**解决方案**：
```powershell
# Windows: 查找占用端口的进程
netstat -ano | findstr :8081

# 结束进程（PID 是上一步找到的进程 ID）
taskkill /PID <PID> /F

# 或者修改 .env 文件中的端口配置
```

### Q2: API_KEY 未配置或无效

**错误信息**：`API key not configured` 或 `401 Unauthorized`

**解决方案**：
1. 检查 `.env` 文件是否存在 `API_KEY` 配置
2. 确认 API Key 格式正确（以 `sk-` 开头）
3. 验证 API Key 是否有效（登录对应平台检查）

### Q3: 知识库未加载

**错误信息**：`Knowledge base not found`

**解决方案**：
```bash
# 构建知识库
uv run python scripts/dev/build_kb_auto.py
```

### Q4: 前端无法连接后端

**检查清单**：
1. 后端服务是否正常启动（访问 http://localhost:8081/docs）
2. 前端配置的后端地址是否正确
3. 检查浏览器控制台的错误信息

### Q5: 检测服务启动失败

**可能原因**：
- 模型文件缺失
- PyTorch 未正确安装

**解决方案**：
```bash
# 重新安装依赖
uv sync

# 检查模型文件是否存在
ls src/algorithms/detection/models/
```

### Q6: uv 命令未找到

**解决方案**：
```powershell
# 安装 uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用系统 Python（需要已激活虚拟环境）
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

---

## 开发技巧

### 查看服务日志

```powershell
# 后端日志（在启动后端的终端查看）
# 前端日志（在启动前端的终端查看）
# 或查看日志文件
tail -f logs/backend.log
```

### 热重载

所有服务都已启用热重载，修改代码后会自动重启：
- **后端**：修改 Python 代码后自动重启
- **前端**：修改 React/Next.js 代码后自动刷新

### 调试模式

```bash
# 后端调试模式（会在控制台输出详细日志）
uv run python service/server.py

# 前端调试模式
cd frontend
npm run dev
```

---

## 停止服务

### 手动停止

在每个终端窗口按 `Ctrl + C` 停止对应服务。

### 一键停止

**macOS / Linux**：
```bash
bash scripts/dev/stop_all_services.sh
```

**Windows**：手动关闭所有终端窗口，或在 PowerShell 中：
```powershell
# 查找所有 Python 进程
Get-Process python | Stop-Process -Force
```

---

## 下一步

部署完成后，建议阅读：

- [项目架构文档](docs/architecture/) - 了解系统设计
- [API 文档](http://localhost:8081/docs) - 查看 API 接口
- [开发指南](docs/guides/) - 学习如何添加新功能

---

## 获取帮助

如果遇到问题：

1. 查看本文档的[常见问题](#常见问题)部分
2. 检查服务的日志文件
3. 访问项目 GitHub Issues 页面
