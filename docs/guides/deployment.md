# RuralBrain 部署指南

本文档介绍 RuralBrain 项目的部署方式，包括 Docker 部署和本地开发两种方式。

---

## 📋 目录

- [环境要求](#环境要求)
- [Docker 部署（推荐）](#docker-部署推荐)
- [本地开发](#本地开发)
- [知识库构建](#知识库构建)
- [验证部署](#验证部署)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 至少 8GB（推荐 16GB）
- **磁盘空间**: 至少 10GB

### 软件要求

#### Docker 部署
- **Docker**: 20.10 或更高版本
- **Docker Compose**: 1.29 或更高版本

#### 本地开发
- **Python**: 3.13+
- **Node.js**: 20+
- **uv**: Python 包管理器

---

## Docker 部署（推荐）

### 方式一：使用 docker 目录配置

项目提供了完整的 Docker 配置文件在 `docker/` 目录：

```bash
# 进入 docker 目录
cd docker

# 启动所有服务（生产环境）
docker-compose up -d

# 或启动开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | Next.js 应用 |
| 后端 API | http://localhost:8080 | FastAPI 主服务 |
| API 文档 | http://localhost:8080/docs | Swagger 文档 |
| 检测服务网关 | http://localhost:8001 | 统一检测服务 |
| 规划咨询 | http://localhost:8003 | RAG 知识库服务 |

### Docker 服务说明

#### 生产环境（docker-compose.yml）
- **前端**：生产构建，无热重载
- **后端**：多进程部署，性能优化
- **检测服务**：整合所有检测算法
- **规划服务**：RAG 知识库服务

#### 开发环境（docker-compose.dev.yml）
- **热重载**：代码修改自动重启服务
- **卷挂载**：源码目录映射到容器
- **调试模式**：详细的日志输出

### Docker 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]

# 重启服务
docker-compose restart [service-name]

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重新构建镜像
docker-compose build [service-name]

# 重新构建并启动
docker-compose up -d --build
```

---

## 本地开发

### 步骤 1：安装 uv 包管理器

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 步骤 2：安装项目依赖

```bash
# 同步 Python 依赖
uv sync

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 步骤 3：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

**必需配置**：
```bash
# 选择模型供应商（deepseek 或 glm）
MODEL_PROVIDER=deepseek

# 配置 API Key（二选一）
DEEPSEEK_API_KEY=your_deepseek_api_key
ZHIPUAI_API_KEY=your_zhipuai_api_key

# Agent 版本（v1 或 v2）
AGENT_VERSION=v2
```

### 步骤 4：启动服务

#### 方式一：使用启动脚本（推荐）

**启动后端服务**：
```bash
uv run python run_server.py
```

**启动前端服务**（新终端）：
```bash
uv run python run_frontend.py
```

#### 方式二：手动启动

**启动后端主服务**（端口 8080）：
```bash
uv run python service/server.py
```

**启动检测服务网关**（端口 8001）：
```bash
uv run python src/algorithms/api/main.py
```

**启动规划服务**（端口 8003）：
```bash
uv run python src/rag/service/main.py
```

**启动前端**（端口 3000）：
```bash
cd frontend
npm run dev
```

#### 方式三：一键启动所有服务

使用开发脚本一键启动所有核心服务：

```bash
# 启动所有服务
bash scripts/dev/start_all_services.sh

# 查看服务状态
bash scripts/dev/check_services.sh

# 停止所有服务
bash scripts/dev/stop_all_services.sh
```

---

## 知识库构建

规划咨询服务需要构建知识库：

```bash
# 自动构建知识库（推荐）
uv run python scripts/dev/build_kb_auto.py
```

知识库将存储在 `knowledge_base/chroma_db/` 目录。

---

## 验证部署

### 健康检查

```bash
# 后端服务
curl http://localhost:8080/health

# 检测服务网关
curl http://localhost:8001/health

# 规划咨询服务
curl http://localhost:8003/health
```

### 功能测试

**测试规划咨询**：
```bash
curl -X POST "http://localhost:8080/chat/planning" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "长宁镇的旅游发展目标是什么？",
    "mode": "auto"
  }'
```

**测试检测服务**：
```bash
# 病虫害检测
curl -X POST "http://localhost:8001/detection/pest/predict" \
  -F "file=@path/to/image.jpg"

# 大米品种识别
curl -X POST "http://localhost:8001/detection/rice/predict" \
  -F "file=@path/to/image.jpg"

# 奶牛检测
curl -X POST "http://localhost:8001/detection/cow/predict" \
  -F "file=@path/to/image.jpg"
```

### 访问前端界面

打开浏览器访问：http://localhost:3000

---

## 常见问题

### Q1: 端口被占用怎么办？

**检查端口占用**：
```bash
# macOS/Linux
lsof -i :8080
lsof -i :8001
lsof -i :3000
```

**解决方案**：
1. 杀死占用端口的进程
2. 或修改配置文件中的端口号

### Q2: Docker 容器启动失败？

**查看详细日志**：
```bash
docker-compose logs [service-name]
```

**常见原因**：
- 端口冲突
- 内存不足
- 镜像构建失败

### Q3: 前端无法连接后端？

**检查事项**：
1. 后端服务是否启动（http://localhost:8080/health）
2. CORS 配置是否正确（`.env` 中的 `ALLOWED_ORIGINS`）
3. API Keys 是否配置正确

### Q4: RAG 查询无结果？

**确认知识库已构建**：
```bash
# 检查知识库目录
ls knowledge_base/chroma_db/

# 重新构建
uv run python scripts/dev/build_kb_auto.py
```

### Q5: 如何切换 Agent 版本？

编辑 `.env` 文件：
```bash
AGENT_VERSION=v1  # 或 v2
```

重启服务生效。

### Q6: 检测服务连接失败？

**确认检测服务网关已启动**：
```bash
curl http://localhost:8001/health
```

如果未启动：
```bash
uv run python src/algorithms/api/main.py
```

---

## 生产环境建议

### 性能优化

1. **使用 GPU 加速**：
   - 安装 GPU 版本的 PyTorch
   - 配置 CUDA 环境

2. **配置反向代理**：
   - 使用 Nginx 作为反向代理
   - 启用 HTTPS

3. **资源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
         cpus: '2.0'
   ```

4. **监控和日志**：
   - 配置 LangSmith 追踪
   - 集中式日志收集

### 安全建议

1. **API Key 保护**：
   - 不要将 `.env` 文件提交到代码仓库
   - 使用环境变量或密钥管理服务

2. **CORS 配置**：
   ```bash
   ALLOWED_ORIGINS=https://your-domain.com
   ```

3. **速率限制**：
   - 防止 API 滥用
   - 限制上传文件大小

4. **输入验证**：
   - 严格验证用户上传的图片
   - 过滤恶意输入

---

## 相关文档

- [服务管理指南](service-management.md) - 详细的服务配置和管理
- [项目结构指南](project-structure.md) - 代码组织规范
- [模型管理指南](model-management.md) - 模型配置和切换
- [V2 Agent 架构](../architecture/v2-agent-upgrade.md) - Agent 架构详解

---

## 获取帮助

- **API 文档**: http://localhost:8080/docs
- **项目文档**: [docs/](../README.md)
- **问题反馈**: https://github.com/Fangziyang0910/RuralBrain/issues

---

**最后更新**: 2026-01-31
**版本**: v2.0
