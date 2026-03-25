"""场景分类工具：智能识别农场巡检图片的场景类型。

通过分析巡检图片（监控/无人机），识别场景类型（牛舍/猪舍/农田），
为 Agent 提供后续工具调用建议。
"""
import os
import base64
from pathlib import Path
from typing import Any

import requests
from langchain_core.tools import tool

from .detection_utils import encode_image_to_base64


# ==================== 配置 ====================

DETECTION_API_URL = os.getenv(
    "SCENE_DETECTION_API_URL",
    "http://detection-service:8001/detection/scene/classify"
)
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# 场景类型定义（仅保留三个场景）
SCENE_TYPES = {
    "cattle": {
        "name": "牛舍",
        "description": "奶牛养殖区域",
        "recommended_tools": [
            {"tool": "cow_detection_tool", "reason": "检测牛只数量"},
            {"tool": "disease_prediction_tool", "reason": "分析牛只健康状况"}
        ]
    },
    "pig": {
        "name": "猪舍",
        "description": "生猪养殖区域",
        "recommended_tools": [
            {"tool": "disease_prediction_tool", "reason": "分析猪只健康状况"}
        ]
    },
    "farmland": {
        "name": "农田",
        "description": "农作物种植区域",
        "recommended_tools": [
            {"tool": "pest_detection_tool", "reason": "检测病虫害"},
            {"tool": "plant_disease_detection_tool", "reason": "识别植物病害"}
        ]
    },
    "unknown": {
        "name": "未知场景",
        "description": "无法识别的场景类型",
        "recommended_tools": []
    }
}


# ==================== 工具实现 ====================

def _mock_scene_classification(image_path: str) -> dict:
    """模拟场景分类（模型未训练时使用）

    TODO: 等场景分类模型训练完成后删除此函数

    Args:
        image_path: 图片路径

    Returns:
        模拟的分类结果
    """
    # 根据文件名简单推断（临时方案）
    filename = Path(image_path).name.lower()

    if "cow" in filename or "cattle" in filename or "牛" in filename:
        scene_type = "cattle"
        confidence = 0.95
    elif "pig" in filename or "猪" in filename:
        scene_type = "pig"
        confidence = 0.92
    elif "farm" in filename or "田" in filename or "crop" in filename or "farmland" in filename:
        scene_type = "farmland"
        confidence = 0.85
    else:
        scene_type = "unknown"
        confidence = 0.0

    return {
        "scene_type": scene_type,
        "confidence": confidence,
        "mock": True
    }


def _call_scene_detection_api(image_path: str) -> dict:
    """调用场景检测服务 API

    TODO: 等场景分类模型训练完成后启用此函数

    Args:
        image_path: 图片路径

    Returns:
        API 返回的分类结果
    """
    try:
        image_base64 = encode_image_to_base64(image_path)

        response = requests.post(
            DETECTION_API_URL,
            json={"image_base64": image_base64},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API 返回错误: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}


def format_classification_result(result: dict) -> str:
    """格式化分类结果为可读文本

    Args:
        result: 分类结果字典

    Returns:
        格式化的结果文本
    """
    if result.get("error"):
        return f"场景分类失败: {result['error']}"

    scene_type = result.get("scene_type", "unknown")
    confidence = result.get("confidence", 0.0)
    is_mock = result.get("mock", False)

    scene_info = SCENE_TYPES.get(scene_type, SCENE_TYPES["unknown"])

    # 构建结果文本
    lines = [
        "## 📍 场景识别结果",
        f"- **场景类型**: {scene_info['name']} ({scene_type})",
        f"- **置信度**: {confidence:.1%}",
        f"- **说明**: {scene_info['description']}"
    ]

    # 添加模拟标记
    if is_mock:
        lines.append("\n> 💡 当前使用模拟分类，请先训练场景分类模型")

    # 添加建议工具
    if scene_info["recommended_tools"]:
        lines.append("\n### 🛠️ 建议的后续工具:")
        for tool in scene_info["recommended_tools"]:
            lines.append(f"- **{tool['tool']}**: {tool['reason']}")
    else:
        lines.append("\n### ⚠️ 无法识别场景，建议人工确认")

    return "\n".join(lines)


@tool
def scene_classifier_tool(image_path: str) -> str:
    """识别农场巡检图片的场景类型。

    根据巡检图片（监控、无人机拍摄），智能识别场景类型：
    - 牛舍 (cattle)：建议调用牛只检测和疾病预测工具
    - 猪舍 (pig)：建议调用疾病预测工具
    - 农田 (farmland)：建议调用病虫害和植物病害检测工具

    Args:
        image_path: 图片文件的本地路径，支持格式：jpg、jpeg、png、bmp、webp

    Returns:
        场景识别结果和建议的后续工具调用列表
    """
    try:
        # 验证文件
        path = Path(image_path)
        if not path.exists():
            return "❌ 图片文件不存在"

        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return f"❌ 不支持的图片格式: {path.suffix}"

        # TODO: 模型训练完成后，切换到真实 API
        # result = _call_scene_detection_api(image_path)

        # 当前使用模拟分类
        result = _mock_scene_classification(image_path)

        return format_classification_result(result)

    except Exception as e:
        return f"❌ 场景分类失败: {str(e)}"


# ==================== 辅助函数（供其他工具调用） ====================

def get_scene_recommendations(scene_type: str) -> list[dict]:
    """获取场景对应的推荐工具列表

    Args:
        scene_type: 场景类型

    Returns:
        推荐工具列表
    """
    return SCENE_TYPES.get(scene_type, SCENE_TYPES["unknown"])["recommended_tools"]


def classify_scene_from_path(image_path: str) -> dict:
    """从图片路径分类场景（返回原始数据，供其他工具使用）

    Args:
        image_path: 图片路径

    Returns:
        原始分类结果字典
    """
    try:
        # TODO: 模型训练完成后切换
        # return _call_scene_detection_api(image_path)
        return _mock_scene_classification(image_path)
    except Exception:
        return {"scene_type": "unknown", "confidence": 0.0}


__all__ = ["scene_classifier_tool", "get_scene_recommendations", "classify_scene_from_path"]
scene_classifier_tool.tags = ["detection", "scene", "classification"]
