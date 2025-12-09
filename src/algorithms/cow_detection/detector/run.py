import os
import sys
from pathlib import Path

# 确保工作目录正确设置为脚本所在目录
# 这样相对路径（如 models/best.pt）才能正确解析
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 检测运行环境：Docker 或本地
# Docker环境中，当前目录就是 /app，直接使用相对导入
# 本地环境中，需要添加项目根目录到 Python 路径
if not os.path.exists('/app'):  # 本地环境
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

import uvicorn

# 根据环境使用不同的导入方式
try:
    # Docker环境：使用相对导入
    from app.core.config import settings
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.cow_detection.detector.app.core.config import settings

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

"""
使用说明:

1. 查看API文档
在浏览器中打开：

http://localhost:8002/docs - Swagger UI文档界面
http://localhost:8002/redoc - ReDoc文档界面

2. 测试健康检查
访问：http://localhost:8002/health

3. 测试检测接口
使用 /detect 接口上传图像进行牛只检测

4. 查看支持的牛只类型
访问：http://localhost:8002/supported-cows
"""