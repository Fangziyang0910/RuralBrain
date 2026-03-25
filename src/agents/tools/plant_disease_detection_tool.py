"""植物病害识别工具：智能识别农作物病害。

基于百度飞桨2018年农作物病害数据集，支持10种植物（苹果、樱桃、葡萄、柑桔、桃、草莓、番茄、辣椒、玉米、马铃薯）
共61个分类（包含一般/严重程度），为 Agent 提供病害处理建议。
"""
import os
import base64
from pathlib import Path
from typing import Any

import requests
from langchain_core.tools import tool

from .detection_utils import encode_image_to_base64, save_result_image


# ==================== 配置 ====================

DETECTION_API_URL = os.getenv(
    "PLANT_DISEASE_DETECTION_API_URL",
    "http://detection-service:8001/detection/plant_disease/detect"
)
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# 植物病害分类（根据百度飞桨2018年数据集，61个分类）
PLANT_DISEASE_CLASSES = {
    0: {"name": "苹果（健康）", "crop": "苹果", "disease": "健康", "severity": None},
    1: {"name": "苹果黑星病（一般）", "crop": "苹果", "disease": "黑星病", "severity": "一般"},
    2: {"name": "苹果黑星病（严重）", "crop": "苹果", "disease": "黑星病", "severity": "严重"},
    3: {"name": "苹果灰斑病", "crop": "苹果", "disease": "灰斑病", "severity": None},
    4: {"name": "苹果雪松锈病（一般）", "crop": "苹果", "disease": "雪松锈病", "severity": "一般"},
    5: {"name": "苹果雪松锈病（严重）", "crop": "苹果", "disease": "雪松锈病", "severity": "严重"},
    6: {"name": "樱桃（健康）", "crop": "樱桃", "disease": "健康", "severity": None},
    7: {"name": "樱桃白粉病（一般）", "crop": "樱桃", "disease": "白粉病", "severity": "一般"},
    8: {"name": "樱桃白粉病（严重）", "crop": "樱桃", "disease": "白粉病", "severity": "严重"},
    9: {"name": "玉米（健康）", "crop": "玉米", "disease": "健康", "severity": None},
    10: {"name": "玉米灰斑病（一般）", "crop": "玉米", "disease": "灰斑病", "severity": "一般"},
    11: {"name": "玉米灰斑病（严重）", "crop": "玉米", "disease": "灰斑病", "severity": "严重"},
    12: {"name": "玉米锈病（一般）", "crop": "玉米", "disease": "锈病", "severity": "一般"},
    13: {"name": "玉米锈病（严重）", "crop": "玉米", "disease": "锈病", "severity": "严重"},
    14: {"name": "玉米叶斑病（一般）", "crop": "玉米", "disease": "叶斑病", "severity": "一般"},
    15: {"name": "玉米叶斑病（严重）", "crop": "玉米", "disease": "叶斑病", "severity": "严重"},
    16: {"name": "玉米花叶病毒病", "crop": "玉米", "disease": "花叶病毒病", "severity": None},
    17: {"name": "葡萄（健康）", "crop": "葡萄", "disease": "健康", "severity": None},
    18: {"name": "葡萄黑腐病（一般）", "crop": "葡萄", "disease": "黑腐病", "severity": "一般"},
    19: {"name": "葡萄黑腐病（严重）", "crop": "葡萄", "disease": "黑腐病", "severity": "严重"},
    20: {"name": "葡萄轮斑病（一般）", "crop": "葡萄", "disease": "轮斑病", "severity": "一般"},
    21: {"name": "葡萄轮斑病（严重）", "crop": "葡萄", "disease": "轮斑病", "severity": "严重"},
    22: {"name": "葡萄褐斑病（一般）", "crop": "葡萄", "disease": "褐斑病", "severity": "一般"},
    23: {"name": "葡萄褐斑病（严重）", "crop": "葡萄", "disease": "褐斑病", "severity": "严重"},
    24: {"name": "柑桔（健康）", "crop": "柑桔", "disease": "健康", "severity": None},
    25: {"name": "柑桔黄龙病（一般）", "crop": "柑桔", "disease": "黄龙病", "severity": "一般"},
    26: {"name": "柑桔黄龙病（严重）", "crop": "柑桔", "disease": "黄龙病", "severity": "严重"},
    27: {"name": "桃（健康）", "crop": "桃", "disease": "健康", "severity": None},
    28: {"name": "桃疮痂病（一般）", "crop": "桃", "disease": "疮痂病", "severity": "一般"},
    29: {"name": "桃疮痂病（严重）", "crop": "桃", "disease": "疮痂病", "severity": "严重"},
    30: {"name": "辣椒（健康）", "crop": "辣椒", "disease": "健康", "severity": None},
    31: {"name": "辣椒疮痂病（一般）", "crop": "辣椒", "disease": "疮痂病", "severity": "一般"},
    32: {"name": "辣椒疮痂病（严重）", "crop": "辣椒", "disease": "疮痂病", "severity": "严重"},
    33: {"name": "马铃薯（健康）", "crop": "马铃薯", "disease": "健康", "severity": None},
    34: {"name": "马铃薯早疫病（一般）", "crop": "马铃薯", "disease": "早疫病", "severity": "一般"},
    35: {"name": "马铃薯早疫病（严重）", "crop": "马铃薯", "disease": "早疫病", "severity": "严重"},
    36: {"name": "马铃薯晚疫病（一般）", "crop": "马铃薯", "disease": "晚疫病", "severity": "一般"},
    37: {"name": "马铃薯晚疫病（严重）", "crop": "马铃薯", "disease": "晚疫病", "severity": "严重"},
    38: {"name": "草莓（健康）", "crop": "草莓", "disease": "健康", "severity": None},
    39: {"name": "草莓叶枯病（一般）", "crop": "草莓", "disease": "叶枯病", "severity": "一般"},
    40: {"name": "草莓叶枯病（严重）", "crop": "草莓", "disease": "叶枯病", "severity": "严重"},
    41: {"name": "番茄（健康）", "crop": "番茄", "disease": "健康", "severity": None},
    42: {"name": "番茄白粉病（一般）", "crop": "番茄", "disease": "白粉病", "severity": "一般"},
    43: {"name": "番茄白粉病（严重）", "crop": "番茄", "disease": "白粉病", "severity": "严重"},
    44: {"name": "番茄疮痂病（一般）", "crop": "番茄", "disease": "疮痂病", "severity": "一般"},
    45: {"name": "番茄疮痂病（严重）", "crop": "番茄", "disease": "疮痂病", "severity": "严重"},
    46: {"name": "番茄早疫病（一般）", "crop": "番茄", "disease": "早疫病", "severity": "一般"},
    47: {"name": "番茄早疫病（严重）", "crop": "番茄", "disease": "早疫病", "severity": "严重"},
    48: {"name": "番茄晚疫病菌（一般）", "crop": "番茄", "disease": "晚疫病", "severity": "一般"},
    49: {"name": "番茄晚疫病菌（严重）", "crop": "番茄", "disease": "晚疫病", "severity": "严重"},
    50: {"name": "番茄叶霉病（一般）", "crop": "番茄", "disease": "叶霉病", "severity": "一般"},
    51: {"name": "番茄叶霉病（严重）", "crop": "番茄", "disease": "叶霉病", "severity": "严重"},
    52: {"name": "番茄斑点病（一般）", "crop": "番茄", "disease": "斑点病", "severity": "一般"},
    53: {"name": "番茄斑点病（严重）", "crop": "番茄", "disease": "斑点病", "severity": "严重"},
    54: {"name": "番茄斑枯病（一般）", "crop": "番茄", "disease": "斑枯病", "severity": "一般"},
    55: {"name": "番茄斑枯病（严重）", "crop": "番茄", "disease": "斑枯病", "severity": "严重"},
    56: {"name": "番茄红蜘蛛损伤（一般）", "crop": "番茄", "disease": "红蜘蛛损伤", "severity": "一般"},
    57: {"name": "番茄红蜘蛛损伤（严重）", "crop": "番茄", "disease": "红蜘蛛损伤", "severity": "严重"},
    58: {"name": "番茄黄化曲叶病毒病（一般）", "crop": "番茄", "disease": "黄化曲叶病毒病", "severity": "一般"},
    59: {"name": "番茄黄化曲叶病毒病（严重）", "crop": "番茄", "disease": "黄化曲叶病毒病", "severity": "严重"},
    60: {"name": "番茄花叶病毒病", "crop": "番茄", "disease": "花叶病毒病", "severity": None},
}


