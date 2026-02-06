# Docker 镜像部署指南

本文档介绍如何使用 Docker Hub 上的镜像快速部署 RuralBrain 规划服务。

## 前置要求

部署服务器上需要安装：
- Docker (>= 20.10)
- Docker Compose (>= 1.29)

检查安装：
```bash
docker --version
docker-compose --version
```

## 镜像列表

| 镜像名称 | 说明 | 大小 |
|---------|------|------|
| `zhihongsheng/rural-brain-knowledge-base:latest` | 知识库数据镜像（ChromaDB） | 28.7MB |
| `zhihongsheng/rural-brain-planning-service:latest` | 规划咨询服务 | 3.36GB |

## 快速开始

### 方式一：使用 docker-compose（推荐）

1. **创建部署目录**
   ```bash
   mkdir -p ~/ruralbrain-deploy
   cd ~/ruralbrain-deploy
   ```

2. **创建 docker-compose.yml 文件**
   ```bash
   cat > docker-compose.yml << 'EOF'
   version: '3.8'

   services:
     # 知识库数据服务
     knowledge-base:
       image: zhihongsheng/rural-brain-knowledge-base:latest
       container_name: ruralbrain-kb
       restart: always

     # 规划咨询服务
     planning-service:
       image: zhihongsheng/rural-brain-planning-service:latest
       container_name: ruralbrain-planning
       ports:
         - "8003:8003"
       environment:
         - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
         - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
         - LANGCHAIN_TRACING_V2=true
         - LANGCHAIN_PROJECT=RuralBrain
       volumes_from:
         - knowledge-base
       depends_on:
         - knowledge-base
       restart: always
   EOF
   ```

3. **创建 .env 文件（配置 API 密钥）**
   ```bash
   cat > .env << 'EOF'
   # DeepSeek API 密钥
   DEEPSEEK_API_KEY=你的密钥

   # LangChain API 密钥（用于链路追踪）
   LANGCHAIN_API_KEY=你的密钥
   EOF
   ```

   > 如何获取 API 密钥：
   > - DeepSeek: https://platform.deepseek.com/
   > - LangSmith: https://smith.langchain.com/

4. **启动服务**
   ```bash
   docker-compose up -d
   ```

5. **查看服务状态**
   ```bash
   docker-compose ps
   ```

6. **查看日志**
   ```bash
   # 查看所有服务日志
   docker-compose logs -f

   # 只查看规划服务日志
   docker-compose logs -f planning-service
   ```

7. **测试服务**
   ```bash
   # 健康检查
   curl http://localhost:8003/health

   # 访问 API 文档
   # 在浏览器打开：http://服务器IP:8003/docs
   ```

### 方式二：手动运行容器

1. **拉取镜像**
   ```bash
   docker pull zhihongsheng/rural-brain-knowledge-base:latest
   docker pull zhihongsheng/rural-brain-planning-service:latest
   ```

2. **启动知识库容器**
   ```bash
   docker run -d --name ruralbrain-kb \
     zhihongsheng/rural-brain-knowledge-base:latest
   ```

3. **启动规划服务容器**
   ```bash
   docker run -d --name ruralbrain-planning \
     --volumes-from ruralbrain-kb \
     -p 8003:8003 \
     -e DEEPSEEK_API_KEY=你的密钥 \
     -e LANGCHAIN_API_KEY=你的密钥 \
     zhihongsheng/rural-brain-planning-service:latest
   ```

## 常用操作命令

### 查看服务状态
```bash
docker ps
```

### 查看日志
```bash
# 实时查看日志
docker logs -f ruralbrain-planning

# 查看最近 100 行日志
docker logs --tail 100 ruralbrain-planning
```

### 重启服务
```bash
# 使用 docker-compose
docker-compose restart planning-service

# 或直接重启容器
docker restart ruralbrain-planning
```

### 停止服务
```bash
# 使用 docker-compose
docker-compose down

# 或单独停止容器
docker stop ruralbrain-planning ruralbrain-kb
```

### 更新镜像
```bash
# 1. 拉取最新镜像
docker pull zhihongsheng/rural-brain-planning-service:latest
docker pull zhihongsheng/rural-brain-knowledge-base:latest

# 2. 停止并删除旧容器
docker-compose down

# 3. 重新启动服务
docker-compose up -d
```

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 8003 | Planning Service | 规划咨询 API |

## 测试 API

### 1. 健康检查
```bash
curl http://localhost:8003/health
```

期望返回：
```json
{
  "status": "healthy",
  "service": "planning-service",
  "version": "1.0.0",
  "knowledge_base_loaded": true
}
```

### 2. 访问 API 文档

在浏览器中打开：
```
http://服务器IP:8003/docs
```

### 3. 测试对话接口
```bash
curl -X POST "http://localhost:8003/api/v1/chat/planning" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "乡村旅游发展规划有什么建议？",
    "mode": "fast"
  }'
```

## 故障排查

### 服务无法启动

1. **检查端口占用**
   ```bash
   netstat -tlnp | grep 8003
   ```

2. **查看容器日志**
   ```bash
   docker logs ruralbrain-planning
   ```

3. **检查环境变量**
   ```bash
   docker inspect ruralbrain-planning | grep -A 10 "Env"
   ```

### API 调用失败

1. **确认 API 密钥已配置**
   ```bash
   docker exec ruralbrain-planning env | grep API_KEY
   ```

2. **测试服务连通性**
   ```bash
   docker exec ruralbrain-planning curl http://localhost:8003/health
   ```

### 知识库未加载

检查知识库容器是否运行：
```bash
docker ps | grep ruralbrain-kb
docker logs ruralbrain-kb
```

## 完整部署示例

以下是在一台新服务器上的完整部署流程：

```bash
# 1. 创建部署目录
mkdir -p ~/ruralbrain-deploy
cd ~/ruralbrain-deploy

# 2. 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  knowledge-base:
    image: zhihongsheng/rural-brain-knowledge-base:latest
    container_name: ruralbrain-kb
    restart: always

  planning-service:
    image: zhihongsheng/rural-brain-planning-service:latest
    container_name: ruralbrain-planning
    ports:
      - "8003:8003"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_PROJECT=RuralBrain
    volumes_from:
      - knowledge-base
    depends_on:
      - knowledge-base
    restart: always
EOF

# 3. 配置 API 密钥
cat > .env << 'EOF'
DEEPSEEK_API_KEY=sk-你的实际密钥
LANGCHAIN_API_KEY=lsv2_你的实际密钥
EOF

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps

# 6. 测试服务
curl http://localhost:8003/health
```

## 与主系统集成

如果需要与现有的 RuralBrain 后端服务集成，可以在现有的 `docker-compose.yml` 中添加规划服务：

```yaml
services:
  # ... 其他服务 ...

  knowledge-base:
    image: zhihongsheng/rural-brain-knowledge-base:latest
    container_name: ruralbrain-kb
    restart: always

  planning-service:
    image: zhihongsheng/rural-brain-planning-service:latest
    container_name: ruralbrain-planning
    ports:
      - "8003:8003"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_PROJECT=RuralBrain
    volumes_from:
      - knowledge-base
    depends_on:
      - knowledge-base
    restart: always
```

然后在后端配置中设置：
```bash
PLANNING_SERVICE_URL=http://planning-service:8003
```

## 需要帮助？

如果遇到问题，请检查：
1. Docker 版本是否满足要求
2. API 密钥是否正确配置
3. 端口 8003 是否被占用
4. 防火墙是否允许访问端口 8003

查看日志获取更多信息：
```bash
docker-compose logs -f
```
