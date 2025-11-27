#!/usr/bin/env python3
"""
FastAPI服务启动脚本
用于启动FastAPI开发服务器
"""

import os
import sys
import uvicorn
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动FastAPI开发服务器")
    parser.add_argument("--host", default="127.0.0.1", help="服务器主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用自动重载 (开发模式)")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    parser.add_argument("--log-level", default="info", choices=["critical", "error", "warning", "info", "debug"], help="日志级别 (默认: info)")
    
    args = parser.parse_args()
    
    # 导入FastAPI应用
    try:
        from test_fastapi_basic import app
        print("✅ 成功导入FastAPI应用")
    except ImportError as e:
        print(f"❌ 导入FastAPI应用失败: {e}")
        return
    
    # 启动服务器
    print(f"🚀 启动FastAPI服务器: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"📚 ReDoc文档: http://{args.host}:{args.port}/redoc")
    print(f"🔧 开发模式: {'启用' if args.reload else '禁用'}")
    print(f"🔧 工作进程数: {args.workers}")
    print(f"🔧 日志级别: {args.log_level}")
    print("=" * 50)
    
    uvicorn.run(
        "test_fastapi_basic:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # 重载模式下只能使用1个worker
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()