# 故障排查指南

## 常见问题

### Q: 服务启动失败？

**检查步骤**：

1. 检查端口是否被占用
   ```bash
   lsof -i :8081    # 后端
   lsof -i :8001    # 检测服务
   lsof -i :8003    # 规划服务
   lsof -i :3001    # 前端
   ```

2. 查看容器日志（Docker 部署）
   ```bash
   docker-compose -f docker-compose.dev.yml logs <service>
   ```

3. 常见原因：
   - 端口被占用 → 关闭占用进程或修改端口
   - API Keys 未配置 → 检查 `.env` 文件
   - 依赖未安装 → 运行 `uv sync`

---

### Q: 检测服务无法连接？

**解决方法**：

1. 确认检测服务网关已启动
   ```bash
   curl http://localhost:8001/health
   ```

2. 检查 `.env` 中配置
   ```bash
   DETECTION_SERVICE_URL=http://localhost:8001
   ```

3. 如果未启动，启动检测服务
   ```bash
   uv run python src/algorithms/api/main.py
   ```

---

### Q: RAG 查询无结果？

**解决方法**：

1. 确认知识库已构建
   ```bash
   ls knowledge_base/chroma_db/
   ```

2. 重新构建知识库
   ```bash
   uv run python scripts/dev/build_kb_auto.py
   ```

---

### Q: 前端无法连接后端？

**解决方法**：

1. 检查后端服务是否启动
   ```bash
   curl http://localhost:8081/health
   ```

2. 检查 CORS 配置（`.env` 文件）
   ```bash
   ALLOWED_ORIGINS=http://localhost:3001
   ```

3. 检查 API Keys 是否配置正确

---

### Q: 热重载不工作？

**解决方法**：

1. 检查卷挂载（Docker）
   ```bash
   docker inspect <container> | grep -A 10 Mounts
   ```

2. 重启容器
   ```bash
   docker-compose -f docker-compose.dev.yml restart <service>
   ```

3. Windows 用户：确保 Docker Desktop 有访问项目目录的权限

---

### Q: 如何切换 Agent 版本？

**解决方法**：

编辑 `.env` 文件：
```bash
AGENT_VERSION=v1  # 或 v2
```

重启服务生效。

---

### Q: 模块导入错误？

**解决方法**：

```bash
# 同步依赖
uv sync

# 使用 uv 运行
uv run python <script>
```

---

## 健康检查脚本

使用 `scripts/dev/health_check.sh` 进行系统检查：

```bash
# 完整健康检查
bash scripts/dev/health_check.sh

# 快速检查
bash scripts/dev/health_check.sh --quick

# 详细输出
bash scripts/dev/health_check.sh --verbose

# 检查单个服务
bash scripts/dev/health_check.sh --service backend
```

---

## 获取帮助

- **API 文档**: http://localhost:8081/docs
- **项目文档**: [docs/](../README.md)
- **问题反馈**: https://github.com/Fangziyang0910/RuralBrain/issues

---

**最后更新**: 2026-02-11
