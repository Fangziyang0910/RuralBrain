# Docker ONNX 轻量级部署指南

本文档介绍如何使用基于 ONNX Runtime 的轻量级 Docker 镜像部署 RuralBrain 系统。

## 📋 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [镜像说明](#镜像说明)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [开发模式部署](#开发模式部署)
- [生产模式部署](#生产模式部署)
- [故障排查](#故障排查)
- [性能优化](#性能优化)

## 概述

RuralBrain ONNX 部署方案使用 ONNX Runtime 替代 PyTorch，实现了：

- ✅ **镜像体积减少 60-75%**（从 ~40GB 降至 ~10GB）
- ✅ **构建时间缩短**（从 15-20 分钟降至 3-5 分钟）
- ✅ **推理速度提升**（ONNX Runtime 优化）
- ✅ **内存占用降低**（轻量级依赖）

### 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户层                              │
│  前端 (http://localhost:3001)                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              后端主服务 (8081)                         │
│  - Orchestrator Agent V2                               │
│  - 工具编排与调用                                      │
│  - 流式对话管理                                         │
└─────────┬──────────────────┬────────────────────────────┘
          │                  │
    ┌─────▼─────┐      ┌─────▼──────────┐
    │  检测服务  │      │  规划咨询服务  │
    │  (8001)    │      │  (8003)        │
    │ 病虫害识别  │      │  RAG 知识库   │
    │ 大米品种    │      │  智能规划     │
    │ 奶牛检测    │      │               │
    └───────────┘      └────────────────┘
```

## 前置要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核心 | 4 核心以上 |
| 内存 | 4GB | 8GB 以上 |
| 磁盘 | 15GB | 30GB 以上 |
| 网络 | - | 稳定的互联网连接 |

### 软件要求

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **操作系统**: Windows 10/11, macOS, Linux

### 检查安装

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查 Docker 是否运行
docker info
```

## 镜像说明

### ONNX 镜像列表

| 镜像名称 | 大小 | 说明 | 基础镜像 |
|---------|------|------|----------|
| `ruralbrain-backend:onnx` | ~400MB | 后端主服务 | python:3.13-slim |
| `ruralbrain-detection-service:onnx` | ~14GB | 检测服务（含模型） | python:3.13-slim |
| `ruralbrain-planning-service:onnx` | ~13GB | 规划服务（含向量库） | python:3.13-slim |
| `ruralbrain-frontend:dev` | ~1GB | 前端开发模式 | node:20-alpine |
| `ruralbrain-frontend:onnx` | ~1GB | 前端生产模式 | node:20-alpine |

### 镜像特性

#### 后端镜像
- **轻量级依赖**: 仅包含 FastAPI、LangChain 核心库
- **无重量级包**: 移除 PyTorch、ChromaDB
- **热重载支持**: 开发模式下自动重启

#### 检测服务镜像
- **ONNX Runtime**: 替代 PyTorch 进行推理
- **统一网关**: 整合病虫害、大米、奶牛检测
- **模型内置**: YOLOv8 ONNX 模型已打包

#### 规划服务镜像
- **RAG 支持**: ChromaDB + sentence-transformers
- **知识库**: 预加载乡村规划文档
- **多模式**: fast/deep/auto 三种查询模式

#### 前端镜像
- **开发模式**: 支持热重载和实时调试
- **生产模式**: 优化的 Next.js 构建
- **现代化**: Next.js 14 + React 18 + TypeScript

## 快速开始

### 方式一：使用开发脚本（推荐）

适用于开发环境和快速测试。

#### Windows PowerShell

```powershell
# 1. 进入项目目录
cd C:\Users\PC\Documents\GitHub\RuralBrain

# 2. 构建所有 ONNX 镜像
.\scripts\dev\build-onnx-images.ps1

# 3. 启动所有服务（开发模式）
docker-compose -f docker-compose.dev.yml up -d

# 4. 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 5. 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

#### Linux/macOS

```bash
# 1. 进入项目目录
cd /path/to/RuralBrain

# 2. 构建所有 ONNX 镜像
bash scripts/dev/build-onnx-images.sh

# 3. 启动所有服务（开发模式）
docker-compose -f docker-compose.dev.yml up -d

# 4. 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 5. 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 方式二：手动部署

适用于需要自定义配置的场景。

#### 1. 准备环境文件

创建 `.env` 文件：

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# LangSmith 配置（可选，用于链路追踪）
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=RuralBrain

# 模型配置
MODEL_PROVIDER=deepseek
MODEL_NAME=deepseek-chat
TEMPERATURE=0.7
```

#### 2. 构建镜像

```bash
# 构建检测服务
docker build -f docker/Dockerfile.detection.onnx -t ruralbrain-detection-service:onnx .

# 构建规划服务
docker build -f docker/Dockerfile.planning.onnx -t ruralbrain-planning-service:onnx .

# 构建后端服务
docker build -f docker/Dockerfile.backend.onnx -t ruralbrain-backend:onnx .

# 构建前端服务（开发模式）
docker build -f docker/Dockerfile.frontend.dev -t ruralbrain-frontend:dev ./frontend
```

#### 3. 创建网络

```bash
docker network create ruralbrain-network
```

#### 4. 启动检测服务

```bash
docker run -d \
  --name ruralbrain-detection-service \
  --network ruralbrain-network \
  -p 8001:8001 \
  -e ENVIRONMENT=development \
  -e PYTHONPATH=/app/algorithms \
  --mount type=bind,source="$(pwd)/src/algorithms",target=/app/algorithms \
  ruralbrain-detection-service:onnx
```

#### 5. 启动规划服务

```bash
docker run -d \
  --name ruralbrain-planning-service \
  --network ruralbrain-network \
  -p 8003:8003 \
  --env-file .env \
  -e PYTHONUNBUFFERED=1 \
  -e ENVIRONMENT=development \
  -e SERVICE_PORT=8003 \
  -e SERVICE_HOST=0.0.0.0 \
  --mount type=bind,source="$(pwd)/knowledge_base",target=/app/knowledge_base \
  --mount type=bind,source="$(pwd)/src/rag",target=/app/src/rag \
  --mount type=bind,source="$(pwd)/src/agents",target=/app/src/agents \
  --mount type=bind,source="$(pwd)/src/utils",target=/app/src/utils \
  --mount type=bind,source="$(pwd)/src/config.py",target=/app/src/config.py \
  ruralbrain-planning-service:onnx
```

#### 6. 启动后端服务

```bash
docker run -d \
  --name ruralbrain-backend \
  --network ruralbrain-network \
  -p 8081:8081 \
  --env-file .env \
  -e PYTHONUNBUFFERED=1 \
  -e ENVIRONMENT=development \
  -e PLANNING_SERVICE_URL=http://ruralbrain-planning-service:8003 \
  -e PEST_DETECTION_API_URL=http://ruralbrain-detection-service:8001/detection/pest/detect \
  -e RICE_DETECTION_API_URL=http://ruralbrain-detection-service:8001/detection/rice/predict \
  -e COW_DETECTION_API_URL=http://ruralbrain-detection-service:8001/detection/cow/detect \
  --mount type=bind,source="$(pwd)/knowledge_base",target=/app/knowledge_base,readonly \
  --mount type=bind,source="$(pwd)/service",target=/app/service \
  --mount type=bind,source="$(pwd)/src/agents",target=/app/src/agents \
  --mount type=bind,source="$(pwd)/src/utils",target=/app/src/utils \
  --mount type=bind,source="$(pwd)/src/config.py",target=/app/src/config.py \
  --tmpfs /tmp/ruralbrain:size=500M,mode=0777 \
  ruralbrain-backend:onnx
```

#### 7. 启动前端服务（开发模式）

```bash
docker run -d \
  --name ruralbrain-frontend \
  --network ruralbrain-network \
  -p 3001:3001 \
  -e NODE_ENV=development \
  -e NEXT_TELEMETRY_DISABLED=1 \
  -e BACKEND_URL=http://ruralbrain-backend:8081 \
  --mount type=bind,source="$(pwd)/frontend",target=/app \
  --mount type=volume,target=/app/node_modules \
  --mount type=volume,target=/app/.next \
  ruralbrain-frontend:dev
```

## 详细配置

### 端口分配

| 服务 | 容器端口 | 宿主机端口 | 协议 | 说明 |
|------|----------|------------|------|------|
| 前端 | 3001 | 3001 | HTTP | Next.js 开发服务器 |
| 后端 | 8081 | 8081 | HTTP | FastAPI 主服务 |
| 检测服务 | 8001 | 8001 | HTTP | 统一检测网关 |
| 规划服务 | 8003 | 8003 | HTTP | RAG 知识库服务 |

### 卷挂载说明

#### 后端服务挂载

| 源路径 | 容器路径 | 权限 | 说明 |
|--------|----------|------|------|
| `./knowledge_base` | `/app/knowledge_base` | 只读 | 知识库文件 |
| `./service` | `/app/service` | 读写 | 服务代码（热重载） |
| `./src/agents` | `/app/src/agents` | 读写 | Agent 代码（热重载） |
| `./src/utils` | `/app/src/utils` | 读写 | 工具模块（热重载） |
| `./src/config.py` | `/app/src/config.py` | 读写 | 配置文件 |
| tmpfs | `/tmp/ruralbrain` | 读写 | 临时文件（内存） |

#### 检测服务挂载

| 源路径 | 容器路径 | 权限 | 说明 |
|--------|----------|------|------|
| `./src/algorithms` | `/app/algorithms` | 读写 | 算法代码（热重载） |

#### 规划服务挂载

| 源路径 | 容器路径 | 权限 | 说明 |
|--------|----------|------|------|
| `./knowledge_base` | `/app/knowledge_base` | 读写 | 知识库数据 |
| `./src/rag` | `/app/src/rag` | 读写 | RAG 代码（热重载） |
| `./src/agents` | `/app/src/agents` | 读写 | Agent 代码（必需） |
| `./src/utils` | `/app/src/utils` | 读写 | 工具模块（热重载） |
| `./src/config.py` | `/app/src/config.py` | 读写 | 配置文件 |

#### 前端服务挂载

| 源路径 | 容器路径 | 权限 | 说明 |
|--------|----------|------|------|
| `./frontend` | `/app` | 读写 | 前端代码（热重载） |
| - | `/app/node_modules` | 读写 | 依赖卷（独立） |
| - | `/app/.next` | 读写 | 构建缓存（独立） |

### 环境变量配置

#### 必需环境变量

```bash
# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# 模型配置（必需）
MODEL_PROVIDER=deepseek
MODEL_NAME=deepseek-chat
```

#### 可选环境变量

```bash
# LangSmith 追踪（可选）
LANGCHAIN_API_KEY=lsv2_xxxxxxxxxxx
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=RuralBrain

# 模型参数（可选）
TEMPERATURE=0.7
MAX_TOKENS=2000

# 服务配置（可选）
ENVIRONMENT=development  # 或 production
PYTHONUNBUFFERED=1
```

## 开发模式部署

开发模式支持代码热重载，修改本地代码后容器自动重启。

### 启动开发环境

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 特性

- ✅ **热重载**: 修改 Python/JS 代码后自动重启服务
- ✅ **详细日志**: 控制台输出完整的调试信息
- ✅ **源码映射**: 可以在宿主机直接修改代码
- ✅ **快速迭代**: 无需重新构建镜像

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

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
docker-compose -f docker-compose.dev.yml restart frontend
```

### 停止服务

```bash
docker-compose -f docker-compose.dev.yml down
```

## 生产模式部署

生产模式使用优化的配置和独立的构建产物。

### 启动生产环境

```bash
docker-compose -f docker-compose.onnx.yml up -d
```

### 特性

- ✅ **优化构建**: 前端使用 `npm build` 生产产物
- ✅ **只读挂载**: 源代码只读，防止意外修改
- ✅ **健康检查**: 自动监测服务状态
- ✅ **自动重启**: 服务异常时自动恢复
- ✅ **资源限制**: 可配置 CPU 和内存限制

### 生产模式配置

```yaml
services:
  backend:
    image: ruralbrain-backend:onnx
    restart: always
    healthcheck:
      interval: 30s
      timeout: 10s
      start_period: 60s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 故障排查

### 常见问题

#### 1. 端口冲突

**症状**: 服务无法启动，提示端口已被占用

**解决**:
```bash
# Windows
netstat -ano | findstr :3001
netstat -ano | findstr :8081

# Linux/macOS
lsof -i :3001
lsof -i :8081

# 杀死占用端口的进程或修改 docker-compose.yml 中的端口映射
```

#### 2. 容器无法访问后端

**症状**: 前端报错 `ECONNREFUSED`

**原因**: 环境变量配置错误

**解决**:
```bash
# 确保前端容器使用正确的环境变量
docker exec ruralbrain-frontend env | grep BACKEND_URL
# 应该输出: BACKEND_URL=http://ruralbrain-backend:8081

# 如果不正确，重启容器
docker stop ruralbrain-frontend && docker rm ruralbrain-frontend
docker run -d ... (使用正确的环境变量)
```

#### 3. 规划服务报错 `No module named 'src.agents'`

**症状**: 规划服务启动失败，日志显示模块导入错误

**原因**: 缺少 `src/agents` 目录挂载

**解决**:
```bash
# 确保规划服务挂载了 src/agents
docker inspect ruralbrain-planning-service | grep agents

# 重新创建容器，添加 src/agents 挂载
docker stop ruralbrain-planning-service && docker rm ruralbrain-planning-service
docker run -d \
  ... \
  --mount type=bind,source="$(pwd)/src/agents",target=/app/src/agents \
  ruralbrain-planning-service:onnx
```

#### 4. 大米识别无法显示标注图片

**症状**: 检测成功但图片显示失败

**原因**: OpenCV 编码问题（非致命错误）

**影响**: 检测结果正常返回，仅无法显示标注图片

**解决**: 这是已知问题，不影响核心功能。可以忽略或等待修复。

#### 5. 知识库未找到

**症状**: 规划服务日志显示 `知识库未找到`

**解决**:
```bash
# 1. 检查知识库是否存在
ls -la knowledge_base/chroma_db

# 2. 如果不存在，构建知识库
docker exec ruralbrain-planning-service python -c "
from src.rag.core.build_kb import build_knowledge_base
build_knowledge_base()
"

# 3. 或者从本地复制
docker cp knowledge_base/chroma_db ruralbrain-planning-service:/app/knowledge_base/

# 4. 重启服务
docker restart ruralbrain-planning-service
```

### 调试命令

#### 查看容器状态

```bash
# 查看所有容器
docker ps -a

# 查看容器详细信息
docker inspect ruralbrain-backend

# 查看容器资源使用
docker stats
```

#### 进入容器调试

```bash
# 进入后端容器
docker exec -it ruralbrain-backend bash

# 进入规划服务容器
docker exec -it ruralbrain-planning-service bash

# 进入检测服务容器
docker exec -it ruralbrain-detection-service bash

# 进入前端容器
docker exec -it ruralbrain-frontend sh
```

#### 测试服务连通性

```bash
# 测试后端健康检查
curl http://localhost:8081/docs

# 测试检测服务
curl http://localhost:8001/docs

# 测试规划服务
curl http://localhost:8003/docs

# 测试前端
curl http://localhost:3001
```

### 日志分析

```bash
# 实时查看日志
docker logs -f ruralbrain-backend

# 查看最近 100 行
docker logs --tail 100 ruralbrain-backend

# 查看带时间戳的日志
docker logs -t ruralbrain-backend

# 查看特定时间范围的日志
docker logs --since 2024-01-01T00:00:00 ruralbrain-backend
```

## 性能优化

### 镜像优化

#### 1. 清理未使用的镜像

```bash
# 清理悬空镜像
docker image prune -f

# 清理所有未使用的镜像
docker image prune -a -f

# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

#### 2. 清理旧镜像

```bash
# 删除旧的 latest 标签镜像
docker rmi ruralbrain-backend:latest
docker rmi ruralbrain-detection-service:latest
docker rmi ruralbrain-planning-service:latest
docker rmi ruralbrain-frontend:latest

# 仅保留 onnx 和 dev 标签
```

### 容器优化

#### 1. 限制资源使用

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

#### 2. 使用 tmpfs

```yaml
services:
  backend:
    tmpfs:
      - /tmp/ruralbrain:size=500M,mode=0777
```

### 网络优化

#### 1. 使用 Docker 网络

```bash
# 创建专用网络
docker network create --driver bridge ruralbrain-network

# 指定网络参数
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --gateway=172.20.0.1 \
  ruralbrain-network
```

#### 2. DNS 优化

```yaml
services:
  backend:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

## 附录

### A. 完整的 docker-compose.dev.yml

参见项目根目录下的 `docker-compose.dev.yml` 文件。

### B. Dockerfile 位置

| 服务 | Dockerfile 路径 |
|------|-----------------|
| 后端 | `docker/Dockerfile.backend.onnx` |
| 检测服务 | `docker/Dockerfile.detection.onnx` |
| 规划服务 | `docker/Dockerfile.planning.onnx` |
| 前端（开发） | `docker/Dockerfile.frontend.dev` |
| 前端（生产） | `docker/Dockerfile.frontend.onnx` |

### C. 相关文档

- [开发工作流指南](development-workflow.md)
- [前端开发指南](frontend.md)
- [模型管理指南](model-management.md)
- [服务管理指南](service-management.md)

### D. 获取帮助

如果遇到问题：

1. 检查本文档的[故障排查](#故障排查)部分
2. 查看容器日志获取详细错误信息
3. 确认所有环境变量配置正确
4. 验证网络连接和端口可用性

---

**文档版本**: v1.0
**最后更新**: 2026-02-09
**维护者**: RuralBrain Team
