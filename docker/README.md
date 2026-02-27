# RuralBrain Docker 使用指南

## 📖 概述

本目录包含 RuralBrain 项目的 Docker 镜像构建文件（Dockerfile）。

**重要**：开发必须使用 Docker 热重载模式，确保开发环境与生产环境一致。

## 🏗️ 文件结构

```
docker/
├── Dockerfile.backend.onnx       # 后端服务镜像（ONNX Runtime）
├── Dockerfile.detection.onnx      # 检测服务统一网关镜像（YOLO 模型）
├── Dockerfile.frontend.onnx       # 前端生产镜像（优化构建）
├── Dockerfile.frontend.dev        # 前端开发镜像（支持热重载）
├── nginx.conf                     # Nginx 配置（可选）
└── README.md                      # 本文档
```

**注意**：规划服务（`src/rag/service/`）不再作为独立容器部署，其功能已集成到主 Agent 中。

**Docker Compose 配置文件**（位于项目根目录）：
- `docker-compose.dev.yml` - 开发环境（热重载）
- `docker-compose.onnx.yml` - 生产环境（标准部署）

---

## 🚀 快速开始

### 前置要求

- Docker Desktop（推荐 4.0+）
- 8GB+ 内存分配给 Docker
- 已配置 `.env` 文件（在项目根目录）

### 协作者快速启动（推荐）⭐

**重要**：不要本地构建镜像，直接拉取 Docker Hub 上的镜像。

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要的配置

# 2. 拉取镜像（可选，启动时会自动拉取）
docker pull zwxdockerbeginner/ruralbrain:backend-onnx
docker pull zwxdockerbeginner/ruralbrain:detection-onnx

# 3. 启动开发环境（在项目根目录执行）
docker compose -f docker-compose.dev.yml up -d

# 4. 查看服务状态
docker compose -f docker-compose.dev.yml ps

# 5. 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 6. 停止服务
docker compose -f docker-compose.dev.yml down
```

> **详细说明**：参阅 [Docker Hub 镜像使用指南](../docs/guides/docker-hub.md)

### 本地构建镜像（不推荐）

如果你需要本地构建镜像（仅限镜像维护者）：

```bash
# Windows PowerShell
.\scripts\dev\build-onnx-images.ps1

