# RuralBrain 服务管理指南

本文档详细说明 RuralBrain 项目中所有微服务的配置、启动方式和端口分配。

---

## 服务架构概览

RuralBrain 采用微服务架构，包含以下核心服务：

```
前端 (3000)
    ↓
后端主服务 (8081) - Orchestrator Agent
    ↓
    ├─→ 病虫害检测服务 (8000)
    ├─→ 大米识别服务 (8001)
    └─→ 奶牛检测服务 (8002)
```

---

## 端口分配规范

| 服务 | 端口 | 配置文件 | 说明 |
|------|------|----------|------|
| **前端服务** | 3000 | `frontend/my-app/next.config.mjs` | Next.js 开发服务器 |
| **后端主服务** | 8081 | `service/settings.py` + `.env` | FastAPI + Orchestrator Agent |
| **病虫害检测** | 8000 | `src/algorithms/pest_detection/detector/app/core/config.py` | 害虫识别和计数 |
| **大米识别** | 8001 | `src/algorithms/rice_detection/detector/app/core/config.py` | 大米品种识别 |
| **奶牛检测** | 8002 | `src/algorithms/cow_detection/detector/app/core/config.py` | 牛只识别和计数 |

### 端口规范说明
- **3000-3999**：前端服务
- **8000-8999**：后端微服务（按功能顺序排列）
- 8000/8001/8002：三个检测服务，连续编号便于管理

---

## 服务详细信息

### 1. 前端服务 (Next.js)

**位置**：`frontend/my-app/`

**配置文件**：
- `next.config.mjs`：Next.js 配置
- `src/app/api/`：API 路由
- 环境变量：无特殊配置

**启动方式**：
```bash
cd frontend/my-app
npm install        # 首次运行安装依赖
npm run dev        # 开发模式（热重载）
npm run build      # 生产构建
npm start          # 生产模式
```

**访问地址**：http://localhost:3000

**依赖**：无（独立运行）

---

### 2. 后端主服务 (FastAPI + Orchestrator Agent)

**位置**：`service/`

**配置文件**：
- `service/settings.py`：主配置文件
- `.env`：环境变量（端口配置）
- `service/server.py`：启动脚本

**关键配置**：
```python
# service/settings.py
HOST = "127.0.0.1"  # 本地监听
PORT = 8081          # 默认端口（会被 .env 覆盖）
```

```bash
# .env
PORT=8081  # 实际运行端口
```

**启动方式**：
```bash
# 使用 uv（推荐）
uv run python service/server.py

# 或使用虚拟环境
source .venv/bin/activate
python service/server.py
```

**访问地址**：http://localhost:8081
**API 文档**：http://localhost:8081/docs

**依赖**：
- 可选：检测服务（8000/8001/8002）用于图像检测
- 内置：Orchestrator Agent，无需外部服务

---

### 3. 病虫害检测服务

**位置**：`src/algorithms/pest_detection/detector/`

**配置文件**：`src/algorithms/pest_detection/detector/app/core/config.py`

**关键配置**：
```python
HOST = "0.0.0.0"
PORT = 8000  # 病虫害检测服务
MODEL_PATH = "models/best.pt"
```

**启动方式**：
```bash
# 方法1：使用启动脚本（推荐）
cd src/algorithms/pest_detection/detector
python start_service.py

# 方法2：使用 uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**访问地址**：http://localhost:8000
**API 文档**：http://localhost:8000/docs

**依赖**：无（独立服务）

---

### 4. 大米识别服务

**位置**：`src/algorithms/rice_detection/detector/`

**配置文件**：`src/algorithms/rice_detection/detector/app/core/config.py`

**关键配置**：
```python
HOST = "0.0.0.0"
PORT = 8001  # 大米识别服务
WEIGHTS_PATH_FL = "models/weights_fl/best.pt"  # 番莉大米
WEIGHTS_PATH_XJ = "models/weights_xj/best.pt"  # 新京大米
```

**启动方式**：
```bash
# 方法1：使用启动脚本（推荐）
cd src/algorithms/rice_detection/detector
python start_service.py

# 方法2：使用 uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**访问地址**：http://localhost:8001
**API 文档**：http://localhost:8001/docs

**依赖**：无（独立服务）

---

### 5. 奶牛检测服务

**位置**：`src/algorithms/cow_detection/detector/`

**配置文件**：`src/algorithms/cow_detection/detector/app/core/config.py`

**关键配置**：
```python
HOST = "0.0.0.0"
PORT = 8002  # 奶牛检测服务
MODEL_PATH = "models/yolov8n.pt"
```

**启动方式**：
```bash
# 方法1：使用启动脚本（推荐）
cd src/algorithms/cow_detection/detector
python start_service.py

# 方法2：使用 uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

**访问地址**：http://localhost:8002
**API 文档**：http://localhost:8002/docs

**依赖**：无（独立服务）

---

## 快速启动指南

### 方式一：使用统一启动脚本（推荐）

**启动所有服务**：
```bash
# 一键启动所有服务
bash scripts/dev/start_all_services.sh

# 查看服务状态
bash scripts/dev/check_services.sh
```

**停止所有服务**：
```bash
bash scripts/dev/stop_all_services.sh
```

### 方式二：手动启动

**完整启动顺序**：
```bash
# 1. 启动检测服务（可选，后端服务可独立运行）
# 依次在三个终端执行：
cd src/algorithms/pest_detection/detector
uv run python start_service.py

cd src/algorithms/rice_detection/detector
uv run python start_service.py

cd src/algorithms/cow_detection/detector
uv run python start_service.py

