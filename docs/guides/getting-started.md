# RuralBrain 快速开始

## 环境要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 至少 8GB（推荐 16GB）
- **磁盘空间**: 至少 10GB

### 软件要求

#### Docker 部署（推荐）
- **Docker**: 20.10 或更高版本
- **Docker Compose**: 1.29 或更高版本

#### 本地开发
- **Python**: 3.13+
- **Node.js**: 20+
- **uv**: Python 包管理器

---

## Docker 部署（推荐）

### 快速启动

```bash
# 进入 docker 目录
cd docker

# 启动开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3001 | Web 用户界面 |
| 后端 API | http://localhost:8081 | FastAPI 主服务 |
| API 文档 | http://localhost:8081/docs | Swagger 文档 |
| 检测服务 | http://localhost:8001 | 统一检测服务网关 |
| 规划咨询 | http://localhost:8003 | RAG 知识库服务 |

### 停止服务

```bash
cd docker
docker-compose -f docker-compose.dev.yml down
```

---

## 本地开发

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
AGENT_VERSION=v2
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

## 知识库构建

规划咨询服务需要先构建知识库：

```bash
uv run python src/rag/build.py
```

---

## 验证部署

### 健康检查

```bash
# 后端服务
curl http://localhost:8081/health

# 检测服务网关
curl http://localhost:8001/health

# 规划咨询服务
curl http://localhost:8003/health
```

### 功能测试

```bash
# 快速测试
bash scripts/dev/test_services.sh --fast

# 正常测试
bash scripts/dev/test_services.sh --normal
```

---

## 更多命令

详细的命令说明请参考 [统一命令参考](../commands.md)。

---

## 相关文档

- [开发工作流](development.md) - 热重载和测试流程
- [统一命令参考](../commands.md) - 完整命令列表
- [故障排查](troubleshooting.md) - 常见问题解决

---

**最后更新**: 2026-02-11
