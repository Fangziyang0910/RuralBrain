# Docker Hub 镜像使用指南

## 📦 仓库信息

- **Docker Hub 仓库**: https://hub.docker.com/r/zwxdockerbeginner/ruralbrain
- **维护者**: zwxdockerbeginner
- **版本**: v4.0.0
- **最后更新**: 2026-04-18
- **重要变更**: v4 版本修复启动命令、网络别名配置、外部服务跳转地址固化

---

## 🏷️ 镜像列表

### 后端服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `backend-onnx-v4` | 后端主服务（FastAPI + Agents + RAG + 知识库）| ~1.1GB | 生产环境 |
| `backend-onnx-v3` | 后端主服务（旧版本） | ~1.1GB | 开发环境 |
| `latest` | 指向最新稳定版 | - | 默认拉取 |

**v4 版本更新**：
- ✅ 修复启动命令（使用 `uvicorn service.server:app`）
- ✅ 添加 `src/data` 目录（疾病知识库数据）
- ✅ 包含最新 `src/config.py`（支持 Qwen、GLM-4、DeepSeek 三模型）
- ✅ 内嵌规划知识库和疾病知识库

**功能**：
- Orchestrator Agent V2 编排（Skills 架构）
- 意图识别和路由
- 工具调用管理（TTL 生命周期）
- 流式对话支持
- 疾病预测工具（集成 RAG 知识库检索）
- 规划知识库（内嵌）
- 疾病知识库（内嵌）
- 联网搜索（Tavily）
- ChromaDB 向量数据库支持

**内嵌知识库**：
- 规划知识库 (`/app/knowledge_base/chroma_db`)
- 疾病知识库 (`/app/knowledge_base/diseases/chroma_db`)

---

### 前端服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `frontend-onnx-v4` | 前端生产版本（外部服务跳转已固化） | ~229MB | 生产环境 |
| `frontend-dev` | 前端开发版本（支持热重载） | ~1.8GB | 开发环境 |

**v4 版本更新**：
- ✅ 外部服务跳转地址固化（构建时通过 ARG 参数）
- ✅ 乡村经营服务跳转：`http://114.132.186.148:3000`
- ✅ 乡村规划服务跳转：`http://114.132.186.148:3003`（可配置）
- ✅ 法律咨询服务跳转：`http://114.132.186.148:3004`（可配置）
- ✅ 网络别名兼容（支持 `backend` 和 `detection-service` 别名）
- ✅ 健康检查修复（安装 curl，设置 HOSTNAME=0.0.0.0）

**构建时固化地址**：
```bash
docker build --build-arg NEXT_PUBLIC_MANAGEMENT_URL=http://your-server:3000 \
             --build-arg NEXT_PUBLIC_PLANNING_URL=http://your-server:3003 \
             --build-arg NEXT_PUBLIC_LEGAL_URL=http://your-server:3004 \
             -t frontend-onnx-v4 ./frontend
```

---

### 检测服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `detection-onnx-v4` | 检测服务统一网关（ONNX 优化版） | ~1.8GB | 生产环境 |
| `detection-onnx-v3` | 检测服务（旧版本） | ~1.5GB | 开发环境 |

**v4 版本更新**：
- ✅ 修复工作目录（`WORKDIR /app/algorithms`）
- ✅ 包含最新检测代码（大米检测增强）
- ✅ 支持 6 种检测算法

**功能**：
- 病虫害检测（`/detection/pest/detect`）
- 大米品种识别（`/detection/rice/predict`、`/detection/rice/predict_detailed`）
- 奶牛目标检测（`/detection/cow/detect`、`/detection/cow/detect_detailed`）
- 疾病检测（`/detection/disease/detect`）
- 场景分类（`/detection/scene/classify`）
- 植物病害（`/detection/plant_disease/detect`）
- ONNX Runtime 推理引擎

---

## 🚀 快速开始

### 前提条件

1. **安装 Docker**
   - Windows: 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Linux: `sudo apt-get install docker.io docker-compose-plugin`
   - macOS: 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **配置环境变量**
   - 复制 `.env.example` 到 `.env`
   - 填写必要的 API 密钥和配置

