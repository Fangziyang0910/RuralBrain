# 🐄 智能牛检测 API - Docker 部署指南

## 📋 目录结构

确保你的部署目录包含以下文件：

```
cow_detection/
├── app/                    # 应用代码目录
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── agent_routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── detection.py
│   │   └── agent.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_service.py
│   │   └── agent_service.py
│   └── utils/
│       └── __init__.py
├── models/                 # 模型文件目录
│   └── best.pt            # YOLOv8 模型文件 (可选)
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── pyproject.toml/uv.lock # Python 依赖（统一管理）
├── run.py                 # 启动脚本
├── .dockerignore          # Docker 忽略文件
└── README.md              # 项目说明文档
```

---

## 🚀 快速部署（3步完成）

### 前提条件

- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 确保 Docker 服务正在运行

### 步骤 1：进入项目目录

```bash
cd src/cow_detection
```

### 步骤 2：构建并启动服务

```bash
docker-compose up -d --build
```

### 步骤 3：验证服务

打开浏览器访问：
- **API 文档**: http://localhost:8002/docs
- **健康检查**: http://localhost:8002/health

---

## 📖 详细命令说明

### 构建镜像

```bash
# 构建镜像（首次或代码更新后）
docker-compose build

# 强制重新构建（不使用缓存）
docker-compose build --no-cache
```

### 启动服务

```bash
# 后台启动
docker-compose up -d

# 前台启动（可以看到日志）
docker-compose up

# 构建并启动
docker-compose up -d --build
```

### 查看状态

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs

# 实时查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

### 停止服务

```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v
```

### 重启服务

```bash
docker-compose restart
```

---

## 🔧 配置说明

### 修改端口

如果 8002 端口被占用，编辑 `docker-compose.yml`：

```yaml
services:
  cow-detector:
    ports:
      - "8003:8002"  # 改为 8003 或其他端口
```

### 环境变量

可以在 `docker-compose.yml` 中添加环境变量：

```yaml
environment:
  - LOG_LEVEL=DEBUG    # 日志级别：DEBUG, INFO, WARNING, ERROR
  - HOST=0.0.0.0       # 监听地址
  - PORT=8002          # 端口号
```

---

## 🧪 测试 API

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8002/health

# 获取模型列表
curl http://localhost:8002/api/v1/models

# 牛检测（替换 YOUR_BASE64_IMAGE 为实际的 base64 图像数据）
curl -X POST "http://localhost:8002/api/v1/detect/image/base64" \
     -H "Content-Type: application/json" \
     -d '{"image_data": "YOUR_BASE64_IMAGE"}'
```

### 使用 Python 测试

```python
import requests
import base64

# 读取图像并转换为 base64
with open('cow_image.jpg', 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送检测请求
response = requests.post(
    'http://localhost:8002/api/v1/detect/image/base64',
    json={'image_data': img_base64}
)

# 打印结果
result = response.json()
print(f"检测结果: {result}")
```

---

## ❓ 常见问题

### 1. 构建时网络超时

**解决方案**：配置 Docker 镜像加速器

在 Docker Desktop 设置中，添加镜像加速器：
```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io"
  ]
}
```

### 2. 端口被占用

**错误信息**: `Bind for 0.0.0.0:8002 failed: port is already allocated`

**解决方案**：
```bash
# 查看占用端口的进程
netstat -ano | findstr :8002

# 或者修改 docker-compose.yml 使用其他端口
```

### 3. 模型文件不存在

**错误信息**: `模型文件不存在`

**解决方案**：确保 `models/` 目录下有模型文件，或者系统会自动下载默认模型

### 4. 内存不足

**错误信息**: `OOMKilled`

**解决方案**：在 `docker-compose.yml` 中限制内存：
```yaml
services:
  cow-detector:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 5. 清理 Docker 占用的磁盘空间

```bash
# 清理未使用的镜像、容器、网络
docker system prune -a

# 查看磁盘使用情况
docker system df
```

---

## 📊 API 接口说明

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务首页信息 |
| `/health` | GET | 健康检查 |
| `/api/v1/models` | GET | 获取可用模型列表 |
| `/api/v1/detect/image` | POST | 图像检测（文件上传） |
| `/api/v1/detect/image/base64` | POST | 图像检测（Base64） |
| `/api/v1/detect/video` | POST | 视频检测（文件上传） |
| `/api/v1/detect/video/base64` | POST | 视频检测（Base64） |
| `/api/v1/agent/chat` | POST | 智能对话接口 |
| `/docs` | GET | Swagger API 文档 |
| `/redoc` | GET | ReDoc API 文档 |

### 图像检测接口 `/api/v1/detect/image/base64`

**请求格式**：
```json
{
  "image_data": "Base64编码的图像数据",
  "confidence_threshold": 0.5,
  "model_name": "yolov8n"
}
```

**响应格式**：
```json
{
  "success": true,
  "detection_count": 2,
  "detections": [
    {
      "class": "cow",
      "confidence": 0.85,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "result_image": "Base64编码的标注后图像"
}
```

---

## 🔄 更新部署

当代码或模型更新时：

```bash
# 停止旧容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

---

## 📞 技术支持

如有问题，请检查：
1. Docker 服务是否正常运行
2. 模型文件是否存在且完整
3. 端口是否被占用
4. 查看容器日志排查错误
