import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .schemas import RicePredictionRequest, RicePredictionResponse
from .service import get_rice_service

app = FastAPI(title='乡村振兴大脑 - 大米识别服务')

# 可选 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rice_service = None


@app.on_event('startup')
async def startup_event():
    global rice_service
    # 在启动时创建单例并加载模型
    rice_service = get_rice_service()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={'success': False, 'detections': [], 'message': str(exc)})


@app.post('/predict', response_model=RicePredictionResponse)
async def predict_endpoint(req: RicePredictionRequest):
    """
    接受 Base64 图片，返回 JSON 检测结果（无状态）。
    """
    global rice_service
    if rice_service is None:
        rice_service = get_rice_service()

    result = rice_service.predict(req.image_base64)
    if not result.get('success', False):
        return RicePredictionResponse(success=False, detections=[], message=result.get('message'))

    return RicePredictionResponse(success=True, detections=result.get('detections', []), result_image=result.get('result_image'))


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8081))
    uvicorn.run('src.backend.main:app', host='0.0.0.0', port=port, reload=False)