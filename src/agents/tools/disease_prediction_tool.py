"""疾病预测工具：为可能患病的畜禽提供疾病预测。

收集动物的基本信息、症状描述及患处图片/视频，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行可靠的医疗建议或就医指南以及预测补充。

集成 RAG 知识库检索，基于专业兽医文献提供更准确的疾病预测。

支持多模态和非多模态模型：
- 多模态模型：自动从消息历史中提取 base64 图片
- 非多模态模型：自动从消息历史中提取图片路径
"""
import os
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

import requests
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from ...utils import ModelManager
from ...rag.config import get_embeddings_cached
from ...config import AVAILABLE_MODELS
from .detection_utils import (
    encode_image_to_base64,
    extract_image_from_messages,
)


def _is_model_multimodal(model_id: str) -> bool:
    """判断指定模型是否支持多模态

    通过 model_name 匹配，因为 AVAILABLE_MODELS 的 key 是简称
    """
    for config in AVAILABLE_MODELS.values():
        if config.get("model_name") == model_id:
            return config.get("is_multimodal", False)
    return False

logger = logging.getLogger(__name__)


# ==================== 常量配置 ====================

DISEASE_DETECTION_API_URL = os.getenv(
    "DISEASE_DETECTION_API_URL",
    "http://detection-service:8001/detection/disease/detect"
)
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov'}
SUPPORTED_MEDIA_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS


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


# ==================== 图片识别 ====================

def _analyze_image_with_model(image_source: str | dict, animal_type: str) -> dict:
    """使用真实视觉模型分析患处图片/视频

    调用疾病检测服务 API 进行图片识别。
    支持两种输入格式：
    - str: 图片文件路径
    - dict: {"base64": str, "mime_type": str} 多模态格式

    Args:
        image_source: 图片路径或 base64 数据字典
        animal_type: 动物类型

    Returns:
        识别结果字典，包含：
        - success: 是否成功
        - detected_diseases: 检测到的疾病列表
        - primary_disease: 主要疾病
        - animal_type: 识别的动物类型
        - severity: 严重程度
        - error: 错误信息（失败时）
    """
    image_base64 = None

    # 处理不同输入格式
    if isinstance(image_source, dict):
        # 多模态格式（直接提供 base64）
        image_base64 = image_source.get("base64")
        if not image_base64:
            return {"error": "未提供有效的图片数据"}
    else:
        # 路径格式（需要读取文件并编码）
        media_path = image_source
        if not os.path.exists(media_path):
            return {"error": "文件不存在"}

        ext = os.path.splitext(media_path)[1].lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            return {"error": f"不支持的文件格式: {ext}"}

        try:
            image_base64 = encode_image_to_base64(media_path)
        except Exception as e:
            return {"error": f"读取图片失败: {str(e)}"}

    try:
        # 调用检测服务 API
        response = requests.post(
            DISEASE_DETECTION_API_URL,
            json={"image_base64": image_base64},
            timeout=10
        )

        if response.status_code != 200:
            return {"error": f"API 调用失败: {response.status_code}"}

        result = response.json()
        if not result.get("success"):
            return {"error": result.get("message", "检测失败")}

        # 解析检测结果
        detections = result.get("detections", [])
        confidences = [det.get("confidence", 0) for det in detections]
        disease_names = [det.get("name", "") for det in detections]
        max_confidence = max(confidences) if confidences else 0

        # 计算严重程度（基于最高置信度）
        if max_confidence > 0.8:
            severity = "高"
        elif max_confidence > 0.5:
            severity = "中"
        else:
            severity = "低"

        return {
            "success": True,
            "detected_diseases": disease_names,
            "primary_disease": result.get("primary_disease"),
            "animal_type": result.get("animal_type"),
            "confidences": confidences,
            "severity": severity,
            "max_confidence": max_confidence,
            "detection_count": len(detections)
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"检测服务不可用: {str(e)}"}
    except Exception as e:
        return {"error": f"图片分析失败: {str(e)}"}


# ==================== 辅助函数 ====================

def _format_disease_name(name: str) -> str:
    """格式化疾病名称（将下划线替换为空格）"""
    return name.replace("_", " ") if name else "未知"


# ==================== LLM 疾病预测 ====================