3. **知识库**（已内嵌，无需本地准备）
   - 规划知识库和疾病知识库已内嵌在镜像中
   - 协作者无需构建或挂载本地知识库

---

### 拉取镜像

```bash
# 拉取 v4 版本镜像（生产环境推荐）
docker pull zwxdockerbeginner/ruralbrain:frontend-onnx-v4
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v4
docker pull zwxdockerbeginner/ruralbrain:detection-onnx-v4

# 或拉取开发版本
docker pull zwxdockerbeginner/ruralbrain:frontend-dev
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v3
docker pull zwxdockerbeginner/ruralbrain:detection-onnx-v3
```

---

### 启动项目

#### 方式一：开发环境（热重载）

```bash
# 启动开发环境
docker compose -f docker-compose.dev.yml up -d

# 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 停止服务
docker compose -f docker-compose.dev.yml down
```

#### 方式二：生产环境部署

**服务器部署步骤**：

```bash
# 1. 创建项目目录
mkdir -p ~/ruralbrain && cd ~/ruralbrain

# 2. 创建 .env 文件
nano .env
# 粘贴 API 密钥配置

# 3. 创建 docker-compose.prod.yml
nano docker-compose.prod.yml
# 粘贴下方配置文件内容

# 4. 拉取镜像
docker pull zwxdockerbeginner/ruralbrain:frontend-onnx-v4
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v4
docker pull zwxdockerbeginner/ruralbrain:detection-onnx-v4

# 5. 启动服务
docker compose -f docker-compose.prod.yml up -d

# 6. 查看状态
docker compose -f docker-compose.prod.yml ps

# 7. 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

**生产环境 docker-compose.prod.yml**：

```yaml
# RuralBrain 生产环境部署配置
# 所有内容已内置在镜像中，无需本地文件挂载

services:
  frontend:
    image: zwxdockerbeginner/ruralbrain:frontend-onnx-v4
    container_name: ruralbrain-frontend
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - NEXT_TELEMETRY_DISABLED=1
      - BACKEND_URL=http://backend:8081
      - NEXT_PUBLIC_API_URL=http://114.132.186.148:8081
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      ruralbrain-network:
        aliases:
          - frontend

  backend:
    image: zwxdockerbeginner/ruralbrain:backend-onnx-v4
    container_name: ruralbrain-backend
    ports:
      - "8081:8081"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - ENVIRONMENT=production
      - PEST_DETECTION_API_URL=http://detection-service:8001/detection/pest/detect
      - RICE_DETECTION_API_URL=http://detection-service:8001/detection/rice/predict
      - RICE_DETECTION_API_URL_DETAILED=http://detection-service:8001/detection/rice/predict_detailed
      - COW_DETECTION_API_URL=http://detection-service:8001/detection/cow/detect
      - COW_DETECTION_API_URL_DETAILED=http://detection-service:8001/detection/cow/detect_detailed
      - DISEASE_DETECTION_API_URL=http://detection-service:8001/detection/disease/detect
    tmpfs:
      - /tmp/ruralbrain:size=500M,mode=0777
    depends_on:
      - detection-service
    restart: unless-stopped
    networks:
      ruralbrain-network:
        aliases:
          - backend

  detection-service:
    image: zwxdockerbeginner/ruralbrain:detection-onnx-v4
    container_name: ruralbrain-detection-service
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - PYTHONPATH=/app/algorithms
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      ruralbrain-network:
        aliases:
          - detection-service
    deploy:
      resources:
        limits:
          memory: 2G

networks:
  ruralbrain-network:
    driver: bridge
    name: ruralbrain-network