# ==================== 工具实现 ====================

def _mock_plant_disease_detection(image_path: str) -> dict:
    """模拟植物病害检测（模型未训练时使用）

    TODO: 等植物病害识别模型训练完成后删除此函数

    Args:
        image_path: 图片路径

    Returns:
        模拟的检测结果
    """
    filename = Path(image_path).name.lower()

    # 根据文件名简单推断（临时方案）
    if "tomato" in filename and "late" in filename:
        class_id = 48
        confidence = 0.88
    elif "tomato" in filename and "early" in filename:
        class_id = 46
        confidence = 0.82
    elif "tomato" in filename:
        class_id = 41
        confidence = 0.75
    elif "corn" in filename or "maize" in filename:
        class_id = 9
        confidence = 0.90
    elif "apple" in filename:
        class_id = 0
        confidence = 0.85
    elif "grape" in filename:
        class_id = 17
        confidence = 0.78
    else:
        class_id = 0  # 默认健康
        confidence = 0.5

    disease_info = PLANT_DISEASE_CLASSES.get(class_id, PLANT_DISEASE_CLASSES[0])

    return {
        "success": True,
        "class_id": class_id,
        "disease_name": disease_info["name"],
        "crop": disease_info["crop"],
        "disease": disease_info["disease"],
        "severity": disease_info["severity"] or "无",
        "confidence": confidence,
        "mock": True
    }


