# 🐛 智能害虫检测 API - Docker 部署指南

## 📋 目录结构

确保你的部署目录包含以下文件：

```
insect_detector/
├── app/                    # 应用代码目录
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── detection.py
│   └── services/
│       ├── __init__.py
│       └── model_service.py
├── models/                 # 模型文件目录
│   ├── best.pt            # YOLOv8 模型文件 (必需)
│   └── classes.txt        # 类别名称文件 (必需)
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── pyproject.toml/uv.lock # Python 依赖（统一管理）
├── run.py                 # 启动脚本
└── .dockerignore          # Docker 忽略文件
```

---

## 🚀 快速部署（3步完成）

### 前提条件

- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 确保 Docker 服务正在运行

### 步骤 1：进入项目目录

```bash
cd insect_detector
```

### 步骤 2：构建并启动服务

```bash
docker-compose up -d --build
```

### 步骤 3：验证服务

打开浏览器访问：
- **API 文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

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

如果 8001 端口被占用，编辑 `docker-compose.yml`：

```yaml
services:
  insect-detector:
    ports:
      - "8002:8001"  # 改为 8002 或其他端口
```

### 环境变量

可以在 `docker-compose.yml` 中添加环境变量：

```yaml
environment:
  - LOG_LEVEL=DEBUG    # 日志级别：DEBUG, INFO, WARNING, ERROR
  - HOST=0.0.0.0       # 监听地址
  - PORT=8001          # 端口号
```

---

## 🧪 测试 API

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8001/health

# 害虫检测（替换 YOUR_BASE64_IMAGE 为实际的 base64 图像数据）
curl -X POST "http://localhost:8001/detect" \
     -H "Content-Type: application/json" \
     -d '{"image_base64": "YOUR_BASE64_IMAGE"}'
```

### 使用 Python 测试

```python
import requests
import base64

# 读取图像并转换为 base64
with open('test_image.jpg', 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送检测请求
response = requests.post(
    'http://localhost:8001/detect',
    json={'image_base64': img_base64}
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

**错误信息**: `Bind for 0.0.0.0:8001 failed: port is already allocated`

**解决方案**：
```bash
# 查看占用端口的进程
netstat -ano | findstr :8001

# 或者修改 docker-compose.yml 使用其他端口
```

### 3. 模型文件不存在

**错误信息**: `模型文件不存在: models/best.pt`

**解决方案**：确保 `models/` 目录下有 `best.pt` 和 `classes.txt` 文件

### 4. 内存不足

**错误信息**: `OOMKilled`

**解决方案**：在 `docker-compose.yml` 中限制内存：
```yaml
services:
  insect-detector:
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
| `/health/detailed` | GET | 详细健康状态 |
| `/detect` | POST | 害虫检测（核心接口） |
| `/supported-pests` | GET | 支持的害虫类型列表 |
| `/docs` | GET | Swagger API 文档 |
| `/redoc` | GET | ReDoc API 文档 |

### 检测接口 `/detect`

**请求格式**：
```json
{
  "image_base64": "Base64编码的图像数据"
}
```

**响应格式**：
```json
{
  "success": true,
  "detections": [
    {"name": "瓜实蝇", "count": 2},
    {"name": "蚜虫", "count": 1}
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
