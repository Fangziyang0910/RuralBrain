# Docker Hub 镜像使用指南

## 📦 仓库信息

- **仓库地址**: https://hub.docker.com/r/zwxdockerbeginner/ruralbrain
- **维护者**: zwxbeginner
- **版本**: v2.2.0
- **最后更新**: 2026-02

---

## 🏷️ 镜像列表

### 后端服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `backend-onnx` | 后端主服务（FastAPI + Agents） | 394MB | 开发/生产 |
| `latest` | 指向 `backend-onnx`（最新稳定版） | 394MB | 默认拉取 |

**功能**：
- Orchestrator Agent V2 编排
- 意图识别和路由
- 工具调用管理
- 流式对话支持

---

### 前端服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `frontend-onnx` | 前端生产版本（优化构建） | 1.02GB | 生产环境 |
| `frontend-dev` | 前端开发版本（支持热重载） | 1.81GB | 开发环境 |

**frontend-onnx 特点**：
- 多阶段构建优化
- 生产环境启动（`npm start`）
- 镜像体积小

**frontend-dev 特点**：
- 包含完整开发依赖
- 支持热模块替换（HMR）
- 需要挂载本地代码

---

### 检测服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `detection-onnx` | 检测服务统一网关（YOLO 模型） | 13.7GB | 开发/生产 |

**功能**：
- 病虫害检测（`/detection/pest/detect`）
- 大米品种识别（`/detection/rice/predict`）
- 奶牛目标检测（`/detection/cow/detect`）
- ONNX Runtime 推理引擎

**包含模型**：
- 病虫害检测 YOLO 模型
- 大米品种识别模型
- 奶牛检测 YOLO 模型

---

### 规划服务

| 标签 | 说明 | 大小 | 使用场景 |
|------|------|------|---------|
| `planning-onnx` | 规划咨询服务（RAG + ChromaDB） | 12.7GB | 开发/生产 |

**功能**：
- RAG 知识库检索
- 7 个核心检索工具
- 文档摘要和上下文管理
- 向量缓存优化

**包含组件**：
- ChromaDB 向量数据库
- Sentence Transformers 嵌入模型
- FastAPI 服务接口

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

3. **准备知识库**（可选）
   - 下载或构建知识库到 `knowledge_base/` 目录
   - 参考：[知识库构建指南](../commands.md#知识库构建)

---

### 拉取镜像

```bash
# 拉取后端服务
docker pull zwxdockerbeginner/ruralbrain:backend-onnx

# 拉取检测服务
docker pull zwxdockerbeginner/ruralbrain:detection-onnx

# 拉取规划服务
docker pull zwxdockerbeginner/ruralbrain:planning-onnx

# 拉取前端生产版
docker pull zwxdockerbeginner/ruralbrain:frontend-onnx

# 拉取前端开发版
docker pull zwxdockerbeginner/ruralbrain:frontend-dev

# 或拉取最新版本（指向 backend-onnx）
docker pull zwxdockerbeginner/ruralbrain:latest
```

---

### 启动项目

#### 方式一：使用 docker-compose（推荐）

**开发环境**（热重载）：
```bash
# 拉取最新镜像（可选）
docker compose -f docker-compose.dev.yml pull

# 启动开发环境
docker compose -f docker-compose.dev.yml up -d

# 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 停止服务
docker compose -f docker-compose.dev.yml down
```

**生产环境**（标准部署）：
```bash
# 拉取最新镜像（可选）
docker compose -f docker-compose.onnx.yml pull

# 启动生产环境
docker compose -f docker-compose.onnx.yml up -d

# 查看日志
docker compose -f docker-compose.onnx.yml logs -f

# 停止服务
docker compose -f docker-compose.onnx.yml down
```

#### 方式二：手动启动单个容器

```bash
# 启动后端
docker run -d \
  --name ruralbrain-backend \
  -p 8081:8081 \
  --env-file .env \
  -v $(pwd)/knowledge_base:/app/knowledge_base:ro \
  zwxdockerbeginner/ruralbrain:backend-onnx

# 启动检测服务
docker run -d \
  --name ruralbrain-detection \
  -p 8001:8001 \
  -v $(pwd)/src/algorithms/detection/models:/app/algorithms/detection/models:ro \
  zwxdockerbeginner/ruralbrain:detection-onnx

# 启动规划服务
docker run -d \
  --name ruralbrain-planning \
  -p 8003:8003 \
  --env-file .env \
  -v $(pwd)/knowledge_base:/app/knowledge_base:ro \
  zwxdockerbeginner/ruralbrain:planning-onnx

# 启动前端（生产版）
docker run -d \
  --name ruralbrain-frontend \
  -p 3001:3001 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8081 \
  zwxdockerbeginner/ruralbrain:frontend-onnx
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
docker pull zwxdockerbeginner/ruralbrain:backend-onnx
docker pull zwxdockerbeginner/ruralbrain:detection-onnx
docker pull zwxdockerbeginner/ruralbrain:planning-onnx
docker pull zwxdockerbeginner/ruralbrain:frontend-onnx

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
docker pull zwxdockerbeginner/ruralbrain:backend-onnx
docker pull zwxdockerbeginner/ruralbrain:detection-onnx
docker pull zwxdockerbeginner/ruralbrain:planning-onnx
docker pull zwxdockerbeginner/ruralbrain:frontend-onnx

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
   docker tag ruralbrain-backend:onnx zwxdockerbeginner/ruralbrain:v2.3.0

   # 或使用日期标签
   docker tag ruralbrain-backend:onnx zwxdockerbeginner/ruralbrain:2026-02-11
   ```

4. **推送到 Docker Hub**
   ```bash
   docker push zwxdockerbeginner/ruralbrain:v2.3.0
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
- `latest`：最新稳定版（指向 backend-onnx）
- `backend-onnx`：后端 ONNX 版本
- `detection-onnx`：检测服务 ONNX 版本
- `planning-onnx`：规划服务 ONNX 版本
- `frontend-onnx`：前端生产版本
- `frontend-dev`：前端开发版本（热重载）
- `v2.2.0`：语义化版本号
- `2026-02-11`：日期版本号（可选）

---

## 🐛 常见问题

### Q1: 拉取镜像速度慢？

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

**网易云加速**：
```bash
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com"
  ]
}
```

---

### Q2: 如何验证镜像完整性？

**A**: 检查镜像摘要

```bash
# 查看镜像摘要
docker images --digests zwxdockerbeginner/ruralbrain

