# RuralBrain Docker 部署指南

本文档介绍如何使用 Docker 部署 RuralBrain 全栈智能检测系统。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [服务说明](#服务说明)
- [配置选项](#配置选项)
- [生产环境部署](#生产环境部署)
- [故障排除](#故障排除)

## 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 至少 8GB（推荐 16GB）
- **磁盘空间**: 至少 10GB

### 软件要求
- **Docker**: 20.10 或更高版本
- **Docker Compose**: 1.29 或更高版本

### 检查 Docker 环境
```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查 Docker 运行状态
docker ps
```

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain
```

### 2. 一键启动所有服务
```bash
# 构建并启动所有服务（首次运行需要较长时间）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | Web 用户界面 |
| 后端 API | http://localhost:8080 | FastAPI 主服务 |
| API 文档 | http://localhost:8080/docs | Swagger API 文档 |
| 病虫害检测 | http://localhost:8001 | 病虫害检测服务 |
| 大米识别 | http://localhost:8081 | 大米识别服务 |
| 奶牛检测 | http://localhost:8002 | 奶牛检测服务 |

## 服务说明

### 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                   RuralBrain System                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│  │ Frontend │────▶│ Backend  │────▶│   Agent  │        │
│  │  :3000   │     │  :8080   │     │ Services │        │
│  └──────────┘     └──────────┘     └──────────┘        │
│       │                │                 │              │
│       ▼                ▼                 ▼              │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│  │  Next.js │     │ FastAPI  │     │ Pest :8001│       │
│  │          │     │ + Lang   │     │ Rice :8081│       │
│  │          │     │   Graph  │     │  Cow :8002│       │
│  └──────────┘     └──────────┘     └──────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
         ruralbrain-network (Docker Network)
```

### 服务列表

#### 1. Frontend (前端服务)
- **镜像**: ruralbrain-frontend
- **容器名**: ruralbrain-frontend
- **端口**: 3000
- **技术栈**: Next.js 14, TypeScript, Tailwind CSS
- **功能**: 提供 Web 用户界面

#### 2. Backend (后端主服务)
- **镜像**: ruralbrain-backend
- **容器名**: ruralbrain-backend
- **端口**: 8080
- **技术栈**: Python 3.13, FastAPI, LangChain, LangGraph
- **功能**: API 网关和 Agent 编排

#### 3. Pest Detector (病虫害检测)
- **镜像**: pest-detector
- **容器名**: pest-detector
- **端口**: 8001
- **功能**: 农作物病虫害识别

#### 4. Rice Detector (大米识别)
- **镜像**: rice-detector
- **容器名**: rice-detector
- **端口**: 8081
- **功能**: 大米品种识别

#### 5. Cow Detector (奶牛检测)
- **镜像**: cow-detector
- **容器名**: cow-detector
- **端口**: 8002
- **功能**: 奶牛目标检测

## 配置选项

### 环境变量

在 `docker-compose.yml` 中可以配置以下环境变量：

#### 后端服务
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - ENVIRONMENT=production
```

#### 前端服务
```yaml
environment:
  - NODE_ENV=production
  - NEXT_TELEMETRY_DISABLED=1
```

### 数据卷

以下目录会挂载到宿主机，便于数据持久化：

```yaml
volumes:
  - ./uploads:/app/uploads              # 上传文件
  - ./pest_results:/app/pest_results    # 病虫害检测结果
  - ./cow_results:/app/cow_results      # 奶牛检测结果
  - ./rice_results:/app/rice_results    # 大米识别结果
```

### 资源限制

可以在 `docker-compose.yml` 中为每个服务设置资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

## 生产环境部署

### 1. 使用环境变量文件

创建 `.env` 文件：
```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

### 2. 配置反向代理（推荐）

使用 Nginx 作为反向代理：

```nginx
upstream frontend {
    server localhost:3000;
}

upstream backend {
    server localhost:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 使用 HTTPS

配置 SSL 证书：
```bash
# 使用 Let's Encrypt
certbot --nginx -d your-domain.com
```

### 4. 健康检查

所有服务都配置了健康检查：
```bash
# 检查服务健康状态
docker-compose ps

# 测试健康检查端点
curl http://localhost:8080/docs
curl http://localhost:8001/health
curl http://localhost:8081/health
curl http://localhost:8002/health
```

### 5. 日志管理

```bash
# 查看所有日志
docker-compose logs

# 查看特定服务日志
docker-compose logs frontend
docker-compose logs backend

# 实时查看日志
docker-compose logs -f

# 配置日志轮转
```

在 `docker-compose.yml` 中配置：
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 常用命令

### 服务管理
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看资源使用情况
docker stats
```

### 构建和更新
```bash
# 重新构建镜像
docker-compose build

# 重新构建并启动
docker-compose up -d --build

# 重新构建特定服务
docker-compose build backend
```

### 清理
```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、数据卷
docker-compose down -v

# 删除未使用的镜像
docker image prune

# 删除所有未使用的资源
docker system prune -a
```

## 仅启动检测服务

如果只需要启动检测算法服务（不包含前后端）：

```bash
# 使用 docker-compose.all.yml
docker-compose -f docker-compose.all.yml up -d

# 查看状态
docker-compose -f docker-compose.all.yml ps
```

## 故障排除

### 问题 1: 端口被占用
```bash
# 检查端口占用
netstat -ano | findstr :3000
netstat -ano | findstr :8080

# 修改 docker-compose.yml 中的端口映射
ports:
  - "3001:3000"  # 将宿主机端口改为 3001
```

### 问题 2: 服务启动失败
```bash
# 查看服务日志
docker-compose logs [service-name]

# 查看详细错误信息
docker-compose logs --tail=100 [service-name]

# 进入容器调试
docker-compose exec backend bash
```

### 问题 3: 内存不足
```bash
# 增加 Docker 内存限制
# Docker Desktop -> Settings -> Resources -> Memory

# 或者在 docker-compose.yml 中限制内存
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

### 问题 4: 网络连接问题
```bash
# 检查网络
docker network ls
docker network inspect ruralbrain-network

# 重建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 问题 5: 文件权限问题
```bash
# Linux/Mac: 修改文件权限
chmod -R 755 ./uploads
chmod -R 755 ./pest_results
chmod -R 755 ./cow_results
chmod -R 755 ./rice_results
```

## 监控和调试

### 查看服务健康状态
```bash
# 检查所有服务
docker-compose ps

# 测试 API 端点
curl http://localhost:8080/docs
curl http://localhost:8001/health
curl http://localhost:8081/health
curl http://localhost:8002/health
```

### 性能监控
```bash
# 查看资源使用
docker stats

# 查看容器详情
docker inspect ruralbrain-backend
```

## 更多信息

- [项目主文档](../PROJECT_OVERVIEW.md)
- [README](../README.md)
- [病虫害检测服务文档](../src/algorithms/pest_detection/DOCKER_DEPLOY.md)

---

**最后更新**: 2025年12月23日
**版本**: v1.1.0
