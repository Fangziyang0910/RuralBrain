# 🐛 昆虫检测API

基于 YOLOv8 深度学习模型的昆虫检测 FastAPI 服务，支持 29 种常见农业害虫的智能识别。

## 🚀 快速部署

### 方法1：使用部署包（推荐）
```
1. 进入 deployment_package 目录
2. 双击运行 "本地部署.bat" 
3. 等待自动安装完成
4. 访问 http://localhost:8001/docs
```

### 方法2：手动部署
```bash
# 安装依赖
uv sync

# 启动服务
uv run python run.py
```

## 🌐 访问地址
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **检测接口**: POST http://localhost:8001/api/detect

## 📁 项目结构

```
insect_detector/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI应用入口
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── schemas/           # 数据模型
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── models/                # 模型文件
│   └── best.pt           # YOLOv8训练的模型
├── deployment_package/    # 便携部署包
│   ├── 本地部署.bat       # 一键部署脚本
│   └── ...               # 完整应用副本
├── output_images/         # 输出图像目录
├── pyproject.toml/uv.lock # Python依赖（统一管理）
└── run.py                # 启动脚本
```

## 🧪 使用示例

### Python调用
```python
import requests

# 上传图像进行检测
with open('insect_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/api/detect',
        files={'file': f}
    )

result = response.json()
print(result)
```

### curl调用
```bash
curl -X POST "http://localhost:8001/api/detect" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@insect_image.jpg"
```

## 🐛 支持的昆虫类型 (29种)

包括瓜实蝇、小菜蛾、草地贪夜蛾、稻飞虱、蚜虫等29种常见农业害虫。

详细列表请访问 API 文档：http://localhost:8001/docs

## 📋 系统要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python版本**: 3.8-3.11
- **内存要求**: 至少2GB可用内存
- **网络**: 首次安装需要网络连接下载依赖

## ⚠️ 注意事项

- 模型文件 `models/best.pt` 必须存在
- 支持的图像格式：JPEG, PNG, BMP
- 推荐图像尺寸：640x640像素以上
- 首次运行会自动下载必要的依赖包

## 📞 获取帮助

- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **部署问题**: 查看 `deployment_package/README.md`

---
*版本: v1.0 | 更新日期: 2025年12月2日*