def _predict_with_llm(
    animal_type: str,
    symptoms: str,
    age: Optional[int] = None,
    temperature: Optional[float] = None,
    other_signs: Optional[str] = None,
    image_source: Optional[str | dict] = None,
    detection_result: Optional[dict] = None
) -> dict:
    """使用 LLM 进行疾病预测

    通过构造专业的兽医诊断提示词，让 LLM 分析症状并返回格式化的报告。
    支持多模态输入：图片（base64）+ 检测结果 + 症状描述。

    Args:
        animal_type: 动物类型
        symptoms: 症状描述
        age: 动物年龄（月龄）
        temperature: 体温（摄氏度）
        other_signs: 其他体征描述
        image_source: 图片来源（路径或 base64 字典）
        detection_result: 检测 API 的结果

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
        if len(symptoms) < 10:
            missing_info.append("更详细的症状描述")

        # 检索疾病知识库
        knowledge_context = ""
        try:
            search_query = f"{animal_type} {symptoms}"
            if temperature:
                search_query += f" 体温{temperature}°C"
            if age:
                search_query += f" {age}月龄"
            knowledge_context = _search_disease_knowledge(search_query, top_k=3)
        except Exception:
            pass

        # 构建知识库参考部分
        knowledge_section = ""
        if knowledge_context:
            knowledge_section = f"""
## 知识库参考
以下是从专业兽医文献中检索到的相关信息：

{knowledge_context}

请参考以上知识库内容进行分析，但也要根据实际情况进行判断。
"""

        # 构建检测结果参考部分
        detection_section = ""
        if detection_result and detection_result.get("success"):
            detected_diseases = detection_result.get("detected_diseases", [])
            primary_disease = detection_result.get("primary_disease", "")
            detected_animal = detection_result.get("animal_type", "")
            severity = detection_result.get("severity", "")
            max_conf = detection_result.get("max_confidence", 0)

            disease_names = ", ".join([_format_disease_name(d) for d in detected_diseases])

            detection_section = f"""
## 检测 API 参考结果
专业疾病检测模型的识别结果（供参考）：
- 识别动物类型：{detected_animal}
- 检测到的疾病：{disease_names}
- 主要疾病：{_format_disease_name(primary_disease)}
- 置信度：{max_conf:.1%}
- 严重程度：{severity}

**注意**：此结果由专门训练的检测模型提供，请将其作为重要参考，但也要结合图片观察和症状描述进行综合判断。
"""

        # 多模态模型专用提示词
        multimodal_instruction = ""
        model_id = model_manager.config.get("default_model", "")
        if image_source and _is_model_multimodal(model_id):
            multimodal_instruction = """
## 图片分析要求
你能够直接看到用户上传的患处图片，请仔细观察：
- 病灶的形态、颜色、大小、分布特征
- 是否有红肿、溃疡、分泌物、结痂等表现
- 病变区域与正常组织的对比
- 结合检测API结果和症状描述，进行综合分析

**重要**：请充分利用你的视觉能力，不要仅依赖文本描述。
"""

        # 信息完整度提示
        info_status = ""
        if missing_info and len(missing_info) >= 2:
            info_status = f"""
**注意**：当前提供的信息不够完整，以下分析基于现有症状，建议补充{len(missing_info)}项信息以获得更准确的诊断。
"""

        # 构建追问部分
        followup_section = ""
        if missing_info and len(missing_info) >= 2:
            followup_section = """

### 💡 补充信息建议（可选）

为了获得更准确的诊断，您可以补充以下信息：
- **年龄**：动物大概多大？
- **体温**：有没有测量体温？
- **其他症状**：如粪便、呼吸、皮肤状态等

补充这些信息后我可以提供更精准的分析。"""

        # 构建完整提示词
        prompt = f"""你是一位专业的兽医专家，请根据以下信息进行疾病预测分析。

## 动物信息
- 动物类型：{animal_type}
- 年龄：{age_info}
- 体温：{temp_info}
- 症状描述：{symptoms}
{f"- 其他体征：{other_signs}" if other_signs else ""}

