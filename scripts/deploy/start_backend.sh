#!/bin/bash
# Backend 服务启动脚本

echo "启动 Backend 服务..."
# 直接启动，Python 代码会加载 .env
python3 -m uvicorn service.server:app --host 0.0.0.0 --port 8080
