"""疾病预测工具：为可能患病的畜禽提供疾病预测。

收集动物的基本信息、症状描述及患处图片/视频，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行可靠的医疗建议或就医指南以及预测补充。
"""
import json
import os
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from ...utils import ModelManager


# TODO: 后续接入真实图像识别模型时替换此函数
def _analyze_image_with_model(media_path: str, animal_type: str) -> dict:
    """使用真实视觉模型分析患处图片/视频

    预留接口，后续接入时实现：
    - 加载训练好的图像识别模型（如 CNN、ViT 等）
    - 图像预处理
    - 模型推理
    - 返回识别结果

    Args:
        media_path: 图片或视频文件路径
        animal_type: 动物类型

    Returns:
        识别结果字典，包含：
        - detected_symptoms: 检测到的症状
        - affected_areas: 患处区域
        - severity: 严重程度
    """
    # 预留：后续接入真实视觉模型
    # model = load_vision_model(f"models/{animal_type}_vision_model.pth")
    # image = preprocess_image(media_path)
    # results = model.predict(image)
    # return format_vision_results(results)
    pass


def _simple_image_analyze(media_path: str, animal_type: str) -> dict:
    """简单图像分析模拟（临时占位）"""
    if not os.path.exists(media_path):
        return {"error": "文件不存在"}

    # 简单的文件类型检查
    ext = os.path.splitext(media_path)[1].lower()
    supported = ['.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov']

    if ext not in supported:
        return {"error": f"不支持的文件格式: {ext}"}

    # 模拟分析结果
    return {
        "media_type": "video" if ext in ['.mp4', '.avi', '.mov'] else "image",
        "file_name": os.path.basename(media_path),
        "detected_symptoms": ["患处红肿", "皮肤异常"],
        "affected_areas": ["腿部", "腹部"],
        "severity": "中度",
        "confidence": 0.65
    }


# TODO: 后续接入真实模型时替换此函数
def _predict_with_actual_model(animal_type: str, symptoms: str, **kwargs) -> dict:
    """使用真实ML模型进行预测

    预留接口，后续接入时实现：
    - 加载训练好的模型
    - 特征提取和预处理
    - 模型推理
    - 返回预测结果

    Args:
        animal_type: 动物类型
        symptoms: 症状描述
        **kwargs: 其他特征（体温、年龄等）

    Returns:
        预测结果字典
    """
    # 预留：后续接入真实模型
    # model = load_model(f"models/{animal_type}_disease_model.pkl")
    # features = extract_features(symptoms, kwargs)
    # predictions = model.predict_proba(features)
    # return format_predictions(predictions)
    pass


