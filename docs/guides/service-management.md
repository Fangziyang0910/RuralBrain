# RuralBrain 服务管理指南

本文档详细说明 RuralBrain 项目中所有微服务的配置、启动方式和端口分配。

---

## 🏗️ 服务架构概览

RuralBrain 采用微服务架构，包含以下核心服务：

```
前端 (3000)
    ↓
后端主服务 (8080) - Orchestrator Agent V2
    ↓
    ├─→ 检测服务网关 (8001) - 整合所有检测
    └─→ 规划咨询服务 (8003) - RAG 知识库
```

---

## 🔌 端口分配规范

| 服务 | 端口 | 配置文件 | 说明 |
|------|------|----------|------|
| **前端服务** | 3000 | `frontend/package.json` | Next.js 应用 |
| **后端主服务** | 8080 | `service/settings.py` + `.env` | FastAPI + Orchestrator Agent |
| **检测服务网关** | 8001 | `src/algorithms/api/main.py` | 统一检测服务（所有检测类型） |
| **规划咨询服务** | 8003 | `src/rag/service/config.py` | RAG 知识库服务 |

### 端口规范说明
- **3000-3999**：前端服务
- **8000-8999**：后端微服务
  - 8000: 留用（可用于其他服务）
  - 8001: 检测服务统一网关
  - 8002: 留用（可用于其他服务）
  - 8003: 规划咨询服务
  - 8080: 后端主服务

---

## 📦 服务详细信息

### 1. 前端服务 (Next.js)

**位置**：`frontend/`

**配置文件**：
- `package.json`：依赖和脚本
- `next.config.mjs`：Next.js 配置

**启动方式**：
```bash
# 方式一：使用启动脚本（推荐）
uv run python run_frontend.py

# 方式二：手动启动
cd frontend
npm install          # 首次运行
npm run dev          # 开发模式（热重载）
npm run build        # 生产构建
npm start            # 生产模式
```

**访问地址**：http://localhost:3000

**依赖**：无（独立运行）

---

### 2. 后端主服务 (FastAPI + Orchestrator Agent)

**位置**：`service/`

**配置文件**：
- `service/settings.py`：主配置文件
- `service/server.py`：启动脚本
- `.env`：环境变量（端口、模型配置等）

**关键配置**：
```python
# service/settings.py
HOST = "127.0.0.1"      # 本地监听
PORT = 8080              # 默认端口（会被 .env 覆盖）
ALLOWED_ORIGINS = [...]  # CORS 配置
```

```bash
# .env
PORT=8080                # 实际运行端口
MODEL_PROVIDER=deepseek  # 模型供应商
AGENT_VERSION=v2         # Agent 版本
```

**启动方式**：
```bash
# 方式一：使用启动脚本（推荐）
uv run python run_server.py

# 方式二：手动启动
uv run python service/server.py

# 方式三：使用 uvicorn
uv run uvicorn service.server:app --host 127.0.0.1 --port 8080 --reload
```

**访问地址**：
- 服务：http://localhost:8080
- API 文档：http://localhost:8080/docs

**依赖**：
- 可选：检测服务网关（8001）用于图像检测
- 可选：规划服务（8003）用于规划咨询
- 内置：Orchestrator Agent V2，支持多模态对话

---

### 3. 检测服务网关

**位置**：`src/algorithms/api/`

**配置文件**：
- `main.py`：FastAPI 服务入口
- 环境变量：可选，使用默认配置

**关键配置**：
```python
# 默认配置
HOST = "0.0.0.0"
PORT = 8001  # 检测服务统一网关
```

**服务路由**：
```
http://localhost:8001
├── /detection/pest/*    # 病虫害检测
├── /detection/rice/*    # 大米品种识别
├── /detection/cow/*     # 奶牛检测
└── /health              # 健康检查
```

**启动方式**：
```bash
# 启动检测服务网关
uv run python src/algorithms/api/main.py
```

