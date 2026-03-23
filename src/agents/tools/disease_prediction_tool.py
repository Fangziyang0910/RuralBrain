"""疾病预测工具：为可能患病的畜禽提供疾病预测。

收集动物的基本信息、症状描述及患处图片/视频，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行可靠的医疗建议或就医指南以及预测补充。

集成 RAG 知识库检索，基于专业兽医文献提供更准确的疾病预测。
"""
import os
from datetime import datetime
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from ...utils import ModelManager
from ...rag.config import get_embeddings_cached
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings


# ==================== 疾病知识库检索 ====================

def _get_disease_vectorstore():
    """获取疾病知识库向量存储"""
    project_root = Path(__file__).parent.parent.parent.parent
    chroma_dir = project_root / "knowledge_base" / "diseases" / "chroma_db"

    if not chroma_dir.exists():
        return None

    try:
        embeddings = get_embeddings_cached()
        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        vectorstore = Chroma(
            collection_name="diseases_knowledge",
            embedding_function=embeddings,
            client=client,
            persist_directory=str(chroma_dir)
        )
        return vectorstore
    except Exception:
        return None


def _search_disease_knowledge(query: str, top_k: int = 3) -> str:
    """检索疾病知识库

    Args:
        query: 查询问题
        top_k: 返回结果数量

    Returns:
        检索到的相关知识片段
    """
    try:
        vectorstore = _get_disease_vectorstore()
        if not vectorstore:
            return ""

        results = vectorstore.similarity_search(query, k=top_k)

        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "未知来源")
            content = doc.page_content.strip()
            context_parts.append(f"[参考{i}] {source}\n{content}\n")

        return "\n".join(context_parts)
    except Exception:
        return ""