```

**关键配置说明**：

| 配置项 | 说明 |
|--------|------|
| `aliases: [backend]` | 让前端能用 `backend` 名称访问后端 |
| `aliases: [detection-service]` | 让后端能用 `detection-service` 访问检测服务 |
| `BACKEND_URL` | 前端代理后端 API 的地址（容器内网络） |
| `NEXT_PUBLIC_API_URL` | 前端直接访问后端的地址（外部访问） |
| `*_DETAILED` URL | 详细检测 API（返回 bbox 和置信度） |
| `tmpfs` | 临时文件存储（检测结果图片） |

**服务访问地址**：

| 服务 | 地址 |
|------|------|
| 前端界面 | `http://114.132.186.148:3001` |
| 后端 API | `http://114.132.186.148:8081` |
| API 文档 | `http://114.132.186.148:8081/docs` |
| 检测服务 | `http://114.132.186.148:8001` |
| 乡村经营服务 | `http://114.132.186.148:3000`（外部服务） |

---

#### 方式三：手动启动单个容器

```bash
# 创建网络（必须，用于服务间通信）
docker network create ruralbrain-network

# 1. 启动检测服务（添加网络别名）
docker run -d --name ruralbrain-detection \
  --network ruralbrain-network \
  --network-alias detection-service \
  -p 8001:8001 \
  zwxdockerbeginner/ruralbrain:detection-onnx-v4

# 2. 启动后端（添加网络别名）
docker run -d --name ruralbrain-backend \
  --network ruralbrain-network \
  --network-alias backend \
  -p 8081:8081 \
  --env-file .env \
  -e PEST_DETECTION_API_URL=http://detection-service:8001/detection/pest/detect \
  -e RICE_DETECTION_API_URL=http://detection-service:8001/detection/rice/predict \
  -e COW_DETECTION_API_URL=http://detection-service:8001/detection/cow/detect \
  zwxdockerbeginner/ruralbrain:backend-onnx-v4

# 3. 启动前端
docker run -d --name ruralbrain-frontend \
  --network ruralbrain-network \
  -p 3001:3001 \
  -e BACKEND_URL=http://backend:8081 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8081 \
  zwxdockerbeginner/ruralbrain:frontend-onnx-v4
```

---

## 📋 协作者使用指南

### ⚠️ 重要原则

**不要本地构建镜像，直接拉取 Docker Hub 上的镜像**

**原因**：
1. **节省时间**：构建大镜像（detection、planning）需要 1-2 小时
2. **节省流量**：避免重复下载依赖包（每次构建都需要）
3. **保持一致性**：所有协作者使用相同的镜像环境
4. **减少问题**：避免因本地环境差异导致的奇怪错误

---

### 正确工作流程

#### ✅ 推荐流程

```bash
# 1. 克隆项目
git clone https://github.com/Fangziyang0910/RuralBrain.git
cd RuralBrain

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要的配置

# 3. 拉取 Docker Hub 镜像
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v2
docker pull zwxdockerbeginner/ruralbrain:detection-onnx-v2
docker pull zwxdockerbeginner/ruralbrain:frontend-dev

# 4. 启动服务
docker compose -f docker-compose.dev.yml up -d

# 5. 访问应用
open http://localhost:3001
```

#### ❌ 不推荐流程

```bash
# ❌ 不要这样做：
# cd docker
# ./build-onnx-images.sh  # 不要本地构建！

# 原因：
# - 耗时长（1-2 小时）
# - 消耗流量（需要下载所有依赖）
# - 可能因环境差异导致错误
```

---

### 镜像更新流程

当镜像有更新时：

```bash
# 1. 查看本地镜像版本
docker images zwxdockerbeginner/ruralbrain

# 2. 拉取最新镜像
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v2
docker pull zwxdockerbeginner/ruralbrain:detection-onnx-v2
docker pull zwxdockerbeginner/ruralbrain:frontend-dev

# 3. 删除旧镜像（可选）
docker rmi $(docker images zwxdockerbeginner/ruralbrain -q | grep '<none>') 2>/dev/null

# 4. 重启服务
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d
```

---

## 🔧 镜像维护指南

### 责任分配

**镜像发布负责人**：zwxbeginner

**职责**：
- ✅ 构建和更新 Docker 镜像
- ✅ 推送镜像到 Docker Hub
- ✅ 管理镜像版本标签
- ✅ 维护镜像更新日志

