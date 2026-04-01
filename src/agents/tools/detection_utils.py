"""检测工具共享模块。

提供图像检测工具的通用辅助函数，包括结果保存、编码和格式化。
支持多模态检测结果解释（使用 LLM 生成自然语言分析）。
"""
import base64
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
import uuid
import mimetypes

from langchain_core.messages import HumanMessage

from service.settings import DETECTION_RESULTS_DIR, MAX_CACHE_SIZE
from src.utils.file_manager import cleanup_lru
from src.utils import ModelManager
from src.config import AVAILABLE_MODELS

logger = logging.getLogger(__name__)


def save_result_image(
    image_content: bytes,
    detection_type: str,
    file_prefix: str,
) -> str:
    """保存检测结果图片（带自动 LRU 清理）

    Args:
        image_content: 图片二进制内容
        detection_type: 检测类型（pest/cow/rice）
        file_prefix: 结果文件名前缀

    Returns:
        图片访问路径（URL 路径）
    """
    # 1. 确定保存目录
    results_dir = DETECTION_RESULTS_DIR / detection_type
    results_dir.mkdir(exist_ok=True)

    # 2. 检查并清理（如果容量超限）
    cleanup_lru(DETECTION_RESULTS_DIR, MAX_CACHE_SIZE)

    # 3. 保存新文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{file_prefix}_result_{timestamp}_{unique_id}.jpg"
    file_path = results_dir / filename
    file_path.write_bytes(image_content)

    # 4. 返回访问路径
    return f"/{detection_type}_results/{filename}"


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串。

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的图片字符串
    """
    image_bytes = Path(image_path).read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def format_detection_result(
    success: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> str:
    """格式化检测结果为 JSON 字符串。

    Args:
        success: 操作是否成功
        data: 成功时的结果数据
        error: 失败时的错误信息

    Returns:
        JSON 格式的结果字符串
    """
    result: dict[str, Any] = {"success": success}

    if success:
        if data:
            result.update(data)
    else:
        result["error"] = error or "未知错误"

    return json.dumps(result, ensure_ascii=False)


def extract_image_from_messages(messages: list) -> dict | None:
    """从消息历史中提取图片信息。

    支持两种消息格式：
    - 多模态消息：从 content blocks 中提取 base64 图片数据
    - 纯文本消息：从文本中提取图片路径（[图片路径 N: /path] 格式）

    Args:
        messages: LangChain 消息历史列表

    Returns:
        包含图片信息的字典：
        - {"base64": str, "mime_type": str} - 多模态格式
        - {"path": str} - 路径格式
        - None - 未找到图片
    """
    for message in reversed(messages):
        if not isinstance(message, HumanMessage):
            continue

        content = message.content

        # 多模态消息格式（列表形式）
        if isinstance(content, list):
            for block in content:
                # LangChain 标准 image block 格式
                if block.get("type") == "image":
                    base64_data = block.get("base64")
                    if base64_data:
                        logger.info("从多模态消息中提取到 base64 图片")
                        return {
                            "base64": base64_data,
                            "mime_type": block.get("mime_type", "image/jpeg"),
                        }

                # OpenAI 兼容格式 (image_url)
                elif block.get("type") == "image_url":
                    image_url = block.get("image_url", {})
                    url = image_url.get("url", "")
                    # data:image/jpeg;base64,<data>
                    if url.startswith("data:"):
                        match = re.match(r"data:(.+);base64,(.+)", url)
                        if match:
                            mime_type, base64_data = match.groups()
                            logger.info("从 OpenAI 兼容格式中提取到 base64 图片")
                            return {
                                "base64": base64_data,
                                "mime_type": mime_type,
                            }

        # 纯文本消息格式（从中提取路径）
        elif isinstance(content, str):
            # 匹配 [图片路径 N: /path] 格式
            match = re.search(r"\[图片路径\s*\d*:\s*(.+?)\]", content)
            if match:
                path = match.group(1).strip()
                logger.info(f"从文本消息中提取到图片路径: {path}")
                return {"path": path}

    logger.warning("未从消息历史中找到图片信息")
    return None


# ==================== 多模态解释层 ====================

# 解释功能开关（环境变量控制）
ENABLE_DETECTION_EXPLANATION = os.getenv("ENABLE_DETECTION_EXPLANATION", "true").lower() == "true"


def is_model_multimodal(model_id: str) -> bool:
    """判断指定模型是否支持多模态。

    Args:
        model_id: 模型标识（如 "qwen"、"deepseek"）

    Returns:
        True 如果支持多模态，否则 False
    """
    # 直接通过 model_id 匹配 AVAILABLE_MODELS 的 key
    if model_id in AVAILABLE_MODELS:
        return AVAILABLE_MODELS[model_id].get("is_multimodal", False)

    # 也可以通过 model_name 匹配
    for config in AVAILABLE_MODELS.values():
        if config.get("model_name") == model_id:
            return config.get("is_multimodal", False)

    return False


# 各检测类型的解释 Prompt 模板
EXPLANATION_PROMPTS = {
    "pest": """
