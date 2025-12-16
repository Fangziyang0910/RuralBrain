import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# 兼容 Docker 和本地环境的导入
try:
    # Docker 环境：使用相对导入
    from app.api.routes import router as api_router
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.rice_detection.detector.app.api.routes import router as api_router

# 创建FastAPI应用实例
app = FastAPI(title='乡村振兴大脑 - 大米识别服务')

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)

# 根路径
@app.get("/")
def root():
    """
    🏠 欢迎使用大米品种识别API
    """
    return {
        "service_name": "大米品种识别服务",
        "version": "1.0.0",
        "status": "🟢 运行中"
    }

# 健康检查接口
@app.get("/health")
def health_check():
    """
    ⚡ 快速健康检查
    """
    return {
        "status": "healthy",
        "service": "大米品种识别服务",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True
    )