import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 确保工作目录正确设置为脚本所在目录
# 这样相对路径（如 models/best.pt）才能正确解析
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import uvicorn
from src.algorithms.pest_detection.detector.app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Server will run on http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False  # 生产环境设置为False
    )
"""1. 查看API文档
在浏览器中打开：

http://localhost:8001/docs - Swagger UI文档界面
http://localhost:8001/redoc - ReDoc文档界面
2. 测试健康检查
访问：http://localhost:8001/health"""