**访问地址**：
- 服务：http://localhost:8001
- API 文档：http://localhost:8001/docs
- 健康检查：http://localhost:8001/health

**依赖**：无（独立服务）

**支持的检测类型**：
1. **病虫害检测** - 农作物病虫害识别和防治建议
2. **大米品种识别** - 5种大米品种识别（糯米、珍珠大米、五常糯米、丝苗米、泰国香米）
3. **奶牛检测** - 牛只识别和计数

---

### 4. 规划咨询服务 (RAG)

**位置**：`src/rag/service/`

**配置文件**：
- `main.py`：FastAPI 服务入口
- `config.py`：服务配置

**关键配置**：
```python
HOST = "0.0.0.0"
PORT = 8003  # 规划咨询服务
```

**启动方式**：
```bash
# 启动规划服务
uv run python src/rag/service/main.py
```

**访问地址**：
- 服务：http://localhost:8003
- API 文档：http://localhost:8003/docs
- 健康检查：http://localhost:8003/health

**前置要求**：
- 需要先构建知识库：`uv run python scripts/dev/build_kb_auto.py`
- 知识库位置：`knowledge_base/chroma_db/`

**依赖**：
- ChromaDB：向量数据库
- sentence-transformers：文本嵌入模型

---

## 🚀 快速启动指南

### 方式一：使用启动脚本（推荐）

**启动后端和前端**：
```bash
# 终端 1：启动后端
uv run python run_server.py

# 终端 2：启动前端
uv run python run_frontend.py
```

### 方式二：使用开发脚本

**一键启动所有服务**：
```bash
# 启动所有核心服务
bash scripts/dev/start_all_services.sh

# 查看服务状态
bash scripts/dev/check_services.sh

# 停止所有服务
bash scripts/dev/stop_all_services.sh
```

### 方式三：手动启动（完整启动）

**完整启动顺序**：

1. **启动检测服务网关**（可选，用于图像检测）
```bash
uv run python src/algorithms/api/main.py
```

2. **启动规划服务**（可选，用于规划咨询）
```bash
# 先构建知识库
uv run python scripts/dev/build_kb_auto.py

# 启动服务
uv run python src/rag/service/main.py
```

3. **启动后端主服务**
```bash
uv run python service/server.py
```

4. **启动前端服务**
```bash
cd frontend
npm run dev
```

**最小启动**（仅测试对话功能）：
```bash
# 仅启动后端和前端即可（Orchestrator Agent 内置）
uv run python service/server.py
cd frontend && npm run dev
```

---

## 🔍 服务健康检查

### 检查所有服务状态

```bash
# 使用检查脚本
bash scripts/dev/check_services.sh

# 或手动检查
curl http://localhost:3000       # 前端
curl http://localhost:8080/docs  # 后端
curl http://localhost:8001/docs  # 检测服务网关
curl http://localhost:8003/docs  # 规划服务
```

### 检查端口占用

```bash
# Linux/macOS
lsof -i :3000
lsof -i :8080
lsof -i :8001
lsof -i :8003

# 或使用 ss
ss -tlnp | grep -E ":(3000|8080|8001|8003)"
```

---

## ⚙️ 环境变量配置

### 主配置文件 (.env)

```bash
# ============================================
# 后端服务配置
# ============================================
PORT=8080                          # 后端端口
HOST=127.0.0.1                     # 监听地址
ALLOWED_ORIGINS=http://localhost:3000  # CORS 配置

# ============================================
# Agent 配置
# ============================================
MODEL_PROVIDER=deepseek             # 模型供应商（deepseek/glm）
MODEL_TEMPERATURE=0                # 模型温度（0-1）
AGENT_VERSION=v2                   # Agent 版本（v1/v2）
AGENT_AUTO_FALLBACK=true           # V2 失败时自动回退到 V1

# ============================================
# API Keys（配置一个即可）
# ============================================
DEEPSEEK_API_KEY=your_deepseek_api_key
ZHIPUAI_API_KEY=your_zhipuai_api_key

# ============================================
# LangSmith 可观测性（可选）
# ============================================
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=ruralbrain

# ============================================
# 规划服务配置（可选）
# ============================================
PLANNING_SERVICE_URL=http://localhost:8003
PLANNING_SERVICE_TIMEOUT=120        # 请求超时（秒）

# ============================================
# 检测服务配置（可选）
# ============================================
DETECTION_SERVICE_URL=http://localhost:8001
```

