# Planning Service 部署指南

乡村规划咨询服务微服务部署文档。

## 目录

1. [服务概述](#服务概述)
2. [本地开发](#本地开发)
3. [Docker 部署](#docker-部署)
4. [服务集成](#服务集成)
5. [监控与日志](#监控与日志)
6. [故障排查](#故障排查)

---

## 服务概述

### 功能

Planning Service 是一个基于 RAG（检索增强生成）技术的乡村规划咨询服务，提供：

- **智能咨询**：基于知识库的规划问答
- **快速浏览**：使用摘要快速了解文档核心
- **深度分析**：完整阅读文档进行深度理解
- **知识检索**：跨文档的智能检索能力

### 技术架构

```
Frontend (3000)
    ↓
Backend API Gateway (8080)
    ↓ (意图识别)
Planning Service (8003)
    ↓
ChromaDB 知识库
```

### 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | Next.js 前端界面 |
| Backend | 8080 | 主 API 网关 |
| Planning Service | 8003 | 规划咨询服务 |

---

## 本地开发

### 前置要求

- Python 3.13+
- Node.js 20+
- uv 包管理器

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，至少配置一个 API 密钥
```

**必需配置**：
```bash
# 选择模型提供商
MODEL_PROVIDER=deepseek

# API 密钥（二选一）
DEEPSEEK_API_KEY=your_key_here
# 或
ZHIPUAI_API_KEY=your_key_here
```

**可选配置**：
```bash
# Planning Service 地址
PLANNING_SERVICE_URL=http://localhost:8003

# 请求超时（秒）
PLANNING_SERVICE_TIMEOUT=120
```

### 2. 构建知识库

```bash
# 方式1：自动构建（推荐）
python build_kb_auto.py

# 方式2：交互式构建
python src/rag/build.py
```

### 3. 启动 Planning Service

```bash
# 方式1：使用启动脚本
chmod +x src/rag/scripts/start_with_env.sh
src/rag/scripts/start_with_env.sh

# 方式2：直接运行
python3 -m uvicorn src.rag.service.main:app --host 0.0.0.0 --port 8003
```

### 4. 测试服务

```bash
# 健康检查
curl http://localhost:8003/health

# API 文档
open http://localhost:8003/docs

# 运行测试脚本
chmod +x src/rag/scripts/test_service.sh
src/rag/scripts/test_service.sh
```

### 5. 启动 Backend（可选）

如果需要通过 Backend 访问 Planning Service：

```bash
# 使用启动脚本
chmod +x start_backend.sh
./start_backend.sh
```

---

## Docker 部署

### 快速启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f planning-service
```

### 单独部署 Planning Service

```bash
cd src/rag
docker-compose -f docker-compose.service.yml up -d
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8003/health

# 预期响应
# {"status":"healthy","service":"planning-service","version":"1.0.0","knowledge_base_loaded":true}
```

### 服务日志

```bash
# 查看实时日志
docker-compose logs -f planning-service

# 查看最近100行日志
docker-compose logs --tail=100 planning-service
```

---

## 服务集成

### 通过 Backend 访问

Backend 提供 `/chat/planning` 端点，自动代理到 Planning Service。

**请求示例**：
```bash
curl -X POST "http://localhost:8080/chat/planning" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "长宁镇的旅游发展目标是什么？",
    "mode": "auto"
  }'
```

**响应格式**（SSE 流式）：
```
data: {"type": "start", "thread_id": "...", "mode": "auto"}
data: {"type": "content", "content": "我来"}
data: {"type": "content", "content": "帮您"}
data: {"type": "tool", "tool_name": "list_available_documents", "status": "started"}
data: {"type": "tool", "tool_name": "list_available_documents", "status": "completed"}
data: {"type": "end", "thread_id": "...", "tools_used": [...]}
```

### 意图识别规则

Backend 根据以下规则自动路由：

1. **有图片** → 图像检测服务
2. **规划关键词** → Planning Service
   - 规划、发展、策略、旅游、产业、博罗、罗浮山等
3. **检测关键词** → 图像检测服务
   - 识别、检测、害虫、病害、大米、品种等
4. **默认** → Planning Service

### 工作模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `auto` | AI 自动选择 | 大多数情况 |
| `fast` | 快速浏览 | 简单问题、时间有限 |
| `deep` | 深度分析 | 复杂决策、详细分析 |

---

## 监控与日志

### 日志级别

- `DEBUG`: 调试信息
- `INFO`: 关键操作（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 配置日志

在 `.env` 中设置：
```bash
LOG_LEVEL=INFO
```

### LangSmith 追踪（可选）

用于 Agent 调试和可观测性：

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key
```

访问 https://smith.langchain.com 查看追踪。

### 关键指标

监控以下指标：

- **请求延迟**: P50, P95, P99
- **错误率**: 目标 < 5%
- **可用性**: 目标 > 99%
- **工具调用成功率**: 目标 > 95%

---

## 故障排查

### 问题1: 服务无法启动

**症状**：
```
ValidationError: DEEPSEEK_API_KEY must be set
```

**解决方案**：
1. 检查 `.env` 文件是否存在
2. 确认至少配置了一个 API 密钥
3. 确认环境变量正确加载

```bash
# 检查 API 密钥
grep DEEPSEEK_API_KEY .env

# 测试环境变量加载
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DEEPSEEK_API_KEY'))"
```

### 问题2: 知识库未加载

**症状**：
```json
{"knowledge_base_loaded": false}
```

**解决方案**：
1. 确认知识库已构建
2. 检查 `knowledge_base/chroma_db/` 目录是否存在
3. 重新构建知识库

```bash
# 重新构建知识库
python build_kb_auto.py
```

### 问题3: Backend 无法连接 Planning Service

**症状**：
```
无法连接到 Planning Service，请确认服务已启动
```

**解决方案**：
1. 确认 Planning Service 运行中
2. 检查 `PLANNING_SERVICE_URL` 配置
3. 检查网络连接

```bash
# 检查服务状态
curl http://localhost:8003/health

# 检查配置
echo $PLANNING_SERVICE_URL

# 测试连接
curl $PLANNING_SERVICE_URL/health
```

### 问题4: 响应超时

**症状**：
```
Planning Service 响应超时（120秒）
```

**解决方案**：
1. 增加超时时间
2. 检查知识库大小
3. 检查 LLM API 响应时间

```bash
# 增加超时时间（.env）
PLANNING_SERVICE_TIMEOUT=180
```

### 问题5: Docker 容器启动失败

**症状**：
```
docker-compose up -d
# 容器反复重启
```

**解决方案**：
1. 查看容器日志
2. 检查镜像构建
3. 检查端口冲突

```bash
# 查看详细日志
docker-compose logs planning-service

# 重新构建镜像
docker-compose build planning-service

# 检查端口占用
lsof -i :8003
```

---

## 性能优化

### 1. 减少响应时间

- **使用快速模式**：`mode: fast`
- **优化检索数量**：`DEFAULT_TOP_K=3`
- **使用更快的模型**：调整 `MODEL_TEMPERATURE`

### 2. 提高并发能力

- **增加 Worker 数量**：
  ```bash
  uvicorn workers:4
  ```

- **使用缓存**：
  ```bash
  ENABLE_CACHE=true
  CACHE_TTL=300
  ```

### 3. 优化知识库

- **调整分块大小**：`CHUNK_SIZE=2000`
- **使用更快的 Embedding 模型**
- **定期清理不需要的文档**

---

## 安全建议

### 生产环境配置

1. **限制 CORS 来源**：
   ```python
   ALLOWED_ORIGINS=["https://your-domain.com"]
   ```

2. **使用 HTTPS**：配置反向代理（Nginx）

3. **隐藏 API 密钥**：使用密钥管理服务

4. **限制请求频率**：添加 Rate Limiting

5. **日志脱敏**：避免记录敏感信息

---

## 参考资料

- [服务化规划文档](../src/rag/SERVICE_DEPLOYMENT_PLAN.md)
- [RAG 模块 README](../src/rag/README.md)
- [API 文档](http://localhost:8003/docs)

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-17 | 1.0.0 | 初始版本 |
