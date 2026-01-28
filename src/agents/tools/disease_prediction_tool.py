"""疾病预测工具：为可能患病的畜禽提供疾病预测。

收集动物的基本信息、症状描述及患处图片/视频，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行可靠的医疗建议或就医指南以及预测补充。
"""
import json
import os
from typing import Optional
from langchain_core.tools import tool


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


def _simple_rule_predict(animal_type: str, symptoms: str, **kwargs) -> dict:
    """简单规则预测（临时模拟实现）

    后续会被真实模型替换，这里只是占位实现。
    """
    # 简单的关键词匹配模拟
    symptom_lower = symptoms.lower()

    # 模拟预测结果
    predictions = []

    if "发热" in symptom_lower or "发烧" in symptom_lower:
        predictions.append({"disease": "感染性疾病", "probability": 0.75})
    if "咳嗽" in symptom_lower or "喘" in symptom_lower:
        predictions.append({"disease": "呼吸道疾病", "probability": 0.68})
    if "拉稀" in symptom_lower or "腹泻" in symptom_lower:
        predictions.append({"disease": "消化道疾病", "probability": 0.72})
    if "不食" in symptom_lower or "厌食" in symptom_lower:
        predictions.append({"disease": "代谢紊乱", "probability": 0.55})

    # 如果没有匹配，返回默认
    if not predictions:
        predictions.append({"disease": "待进一步检查", "probability": 0.5})

    return {"predictions": predictions}


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

    根据动物类型、症状描述、患处图片/视频等信息，预测可能的疾病。
    注意：当前为模拟实现，仅供参考，不能替代专业兽医诊断。

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
        # TODO: 后续切换到真实模型
        # result = _predict_with_actual_model(animal_type, symptoms)

        # 当前使用简单规则模拟
        result = _simple_rule_predict(animal_type, symptoms)

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


# 为工具添加标签，供 ToolSelectorMiddleware 使用
disease_prediction_tool.tags = ["prediction", "disease", "health"]