你是农业病虫害防治专家。请根据以下检测结果，提供专业的分析和建议。

检测结果：{detections}

请按以下格式输出：

### 🐛 病虫害分析

#### 检测结果解读
简要描述检测到的病虫害种类和数量，说明其危害程度。

#### 危害评估
判断当前情况的严重程度（轻微/中等/严重），说明可能造成的损失。

#### 防治建议
1. **化学防治**：推荐合适的农药（名称、浓度、使用方法）
2. **物理防治**：其他辅助措施（如清除虫源、诱杀等）
3. **时机建议**：最佳防治时间和频次

#### 预防措施
长期预防建议，包括田间管理、轮作、抗虫品种选择等。

#### ⚠️ 注意事项
使用农药的安全提醒、环境保护建议等。
""",

    "rice": """
你是粮油作物品质鉴定专家。请根据以下大米品种识别结果，提供专业分析。

检测结果：{detections}

请按以下格式输出：

### 🌾 大米品种分析

#### 品种识别结果
说明识别到的大米品种及其特征（外观、口感、产地等）。

#### 品质评估
根据品种特点评估大米品质等级和市场定位。

#### 储存建议
大米储存的温湿度条件、防虫防潮措施。

#### 食用建议
该品种的最佳烹饪方法、搭配建议。

#### 市场价值
该品种的市场价格区间、销售渠道建议。
""",

    "cow": """
你是畜牧养殖专家。请根据以下奶牛检测结果，提供专业分析。

检测结果：{detections}

请按以下格式输出：

### 🐄 奶牛检测分析

#### 检测结果解读
描述检测到的奶牛数量、分布情况。

#### 健康评估
根据图片观察奶牛的整体状态（体态、毛色、精神状态等）。

#### 管理建议
1. **饲养管理**：饲料配比、饮水供应建议
2. **环境管理**：牛舍清洁、通风、温控建议
3. **健康监测**：定期检查要点

#### 注意事项
奶牛养殖中需要注意的健康指标、常见问题预防。
""",

    "plant_disease": """
你是植物病理学专家。请根据以下检测结果，提供专业的病害分析和防治建议。

检测结果：
- 病害名称：{disease_name}
- 作物类型：{crop}
- 病害类型：{disease}
- 严重程度：{severity}
- 置信度：{confidence:.1%}

请按以下格式输出：

### 🌿 植物病害分析

#### 病害诊断
解释该病害的症状特征、发病原因、传播途径。

#### 危害评估
判断病害对作物的危害程度，可能造成的产量损失。

#### 防治建议
1. **化学防治**：推荐药剂（名称、浓度、喷施方法）
2. **农业防治**：田间管理措施（清除病株、合理施肥等）
3. **生物防治**：可选的生物防治方法

#### 预防措施
下季种植的预防建议（品种选择、田间卫生、轮作等）。

