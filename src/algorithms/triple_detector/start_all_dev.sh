#!/bin/bash

set -e

echo "🔥 启动开发模式检测服务（热重载已启用）..."

# 启动病虫害检测服务（带热重载）
echo "🐛 启动病虫害检测 (8001)..."
cd /app/pest
PYTHONPATH=/app/pest:$PYTHONPATH \
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
PID_PEST=$!

# 启动大米检测服务（带热重载）
echo "🍚 启动大米检测 (8081)..."
cd /app/rice
PYTHONPATH=/app/rice:$PYTHONPATH \
    uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload &
PID_RICE=$!

# 启动牛只检测服务（带热重载）
echo "🐄 启动牛只检测 (8002)..."
cd /app/cow
PYTHONPATH=/app/cow:$PYTHONPATH \
    uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
PID_COW=$!

echo "✅ 所有检测服务已启动（热重载模式）"
echo "  - Pest:  PID=$PID_PEST,  Port=8001"
echo "  - Rice:  PID=$PID_RICE,  Port=8081"
echo "  - Cow:   PID=$PID_COW,  Port=8002"

# 等待所有后台进程
wait $PID_PEST $PID_RICE $PID_COW
