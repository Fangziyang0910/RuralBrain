#!/usr/bin/env python3
"""
牛检测API服务启动脚本
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent  # 上级目录是src，再上级是项目根目录
web_cow_root = project_root.parent  # 项目根目录是web_cow

sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(web_cow_root))

from app.core.config import settings


def start_server(host=None, port=None, reload=None, workers=None):
    """启动服务器"""
    # 使用命令行参数或配置文件中的默认值
    host = host or settings.HOST
    port = port or settings.PORT
    reload = reload if reload is not None else True  # 默认开启热重载
    workers = workers or 1  # 默认使用单进程
    
    print(f"启动牛检测API服务...")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    print(f"ReDoc文档: http://{host}:{port}/redoc")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else None,  # 热重载模式下不能使用多进程
        log_level="info"
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="牛检测API服务启动脚本")
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"服务器主机地址 (默认: {settings.HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"服务器端口 (默认: {settings.PORT})"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="禁用热重载"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="工作进程数 (默认: 1，禁用热重载时可用)"
    )
    
    args = parser.parse_args()
    
    # 确保必要的目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(current_dir / "models", exist_ok=True)
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        workers=args.workers
    )


if __name__ == "__main__":
    main()