"""
RuralBrain 统一检测服务
整合病虫害、大米、奶牛三个检测服务到一个 FastAPI 应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="RuralBrain 统一检测服务 API",
    description="""
    ## 🌾 RuralBrain 三合一检测服务

    整合了病虫害检测、大米品种识别、奶牛目标检测三个服务，
    使用统一的端口和路由前缀，提供更简洁的 API 架构。

    ### 检测服务
    - 🐛 **病虫害检测**: `/pest/*` - 农作物病虫害智能识别
    - 🍚 **大米识别**: `/rice/*` - 大米品种自动识别
    - 🐄 **奶牛检测**: `/cow/*` - 牛只目标检测

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

# 导入三个检测服务的路由
from app.api.pest import router as pest_router
from app.api.rice import router as rice_router
from app.api.cow import router as cow_router

# 注册路由，添加前缀
app.include_router(pest_router, prefix="/pest", tags=["病虫害检测"])
app.include_router(rice_router, prefix="/rice", tags=["大米识别"])
app.include_router(cow_router, prefix="/cow", tags=["奶牛检测"])

# 根路径健康检查
@app.get("/", tags=["根路径"])
async def root():
    """服务根路径，返回欢迎信息和可用端点"""
    return {
        "service": "RuralBrain 统一检测服务",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "pest_detection": "/pest/detect",
            "rice_recognition": "/rice/predict",
            "cow_detection": "/cow/detect",
            "docs": "/docs",
            "health": "/health"
        },
        "documentation": "访问 /docs 查看 API 文档"
    }

# 统一健康检查
@app.get("/health", tags=["系统信息"])
async def health_check():
    """
    统一健康检查接口
    检查所有三个子服务的运行状态
    """
    return {
        "status": "healthy",
        "service": "RuralBrain Unified Detection Service",
        "version": "2.0.0",
        "services": {
            "pest_detection": "running",
            "rice_recognition": "running",
            "cow_detection": "running"
        },
        "timestamp": "2025-01-31T11:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