**协作者**：
- ✅ 仅拉取和使用镜像
- ✅ 不要本地构建镜像
- ✅ 发现问题及时反馈

---

### 版本发布流程

**当需要更新镜像时**：

1. **修改代码**
   ```bash
   # 更新代码并测试
   git add .
   git commit -m "feat: 新功能"
   git push origin dev
   ```

2. **构建新镜像**（由负责人执行）
   ```bash
   # Windows
   .\scripts\dev\build-onnx-images.ps1

   # Linux/macOS
   bash scripts/dev/build-onnx-images.sh
   ```

3. **标记新版本**
   ```bash
   # 语义化版本号
   docker tag zwxdockerbeginner/ruralbrain:backend-onnx-v2 zwxdockerbeginner/ruralbrain:v2.4.0

   # 或使用日期标签
   docker tag zwxdockerbeginner/ruralbrain:backend-onnx-v2 zwxdockerbeginner/ruralbrain:2026-03-21
   ```

4. **推送到 Docker Hub**
   ```bash
   docker push zwxdockerbeginner/ruralbrain:backend-onnx-v2
   docker push zwxdockerbeginner/ruralbrain:latest
   ```

5. **通知团队**
   - 在项目中发布更新说明
   - 更新 CHANGELOG.md
   - 通知协作者拉取新镜像

---

### 标签管理规范

**标签命名规则**：

```
<服务名>-<变体>          # 示例：backend-onnx
<版本号>                 # 示例：v2.2.0
latest                    # 最新稳定版
dev                       # 开发版本
```

**常用标签**：
- `latest`：最新稳定版（指向 backend-onnx-v2）
- `backend-onnx-v2`：后端 ONNX 版本（v2 优化版）
- `detection-onnx-v2`：检测服务 ONNX 版本（v2 优化版）
- `planning-onnx`：规划服务 ONNX 版本（已废弃，已整合到主 Agent）
- `frontend-onnx-v2`：前端生产版本（v2 优化版）
- `frontend-dev`：前端开发版本（热重载）
- `v2.2.1`：语义化版本号
- `2026-03-01`：日期版本号（可选）

---

## 🐛 常见问题

### Q1: 前端点击检测服务跳转到错误地址？

**A**: 这是网络别名配置问题

**v4 版本需要配置网络别名**：
- 后端容器需要 `--network-alias backend`
- 检测容器需要 `--network-alias detection-service`

**原因**：`next.config.mjs` 中 rewrites 在构建时固化使用 `http://backend:8081`

**解决方案**：
```bash
# 使用 docker-compose.prod.yml（已配置别名）
docker compose -f docker-compose.prod.yml up -d

# 或手动添加别名
docker network connect ruralbrain-network ruralbrain-backend --alias backend
docker network connect ruralbrain-network ruralbrain-detection --alias detection-service
```

---

### Q2: 外部服务跳转地址不对？

**A**: 前端外部服务地址在构建时固化

**v4 版本固化地址**：
- 乡村经营服务：`http://114.132.186.148:3000`
- 乡村规划服务：`http://114.132.186.148:3003`
- 法律咨询服务：`http://114.132.186.148:3004`

**如需修改地址，必须重新构建镜像**：
```bash
docker build -f docker/Dockerfile.frontend.onnx \
  --build-arg NEXT_PUBLIC_MANAGEMENT_URL=http://your-server:3000 \
  --build-arg NEXT_PUBLIC_PLANNING_URL=http://your-server:3003 \
  --build-arg NEXT_PUBLIC_LEGAL_URL=http://your-server:3004 \
  -t zwxdockerbeginner/ruralbrain:frontend-onnx-v4 ./frontend
```

---

### Q3: 检测结果图片无法显示？

**A**: 检查网络别名和静态文件路由

**排查步骤**：
```bash
# 1. 检查网络别名
docker exec ruralbrain-backend curl http://detection-service:8001/health

# 2. 检查后端静态文件路由
curl http://localhost:8081/pest_results/

# 3. 检查前端代理
curl http://localhost:3001/pest_results/test.jpg
```