def _call_plant_disease_detection_api(image_path: str) -> dict:
    """调用植物病害检测服务 API

    TODO: 等植物病害识别模型训练完成后启用此函数

    Args:
        image_path: 图片路径

    Returns:
        API 返回的检测结果
    """
    try:
        image_base64 = encode_image_to_base64(image_path)

        response = requests.post(
            DETECTION_API_URL,
            json={"image_base64": image_base64},
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"API 返回错误: {response.status_code}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def format_detection_result(result: dict) -> str:
    """格式化检测结果为可读文本

    Args:
        result: 检测结果字典

    Returns:
        格式化的结果文本
    """
    if not result.get("success"):
        error_msg = result.get("error", "未知错误")
        return f"❌ 植物病害检测失败: {error_msg}"

    class_id = result.get("class_id", -1)
    disease_name = result.get("disease_name", "未知病害")
    crop = result.get("crop", "未知")
    disease = result.get("disease", "未知")
    severity = result.get("severity", "无")
    confidence = result.get("confidence", 0.0)
    is_mock = result.get("mock", False)

    # 如果是健康状态
    if disease == "健康" or class_id in [0, 6, 9, 17, 24, 27, 30, 33, 38, 41]:
        lines = [
            "## 🌿 植物病害检测结果",
            f"**作物类型**: {crop}",
            f"**检测结果**: 健康",
            f"**置信度**: {confidence:.1%}",
        ]
        if is_mock:
            lines.append("\n> 💡 当前使用模拟检测，请先训练植物病害识别模型")
        return "\n".join(lines)

    # 构建病害检测结果
    severity_icon = "🔴" if severity == "严重" else "🟡" if severity == "一般" else "🟢"

    lines = [
        "## 🌿 植物病害检测结果",
        f"**作物类型**: {crop}",
        f"**病害类型**: {disease}",
        f"**检测详情**: {disease_name}",
        f"**严重程度**: {severity_icon} {severity}",
        f"**置信度**: {confidence:.1%}",
    ]

    if is_mock:
        lines.append("\n> 💡 当前使用模拟检测，请先训练植物病害识别模型")

    # 添加处理建议
    lines.extend([
        "",
        "### 💊 处理建议"
    ])

    if severity == "严重":
        lines.extend([
            "1. **立即隔离**: 封锁病害区域，防止扩散",
            "2. **药剂防治**: 使用针对性杀菌剂进行全面喷洒",
            "3. **清除病株**: 及时清除严重感染的植株并销毁",
            "4. **加强管理**: 改善通风透光条件，降低湿度"
        ])
    elif severity == "一般":
        lines.extend([
            "1. **局部防治**: 对感染区域进行药剂喷洒",
            "2. **密切观察**: 每日监测病害发展情况",
            "3. **农业防治**: 增施有机肥，提高植株抗病力"
        ])
    else:
        lines.extend([
            "1. **预防为主**: 喷洒预防性杀菌剂",
            "2. **加强监测**: 定期巡查，早发现早处理"
        ])

    return "\n".join(lines)


@tool
def plant_disease_detection_tool(image_path: str) -> str:
    """识别农作物的病害类型和严重程度。

    基于百度飞桨2018年农作物病害数据集，支持10种植物的病害识别：
    苹果、樱桃、葡萄、柑桔、桃、草莓、番茄、辣椒、玉米、马铃薯
    共61个分类（包含一般/严重程度）。

    Args:
        image_path: 图片文件的本地路径，支持格式：jpg、jpeg、png、bmp、webp

    Returns:
        病害检测结果和处理建议
    """
    try:
        # 验证文件
        path = Path(image_path)
        if not path.exists():
            return "❌ 图片文件不存在"

        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return f"❌ 不支持的图片格式: {path.suffix}"

        # TODO: 模型训练完成后，切换到真实 API
        # result = _call_plant_disease_detection_api(image_path)

        # 当前使用模拟检测
        result = _mock_plant_disease_detection(image_path)

        return format_detection_result(result)

    except Exception as e:
        return f"❌ 植物病害检测失败: {str(e)}"


# ==================== 辅助函数（供其他工具调用） ====================

def detect_plant_disease(image_path: str) -> dict:
    """检测植物病害（返回原始数据，供其他工具使用）

    Args:
        image_path: 图片路径

    Returns:
        原始检测结果字典
    """
    try:
        # TODO: 模型训练完成后切换
        # return _call_plant_disease_detection_api(image_path)
        return _mock_plant_disease_detection(image_path)
    except Exception:
        return {"success": False, "error": str(Exception)}


__all__ = ["plant_disease_detection_tool", "detect_plant_disease"]
plant_disease_detection_tool.tags = ["detection", "plant", "disease"]