---

## 🐛 常见问题

### 1. 端口冲突

**问题**：启动失败，提示端口已被占用

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或修改 .env 中的端口配置
PORT=8081
```

### 2. 模块导入错误

**问题**：`ModuleNotFoundError: No module named 'xxx'`

**原因**：没有使用 uv 运行，或依赖未安装

**解决方案**：
```bash
# 同步依赖
uv sync

# 使用 uv 运行
uv run python <script>
```

### 3. 模型文件未找到

**问题**：`FileNotFoundError: model file not found`

**解决方案**：
```bash
# 确保模型文件存在于正确位置
ls src/algorithms/detection/models/

# 如果使用检测服务网关，会自动加载模型
```

### 4. CORS 错误

**问题**：前端无法访问后端 API

**解决方案**：
```bash
# 检查 .env 中 CORS 配置
ALLOWED_ORIGINS=http://localhost:3000

# 确保前端地址在允许列表中
```

### 5. 检测服务连接失败

**问题**：后端日志显示检测服务连接失败

**原因**：检测服务网关未启动或端口配置不匹配

**解决方案**：
```bash
# 1. 确认检测服务网关已启动
curl http://localhost:8001/health

# 2. 检查 .env 中配置
DETECTION_SERVICE_URL=http://localhost:8001

# 3. 如果未启动，启动检测服务
uv run python src/algorithms/api/main.py
```

### 6. RAG 查询无结果

**问题**：规划咨询返回无结果或空响应

**原因**：知识库未构建

**解决方案**：
```bash
# 重新构建知识库
uv run python scripts/dev/build_kb_auto.py

# 确认知识库目录存在
ls knowledge_base/chroma_db/
```

---

## 📊 服务依赖关系

### 核心服务（必需）
- **后端主服务** (8080)：核心服务，包含 Orchestrator Agent V2
- **前端服务** (3000)：用户界面

### 可选服务
- **检测服务网关** (8001)：用于图像检测功能
  - 病虫害检测
  - 大米品种识别
  - 奶牛检测
- **规划咨询服务** (8003)：用于规划咨询功能

**重要提示**：
- 检测服务和规划服务是可选的
- 后端主服务可以独立运行（提供纯对话功能）
- 当检测服务不可用时，Agent 会基于知识库或专业知识回答
- 当规划服务不可用时，Agent 会告知用户

---

## 🔧 开发环境配置

### Python 环境

项目使用 `uv` 作为包管理器：

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

### Node.js 环境

前端使用 npm：

```bash
cd frontend
npm install  # 安装依赖
npm run dev  # 开发模式
```

### 热重载配置

**开发模式支持热重载**：
- 后端：使用 `--reload` 参数
- 前端：Next.js 默认支持
- 检测服务：可配置 `--reload`

---

## 📈 性能优化

### 开发模式
- 后端服务启用热重载 (`reload=True`)
- 前端启用 Next.js 快速刷新
- 详细日志输出

### 生产模式
- 关闭热重载
- 使用多进程部署（`workers=N`）
- 启用 Nginx 反向代理
- 配置 HTTPS

---

## 🔗 相关文档

- [部署指南](deployment.md) - Docker 和本地部署
- [项目结构指南](project-structure.md) - 代码组织规范
- [模型管理指南](model-management.md) - 模型配置和切换
- [变更日志](../CHANGELOG.md) - 版本更新记录

---

**最后更新**: 2026-01-31
**版本**: v2.0
