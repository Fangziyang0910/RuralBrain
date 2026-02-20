# RuralBrain 统一命令参考

> 本文档是 RuralBrain 项目的唯一命令参考来源。所有命令的维护和更新都应在此文档进行。

---

## 目录

1. [环境准备](#1-环境准备)
2. [Docker 命令](#2-docker-命令)
3. [本地开发命令](#3-本地开发命令)
4. [测试验证命令](#4-测试验证命令)
5. [知识库管理](#5-知识库管理)
6. [故障排查](#6-故障排查)
7. [服务访问地址](#7-服务访问地址)

---

## 1. 环境准备

### 1.1 安装 uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.2 同步依赖

```bash
uv sync
```

### 1.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置 API Keys
# MODEL_PROVIDER=deepseek  # 或 glm
# API_KEY=sk-xxxxx         # 你的 API 密钥（必需）
```

**获取 API Key**：
- DeepSeek: https://platform.deepseek.com/
- 智谱AI: https://open.bigmodel.cn/

---

## 2. Docker 命令

### 2.1 开发环境（热重载模式）

#### 启动服务

```bash
# 进入 docker 目录
cd docker

# 启动所有服务（后台运行）
docker compose -f docker-compose.dev.yml up -d

# 或查看日志运行
docker compose -f docker-compose.dev.yml up
```

#### 管理服务

| 操作 | 命令 |
|------|------|
| 查看状态 | `docker compose -f docker-compose.dev.yml ps` |
| 查看日志 | `docker compose -f docker-compose.dev.yml logs -f` |
| 查看特定服务日志 | `docker compose -f docker-compose.dev.yml logs -f <service>` |
| 停止服务 | `docker compose -f docker-compose.dev.yml down` |
| 停止并删除卷 | `docker compose -f docker-compose.dev.yml down -v` |
| 重启服务 | `docker compose -f docker-compose.dev.yml restart <service>` |

#### 热重载工作流程

开发环境支持热重载，修改代码后服务会自动重启：

1. 启动服务：`cd docker && docker compose -f docker-compose.dev.yml up -d`
2. 修改代码文件
3. 等待 1-3 秒，服务自动重启
4. 验证更改：`bash scripts/dev/health_check.sh --quick`

### 2.2 生产环境

#### 启动服务

```bash
cd docker
docker compose up -d
```

#### 管理服务

| 操作 | 命令 |
|------|------|
| 查看状态 | `docker compose ps` |
| 查看日志 | `docker compose logs -f` |
| 停止服务 | `docker compose down` |

### 2.3 环境切换

使用环境切换脚本方便地在开发/生产模式间切换：

```bash
# 切换到生产模式
bash scripts/dev/switch_to_production.sh

# 切换到开发模式
bash scripts/dev/switch_to_development.sh
```

### 2.4 构建镜像

```bash
# 使用构建脚本（推荐）
bash scripts/dev/build-onnx-images.sh  # Linux/macOS
.\scripts\dev\build-onnx-images.ps1    # Windows PowerShell

# 或手动构建
cd docker
docker build -f Dockerfile.backend.onnx -t ruralbrain-backend:onnx .
docker build -f Dockerfile.detection.onnx -t ruralbrain-detection-service:onnx .
docker build -f Dockerfile.planning.onnx -t ruralbrain-planning-service:onnx .
```

---

## 3. 本地开发命令

### 3.1 直接启动服务（不使用 Docker）

| 服务 | 命令 |
|------|------|
| 后端服务 | `uv run python run_server.py` |
| 前端服务 | `uv run python run_frontend.py` |
| 检测服务网关 | `uv run python src/algorithms/api/main.py` |
| 规划咨询服务 | `uv run python src/rag/service/main.py` |

### 3.2 单服务调试

```bash
# 进入 docker 目录
cd docker

# 仅启动后端
docker compose -f docker-compose.dev.yml up -d backend

# 仅启动前端
docker compose -f docker-compose.dev.yml up -d frontend

# 仅启动检测服务
docker compose -f docker-compose.dev.yml up -d detection-service

# 仅启动规划服务
docker compose -f docker-compose.dev.yml up -d planning-service
```

### 3.3 进入容器调试

```bash
# 进入后端容器
docker exec -it ruralbrain-backend bash

# 进入前端容器
docker exec -it ruralbrain-frontend sh

# 进入检测服务容器
docker exec -it ruralbrain-detection-service bash

# 进入规划服务容器
docker exec -it ruralbrain-planning-service bash
```

---

## 4. 测试验证命令

### 4.1 健康检查

```bash
# 完整健康检查
bash scripts/dev/health_check.sh

# 快速检查
bash scripts/dev/health_check.sh --quick

# 检查特定服务
bash scripts/dev/health_check.sh --service backend
bash scripts/dev/health_check.sh --service frontend
bash scripts/dev/health_check.sh --service detection
bash scripts/dev/health_check.sh --service planning

# 详细输出
bash scripts/dev/health_check.sh --verbose
```

### 4.2 功能测试

```bash
# 快速测试（< 30秒）
bash scripts/dev/test_services.sh --fast

# 正常测试（< 2分钟）
bash scripts/dev/test_services.sh --normal

# 完整测试（< 5分钟）
bash scripts/dev/test_services.sh --full

# 详细输出
bash scripts/dev/test_services.sh --fast --verbose

# 遇到错误继续测试
bash scripts/dev/test_services.sh --continue
```

### 4.3 生产环境测试

```bash
bash scripts/dev/test_production.sh
```

### 4.4 服务状态检查

```bash
# 使用检查脚本
bash scripts/dev/check_services.sh

# 或手动检查端口
lsof -i :3001  # 前端
lsof -i :8081  # 后端
lsof -i :8001  # 检测服务
lsof -i :8003  # 规划服务
```

---

## 5. 知识库管理

### 5.1 知识库位置

- **向量数据库**: `knowledge_base/chroma_db/`
- **原始文档**: `knowledge_base/documents/`（需要您手动放置调研文档）

### 5.2 构建知识库

> **注意**：知识库构建脚本已被 Docker Compose 工作流替代。规划服务启动时会自动检测并加载已存在的知识库。

**首次使用时**，如果 `knowledge_base/chroma_db/` 目录为空：

```bash
# 使用现有的构建脚本（硬编码特定文件）
uv run python src/rag/build.py
```

**Docker 部署时**，知识库通过卷挂载自动持久化：

```yaml
# docker-compose.dev.yml
planning-service:
  volumes:
    - ./knowledge_base:/app/knowledge_base  # 自动挂载
```

### 5.3 支持的文档格式

- PDF（`.pdf`）
- Word（`.docx`, `.doc`）
- PowerPoint（`.pptx`）
- 文本（`.txt`, `.md`）

文档加载器位于：[src/rag/utils/loaders.py](../src/rag/utils/loaders.py)

---

## 6. 故障排查

### 6.1 查看日志

```bash
# 所有服务
cd docker && docker compose -f docker-compose.dev.yml logs -f

# 特定服务
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f detection-service
docker compose -f docker-compose.dev.yml logs -f planning-service
```

### 6.2 常见问题

| 问题 | 解决方案 |
|------|----------|
| 端口被占用 | 使用 `lsof -i :<port>` (Linux/macOS) 或 `netstat -ano \| findstr :<port>` (Windows) 查看占用进程 |
| 服务启动失败 | 检查 `.env` 配置，确保 API Keys 正确 |
| 镜像构建失败 | 检查 Docker 是否运行，确保磁盘空间充足 |
| 热重载不工作 | 检查卷挂载配置，确保使用 `docker-compose.dev.yml` |
| 知识库未加载 | 运行 `uv run python scripts/dev/build_kb_auto.py` |

### 6.3 添加新依赖

```bash
# 添加 Python 依赖
uv add <package-name>

# 重建镜像
cd docker
docker compose -f docker-compose.dev.yml build <service>
```

---

## 7. 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端界面** | http://localhost:3001 | Web 用户界面 |
| **后端 API 文档** | http://localhost:8081/docs | Swagger 文档 |
| **检测服务文档** | http://localhost:8001/docs | 统一检测网关文档 |
| **规划服务文档** | http://localhost:8003/docs | RAG 服务文档 |

### 检测服务路由

所有检测服务整合在统一网关（端口 8001）：

```
http://localhost:8001
├── /detection/pest/predict    # 病虫害检测
├── /detection/rice/predict    # 大米品种识别
├── /detection/cow/predict     # 奶牛检测
└── /health                     # 健康检查
```

---

## 附录：服务端口分配

| 服务 | 端口 | 配置位置 |
|------|------|----------|
| 前端 | 3000/3001 | `frontend/package.json` + `docker-compose.dev.yml` |
| 后端主服务 | 8081 | `service/settings.py` + `.env` |
| 检测服务网关 | 8001 | `src/algorithms/api/main.py` |
| 规划咨询服务 | 8003 | `src/rag/service/main.py` |

---

**最后更新**: 2026-02-20
**维护者**: RuralBrain Team