# 验证拉取的镜像
docker pull zwxdockerbeginner/ruralbrain:backend-onnx
# Docker 会自动验证校验和
```

---

### Q3: 知识库如何配置？

**A**: 知识库通过 Docker volume 挂载

**目录结构**：
```
RuralBrain/
├── knowledge_base/          # ⭐ 知识库目录（不推送到 GitHub）
│   └── chroma_db/        # ChromaDB 数据
├── docker-compose.dev.yml
└── docker-compose.onnx.yml
```

**volume 配置**：
```yaml
# docker-compose.dev.yml
services:
  planning-service:
    volumes:
      - ./knowledge_base:/app/knowledge_base:ro  # 挂载本地知识库
```

**重要**：
- 知识库已添加到 `.gitignore`，不会推送到 GitHub
- 每个协作者需要自己构建或获取知识库
- 参考：[知识库构建指南](../commands.md#知识库构建)

---

### Q4: 开发环境和生产环境的镜像有区别吗？

**A**: 后端、检测、规划服务的镜像**完全相同**

**共享镜像**：
- `backend-onnx`：开发和生产使用同一个镜像
- `detection-onnx`：开发和生产使用同一个镜像
- `planning-onnx`：开发和生产使用同一个镜像

**不同镜像**：
- `frontend-onnx`：生产环境（1.02GB，优化构建）
- `frontend-dev`：开发环境（1.81GB，包含开发依赖）

**热重载实现**：
- 通过 `docker-compose.yml` 的 `volumes` 挂载本地代码
- 不是通过不同的镜像实现

---

### Q5: 如何查看容器日志？

**A**: 使用 docker-compose 或 docker logs

```bash
# 查看所有服务日志
docker compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f detection-service
docker compose -f docker-compose.dev.yml logs -f planning-service
docker compose -f docker-compose.dev.yml logs -f frontend

# 或使用容器名称
docker logs -f ruralbrain-backend
docker logs -f ruralbrain-detection-service
docker logs -f ruralbrain-planning-service
docker logs -f ruralbrain-frontend
```

---

### Q6: 镜像很大，如何优化？

**A**: 当前镜像已优化

**优化措施**：
- ✅ 使用 ONNX Runtime 替代 PyTorch（减少 60-75% 体积）
- ✅ 多阶段构建前端镜像（减少 ~800MB）
- ✅ 使用 alpine 基础镜像（最小化体积）
- ✅ 清理构建缓存和不必要的文件

**未来优化方向**：
- 考虑拆分检测模型到独立镜像（按需拉取）
- 使用 .dockerignore 排除更多不必要文件

---

## 📚 更多资源

- **项目文档**: [README.md](../../README.md)
- **命令参考**: [commands.md](../commands.md)
- **部署指南**: [docker-onnx-deployment.md](./docker-onnx-deployment.md)
- **GitHub 仓库**: https://github.com/Fangziyang0910/RuralBrain
- **Docker Hub 仓库**: https://hub.docker.com/r/zwxdockerbeginner/ruralbrain

---

## 📄 许可证

MIT License

---

**文档版本**: v1.0
**最后更新**: 2026-02-11
**维护者**: RuralBrain Team
