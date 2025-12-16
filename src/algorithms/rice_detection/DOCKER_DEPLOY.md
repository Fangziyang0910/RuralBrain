# 大米检测服务 Docker 部署指南

## 快速开始

### 1. 环境要求
- Docker 20.10+
- Docker Compose 1.29+
- 至少 4GB 内存
- 2GB 可用磁盘空间

### 2. 构建和启动

```bash
# 构建镜像并启动服务
docker-compose up -d

# 或者使用部署脚本（Windows）
deploy.bat
```

### 3. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试API
curl http://localhost:8081/health
```

### 4. API 端点

- **健康检查**: `GET http://localhost:8081/health`
- **预测接口**: `POST http://localhost:8081/predict`
- **API文档**: `http://localhost:8081/docs`

### 5. 停止服务

```bash
docker-compose down
```

### 6. 重新构建

```bash
docker-compose build --no-cache
docker-compose up -d
```

## 配置说明

### 环境变量
- `PYTHONPATH`: Python路径，默认 `/app`
- `LOG_LEVEL`: 日志级别，默认 `INFO`

### 端口映射
- `8081:8081`: API服务端口

### 卷挂载（可选）
如需持久化日志或模型文件，可在 `docker-compose.yml` 中添加卷挂载配置。

## 故障排除

### 容器启动失败
1. 检查端口是否被占用
2. 检查Docker日志：`docker-compose logs`
3. 确保模型文件存在：`detector/models/` 目录下

### 内存不足
- 增加Docker内存限制
- 或减少批处理大小

### 模型加载失败
- 检查模型文件是否完整
- 检查文件权限

## 性能优化

### 生产环境建议
1. 使用GPU版本的基础镜像（如支持）
2. 配置负载均衡
3. 设置适当的资源限制
4. 监控容器资源使用情况

### 资源限制示例
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## 安全建议

1. 使用非root用户运行容器（已实现）
2. 定期更新基础镜像
3. 扫描镜像漏洞
4. 限制网络访问
5. 使用HTTPS（生产环境）

## 更新日志

### v1.0.0
- 初始版本
- 支持基本的大米品种识别
- 包含健康检查端点