#!/bin/bash
# Planning Service 启动脚本（加载环境变量）

set -e

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 使用 python-dotenv 加载环境变量
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; [os.system(f'export {k}={v}') for k,v in os.environ.items() if k in ['DEEPSEEK_API_KEY','ZHIPUAI_API_KEY','MODEL_PROVIDER']]" 2>/dev/null || true

echo "🏘️  启动 Planning Service..."
echo "端口: 8003"
echo ""

# 直接启动（让 Python 代码加载 .env）
exec python3 -m uvicorn src.rag.service.main:app \
    --host 0.0.0.0 \
    --port 8003
