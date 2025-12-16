# 快速启动

## 1. 环境要求
- Docker 20.10+
- Docker Compose 1.29+

## 2. 一键部署

### Windows
```bash
# 运行部署脚本
deploy.bat
```

### Linux/Mac
```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps
```

## 3. 验证服务

打开浏览器访问：
- API文档: http://localhost:8081/docs
- 健康检查: http://localhost:8081/health

## 4. 测试API

```bash
# 使用curl测试
curl -X POST "http://localhost:8081/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "你的base64图片数据",
    "task_type": "品种分类"
  }'
```

## 5. 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建
docker-compose build --no-cache
```

## 6. 故障排除

### 端口被占用
修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8082:8081"  # 改为其他端口
```

### 内存不足
增加Docker内存限制或减少批处理大小。

### 模型加载失败
检查 `detector/models/` 目录是否包含模型文件。

更多详细信息请参考 [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)