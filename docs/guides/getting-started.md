# RuralBrain 快速开始

## 首页阅读建议

> **新用户必读**：如果你是第一次接触本项目，请按顺序阅读本文档。日常开发请参考 [开发工作流指南](development.md)。

---

## 环境要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 至少 8GB（推荐 16GB）
- **磁盘空间**: 至少 10GB

### 软件要求

#### Docker 部署（推荐）⭐
- **Docker**: 20.10 或更高版本
- **Docker Compose**: 1.29 或更高版本

> **为什么推荐 Docker**：
> - 环境隔离，避免依赖冲突
> - 热重载开发，代码修改自动生效
> - 一键启动所有服务
> - 轻量级 ONNX 镜像（~10GB）

#### 本地开发（不推荐）
- **Python**: 3.13+
- **Node.js**: 20+
- **uv**: Python 包管理器

---

## Docker 部署（推荐）⭐

> **协作者注意**：如果你是项目协作者，请直接拉取 Docker Hub 上的镜像，无需本地构建。详见 [Docker Hub 镜像使用指南](docker-hub.md)。

### 第一步：获取镜像

#### 方式一：拉取镜像（协作者推荐）⭐

```bash
# 拉取后端服务
docker pull zwxdockerbeginner/ruralbrain:backend-onnx

# 拉取检测服务
docker pull zwxdockerbeginner/ruralbrain:detection-onnx

# 拉取规划服务
docker pull zwxdockerbeginner/ruralbrain:planning-onnx

# 拉取前端开发版
docker pull zwxdockerbeginner/ruralbrain:frontend-dev
```

> **详细说明**：参阅 [Docker Hub 镜像使用指南](docker-hub.md)

#### 方式二：本地构建（仅限镜像维护者）

如果你需要本地构建镜像（仅限镜像维护者）：

```bash
# Windows
.\scripts\dev\build-onnx-images.ps1

# Linux/macOS
bash scripts/dev/build-onnx-images.sh
```

### 第二步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# MODEL_PROVIDER=deepseek
# DEEPSEEK_API_KEY=your_api_key_here
```

### 第三步：启动开发环境

```bash
# 启动开发环境（支持热重载）
docker compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker compose -f docker-compose.dev.yml ps

# 查看日志
docker compose -f docker-compose.dev.yml logs -f
```

### 第四步：验证服务

```bash
# 快速健康检查
bash scripts/dev/check.sh --quick

# 快速功能测试
bash scripts/dev/check.sh --test fast
```

### 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3001 | Web 用户界面 |
| 后端 API | http://localhost:8081 | FastAPI 主服务 |
| API 文档 | http://localhost:8081/docs | Swagger 文档 |
| 检测服务 | http://localhost:8001 | 统一检测服务网关 |
| 规划咨询 | http://localhost:8003 | RAG 知识库服务 |

### 停止服务

```bash
# 停止服务
docker compose -f docker-compose.dev.yml down
```

---

## 下一步

现在你已经成功启动了 RuralBrain 开发环境，接下来请阅读：

1. **[开发工作流指南](development.md)** - 了解热重载开发和代码验证流程
2. **[统一命令参考](../commands.md)** - 查看完整的命令列表
3. **[项目结构指南](project-structure.md)** - 了解项目的目录结构

---

## 本地开发（不推荐）

> **注意**：本地开发需要手动管理多个服务和依赖，容易出现环境问题。强烈建议使用 Docker 部署。

如果你确实需要本地开发，请参考 [开发工作流指南](development.md) 中的详细说明。

### 1. 安装依赖

```bash
# 使用 uv 同步依赖
uv sync

# 前端依赖
cd frontend
npm install
cd ..
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**必需配置**：
```bash
MODEL_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
# 终端 1：启动后端
uv run python run_server.py

# 终端 2：启动前端
uv run python run_frontend.py
```

**方式二：手动启动**

```bash
# 后端主服务（端口 8081）
uv run python service/server.py

# 检测服务网关（端口 8001）
uv run python src/algorithms/api/main.py

# 规划服务（端口 8003）
uv run python src/rag/service/main.py

# 前端（端口 3001）
cd frontend
npm run dev
```

---

## 知识库构建（可选）

规划咨询服务需要先构建知识库：

```bash
# Docker 环境下构建
docker exec ruralbrain-planning-service python /app/src/rag/build.py

# 或使用 uv 运行（如果本地有 uv）
uv run python src/rag/build.py
```

---

## 更多命令

详细的命令说明请参考 [统一命令参考](../commands.md)。

---

## 相关文档

- **[Docker Hub 镜像使用指南](docker-hub.md)** - 镜像拉取、版本管理、协作者规范
- **[开发工作流](development.md)** ⭐ - 日常开发必读，了解热重载和测试流程
- **[Skills 开发指南](skills-development.md)** - 添加新技能的完整流程
- [统一命令参考](../commands.md) - 完整命令列表
- [故障排查](troubleshooting.md) - 常见问题解决

---

**最后更新**: 2026-02-22