**常见原因**：
- 网络别名未配置 → 前端无法代理到后端
- 检测服务未运行 → 无法生成结果图片
- 后端启动失败 → 静态文件路由未挂载

---

### Q4: 模型选择只显示 DeepSeek？

**A**: 后端配置问题或网络连接问题

**排查步骤**：
```bash
# 1. 直接测试后端 API
curl http://localhost:8081/models

# 2. 检查返回结果
# 正确：{"models": [{"id": "deepseek"}, {"id": "glm-4"}, {"id": "qwen"}]}
# 错误：{"models": [{"id": "deepseek"}]}

# 3. 如果只显示 deepseek，检查镜像版本
docker images zwxdockerbeginner/ruralbrain
# 应使用 backend-onnx-v4（包含最新 config.py）
```

---

### Q5: 拉取镜像速度慢？

**A**: 配置 Docker 镜像加速器

**阿里云加速**（推荐中国用户）：
```bash
# 编辑 Docker Desktop 配置
# Settings -> Docker Engine -> 添加：

{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

---

### Q6: 如何验证镜像完整性？

**A**: 检查镜像摘要

```bash
# 查看镜像摘要
docker images --digests zwxdockerbeginner/ruralbrain

# 验证拉取的镜像
docker pull zwxdockerbeginner/ruralbrain:backend-onnx-v4
# Docker 会自动验证校验和
```

---

### Q7: 知识库如何配置？

**A**: 知识库已内嵌在镜像中，无需本地配置

**内嵌知识库**：
- 规划知识库：`/app/knowledge_base/chroma_db`
- 疾病知识库：`/app/knowledge_base/diseases/chroma_db`
- 疾病数据：`/app/src/data/diseases/`

**docker-compose.prod.yml 无需挂载知识库目录**

**如需更新知识库**：
1. 本地构建新知识库
2. 重新构建 Docker 镜像
3. 推送到 Docker Hub

---

### Q8: 开发环境和生产环境的镜像有区别吗？

**A**: 后端、检测服务的镜像**完全相同**

**共享镜像**：
- `backend-onnx-v4`：开发和生产使用同一个镜像
- `detection-onnx-v4`：开发和生产使用同一个镜像

**不同镜像**：
- `frontend-onnx-v4`：生产环境（~229MB，优化构建，地址固化）
- `frontend-dev`：开发环境（~1.8GB，包含开发依赖，支持热重载）

**热重载实现**：
- 通过 `docker-compose.dev.yml` 的 `volumes` 挂载本地代码
- 不是通过不同的镜像实现

---

### Q9: 如何查看容器日志？

**A**: 使用 docker-compose 或 docker logs

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f detection-service
docker compose -f docker-compose.prod.yml logs -f frontend

# 或使用容器名称
docker logs -f ruralbrain-backend
docker logs -f ruralbrain-detection-service
docker logs -f ruralbrain-frontend
```

---

### Q10: 镜像很大，如何优化？

**A**: 当前镜像已优化

**优化措施**：
- ✅ 使用 ONNX Runtime 替代 PyTorch（减少 60-75% 体积）
- ✅ 多阶段构建前端镜像（~229MB）
- ✅ 使用 alpine/slim 基础镜像（最小化体积）
- ✅ 清理构建缓存和不必要的文件

**镜像体积对比**：
| 镜像 | v2 版本 | v4 版本 | 减少 |
|------|---------|---------|------|
| frontend | 1.02GB | 229MB | 78% |
| backend | 9GB | 1.1GB | 88% |
| detection | 476MB | 1.8GB | -（增加检测类型）|

---

## 📚 更多资源

- **项目文档**: [README.md](../../README.md)
- **命令参考**: [commands.md](../commands.md)
- **部署指南**: [getting-started.md](./getting-started.md)
- **GitHub 仓库**: https://github.com/Fangziyang0910/RuralBrain
- **Docker Hub 仓库**: https://hub.docker.com/r/zwxdockerbeginner/ruralbrain

---

## 📄 许可证

MIT License

---

**文档版本**: v2.0
**最后更新**: 2026-04-18
**维护者**: RuralBrain Team
