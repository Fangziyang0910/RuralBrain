# 牛检测API服务

基于YOLOv8的牛检测API服务，提供图像和视频中牛只检测功能。

## 项目结构

```
cow_detection/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API路由定义
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # 配置管理
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── detection.py       # 请求和响应数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── model_service.py   # 模型服务
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py                # FastAPI应用入口
├── models/                    # 模型文件目录
├── __init__.py
├── start_service.py           # 服务启动脚本
└── README.md                  # 项目说明文档
```

## 功能特性

- 基于YOLOv8的牛只检测
- 支持图像和视频检测
- RESTful API接口
- 自动文档生成（Swagger UI和ReDoc）
- 线程安全的模型服务

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- fastapi
- uvicorn
- ultralytics
- opencv-python
- pydantic
- pydantic-settings

## 配置说明

配置文件位于 `app/core/config.py`，主要配置项：

- `MODEL_PATH`: 默认模型路径
- `HOST`: 服务器主机地址
- `PORT`: 服务器端口
- `DEFAULT_CONFIDENCE_THRESHOLD`: 默认置信度阈值
- `UPLOAD_DIR`: 文件上传目录

## 启动服务

### 方法一：使用启动脚本

```bash
# 默认配置启动
python start_service.py

# 指定主机和端口
python start_service.py --host 0.0.0.0 --port 8002

# 生产环境启动（禁用热重载，使用多进程）
python start_service.py --no-reload --workers 4
```

### 方法二：直接运行FastAPI应用

```bash
cd app
python main.py
```

### 方法三：使用uvicorn命令

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## API接口

服务启动后，可以通过以下地址访问：
- API服务: http://localhost:8002
- API文档: http://localhost:8002/docs
- ReDoc文档: http://localhost:8002/redoc

### 主要接口

#### 1. 健康检查

```
GET /health
```

#### 2. 获取可用模型列表

```
GET /api/v1/models
```

#### 3. 图像检测

```
POST /api/v1/detect/image
Content-Type: multipart/form-data

参数:
- file: 图像文件
- confidence_threshold: 置信度阈值 (可选)
- model_name: 模型名称 (可选)
```

#### 4. 视频检测

```
POST /api/v1/detect/video
Content-Type: multipart/form-data

参数:
- file: 视频文件
- confidence_threshold: 置信度阈值 (可选)
- sample_rate: 采样率 (可选)
- model_name: 模型名称 (可选)
```

#### 5. Base64图像检测

```
POST /api/v1/detect/image/base64
Content-Type: application/json

请求体:
{
    "image_data": "base64编码的图像数据",
    "confidence_threshold": 0.5,
    "model_name": "yolov8n"
}
```

#### 6. Base64视频检测

```
POST /api/v1/detect/video/base64
Content-Type: application/json

请求体:
{
    "video_data": "base64编码的视频数据",
    "confidence_threshold": 0.5,
    "sample_rate": 10,
    "model_name": "yolov8n"
}
```

## 使用示例

### Python客户端示例

```python
import requests
import base64

# 图像检测示例
def detect_cows_in_image(image_path):
    with open(image_path, "rb") as f:
        # 方式1: 上传文件
        files = {"file": f}
        data = {"confidence_threshold": 0.6}
        response = requests.post(
            "http://localhost:8002/api/v1/detect/image",
            files=files,
            data=data
        )
        
        # 方式2: 使用base64
        image_data = base64.b64encode(f.read()).decode("utf-8")
        json_data = {
            "image_data": image_data,
            "confidence_threshold": 0.6
        }
        response = requests.post(
            "http://localhost:8002/api/v1/detect/image/base64",
            json=json_data
        )
    
    return response.json()

# 调用示例
result = detect_cows_in_image("cow_image.jpg")
print(f"检测到 {result['detection_count']} 头牛")
```

### cURL示例

```bash
# 图像检测
curl -X POST "http://localhost:8002/api/v1/detect/image" \
     -F "file=@cow_image.jpg" \
     -F "confidence_threshold=0.6"

# 获取模型列表
curl -X GET "http://localhost:8002/api/v1/models"
```

## 自定义模型

将自定义模型文件（.pt或.pth格式）放入`models/`目录，或通过API接口加载：

```bash
curl -X POST "http://localhost:8002/api/v1/load_model" \
     -F "model_name=my_custom_model" \
     -F "model_file=@my_model.pt"
```

## 注意事项

1. 确保模型文件路径正确
2. 大视频文件处理可能需要较长时间
3. 生产环境建议使用多进程模式启动服务
4. 建议使用GPU加速以提高检测速度

## 故障排除

1. **模型加载失败**: 检查模型文件路径和格式
2. **内存不足**: 减少工作进程数或使用更小的模型
3. **检测速度慢**: 考虑使用GPU加速或减小输入图像尺寸

## 更新日志

### v1.0.0
- 初始版本发布
- 支持图像和视频中的牛只检测
- 提供RESTful API接口
- 支持自定义模型加载