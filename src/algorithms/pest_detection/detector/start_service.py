"""
害虫检测服务启动脚本

使用方法:
    python -m src.algorithms.pest_detection.detector.start_service
    
或从项目根目录:
    python src/algorithms/pest_detection/detector/start_service.py
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置工作目录为 detector 目录，以便正确加载模型文件
detector_dir = Path(__file__).parent
os.chdir(detector_dir)

import uvicorn
from src.algorithms.pest_detection.detector.app.core.config import settings


def start_server(host: str = None, port: int = None, reload: bool = False):
    """启动FastAPI服务器
    
    Args:
        host: 服务器主机地址，默认使用配置文件中的值
        port: 服务器端口，默认使用配置文件中的值
        reload: 是否启用热重载（开发模式）
    """
    host = host or settings.HOST
    port = port or settings.PORT
    
    print(f"🚀 启动 {settings.PROJECT_NAME} v{settings.VERSION}...")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🔧 模型路径: {settings.MODEL_PATH}")
    print(f"🌐 服务器地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"🔍 健康检查: http://{host}:{port}/health")
    print("-" * 60)
    
    uvicorn.run(
        "src.algorithms.pest_detection.detector.app.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    # 开发模式：启用热重载
    # 生产模式：将 reload 设置为 False
    start_server(reload=False)