# 2. 启动后端服务
uv run python service/server.py

# 3. 启动前端服务
cd frontend/my-app
npm run dev
```

**最小启动**（仅测试规划咨询）：
```bash
# 仅启动后端和前端即可
uv run python service/server.py
cd frontend/my-app && npm run dev
```

---

## 服务健康检查

**检查所有服务状态**：
```bash
# 使用检查脚本
bash scripts/dev/check_services.sh

# 或手动检查
curl http://localhost:3000       # 前端
curl http://localhost:8081/docs  # 后端
curl http://localhost:8000/docs  # 病虫害检测
curl http://localhost:8001/docs  # 大米识别
curl http://localhost:8002/docs  # 奶牛检测
```

**检查端口占用**：
```bash
# Linux/Mac
netstat -tlnp | grep -E ":(3000|8000|8001|8002|8081)"

# 或使用 ss
ss -tlnp | grep -E ":(3000|8000|8001|8002|8081)"
```

---

## 常见问题

### 1. 端口冲突

**问题**：启动失败，提示端口已被占用

**解决**：
```bash
# 查找占用端口的进程
lsof -i :8000
# 或
netstat -tlnp | grep 8000

# 杀死进程
kill -9 <PID>

# 或修改服务配置文件中的 PORT
```

### 2. 模块导入错误

**问题**：`ModuleNotFoundError: No module named 'app'`

**原因**：没有在正确的目录启动服务

**解决**：
```bash
# 必须在 detector 目录下启动
cd src/algorithms/pest_detection/detector
python start_service.py

# 或使用完整路径
uv run uvicorn src.algorithms.pest_detection.detector.app.main:app --port 8000
```

### 3. 模型文件未找到

**问题**：`FileNotFoundError: model file not found`

**解决**：
```bash
# 确保模型文件存在于正确位置
ls src/algorithms/pest_detection/detector/models/best.pt

# 如果模型不存在，需要先训练或下载模型
```

### 4. CORS 错误

**问题**：前端无法访问后端 API

**解决**：
```bash
# 检查后端 CORS 配置
# service/settings.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# 确保 .env 中配置正确
echo "ALLOWED_ORIGINS=http://localhost:3000" >> .env
```

### 5. 检测服务连接失败

**问题**：后端日志显示检测服务连接失败

**原因**：检测服务未启动或端口配置不匹配

**解决**：
```bash
# 1. 确认检测服务已启动
curl http://localhost:8000/docs

# 2. 检查端口配置是否一致
# 检测服务配置：src/algorithms/*/detector/app/core/config.py
# 后端调用配置：src/agents/skills/detection_skills.py

# 3. 确保端口一致
grep -r "localhost:8000" src/agents/skills/
```

---

## 服务依赖关系

### 核心服务（必需）
- **后端主服务** (8081)：核心服务，包含 Orchestrator Agent
- **前端服务** (3000)：用户界面

### 可选服务
- **病虫害检测** (8000)：用于病虫害识别场景
- **大米识别** (8001)：用于大米品种识别场景
- **奶牛检测** (8002)：用于牛只检测场景

**注意**：检测服务是可选的，后端主服务可以独立运行。当检测服务不可用时，Orchestrator Agent 会优雅降级，使用知识库或专业知识回答。

---

## 开发环境配置

### Python 环境管理

项目使用 `uv` 作为包管理器：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 运行 Python 代码
uv run python <script>

# 运行测试
uv run pytest
```

### Node.js 环境配置

前端使用 npm：

```bash
cd frontend/my-app
npm install  # 安装依赖
npm run dev  # 开发模式
```

### 环境变量配置

创建 `.env` 文件（项目根目录）：

```bash
# 后端服务配置
PORT=8081
HOST=127.0.0.1
ALLOWED_ORIGINS=http://localhost:3000

# Agent 配置
MODEL_PROVIDER=deepseek  # 或 glm
AGENT_VERSION=v1

# API Keys（根据需要配置）
DEEPSEEK_API_KEY=your_key_here
ZHIPU_API_KEY=your_key_here
```

---

## Docker 部署

如果使用 Docker 部署，所有服务配置已在 `docker-compose.yml` 中定义：

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 服务监控

### 查看服务日志

```bash
# 后端服务
tail -f logs/backend.log

# 检测服务
tail -f logs/pest_detection.log
tail -f logs/rice_detection.log
tail -f logs/cow_detection.log
```

### 实时监控

```bash
# 持续监控服务状态
watch -n 2 'curl -s http://localhost:8081/docs | grep title'
watch -n 2 'ps aux | grep python | grep -E "(8000|8001|8002|8081)"'
```

---

## 性能优化建议

### 1. 开发模式
- 后端服务启用热重载 (`reload=True`)
- 检测服务启用热重载（开发时使用）
- 前端启用 Next.js 快速刷新

### 2. 生产模式
- 关闭热重载
- 使用多进程部署（`workers=N`）
- 启用 Nginx 反向代理
- 配置 HTTPS

### 3. 资源优化
- 检测服务模型加载优化
- API 响应缓存
- 静态资源 CDN

---

## 更新日志

**2026-01-26**：
- 统一检测服务端口为 8000/8001/8002
- 修复端口冲突问题（大米服务 8081 → 8001）
- 更新服务调用配置
- 创建统一启动脚本

---

## 相关文档

- [项目结构指南](PROJECT_STRUCTURE_GUIDE.md)
- [工作进展报告](WORK_PROGRESS_2026-01-26.md)
- [测试报告](TEST_REPORT_2026-01-26.md)
- [CLAUDE.md](../CLAUDE.md) - 项目级配置
