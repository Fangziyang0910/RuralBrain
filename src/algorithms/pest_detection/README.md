# 害虫检测模块

基于 YOLOv8 深度学习模型的智能害虫检测服务，支持 29 种常见农业害虫的识别。已集成到 RuralBrain 主项目。

## 📂 目录结构

```
pest_detection/
├── detector/                    # 核心检测服务（已重构）
│   ├── app/                    # FastAPI应用
│   │   ├── api/               # API路由
│   │   ├── core/              # 配置管理
│   │   ├── schemas/           # 数据模型
│   │   ├── services/          # 模型服务
│   │   └── main.py            # 应用入口
│   ├── models/                # AI模型文件
│   │   ├── best.pt           # YOLOv8模型
│   │   └── classes.txt       # 类别列表
│   ├── start_service.py       # 服务启动脚本
│   └── README_zh.md           # 详细文档
├── test/                       # 测试文件
│   ├── test.py                # 测试脚本
│   └── images/                # 测试图片
└── README.md                   # 本文档
```

## ✅ 重构说明

本模块已完成以下规范化改造：

1. **目录结构优化**: 去除 `new/` 层级，重命名为 `detector/`
2. **导入路径规范**: 使用绝对导入 `from src.algorithms.pest_detection.detector...`
3. **配置管理优化**: 使用绝对路径，支持从任意位置启动
4. **依赖管理整合**: 已合并到主项目 `pyproject.toml`
5. **启动脚本规范**: 创建标准启动脚本 `start_service.py`

## 🚀 快速启动

### 方式一：Docker部署（推荐）

```bash
# 进入detector目录
cd src/algorithms/pest_detection/detector

# 构建并启动服务
docker-compose up -d --build

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 方式二：Python直接运行

**前提：已安装依赖**

```bash
# 从项目根目录
cd D:\sourse code\RuralBrain

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖（如未安装）
uv pip install -e .

# 启动服务
python -m src.algorithms.pest_detection.detector.start_service
```

**或直接运行：**
```bash
cd src/algorithms/pest_detection/detector
python start_service.py
```

### 访问服务

- API文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/health
- 主页: http://localhost:8001

---

## 🐛 支持的害虫（29种）

瓜实蝇、小菜蛾、斑潜蝇、侧多食跗线螨、稻粉虱、荔枝蒂蛀虫、荔枝蝽、荔枝瘿螨、甘蔗螟虫、茶小绿叶蝉、福寿螺、小象甲、烟粉虱、稻纵卷叶螟、大螟、二化螟、稻飞虱、玉米螟、草地贪夜蛾、蚜虫、黄曲条跳甲、甜菜夜蛾、蔬菜蓟马、菜青虫、柑桔红蜘蛛、柑桔锈蜘蛛、桔小实蝇、斜纹夜蛾、柑桔潜叶蛾

## 🔌 与 Agent 集成

通过 `src/agents/tools/pest_detection_tool.py` 集成到 LangGraph Agent：

```python
from src.agents.tools.pest_detection_tool import pest_detection_tool

# 调用检测
result = pest_detection_tool.invoke({
    "image_path": "path/to/pest_image.jpg"
})
```

## 📊 性能指标

- 模型加载: 1-3秒
- 单图检测: 1-3秒
- 内存占用: 200-500MB
- 检测准确率: 95%+

## 🔧 配置说明

默认配置：
- 主机: 0.0.0.0
- 端口: 8001
- 模型路径: 自动配置（绝对路径）

修改配置请编辑 `detector/app/core/config.py`

## 🐛 故障排除

### 模型文件未找到
确认 `detector/models/best.pt` 文件存在

### 端口被占用
修改 `config.py` 中的 `PORT` 配置

### 导入错误
确保从项目根目录运行，并已激活虚拟环境

## 📚 详细文档

查看 [detector/README_zh.md](detector/README_zh.md) 获取更多信息

---
*集成到 RuralBrain 项目 | 版本: 1.0.0*