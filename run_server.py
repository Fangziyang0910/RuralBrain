"""
RuralBrain 后端服务启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    print("=" * 60)
    print("RuralBrain 后端服务启动中...")
    print("=" * 60)
    
    # 启动服务
    uvicorn.run(
        "service.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
