# 害虫检测服务 - 快速开始

## 🎯 最简部署方式

### Docker部署（推荐）

**一行命令启动**：
```bash
cd src/algorithms/pest_detection/detector && docker-compose up -d --build
```

**或使用批处理文件**（Windows）：
```bash
# 双击运行
Docker启动服务.bat
```

访问：http://localhost:8001/docs

---

### Python部署

**从项目根目录**：
```bash
# 1. 激活虚拟环境
.venv\Scripts\activate

# 2. 启动服务
python -m src.algorithms.pest_detection.detector.start_service
```

访问：http://localhost:8001/docs

---

## ✅ 验证安装

```bash
# 运行验证脚本
python src\algorithms\pest_detection\verify_setup.py
```

所有测试通过即可正常使用。

---

## 📚 详细文档

- [完整部署指南](部署使用指南.md)
- [模块说明](README.md)
- [详细文档](detector/README_zh.md)
- [Docker部署](detector/DOCKER_DEPLOY.md)

---

## 🆘 快速故障排除

| 问题 | 解决方案 |
|------|---------|
| Docker启动失败 | 确认Docker Desktop已启动 |
| 端口被占用 | `netstat -ano \| findstr :8001` 查看占用 |
| 模块导入错误 | 确保从项目根目录运行 |
| 模型加载失败 | 确认 `detector/models/best.pt` 存在 |

---

## 📞 联系方式

遇到问题请查看详细文档或提交 Issue。