{info_status}
{detection_section}
{knowledge_section}
{multimodal_instruction}
## 分析要求
请基于以上所有信息（动物信息、症状描述、检测结果、知识库参考、图片观察），输出一份结构清晰、易读的疾病预测分析报告。

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
        # 判断是否需要构建多模态消息
        model_id = model_manager.config.get("default_model", "")
        supports_multimodal = image_source and _is_model_multimodal(model_id)

        if supports_multimodal:
            # 构建多模态消息（图片 + 文本提示词）
            content_blocks = [{"type": "text", "text": prompt}]

            # 处理图片来源
            if isinstance(image_source, dict):
                # base64 格式（多模态消息中已提取）
                mime_type = image_source.get("mime_type", "image/jpeg")
                base64_data = image_source.get("base64", "")
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                })
                logger.info("使用多模态消息中的 base64 图片进行 LLM 分析")
            elif isinstance(image_source, str):
                # 路径格式，需要读取并编码
                try:
                    image_base64 = encode_image_to_base64(image_source)
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(image_source)
                    if mime_type is None:
                        mime_type = "image/jpeg"
                    content_blocks.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
                    })
                    logger.info(f"使用图片路径进行 LLM 分析: {image_source}")
                except Exception as e:
                    logger.error(f"图片编码失败: {e}")
                    # 降级为纯文本
                    supports_multimodal = False
                    content_blocks[0]["text"] += f"\n\n[图片读取失败，仅基于症状和检测结果分析]"

            if supports_multimodal:
                message = HumanMessage(content=content_blocks)
            else:
                message = HumanMessage(content=content_blocks[0]["text"])
        else:
            # 纯文本消息
            message = HumanMessage(content=prompt)

        response = model.invoke([message])
        report_text = response.content.strip().replace("```json", "").replace("```", "").strip()

        return {
            "success": True,
            "report": report_text,
            "model_used": "llm",
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": {
                "animal_type": animal_type,
                "symptoms": symptoms,
                "age": age,
                "temperature": temperature,
                "other_signs": other_signs
            }
        }

    except Exception as e:
        # 降级响应
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


# ==================== 主工具 ====================

@tool
def disease_prediction_tool(
    runtime: ToolRuntime,
    animal_type: str,
    symptoms: str,
    age: Optional[int] = None,
    temperature: Optional[float] = None,
    other_signs: Optional[str] = None,
    media_path: Optional[str] = None
) -> str:
    """预测畜禽可能的疾病。

    根据动物类型、症状描述、患处图片/视频等信息，使用 AI 分析预测可能的疾病。
    自动从对话历史中提取用户上传的图片，无需手动传递图片路径。
    支持多模态模型（base64 图片）和非多模态模型（图片路径）。
    注意：仅供参考，不能替代专业兽医诊断。

    Args:
        runtime: LangGraph 工具运行时，用于访问消息历史
        animal_type: 动物类型，如 牛、猪、鸡、鸭、羊 等
        symptoms: 症状描述，如 发热、咳嗽、精神萎靡、不食等
        age: 动物年龄（月龄），可选
        temperature: 体温（摄氏度），可选
        other_signs: 其他体征描述，可选
        media_path: 患处图片或视频路径（可选，如未提供则自动从消息历史提取）

    Returns:
        格式化的疾病预测分析报告
    """
    try:
        # 步骤1: 确定图片来源（优先使用自动提取，备用手动路径）
        image_source = None

        if media_path:
            # 用户手动指定路径
            image_source = media_path
        else:
            # 自动从消息历史提取图片
            messages = runtime.state["messages"]
            image_info = extract_image_from_messages(messages)

            if image_info:
                if "base64" in image_info:
                    # 多模态格式（base64 数据）
                    image_source = image_info
                    logger.info("使用多模态消息中的 base64 图片进行疾病预测")
                elif "path" in image_info:
                    # 路径格式
                    image_source = image_info["path"]
                    logger.info(f"使用图片路径进行疾病预测: {image_info['path']}")

        # 步骤2: 如果有图片，先进行检测分析
        detection_result = None
        image_analysis_note = ""

        if image_source:
            detection_result = _analyze_image_with_model(image_source, animal_type)

            if detection_result.get("error"):
                image_analysis_note = f"\n\n#### 📷 图片分析结果\n图片分析失败：{detection_result['error']}"

        # 步骤3: 调用 LLM 进行综合疾病预测
        # 现在传入原始症状（不做拼接），让 LLM 综合图片+检测结果+症状进行分析
        result = _predict_with_llm(
            animal_type=animal_type,
            symptoms=symptoms,
            age=age,
            temperature=temperature,
            other_signs=other_signs,
            image_source=image_source,
            detection_result=detection_result
        )

        # 步骤4: 合并 LLM 分析和图片识别结果
        final_report = result.get("report", "")

        # 如果检测失败，在报告中添加错误提示
        if image_analysis_note:
            final_report = final_report + image_analysis_note

        return final_report

    except Exception as e:
        return f"### ⚠️ 分析失败\n\n疾病预测工具遇到错误：{str(e)}\n\n请稍后重试或直接咨询专业兽医。"


__all__ = ["disease_prediction_tool"]
disease_prediction_tool.tags = ["disease", "prediction", "veterinary"]
