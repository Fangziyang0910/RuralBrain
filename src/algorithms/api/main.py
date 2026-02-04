"""
RuralBrain 统一算法服务 API 网关

这是唯一的 FastAPI 应用，所有算法服务在此注册路由。
算法代码保持纯粹，不依赖 FastAPI。
"""
import sys
from pathlib import Path

# 添加 src 到 Python 路径，支持绝对导入
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="RuralBrain 算法服务 API",
    description="""
    ## 🌾 RuralBrain 统一算法服务

    提供多种 AI 算法服务，使用统一的端口和路由前缀。

    ### 当前支持的算法服务
    - 🐛 **病虫害检测**: `/detection/pest/*` - 农作物病虫害智能识别
    - 🍚 **大米识别**: `/detection/rice/*` - 大米品种自动识别
    - 🐄 **奶牛检测**: `/detection/cow/*` - 牛只目标检测

    ### 架构说明
    - **FastAPI 网关**: 统一的 API 服务层
    - **算法模块**: 纯算法实现，可独立测试
    - **可扩展设计**: 新算法只需注册路由即可

    ### 技术栈
    - **深度学习框架**: YOLOv8
    - **Web 框架**: FastAPI + Uvicorn
    - **图像处理**: OpenCV
    - **容器化**: Docker 部署
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入检测算法的路由
from algorithms.api.routes.detection import router as detection_router

# 注册路由，添加前缀
app.include_router(detection_router, prefix="/detection", tags=["检测服务"])

# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """服务根路径，返回欢迎信息和可用端点"""
    return {
        "service": "RuralBrain 算法服务",
        "version": "2.0.0",
        "status": "running",
        "architecture": "FastAPI Gateway + Algorithm Modules",
        "endpoints": {
            "detection": {
                "pest": "/detection/pest/detect",
                "rice": "/detection/rice/predict",
                "cow": "/detection/cow/detect"
            },
            "docs": "/docs",
            "health": "/health"
        },
        "documentation": "访问 /docs 查看 API 文档"
    }

# 健康检查
@app.get("/health", tags=["系统信息"])
async def health_check():
    """统一健康检查接口"""
    return {
        "status": "healthy",
        "service": "RuralBrain Algorithm Service",
        "version": "2.0.0",
        "algorithms": {
            "detection": {
                "pest": "running",
                "rice": "running",
                "cow": "running"
            }
        },
        "timestamp": "2025-01-31T13:30:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