#### ⚠️ 注意事项
用药安全、抗药性管理、环境保护提醒。
""",
}


def generate_detection_explanation(
    detection_type: Literal["pest", "rice", "cow", "plant_disease"],
    detection_result: dict[str, Any],
    image_base64: str | None = None,
    model_id: str | None = None,
) -> str | None:
    """使用多模态模型生成检测结果的自然语言解释。

    Args:
        detection_type: 检测类型（pest/rice/cow/plant_disease）
        detection_result: 检测 API 返回的结果数据
        image_base64: 原图 base64 数据（可选，用于多模态分析）
        model_id: 用户选择的模型 ID（如 "qwen"、"deepseek"），用于判断是否支持多模态

    Returns:
        解释文本，如果禁用或失败则返回 None
    """
    # 1. 检查是否启用解释功能
    if not ENABLE_DETECTION_EXPLANATION:
        logger.info("检测解释功能已禁用（ENABLE_DETECTION_EXPLANATION=false）")
        return None

    # 2. 检测失败时不生成解释
    if not detection_result.get("success"):
        return None

    # 3. 判断用户选择的模型是否支持多模态
    # model_id 是用户在前端选择的模型（通过 runtime.context.model_id 传递）
    if model_id:
        current_provider = model_id
        supports_multimodal = image_base64 and is_model_multimodal(model_id)
    else:
        # 降级：从环境变量读取默认模型
        model_manager = ModelManager.from_env()
        current_provider = model_manager.provider
        supports_multimodal = image_base64 and is_model_multimodal(current_provider)

    logger.info(f"用户选择模型: {model_id}, 当前供应商: {current_provider}, 支持多模态: {supports_multimodal}")

    try:
        # 4. 根据 model_id 获取正确的模型实例
        if model_id and model_id in AVAILABLE_MODELS:
            # 使用用户选择的模型
            config = AVAILABLE_MODELS[model_id]
            model_manager = ModelManager(provider=config["provider"])
            model = model_manager.get_chat_model(model=config["model_name"], temperature=0.3)
        else:
            # 降级：使用环境变量中的默认模型
            model_manager = ModelManager.from_env()
            model = model_manager.get_chat_model(temperature=0.3)

        # 5. 构建 Prompt
        prompt_template = EXPLANATION_PROMPTS.get(detection_type)
        if not prompt_template:
            logger.warning(f"未找到检测类型 {detection_type} 的解释模板")
            return None

        # 根据检测类型格式化检测结果
        if detection_type == "plant_disease":
            detections_str = f"{detection_result.get('disease_name', '未知')}（置信度: {detection_result.get('confidence', 0):.1%}）"
            prompt = prompt_template.format(
                disease_name=detection_result.get("disease_name", "未知"),
                crop=detection_result.get("crop", "未知"),
                disease=detection_result.get("disease", "未知"),
                severity=detection_result.get("severity", "未知"),
                confidence=detection_result.get("confidence", 0),
            )
        else:
            # pest/rice/cow 格式化检测列表
            detections = detection_result.get("detections", [])
            if not detections:
                # 无检测结果
                if detection_type == "pest":
                    return "检测完成，未发现害虫。这是好消息，建议继续保持田间卫生，定期巡查。"
                elif detection_type == "cow":
                    return "检测完成，未识别到奶牛。请确保图片中有清晰的奶牛图像。"
                elif detection_type == "rice":
                    return "检测完成，未识别到大米颗粒。请确保图片中有清晰的大米样本。"

            detection_parts = []
            for det in detections:
                name = det.get("name", "未知")
                count = det.get("count", 0)
                detection_parts.append(f"{name}({count})" if detection_type != "rice" else f"{name}({count}粒)")

            detections_str = "、".join(detection_parts)
            prompt = prompt_template.format(detections=detections_str)

        # 6. 构建消息（多模态或纯文本）
        if supports_multimodal:
            # 多模态消息：图片 + 文本
            mime_type = "image/jpeg"  # 默认
            content_blocks = [
                {"type": "text", "text": prompt + "\n\n**注意**：你能够直接看到用户上传的图片，请结合图片观察和检测结果进行综合分析。"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
                }
            ]
            message = HumanMessage(content=content_blocks)
            logger.info(f"使用多模态模型 {model_id} 生成检测解释")
        else:
            # 纯文本消息
            message = HumanMessage(content=prompt)
            logger.info("使用纯文本模式生成检测解释")

        # 7. 调用模型
        response = model.invoke([message])
        explanation = response.content.strip()

        # 8. 清理输出（移除可能的代码块标记）
        explanation = explanation.replace("```json", "").replace("```", "").strip()

        return explanation

    except Exception as e:
        logger.error(f"生成检测解释失败: {e}", exc_info=True)
        return None


__all__ = [
    "save_result_image",
    "encode_image_to_base64",
    "format_detection_result",
    "extract_image_from_messages",
    "is_model_multimodal",
    "generate_detection_explanation",
    "ENABLE_DETECTION_EXPLANATION",
]
