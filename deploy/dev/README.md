# RuralBrain 开发环境使用指南

## 📖 概述

本目录包含 RuralBrain 项目的 Docker 开发环境配置，支持所有服务的热重载功能。

## 🏗️ 文件结构

```
deploy/dev/
├── docker-compose.dev.yml    # 开发环境编排配置
├── Dockerfile.backend        # 后端开发镜像
├── Dockerfile.planning       # 规划服务开发镜像
├── Dockerfile.detector       # 检测服务开发镜像
├── scripts/
│   ├── dev-start.sh          # 一键启动脚本
│   └── dev-stop.sh           # 一键停止脚本
└── README.md                 # 本文档
```

## 🚀 快速开始

### 前置要求

- Docker Desktop（推荐 4.0+）
- 8GB+ 内存分配给 Docker
- 已配置 `.env` 文件

### 启动开发环境

#### 方式一：使用启动脚本（推荐）

```bash
cd deploy/dev/scripts
chmod +x dev-start.sh dev-stop.sh
./dev-start.sh
```

#### 方式二：手动启动

```bash
cd deploy/dev
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
```

### 停止开发环境

```bash
cd deploy/dev/scripts
./dev-stop.sh
```

或

```bash
cd deploy/dev
docker-compose -f docker-compose.dev.yml down
```

## 🔧 热重载功能

开发环境支持以下服务的热重载：

| 服务 | 热重载方式 | 监听路径 |
|------|-----------|---------|
| 前端 | `next dev` | `frontend/my-app/src`, `frontend/my-app/app` |
| 后端 | `uvicorn --reload` | `service/`, `src/` |
| 检测服务 | `uvicorn --reload` | `src/algorithms/*/detector/` |
| 规划服务 | `uvicorn --reload` | `src/rag/` |

### 如何使用热重载

1. **前端热重载**：
   - 修改 `frontend/my-app/src/` 或 `frontend/my-app/app/` 下的文件
   - 浏览器自动刷新（1-3秒）

2. **后端热重载**：
   - 修改 `service/` 或 `src/` 下的文件
   - 容器自动重启服务（1-3秒）
   - 查看日志：`docker-compose -f docker-compose.dev.yml logs -f backend`

3. **检测服务热重载**：
   - 修改 `src/algorithms/*/detector/` 下的文件
   - 对应检测器自动重启

## 📍 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Next.js 开发服务器 |
| 后端 API | http://localhost:8080/docs | FastAPI 文档 |
| 病虫害检测 | http://localhost:8001/docs | 检测服务 API |
| 大米检测 | http://localhost:8081/docs | 检测服务 API |
| 牛只检测 | http://localhost:8002/docs | 检测服务 API |
| 规划服务 | http://localhost:8003/docs | RAG 服务 API |

## 📝 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
docker-compose -f docker-compose.dev.yml logs -f triple-detector
docker-compose -f docker-compose.dev.yml logs -f planning-service
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.dev.yml restart

# 重启特定服务
docker-compose -f docker-compose.dev.yml restart backend
```

### 进入容器调试

```bash
# 进入后端容器
docker exec -it ruralbrain-backend-dev bash

# 进入前端容器
docker exec -it ruralbrain-frontend-dev sh

# 进入检测服务容器
docker exec -it triple-detector-dev bash

# 进入规划服务容器
docker exec -it planning-service-dev bash
```

### 查看服务状态

```bash
docker-compose -f docker-compose.dev.yml ps
```

## 🔨 添加新依赖

### Python 依赖

1. 修改项目根目录的 `pyproject.toml`
2. 重建相关服务镜像：

```bash
cd deploy/dev
docker-compose -f docker-compose.dev.yml build backend planning-service triple-detector
docker-compose -f docker-compose.dev.yml up -d
```

### Node.js 依赖

1. 修改 `frontend/my-app/package.json`
2. 重建前端镜像：

```bash
cd deploy/dev
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d
```

## ⚠️ 注意事项

### Windows 环境

1. **换行符问题**：
   - `.sh` 脚本需要使用 LF 换行符
   - 解决方案：使用 Git Bash 或 WSL2 运行脚本
   - 或在 Git 中配置：`git config --global core.autocrlf input`

2. **文件监听**：
   - Windows 下的文件监听可能有延迟
   - 解决方案：使用 WSL2 运行 Docker

3. **批处理脚本**：
   - 可以创建 `.bat` 文件替代 `.sh` 脚本
   - 示例见下方

### 性能优化

1. **构建加速**：
   ```bash
   export DOCKER_BUILDKIT=1
   export COMPOSE_DOCKER_CLI_BUILD=1
   ```

2. **内存分配**：
   - 为 Docker Desktop 分配至少 8GB 内存
   - 检测服务需要至少 4GB 内存

3. **端口冲突**：
   - 如果本地已在运行服务，先停止本地服务
   - 或修改 `docker-compose.dev.yml` 中的端口映射

### 常见问题

**Q: 热重载不生效？**
- 检查卷挂载是否正确：`docker inspect ruralbrain-backend-dev`
- 手动重启服务：`docker-compose -f docker-compose.dev.yml restart backend`

**Q: 依赖安装失败？**
- 清理 Docker 缓存：`docker builder prune`
- 使用 `--no-cache` 强制重建：`docker-compose -f docker-compose.dev.yml build --no-cache`

**Q: 知识库查询失败？**
- 重新构建知识库（容器外）：`uv run python src/rag/build.py`
- 检查知识库卷挂载：`docker exec planning-service-dev ls -la /app/knowledge_base`

## 📊 与生产环境对比

| 特性 | 开发环境 | 生产环境 |
|-----|---------|---------|
| 配置文件 | `deploy/dev/docker-compose.dev.yml` | `docker-compose.yml` |
| 镜像 | 包含开发工具，源码挂载 | 最小化镜像，源码内置 |
| 启动命令 | `--reload` / `next dev` | 无 reload / `next start` |
| 代码变更 | Volume 挂载，即时生效 | 需重建镜像 |
| 日志级别 | DEBUG | INFO/WARNING |
| 资源限制 | 宽松 | 严格限制 |

## 🆘 获取帮助

如遇到问题：
1. 查看容器日志：`docker-compose -f docker-compose.dev.yml logs`
2. 检查服务状态：`docker-compose -f docker-compose.dev.yml ps`
3. 参考项目主文档：[CLAUDE.md](../../CLAUDE.md)

## 📝 版本历史

- v1.0.0 - 初始版本，支持所有服务热重载