def _predict_with_llm(animal_type: str, symptoms: str, age: Optional[int] = None,
                      temperature: Optional[float] = None,
                      other_signs: Optional[str] = None) -> dict:
    """使用 DeepSeek LLM 进行疾病预测

    通过构造专业的兽医诊断提示词，让 LLM 分析症状并预测可能的疾病。

    Args:
        animal_type: 动物类型
        symptoms: 症状描述
        age: 动物年龄（月龄）
        temperature: 体温（摄氏度）
        other_signs: 其他体征描述

    Returns:
        预测结果字典，包含可能的疾病列表及概率
    """
    try:
        # 初始化模型管理器
        model_manager = ModelManager.from_env()
        model = model_manager.get_chat_model(temperature=0.3)

        # 构造诊断提示词
        age_info = f"- 年龄：{age}月龄" if age else "- 年龄：未知"
        temp_info = f"- 体温：{temperature}°C" if temperature else "- 体温：未测量"
        signs_info = f"- 其他体征：{other_signs}" if other_signs else ""

        prompt = f"""你是一位专业的兽医专家，请根据以下信息进行疾病预测分析。

## 动物信息
- 动物类型：{animal_type}
{age_info}
{temp_info}
- 症状描述：{symptoms}
{signs_info}

## 分析要求
请根据以上信息，分析可能的疾病，并按以下格式返回：

1. **可能的疾病**（按概率从高到低排序，至少列出3种）
   - 疾病名称：概率（如 75%）
   - 简要说明原因

2. **关键依据**
   - 列出判断的主要依据（症状、体征等）

3. **建议措施**
   - 提供初步的处理建议
   - 是否需要紧急就医
   - 护理要点

请以 JSON 格式返回，格式如下：
{{
  "predictions": [
    {{"disease": "疾病名称", "probability": 75, "reason": "判断原因"}},
    {{"disease": "疾病名称", "probability": 60, "reason": "判断原因"}},
    {{"disease": "疾病名称", "probability": 45, "reason": "判断原因"}}
  ],
  "key_evidence": ["依据1", "依据2", "依据3"],
  "recommendations": ["建议1", "建议2", "建议3"],
  "urgency": "高/中/低"
}}

注意：
- 只返回 JSON，不要有其他文字
- 概率范围为 0-100
- urgency 为"高"、"中"或"低"之一
- 如果症状描述过于简单，请在 recommendations 中说明需要更多信息"""

        # 调用模型
        response = model.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # 尝试解析 JSON
        # 移除可能的 markdown 代码块标记
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # 添加元数据
        result["model_used"] = "deepseek-llm"
        result["analysis_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return result

    except Exception as e:
        # 如果 LLM 调用失败，降级到简单规则
        return {
            "error": f"LLM预测失败: {str(e)}",
            "predictions": [
                {"disease": "需要进一步检查", "probability": 50, "reason": "AI分析暂时不可用，建议咨询专业兽医"}
            ],
            "key_evidence": [f"症状: {symptoms}"],
            "recommendations": ["建议联系专业兽医进行诊断", "注意观察动物状态变化"],
            "urgency": "中"
        }


@tool
def disease_prediction_tool(
    animal_type: str,
    symptoms: str,
    age: Optional[int] = None,
    temperature: Optional[float] = None,
    other_signs: Optional[str] = None,
    media_path: Optional[str] = None
) -> str:
    """预测畜禽可能的疾病。

    根据动物类型、症状描述、患处图片/视频等信息，使用 AI 分析预测可能的疾病。
    注意：仅供参考，不能替代专业兽医诊断。

    Args:
        animal_type: 动物类型，如 牛、猪、鸡、鸭、羊 等
        symptoms: 症状描述，如 发热、咳嗽、精神萎靡、不食等
        age: 动物年龄（月龄），可选
        temperature: 体温（摄氏度），可选
        other_signs: 其他体征描述，可选
        media_path: 患处图片或视频路径，支持 .jpg, .jpeg, .png, .bmp, .mp4, .avi, .mov，可选

    Returns:
        JSON格式的预测报告，包含：
        - predictions: 可能的疾病及概率
        - image_analysis: 图片/视频分析结果（如果有）
    """
    try:
        # 使用 LLM 进行疾病预测
        result = _predict_with_llm(animal_type, symptoms, age, temperature, other_signs)

        # 添加输入信息到结果
        result["input"] = {
            "animal_type": animal_type,
            "symptoms": symptoms,
            "age": age,
            "temperature": temperature,
            "other_signs": other_signs,
            "media_path": media_path
        }

        # 如果提供了图片/视频，进行分析
        if media_path:
            # TODO: 后续切换到真实视觉模型
            # image_result = _analyze_image_with_model(media_path, animal_type)

            # 当前使用简单模拟
            image_result = _simple_image_analyze(media_path, animal_type)
            result["image_analysis"] = image_result

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


if __name__ == "__main__":
    # 测试工具
    test_cases = [
        {
            "animal_type": "牛",
            "symptoms": "发热、咳嗽、精神萎靡",
            "temperature": 39.8
        },
        {
            "animal_type": "猪",
            "symptoms": "拉稀、不食",
            "temperature": 39.2
        },
        {
            "animal_type": "鸡",
            "symptoms": "精神萎靡、羽毛蓬松",
            "media_path": "test_image.jpg"  # 模拟图片路径测试
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n=== 测试用例 {i} ===")
        result = disease_prediction_tool.invoke(case)
        print(result)
