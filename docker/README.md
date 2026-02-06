# RuralBrain Docker 使用指南

## 📖 概述

本目录包含 RuralBrain 项目的所有 Docker 配置文件，包括开发环境和生产环境。

**重要**：开发必须使用 Docker 热重载模式，确保开发环境与生产环境一致。

## 🏗️ 文件结构

```
docker/
├── docker-compose.yml              # 生产环境编排配置
├── docker-compose.dev.yml          # 开发环境编排配置（支持热重载）
├── Dockerfile.backend              # 后端服务镜像
├── Dockerfile.detector             # 检测服务统一网关镜像
├── Dockerfile.detector.dev         # 检测服务开发镜像
├── Dockerfile.planning             # 规划服务镜像
├── Dockerfile.planning.dev         # 规划服务开发镜像
├── nginx.conf                      # Nginx 配置（可选）
└── README.md                       # 本文档
```

## 🚀 快速开始

### 前置要求

- Docker Desktop（推荐 4.0+）
- 8GB+ 内存分配给 Docker
- 已配置 `.env` 文件（在项目根目录）

### 开发环境（强制）

**所有开发工作必须使用 Docker 热重载模式进行**

```bash
# 进入 docker 目录
cd docker

# 构建并启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

### 生产环境部署

```bash
# 进入 docker 目录
cd docker

# 启动生产环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔧 热重载功能

开发环境支持以下服务的热重载：

| 服务 | 热重载方式 | 监听路径 |
|------|-----------|---------|
| 前端 | Next.js HMR | `frontend/` |
| 后端 | uvicorn --reload | `service/`, `src/` |
| 检测服务 | uvicorn --reload | `src/algorithms/` |
| 规划服务 | uvicorn --reload | `src/rag/` |

### 热重载工作流程

1. **启动服务**：`docker-compose -f docker-compose.dev.yml up -d`
2. **修改代码**：在本地编辑器中修改文件
3. **自动重载**：容器自动检测变更并重启服务（1-3秒）
4. **验证更改**：通过浏览器或 API 测试

## 📍 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3001 | Next.js 应用 |
| 后端 API | http://localhost:8081/docs | FastAPI 文档 |
| 检测服务 | http://localhost:8001/docs | 统一检测网关 |
| 规划服务 | http://localhost:8003/docs | RAG 服务 |

**注意**：所有检测服务（病虫害、大米、奶牛）统一使用 8001 端口，通过路由前缀区分：
- `/detection/pest/*` - 病虫害检测
- `/detection/rice/*` - 大米识别
- `/detection/cow/*` - 奶牛检测

## 📝 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
docker-compose -f docker-compose.dev.yml logs -f detection-service
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
docker exec -it ruralbrain-backend bash

# 进入前端容器
docker exec -it ruralbrain-frontend sh

# 进入检测服务容器
docker exec -it ruralbrain-detection-service-dev bash

# 进入规划服务容器
docker exec -it ruralbrain-planning-service-dev bash
```

## 🔨 添加新依赖

### Python 依赖

1. 修改项目根目录的 `pyproject.toml`
2. 重建相关服务镜像：

```bash
# 重建并启动所有服务
docker-compose -f docker-compose.dev.yml up -d --build

# 或重建特定服务
docker-compose -f docker-compose.dev.yml build backend
docker-compose -f docker-compose.dev.yml up -d
```

### Node.js 依赖

1. 修改 `frontend/package.json`
2. 重建前端镜像：

```bash
docker-compose -f docker-compose.dev.yml up -d --build frontend
```

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
   - 或修改 `docker-compose.dev.yml` 中的端口映射

### 常见问题

**Q: 热重载不生效？**
- 检查卷挂载是否正确
- 手动重启服务：`docker-compose -f docker-compose.dev.yml restart backend`

**Q: 依赖安装失败？**
- 清理 Docker 缓存：`docker builder prune`
- 使用 `--no-cache` 强制重建

**Q: 镜像构建失败？**
- 检查网络连接
- 清理构建缓存：`docker system prune -a`

## 📊 环境对比

| 特性 | 开发环境 | 生产环境 |
|-----|---------|---------|
| 配置文件 | `docker-compose.dev.yml` | `docker-compose.yml` |
| 镜像 | 包含开发工具，源码挂载 | 最小化镜像，源码内置 |
| 启动命令 | `--reload` | 无 reload |
| 代码变更 | Volume 挂载，即时生效 | 需重建镜像 |
| 日志级别 | DEBUG | INFO |

## 🆘 获取帮助

如遇问题：
1. 查看容器日志：`docker-compose logs`
2. 检查服务状态：`docker-compose ps`
3. 参考项目主文档：[CLAUDE.md](../CLAUDE.md)

## 📝 版本历史

- v2.0.0 - 优化 Docker 配置，统一 uv 安装方式，移除临时修复配置
- v1.0.0 - 初始版本
