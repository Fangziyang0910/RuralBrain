#!/bin/bash

set -e

echo "Starting triple detection services..."

# 让 Ultralytics 使用可写配置目录
export YOLO_CONFIG_DIR=/app/ultralytics
mkdir -p "$YOLO_CONFIG_DIR"

# 启动病虫害检测服务 (端口 8001)
echo "Starting pest detector on port 8001..."
cd /app/pest
PYTHONPATH=/app/pest:$PYTHONPATH \
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 &
PID_PEST=$!

# 启动大米检测服务 (端口 8081)
echo "Starting rice detector on port 8081..."
cd /app/rice
PYTHONPATH=/app/rice:$PYTHONPATH \
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8081 &
PID_RICE=$!

# 启动牛只检测服务 (端口 8002)
echo "Starting cow detector on port 8002..."
cd /app/cow
PYTHONPATH=/app/cow:$PYTHONPATH \
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 &
PID_COW=$!

echo "All services started!"
echo "Pest detector:  PID=$PID_PEST,  Port=8001"
echo "Rice detector:  PID=$PID_RICE,  Port=8081"
echo "Cow detector:   PID=$PID_COW,  Port=8002"

# 等待所有后台进程
wait $PID_PEST $PID_RICE $PID_COW
