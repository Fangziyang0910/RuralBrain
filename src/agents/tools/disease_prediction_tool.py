"""疾病预测工具：为可能患病的畜禽提供疾病预测。

收集动物的基本信息、症状描述及患处图片/视频，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行可靠的医疗建议或就医指南以及预测补充。
"""
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

    通过构造专业的兽医诊断提示词，让 LLM 分析症状并返回格式化的报告。

    Args:
        animal_type: 动物类型
        symptoms: 症状描述
        age: 动物年龄（月龄）
        temperature: 体温（摄氏度）
        other_signs: 其他体征描述

    Returns:
        预测结果字典，包含格式化的报告文本和结构化数据
    """
    try:
        # 初始化模型管理器
        model_manager = ModelManager.from_env()
        model = model_manager.get_chat_model(temperature=0.3)

        # 构造诊断提示词
        age_info = f"{age}月龄" if age else "未知"
        temp_info = f"{temperature}°C" if temperature else "未测量"

        prompt = f"""你是一位专业的兽医专家，请根据以下信息进行疾病预测分析。

## 动物信息
- 动物类型：{animal_type}
- 年龄：{age_info}
- 体温：{temp_info}
- 症状描述：{symptoms}
{f"- 其他体征：{other_signs}" if other_signs else ""}

## 分析要求
请直接输出一份结构清晰、易读的疾病预测分析报告，按以下格式组织：

---
### 🩺 疾病预测分析

#### 可能的疾病
1. **疾病名称**（可能性：XX%）
   - 判断依据：说明原因

2. **疾病名称**（可能性：XX%）
   - 判断依据：说明原因

3. **疾病名称**（可能性：XX%）
   - 判断依据：说明原因

#### 关键症状依据
- 症状1
- 症状2
- 症状3

#### 紧急程度
🚨 高/⚠️ 中/ℹ️ 低

#### 处理建议
1. 建议内容
2. 建议内容
3. 建议内容

#### ⚠️ 重要提醒
添加任何需要注意的特殊事项

---

注意：
- 直接输出报告文本，不要使用 JSON 格式
- 不要包含代码块标记
- 如果信息不足，请在建议中说明需要补充的信息
- 紧急程度根据疾病传染性、严重程度判断"""

        # 调用模型
        response = model.invoke([HumanMessage(content=prompt)])
        report_text = response.content.strip()

        # 清理可能的 markdown 代码块标记
        report_text = report_text.replace("```json", "").replace("```", "").strip()

        # 返回结构化结果
        return {
            "success": True,
            "report": report_text,
            "model_used": "deepseek-llm",
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 保留原始输入供后续处理
            "input": {
                "animal_type": animal_type,
                "symptoms": symptoms,
                "age": age,
                "temperature": temperature,
                "other_signs": other_signs
            }
        }

    except Exception as e:
        # 如果 LLM 调用失败，降级到简单规则
        return {
            "success": False,
            "error": str(e),
            "report": f"""### 🩺 疾病预测分析

#### 可能的疾病
**需要进一步检查**（可能性：50%）
- AI 分析暂时不可用，建议咨询专业兽医

#### 关键症状依据
- {symptoms}

#### 紧急程度
⚠️ 中

#### 处理建议
1. 建议联系专业兽医进行诊断
2. 注意观察动物状态变化
3. 如有恶化及时就医

#### ⚠️ 重要提醒
本分析仅供参考，不能替代专业兽医诊断。""",
            "model_used": "fallback"
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
        格式化的疾病预测分析报告
    """
    try:
        # 使用 LLM 进行疾病预测
        result = _predict_with_llm(animal_type, symptoms, age, temperature, other_signs)

        # 如果提供了图片/视频，进行分析
        if media_path:
            # TODO: 后续切换到真实视觉模型
            # image_result = _analyze_image_with_model(media_path, animal_type)

            # 当前使用简单模拟
            image_result = _simple_image_analyze(media_path, animal_type)

            # 将图片分析结果附加到报告中
            if image_result.get("error"):
                image_note = f"\n\n#### 📷 图片分析结果\n图片分析失败：{image_result['error']}"
            else:
                media_type = image_result.get("media_type", "image")
                detected = ", ".join(image_result.get("detected_symptoms", []))
                areas = ", ".join(image_result.get("affected_areas", []))
                severity = image_result.get("severity", "未知")

                image_note = f"""
#### 📷 图片/视频分析结果
- 文件类型：{media_type}
- 检测到的症状：{detected}
- 患处区域：{areas}
- 严重程度评估：{severity}"""

            result["report"] = result.get("report", "") + image_note

        # 直接返回格式化的报告文本
        return result.get("report", "分析失败，请重试。")

    except Exception as e:
        return f"### ⚠️ 分析失败\n\n疾病预测工具遇到错误：{str(e)}\n\n请稍后重试或直接咨询专业兽医。"


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
        print(f"\n{'='*50}")
        print(f"测试用例 {i}")
        print(f"{'='*50}")
        result = disease_prediction_tool.invoke(case)
        print(result)
        print(f"{'='*50}\n")