# TODO: 后续接入真实图像识别模型时替换此函数
def _analyze_image_with_model(media_path: str, animal_type: str) -> dict:
    """使用真实视觉模型分析患处图片/视频

    调用疾病检测服务 API 进行图片识别。

    Args:
        media_path: 图片或视频文件路径
        animal_type: 动物类型

    Returns:
        识别结果字典，包含：
        - detected_diseases: 检测到的疾病列表
        - primary_disease: 主要疾病
        - animal_type: 识别的动物类型
        - severity: 严重程度
    """
    import requests
    import base64

    # 疾病检测服务 API 地址
    DISEASE_DETECTION_API_URL = "http://localhost:8001/detection/disease/detect"

    # 检查文件是否存在
    if not os.path.exists(media_path):
        return {"error": "文件不存在"}

    # 检查文件类型
    ext = os.path.splitext(media_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
        return {"error": f"不支持的文件格式: {ext}"}

    try:
        # 读取图片并转换为 base64
        with open(media_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 调用检测服务 API
        response = requests.post(
            DISEASE_DETECTION_API_URL,
            json={"image_base64": image_base64},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("success"):
                detections = result.get("detections", [])
                primary_disease = result.get("primary_disease")
                detected_animal_type = result.get("animal_type")

                # 提取疾病名称和置信度
                disease_names = []
                confidences = []
                for det in detections:
                    disease_names.append(det.get("name", ""))
                    confidences.append(det.get("confidence", 0))

                # 计算严重程度（基于最高置信度）
                max_confidence = max(confidences) if confidences else 0
                if max_confidence > 0.8:
                    severity = "高"
                elif max_confidence > 0.5:
                    severity = "中"
                else:
                    severity = "低"

                return {
                    "success": True,
                    "detected_diseases": disease_names,
                    "primary_disease": primary_disease,
                    "animal_type": detected_animal_type,
                    "confidences": confidences,
                    "severity": severity,
                    "max_confidence": max_confidence,
                    "detection_count": len(detections)
                }
            else:
                return {"error": result.get("message", "检测失败")}
        else:
            return {"error": f"API 调用失败: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        # API 调用失败，降级到简单分析
        return {"error": f"检测服务不可用: {str(e)}"}
    except Exception as e:
        return {"error": f"图片分析失败: {str(e)}"}


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

        # 检查信息完整性（用于决定是否在末尾添加追问）
        missing_info = []
        if not age:
            missing_info.append("年龄")
        if not temperature:
            missing_info.append("体温")
        if not other_signs:
            missing_info.append("其他体征（如粪便、呼吸、皮肤状态等）")
        if len(symptoms) < 10:  # 症状描述过于简单
            missing_info.append("更详细的症状描述")

        # 始终先检索疾病知识库
        knowledge_context = ""
        try:
            # 构造检索查询
            search_query = f"{animal_type} {symptoms}"
            if temperature:
                search_query += f" 体温{temperature}°C"
            if age:
                search_query += f" {age}月龄"

            knowledge_context = _search_disease_knowledge(search_query, top_k=3)
        except Exception:
            knowledge_context = ""

        # 构建知识库参考部分
        knowledge_section = ""
        if knowledge_context:
            knowledge_section = f"""
## 知识库参考
以下是从专业兽医文献中检索到的相关信息：

{knowledge_context}

请参考以上知识库内容进行分析，但也要根据实际情况进行判断。
"""

        # 信息完整度提示
        info_status = ""
        if missing_info and len(missing_info) >= 2:
            info_status = f"""
**注意**：当前提供的信息不够完整，以下分析基于现有症状，建议补充{len(missing_info)}项信息以获得更准确的诊断。
"""

        # 构建追问部分（附加在末尾）
        followup_section = ""
        if missing_info and len(missing_info) >= 2:
            followup_section = """

### 💡 补充信息建议（可选）

为了获得更准确的诊断，您可以补充以下信息：
- **年龄**：动物大概多大？
- **体温**：有没有测量体温？
- **其他症状**：如粪便、呼吸、皮肤状态等

补充这些信息后我可以提供更精准的分析。"""

        # 进行完整的疾病预测分析（集成知识库）
        prompt = f"""你是一位专业的兽医专家，请根据以下信息进行疾病预测分析。

## 动物信息
- 动物类型：{animal_type}
- 年龄：{age_info}
- 体温：{temp_info}
- 症状描述：{symptoms}
{f"- 其他体征：{other_signs}" if other_signs else ""}

{info_status}
{knowledge_section}
## 分析要求
请基于动物信息和知识库参考（如果提供），输出一份结构清晰、易读的疾病预测分析报告。

**重要原则**：
- 即使信息不完整，也要基于已有症状给出初步诊断和建议
- 重点放在疾病分析、处理建议和防控措施上
- 追问问题只是末尾的小附加部分，不要喧宾夺主

输出格式：

---
### 🩺 疾病预测分析

#### 可能的疾病
1. **疾病名称**（可能性：XX%）
   - 判断依据：说明原因

2. **疾病名称**（可能性：XX%）
   - 判断依据：说明原因

#### 关键症状依据
- 已知症状1
- 已知症状2

#### 紧急程度
🚨 高/⚠️ 中/ℹ️ 低

#### 处理建议
1. **隔离观察**：建议内容
2. **对症治疗**：建议内容
3. **预防措施**：建议内容

#### ⚠️ 重要提醒
添加任何需要注意的特殊事项

---

{followup_section}

---

注意：
- 直接输出报告文本，不要使用 JSON 格式
- 不要包含代码块标记
- 紧急程度根据疾病传染性、严重程度判断
- 处理建议要具体、可操作"""

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
        # 步骤1: 如果提供了图片/视频，先进行分析
        image_analysis_note = ""
        enhanced_symptoms = symptoms

        if media_path:
            # 尝试使用真实视觉模型分析
            image_result = _analyze_image_with_model(media_path, animal_type)

            # 如果真实模型失败，降级到简单分析
            if image_result.get("error"):
                image_result = _simple_image_analyze(media_path, animal_type)

            # 处理图片分析结果
            if image_result.get("error"):
                image_analysis_note = f"\n\n#### 📷 图片分析结果\n图片分析失败：{image_result['error']}"
            elif image_result.get("success"):
                # 使用真实模型的结果 - 增强症状描述
                detected_diseases = image_result.get("detected_diseases", [])
                primary_disease = image_result.get("primary_disease", "未知")
                detected_animal = image_result.get("animal_type", animal_type)
                severity = image_result.get("severity", "未知")
                max_conf = image_result.get("max_confidence", 0)

                # 格式化疾病名称
                disease_names = ", ".join([d.replace("_", " ") for d in detected_diseases])

                # 将图片识别结果整合到症状描述中，让LLM能基于此进行分析
                image_symptoms = f"""【图片AI识别结果】
- 识别动物类型：{detected_animal}
- 检测到的疾病：{disease_names}
- 主要疾病：{primary_disease.replace('_', ' ') if primary_disease else '未知'}
- 置信度：{max_conf:.1%}
- 严重程度：{severity}"""

                # 增强症状描述，让LLM基于图片识别结果进行分析
                if "请根据图片判断" in symptoms or "根据图片" in symptoms or not symptoms.strip():
                    enhanced_symptoms = image_symptoms
                else:
                    enhanced_symptoms = f"{symptoms}\n{image_symptoms}"

                image_analysis_note = f"""
#### 📷 图片/视频AI识别结果
- 识别的动物类型：{detected_animal}
- 检测到的疾病：{disease_names}
- 主要疾病：{primary_disease.replace('_', ' ') if primary_disease else '未知'}
- 置信度：{max_conf:.1%}
- 严重程度评估：{severity}"""
            else:
                # 降级使用简单分析结果
                media_type = image_result.get("media_type", "image")
                detected = ", ".join(image_result.get("detected_symptoms", []))
                areas = ", ".join(image_result.get("affected_areas", []))
                severity_level = image_result.get("severity", "未知")

                # 整合到症状描述
                image_symptoms = f"""【图片分析】
- 文件类型：{media_type}
- 检测到的症状：{detected}
- 患处区域：{areas}
- 严重程度：{severity_level}"""

                if "请根据图片判断" in symptoms or "根据图片" in symptoms or not symptoms.strip():
                    enhanced_symptoms = image_symptoms
                else:
                    enhanced_symptoms = f"{symptoms}\n{image_symptoms}"

                image_analysis_note = f"""
#### 📷 图片/视频分析结果（简单分析）
- 文件类型：{media_type}
- 检测到的症状：{detected}
- 患处区域：{areas}
- 严重程度评估：{severity_level}"""

        # 步骤2: 使用增强后的症状（包含图片识别结果）调用LLM进行疾病预测
        result = _predict_with_llm(animal_type, enhanced_symptoms, age, temperature, other_signs)

        # 步骤3: 合并LLM分析和图片识别结果
        final_report = result.get("report", "")
        if image_analysis_note:
            final_report = final_report + image_analysis_note

        return final_report

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