# Linux/macOS
bash scripts/dev/build-onnx-images.sh
```

---

## 📦 镜像说明

### 后端服务镜像

- **镜像名**: `ruralbrain-backend:onnx`
- **基于**: Python 3.13 slim + ONNX Runtime
- **功能**: FastAPI + Orchestrator Agent V2 + 意图识别

### 检测服务镜像

- **镜像名**: `ruralbrain-detection-service:onnx`
- **基于**: Python 3.13 slim + ONNX Runtime
- **功能**: 病虫害/大米/奶牛检测统一网关
- **包含**: YOLO 模型文件（需要挂载）

### 前端镜像

| 镜像 | 文件 | 大小 | 用途 |
|------|------|------|---------|
| `ruralbrain-frontend:dev` | Dockerfile.frontend.dev | ~1.8GB | 开发环境（热重载） |
| `ruralbrain-frontend:onnx` | Dockerfile.frontend.onnx | ~1.0GB | 生产环境 |

---

## 🔧 热重载功能

开发环境支持以下服务的热重载：

| 服务 | 热重载方式 | 监听路径 |
|------|-----------|---------|
| 前端 | Next.js HMR | `frontend/` |
| 后端 | uvicorn --reload | `service/`, `src/agents/`, `src/utils/`, `src/config.py` |
| 检测服务 | uvicorn --reload | `src/algorithms/` |

### 热重载工作流程

1. **启动服务**：`docker compose -f docker-compose.dev.yml up -d`
2. **修改代码**：在本地编辑器中修改文件
3. **自动重载**：容器自动检测变更并重启服务（1-3秒）
4. **验证更改**：通过浏览器或 API 测试

---

## 📍 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3001 | Next.js 应用 |
| 后端 API | http://localhost:8081/docs | FastAPI 文档（包含 RAG 知识库） |
| 检测服务 | http://localhost:8001/docs | 统一检测网关 |

**检测服务路由**（统一网关端口 8001）：
- `/detection/pest/*` - 病虫害检测
- `/detection/rice/*` - 大米识别
- `/detection/cow/*` - 奶牛检测

---

## 📝 常用命令

> **注意**：以下命令在项目根目录执行

### 查看日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.dev.yml logs

# 查看特定服务日志
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f detection-service
```

### 重启服务

```bash
# 重启所有服务
docker compose -f docker-compose.dev.yml restart

# 重启特定服务
docker compose -f docker-compose.dev.yml restart backend
```

### 进入容器调试

```bash
# 进入后端容器
docker exec -it ruralbrain-backend bash

# 进入前端容器
docker exec -it ruralbrain-frontend sh

# 进入检测服务容器
docker exec -it ruralbrain-detection-service bash
```

---

## 🔨 添加新依赖

### Python 依赖

1. 修改项目根目录的 `pyproject.toml`
2. 重建相关服务镜像：

```bash
# 重建并启动所有服务
docker compose -f docker-compose.dev.yml up -d --build

# 或重建特定服务
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml up -d
```

### Node.js 依赖

1. 修改 `frontend/package.json`
2. 重建前端镜像：

```bash
docker compose -f docker-compose.dev.yml up -d --build frontend
```

---

## 🌐 生产环境部署

```bash
# 启动生产环境
docker compose -f docker-compose.onnx.yml up -d

# 查看服务状态
docker compose -f docker-compose.onnx.yml ps

# 查看日志
docker compose -f docker-compose.onnx.yml logs -f

# 停止服务
docker compose -f docker-compose.onnx.yml down
```

---

## ⚠️ 注意事项

### 性能优化

1. **构建加速**：
   ```bash
   export DOCKER_BUILDKIT=1
   export COMPOSE_DOCKER_CLI_BUILD=1
   ```

2. **内存分配**：
   - 为 Docker Desktop 分配至少 8GB 内存
   - 检测服务需要至少 2GB 内存

3. **端口冲突**：
   - 如果本地已在运行服务，先停止本地服务
   - 或修改 compose 文件中的端口映射

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 热重载不生效 | 检查卷挂载是否正确，手动重启：`docker compose -f docker-compose.dev.yml restart backend` |
| 依赖安装失败 | 清理 Docker 缓存：`docker builder prune` |
| 镜像构建失败 | 检查网络连接，清理构建缓存：`docker system prune -a` |
| 容器无法启动 | 检查 `.env` 配置，确保 API Keys 正确 |

---

## 📊 环境对比

| 特性 | 开发环境 | 生产环境 |
|-----|---------|---------|
| 配置文件 | `docker-compose.dev.yml` | `docker-compose.onnx.yml` |
| 镜像 | 包含开发工具，源码挂载 | 最小化镜像，源码内置 |
| 启动命令 | `--reload` | 无 reload |
| 代码变更 | Volume 挂载，即时生效 | 需重建镜像 |
| 日志级别 | DEBUG | INFO |

---

## 🔗 相关文档

- **[Docker Hub 镜像使用指南](../docs/guides/docker-hub.md)** - 镜像拉取、版本管理、协作者规范
- **[统一命令参考](../docs/commands.md)** - 完整的命令列表
- **[快速开始指南](../docs/guides/getting-started.md)** - 新用户入门
- **[开发工作流指南](../docs/guides/development.md)** - 日常开发流程

---

## 🆘 获取帮助

如遇问题：
1. 查看容器日志：`docker compose logs`
2. 检查服务状态：`docker compose ps`
3. 参考项目主文档：[CLAUDE.md](../CLAUDE.md)

---

**最后更新**: 2026-02-26
**版本**: v3.1
**维护者**: RuralBrain Team
