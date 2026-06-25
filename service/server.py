"""
RuralBrain FastAPI 服务器
提供图像检测对话接口和规划咨询接口
"""
import sys
import json
import uuid
import logging
import re
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from service.settings import (
    ALLOWED_ORIGINS,
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
)
from service.schemas import ChatRequest, UploadResponse
from src.agents.middleware.dynamic_tool_middleware import set_kb_switch_state, set_web_search_switch_state
from src.agents.context import AgentContext
from src.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID
from src.utils.multimodal_message import build_multimodal_message
from src.rag.service.schemas.chat import KnowledgeUpdateRequest, KnowledgeUpdateResponse
from src.rag.service.api.routes import _update_knowledge_base_impl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SSE 响应头常量
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}

SCRATCHPAD_SECTION_PATTERN = re.compile(
    r"(?:^|\n)(?:#{1,6}\s*)?(SESSION INTENT|SUMMARY|ARTIFACTS|NEXT STEPS|PLAN|WORKLOG|INTERNAL NOTES|REASONING)\s*\n(?:.*?)(?=(?:\n(?:#{1,6}\s*)?(?:SESSION INTENT|SUMMARY|ARTIFACTS|NEXT STEPS|PLAN|WORKLOG|INTERNAL NOTES|REASONING)\s*\n)|\Z)",
    re.IGNORECASE | re.DOTALL,
)

INLINE_SCRATCHPAD_PATTERNS = [
    re.compile(r"<(?:think|thinking|analysis|reasoning)>[\s\S]*?</(?:think|thinking|analysis|reasoning)>", re.IGNORECASE),
    re.compile(r"```(?:thinking|analysis|reasoning|scratchpad)?\s*[\s\S]*?```", re.IGNORECASE),
    re.compile(r"(?:^|\n)\s*(?:思考过程|推理过程|内部分析|工作思路|分析过程)[:：].*?(?=\n\n|\Z)", re.IGNORECASE | re.DOTALL),
]


FINAL_ANSWER_CUE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^(?:最终(?:建议|回答|结论)|结论|建议如下|总结如下|综合建议|可以按以下|给您的建议)",
        r"^(?:检测结果|识别结果|分析结果|查询结果|定价建议|防治建议|处理建议)[:：]",
        r"^(?:根据(?:知识库|检测结果|您的情况)|结合(?:政策|案例|检测结果))",
    ]
]


def strip_internal_scratchpad_content(text: str) -> str:
    """移除误流出给前端的内部工作态文本块。"""
    if not text:
        return ""

    cleaned = SCRATCHPAD_SECTION_PATTERN.sub("\n", text)
    for pattern in INLINE_SCRATCHPAD_PATTERNS:
        cleaned = pattern.sub("\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip("\n")


# ==================== 检测工具结构化数据解析 ====================

def parse_farm_inspection_output(tool_output: str) -> dict | None:
    """解析巡检工具的输出，提取结构化数据

    Args:
        tool_output: 工具返回的 JSON 字符串

    Returns:
        结构化的巡检数据，解析失败返回 None
    """
    try:
        import re

        # 尝试解析 JSON
        data = json.loads(tool_output)

        # 验证基本结构
        if not isinstance(data, dict):
            return None

        # 提取巡检类型
        inspection_type = data.get("inspection_type", "")

        # 构建返回数据
        result = {
            "inspection_type": inspection_type,
            "inspection_time": data.get("inspection_time", ""),
            "farm_id": data.get("farm_id", ""),
        }

        # 智能巡检模式
        if inspection_type in ["智能巡检", "多图智能巡检"]:
            result["media_type"] = data.get("media_type", "")
            result["media_type_name"] = data.get("media_type_name", "")
            result["image_count"] = data.get("image_count", 0)

            # 场景分类
            scene_classification = data.get("scene_classification", {})
            if scene_classification:
                result["scene_classification"] = {
                    "primary_scene": scene_classification.get("primary_scene", ""),
                    "primary_scene_type": scene_classification.get("primary_scene_type", ""),
                    "all_scenes": scene_classification.get("all_scenes", [])
                }

            # 推荐工具
            recommended_tools = data.get("recommended_tools", [])
            if recommended_tools:
                result["recommended_tools"] = recommended_tools

            # 多模态分析报告
            multimodal_analysis = data.get("multimodal_analysis")
            if multimodal_analysis and multimodal_analysis.get("report"):
                result["multimodal_analysis"] = {
                    "enabled": multimodal_analysis.get("enabled", False),
                    "report": multimodal_analysis.get("report", "")
                }

            # 建议行动（如果没有多模态报告）
            if not multimodal_analysis and data.get("suggested_actions"):
                result["suggested_actions"] = data.get("suggested_actions", [])

        # 传感器巡检模式
        elif inspection_type == "传感器巡检":
            sensor_data = data.get("data", {})
            if sensor_data:
                result["sensor_data"] = sensor_data

        return result

    except json.JSONDecodeError as e:
        logger.warning(f"解析巡检工具输出 JSON 失败: {e}")
        return None
    except Exception as e:
        logger.warning(f"解析巡检工具输出失败: {e}")
        return None


def parse_detection_tool_output(tool_output: str, tool_name: str) -> dict | None:
    """解析检测工具的输出，提取结构化数据

    Args:
        tool_output: 工具返回的文本内容
        tool_name: 工具名称

    Returns:
        结构化的检测数据，解析失败返回 None
    """
    try:
        import re

        # 优先尝试解析增强的 JSON 输出格式
        # 增强格式：{"text": "...", "data": {...}}
        if tool_output.strip().startswith("{"):
            try:
                parsed_json = json.loads(tool_output)
                if "data" in parsed_json:
                    data = parsed_json["data"]
                    # 提取详细检测数据
                    result = {
                        "detections": data.get("detections", []),
                        "totalCount": data.get("totalCount", 0),
                        "severity": data.get("severity", "none"),
                        "summary": data.get("summary", ""),
                        "suggestions": data.get("suggestions"),
                        # 新增：详细检测数据（bbox、confidence）
                        "detailed_detections": data.get("detailed_detections", []),
                        "image_info": data.get("image_info", {}),
                        "avg_confidence": data.get("avg_confidence", 0.0),
                    }
                    logger.info(f"{tool_name} JSON 格式解析成功: {len(result['detailed_detections'])} 个详细检测")
                    return result
            except json.JSONDecodeError:
                pass  # 不是 JSON，继续使用文本解析

        # 清理 Markdown 格式标记（**粗体**）
        def clean_markdown(text: str) -> str:
            """清理文本中的 Markdown 标记"""
            # 移除 **粗体** 标记
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            # 移除 *斜体* 标记（包括 *斜体内容*）
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            # 移除 `代码` 标记
            text = re.sub(r'`(.+?)`', r'\1', text)
            # 移除括号中的学名如 （*Spodoptera exigua*）
            text = re.sub(r'\([^*]*\*[^)]*\)', '', text)
            return text.strip()

        # 多种格式的检测结果解析
        detections = []
        total_count = 0
        summary_text = ""

        # 格式1: "检测结果: 瓜实蝇(3只)、斜纹夜蛾(1只)"
        match1 = re.search(r'检测结果[:：]\s*([^\n]+)', tool_output)
        if match1:
            result_str = match1.group(1)
            # 匹配 "名称(数量只)" 或 "名称(数量粒)" 或 "名称(数量头)"
            for det_match in re.finditer(r'([^\(、]+?)\((\d+)[只粒头个]\)', result_str):
                name = clean_markdown(det_match.group(1).strip())
                count = int(det_match.group(2))
                if name and count >= 0:
                    detections.append({"name": name, "count": count})
                    total_count += count

        # 格式2: "**检测对象**：甜菜夜蛾（*Spodoptera exigua*）。**数量**：1头"
        if not detections:
            object_match = re.search(r'\*{0,2}检测对象\*{0,2}[:：]\s*([^\n。]+?)(?:\*\*数量|数量|\.|$)', tool_output, re.IGNORECASE)
            count_match = re.search(r'\*{0,2}数量\*{0,2}[:：]\s*(\d+)', tool_output, re.IGNORECASE)

            if object_match:
                name = clean_markdown(object_match.group(1).strip())
                count = int(count_match.group(1)) if count_match else 1
                if name:
                    detections.append({"name": name, "count": count})
                    total_count += count

        # 格式3: "检测到 X 个Y" 或 "发现 Y: X个"
        if not detections:
            # 匹配 "检测到3只瓜实蝇"
            for det_match in re.finditer(r'(?:检测到|发现|识别出)\s*(\d+)\s*[只粒头个]*(?:的)?\s*([^\n，。、]+?)(?:[,，。、]|\s|$)', tool_output):
                count = int(det_match.group(1))
                name = clean_markdown(det_match.group(2).strip())
                if name and count >= 0:
                    detections.append({"name": name, "count": count})
                    total_count += count

        # 格式4: "瓜实蝇: 3只" 或 "瓜实蝇 - 3只"
        if not detections:
            for det_match in re.finditer(r'([^\n:：-]+?)[:：\s*-]\s*(\d+)\s*[只粒头个]', tool_output):
                name = clean_markdown(det_match.group(1).strip())
                count = int(det_match.group(2))
                if name and count >= 0 and len(name) < 50:  # 名称长度限制
                    # 排除非检测内容的行
                    if not any(kw in name for kw in ["成本", "价格", "品质", "市场", "建议", "数据"]):
                        detections.append({"name": name, "count": count})
                        total_count += count

        # 计算严重程度
        if total_count == 0:
            severity = "none"
        elif total_count <= 3:
            severity = "low"
        elif total_count <= 10:
            severity = "medium"
        else:
            severity = "high"

        # 提取建议部分
        suggestions = []
        suggestion_sections = ["防治建议", "处理建议", "建议措施", "应对措施", "建议"]
        for section_name in suggestion_sections:
            if section_name in tool_output:
                section_match = re.search(
                    rf'{section_name}[:：]\s*\n((?:[^#\n].*\n?){{1,10}})',
                    tool_output,
                    re.IGNORECASE
                )
                if section_match:
                    section_text = section_match.group(1)
                    for line in section_text.split("\n"):
                        line = clean_markdown(line.strip())
                        if line and not line.startswith("#") and 10 < len(line) < 150:
                            if line.startswith(("-", "•", "*", "·")):
                                suggestions.append(line.lstrip("-•*· ").strip())
                            elif re.match(r'^\d+[.、)]', line):
                                suggestions.append(re.sub(r'^\d+[.、)]\s*', '', line))
                            elif not any(kw in line for kw in ["检测", "结果", "数量", "形态", "注意"]):
                                suggestions.append(line)
                    if suggestions:
                        break

        # 提取描述/摘要
        summary_parts = []
        # 优先使用专门的摘要或结论
        summary_patterns = [
            r'(?:摘要|结论|综合判断)[:：]\s*([^\n]+)',
            r'(?:当前)?严重程度[:：]\s*([^\n]+)',
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, tool_output)
            if match:
                summary_parts.append(clean_markdown(match.group(1).strip()))
                break

        # 如果没有找到专门的摘要，提取第一段有效内容
        if not summary_parts:
            for line in tool_output.split("\n")[:5]:
                cleaned = clean_markdown(line.strip())
                if cleaned and not cleaned.startswith("#") and 15 < len(cleaned) < 200:
                    # 排除标题行
                    if not any(kw in cleaned for kw in ["检测结果", "检测对象", "数量统计", "形态辨析"]):
                        summary_parts.append(cleaned)
                        if len(summary_parts) >= 2:
                            break

        # 构建返回数据
        if detections or total_count > 0:
            return {
                "detections": detections,
                "totalCount": total_count,
                "severity": severity,
                "summary": " ".join(summary_parts) if summary_parts else f"检测到 {total_count} 个目标",
                "suggestions": suggestions[:5] if suggestions else None,
            }
        elif "未检测到" in tool_output or "未发现" in tool_output:
            return {
                "detections": [],
                "totalCount": 0,
                "severity": "none",
                "summary": "未检测到相关目标",
                "suggestions": ["继续保持田间卫生", "定期巡查监测"][:2]
            }

        return None
    except Exception as e:
        logger.warning(f"解析检测工具输出失败: {e}")
        return None


def parse_disease_prediction_output(tool_output: str) -> dict | None:
    """解析疾病预测工具的输出，提取结构化数据

    使用正则表达式从人类可读报告中提取疾病预测信息。

    Args:
        tool_output: 工具返回的文本内容

    Returns:
        结构化的疾病预测数据，解析失败返回 None
    """
    try:
        import re

        # 如果不是字符串，转换为字符串
        if not isinstance(tool_output, str):
            tool_output = str(tool_output)

        # ========== 优先尝试解析新版本的 JSON 格式 ==========
        stripped = tool_output.strip()
        if stripped.startswith('{'):
            try:
                parsed = json.loads(stripped)

                # 检查是否包含数据字段
                if "data" in parsed:
                    data = parsed["data"]
                    # 验证数据结构
                    if "diseases" in data and isinstance(data["diseases"], list):
                        logger.info(f"疾病预测 JSON 解析成功: {len(data['diseases'])} 个疾病")
                        return {
                            "diseases": data["diseases"],
                            "urgency": data.get("urgency", "medium"),
                            "symptoms": data.get("symptoms", []),
                            "suggestions": data.get("suggestions", {}),
                            "reminder": data.get("reminder")
                        }
                elif "diseases" in parsed and isinstance(parsed["diseases"], list):
                    # 直接包含 diseases 字段
                    logger.info(f"疾病预测 JSON 解析成功: {len(parsed['diseases'])} 个疾病")
                    return {
                        "diseases": parsed["diseases"],
                        "urgency": parsed.get("urgency", "medium"),
                        "symptoms": parsed.get("symptoms", []),
                        "suggestions": parsed.get("suggestions", {}),
                        "reminder": parsed.get("reminder")
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"疾病预测 JSON 解析失败: {e}, 降级到文本解析")

        # ========== 降级：使用正则表达式从人类可读报告中提取结构化数据 ==========

        # ========== 使用正则表达式从人类可读报告中提取结构化数据 ==========

        # 清理 Markdown 格式标记
        def clean_markdown(text: str) -> str:
            """清理文本中的 Markdown 标记"""
            # 清理 **粗体**
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            # 清理 *斜体*
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            # 清理 `代码`
            text = re.sub(r'`([^`]+)`', r'\1', text)
            return text.strip()

        # 解析可能的疾病（多种格式支持）
        diseases = []

        # 添加调试日志
        logger.info(f"疾病预测解析 - 输出片段: {tool_output[:800] if tool_output else 'None'}...")

        # 格式1: "**疾病名称**（可能性：XX%）" - 修复：精确匹配 **...** 格式
        pattern1 = r'\*\*([^**]+)\*\*\s*[（(]\s*可能性\s*[：:]?\s*(\d+)\s*%?\s*[）)]'
        for match in re.finditer(pattern1, tool_output):
            name = clean_markdown(match.group(1).strip())
            probability = int(match.group(2))
            logger.info(f"匹配到疾病候选: '{name}' ({probability}%)")

            # 更严格的过滤条件
            invalid_keywords = ["可能性", "依据", "分析", "病变", "发展阶段", "处于", "不同", "可能", "提示", "建议", "需要", "考虑"]
            is_valid = (
                len(name) >= 2 and
                len(name) < 30 and
                not any(kw in name for kw in invalid_keywords) and
                not name.endswith(("处于", "可能", "不同", "阶段")) and
                # 疾病名称应该包含医学相关词汇
                any(medical_kw in name for medical_kw in ["炎", "病", "症", "感染", "中毒", "综合征", "损伤", "障碍"])
            )

            if is_valid and name not in [d["name"] for d in diseases]:
                diseases.append({"name": name, "probability": probability, "reason": ""})

        # 格式2: "1. **疾病名称**（可能性：XX%）" 或列表格式
        if not diseases:
            pattern2 = r'(?:^\d+[\.\)]\s*|[-*])\s*\*\*([^**]+)\*\*\s*[（(]\s*(?:可能性)?\s*(\d+)\s*%?\s*[）)]'
            for match in re.finditer(pattern2, tool_output, re.MULTILINE):
                name = clean_markdown(match.group(1).strip())
                probability = int(match.group(2))
                if len(name) >= 2 and len(name) < 30 and name not in [d["name"] for d in diseases]:
                    diseases.append({"name": name, "probability": probability, "reason": ""})

        # 格式3: "可能是X疾病" 或 "疑似X"
        if not diseases:
            pattern3 = r'(?:可能是|疑似|怀疑为|考虑|提示)\s*\*{0,2}([^*，。、]+?)(?:病|综合症|征)?\*{0,2}(?:[，。、]|$)'
            for match in re.finditer(pattern3, tool_output):
                name = clean_markdown(match.group(1).strip())
                # 如果没有以"病"结尾，添加它
                if not name.endswith(("病", "症", "炎", "感染")):
                    name = name + "病"
                if len(name) >= 2 and len(name) < 30 and name not in [d["name"] for d in diseases]:
                    diseases.append({"name": name, "probability": 60, "reason": ""})

        # 为每个疾病查找判断依据
        for disease in diseases:
            # 尝试多种方式找到判断依据
            reason_patterns = [
                rf'{re.escape(disease["name"])}[^。\n]*?判断依据[：:]\s*([^。\n]+)',
                rf'[:#]\s*{re.escape(disease["name"])}.*?[:：]\s*([^。\n]+?)(?=\n|$|\d+[\.)])',
            ]
            for pattern in reason_patterns:
                match = re.search(pattern, tool_output, re.DOTALL)
                if match:
                    disease["reason"] = clean_markdown(match.group(1).strip())[:100]
                    break

        # 解析紧急程度（多种格式）
        urgency = "medium"
        urgency_patterns = [
            r"紧急程度\s*[:：]\s*(🚨\s*高|⚠️\s*中|ℹ️\s*低|高|中|低)",
            r"(?:紧急|严重)(?:程度|性)?[：:]\s*(高|中|低)",
            r"🚨|⚠️|ℹ️",  # 仅表情符号
        ]
        for pattern in urgency_patterns:
            match = re.search(pattern, tool_output)
            if match:
                urgency_text = match.group(1) if match.lastindex and match.group(1) else ""
                if not urgency_text and match.group(0):
                    urgency_text = match.group(0)
                urgency_text = urgency_text.replace("🚨", "").replace("⚠️", "").replace("ℹ️", "").strip()
                if "高" in urgency_text:
                    urgency = "high"
                elif "低" in urgency_text:
                    urgency = "low"
                else:
                    urgency = "medium"
                break

        # 解析关键症状
        symptoms = []
        symptoms_patterns = [
            r"(?:关键)?症状依据?[:：]\s*\n((?:[^#\n].*\n?){1,15})",
            r"(?:主要)?症状[:：]\s*([^\n]+)",
            r"(?:临床表现|临表)[：:]\s*([^\n]+)",
        ]
        for pattern in symptoms_patterns:
            match = re.search(pattern, tool_output, re.DOTALL)
            if match:
                section_text = match.group(1) if match.lastindex >= 1 else match.group(0)
                for line in section_text.split("\n"):
                    line = clean_markdown(line.strip())
                    if line and not line.startswith("#") and len(line) < 80:
                        if line.startswith(("-", "•", "*", "·")):
                            symptoms.append(clean_markdown(line.lstrip("-•*· ").strip())[:50])
                        elif re.match(r'^\d+[\.)]', line):
                            symptoms.append(clean_markdown(re.sub(r'^\d+[\.)]\s*', '', line))[:50])
                        elif not any(kw in line for kw in ["建议", "处理", "预防", "提醒"]):
                            symptoms.append(line[:50])
                if symptoms:
                    break

        # 如果没找到专门的症状部分，尝试从整个文本中提取
        if not symptoms:
            for line in tool_output.split("\n"):
                line = clean_markdown(line.strip())
                if line and 15 < len(line) < 100:
                    if any(kw in line for kw in ["发热", "咳嗽", "精神", "食欲", "粪便", "皮肤", "肿胀"]):
                        symptoms.append(line[:50])
                        if len(symptoms) >= 5:
                            break

        # 解析处理建议
        suggestions = {}
        suggestions_section = re.search(
            r"(?:处理建议|应对措施|治疗方案|防控措施)[：:]\s*\n((?:[^#\n].*\n?){1,20})",
            tool_output,
            re.DOTALL | re.IGNORECASE
        )
        if suggestions_section:
            suggestions_text = suggestions_section.group(1)

            # 隔离观察（多种关键词）
            isolation_patterns = [
                r"(?:隔离|分开)[^。\n]{0,20}",
                r"1[\.\)]\s*[^。\n]{0,30}",
            ]
            for pattern in isolation_patterns:
                match = re.search(pattern, suggestions_text, re.IGNORECASE)
                if match:
                    suggestions["isolation"] = clean_markdown(match.group(0).strip())[:100]
                    break

            # 对症治疗
            treatment_patterns = [
                r"(?:对症治疗|治疗|用药)[：:][^。\n]{0,100}",
                r"2[\.\)]\s*[^。\n]{0,30}",
            ]
            for pattern in treatment_patterns:
                match = re.search(pattern, suggestions_text, re.IGNORECASE)
                if match:
                    suggestions["treatment"] = clean_markdown(match.group(0).strip())[:100]
                    break

            # 预防措施
            prevention_patterns = [
                r"(?:预防|防控)[^。\n]{0,100}",
                r"3[\.\)]\s*[^。\n]{0,30}",
            ]
            for pattern in prevention_patterns:
                match = re.search(pattern, suggestions_text, re.IGNORECASE)
                if match:
                    suggestions["prevention"] = clean_markdown(match.group(0).strip())[:100]
                    break

        # 解析重要提醒
        reminder = ""
        reminder_patterns = [
            r"(?:重要提醒|注意事项|注意)[：:]\s*([^\n]+)",
            r"⚠️\s*([^\n]+)",
        ]
        for pattern in reminder_patterns:
            match = re.search(pattern, tool_output, re.IGNORECASE)
            if match:
                reminder = clean_markdown(match.group(1) if match.lastindex >= 1 else match.group(0)).strip()[:150]
                break

        if diseases or symptoms:
            return {
                "diseases": diseases[:5],
                "urgency": urgency,
                "symptoms": symptoms[:8],
                "suggestions": suggestions,
                "reminder": reminder if reminder else None
            }

        return None
    except Exception as e:
        logger.warning(f"解析疾病预测输出失败: {e}")
        return None


# ==================== 工具输出清理 ====================

def clean_tool_output_json(output: str) -> str:
    """清理工具输出中的 JSON 部分，只保留人类可读的报告

    如果输出是纯JSON（用于结构化数据），则返回空字符串。

    Args:
        output: 原始工具输出文本

    Returns:
        清理后的文本（移除 JSON 代码块）
    """
    import re

    # 检查是否是纯 JSON 输出（用于结构化数据）
    stripped = output.strip()
    if stripped.startswith('{') and '"diseases"' in stripped:
        # 尝试解析为 JSON
        try:
            json.loads(stripped)
            # 是有效的 JSON，返回空字符串（不显示在聊天气泡中）
            logger.info(f"clean_tool_output_json: 检测到纯JSON输出，返回空字符串")
            return ""
        except json.JSONDecodeError:
            pass

    # 移除 ```json ... ``` 代码块（支持多行）
    cleaned = re.sub(r'```json\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*```', '', output, flags=re.DOTALL)
    if cleaned.strip() != output:
        # 成功移除了 JSON 代码块
        logger.info(f"clean_tool_output_json: 移除了JSON代码块")
        return cleaned.strip()

    # 移除独立的 JSON 对象（包含 "diseases"、"inspection_type" 等字段的）
    # 匹配从 { 开始到对应的 } 结束的完整 JSON 对象
    json_patterns = [
        r'\{[^{}]*"diseases"[^{}]*\}',  # 疾病预测 JSON
        r'\{[^{}]*"inspection_type"[^{}]*\}',  # 巡检 JSON
        r'\{[^{}]*"ai_summary"[^{}]*\}',  # 联网搜索 JSON
    ]

    for pattern in json_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)

    result = cleaned.strip()
    if result:
        logger.info(f"clean_tool_output_json: 清理后剩余内容长度: {len(result)}")
    else:
        logger.info(f"clean_tool_output_json: 清理后无剩余内容")
    return result


def clean_json_from_content(content: str) -> str:
    """从内容中清理 JSON 代码块（用于流式输出）

    专门用于清理流式传输中的 JSON 代码块，避免将其显示给用户。

    Args:
        content: 流式内容

    Returns:
        清理后的内容
    """
    import re

    # 移除 ```json 开始标记
    content = re.sub(r'```json\s*', '', content)

    # 如果检测到 JSON 代码块开始，标记直到找到结束标记
    lines = content.split('\n')
    filtered_lines = []
    in_json_block = False

    for line in lines:
        # 检查是否在 JSON 块中
        if in_json_block:
            if line.strip().startswith('```'):
                in_json_block = False
            # 跳过 JSON 块内的所有行
            continue

        # 检查 JSON 块开始
        if line.strip().startswith('```json'):
            in_json_block = True
            continue

        # 跳过独立的 JSON 对象行
        stripped = line.strip()
        if stripped.startswith('{') and '"diseases"' in stripped:
            # 这是一个 JSON 对象，检查是否在同一行内结束
            if not stripped.endswith('}'):
                # 多行 JSON，跳过后续行直到找到 }
                continue

        filtered_lines.append(line)

    return '\n'.join(filtered_lines)


# ==================== 推理过程过滤器 ====================

class ThinkingProcessFilter:
    """
    过滤 Agent 推理过程的冗余输出。

    对明显的过程性、工作态和寒暄式过渡语句直接拦截，
    尽量只保留面向用户的结论、建议和结果。
    """

    THINKING_PATTERNS = [
        r"^(让我|现在让我|接下来让我|首先让我|下面让我)",
        r"^(我来帮您|我来|我先|先来)",
        r"^(很好[！!，,]?|好的[，,]?|当然[，,]?|接下来[，,]?|现在[，,]?)",
        r"^(让我先|让我先查看|让我先尝试|先分析一下|先看一下)",
        r"^(我已经获取了|我将|我正在|我会先|我需要先)",
        r"^(思考过程|推理过程|内部分析|工作思路|分析过程)[:：]",
    ]

    def __init__(self):
        self.current_sentence = ""
        self.in_final_answer = False

    def process(self, content: str) -> tuple[str, bool]:
        """
        处理流式内容，返回（过滤后的内容，是否应发送）。
        """
        self.current_sentence += content

        if not self._is_sentence_boundary(self.current_sentence[-1:]):
            return "", False

        sentence = self.current_sentence
        self.current_sentence = ""

        cleaned_sentence = strip_internal_scratchpad_content(clean_json_from_content(sentence)).strip()
        if not cleaned_sentence:
            return "", False

        if self._looks_like_final_answer(cleaned_sentence):
            self.in_final_answer = True
            return cleaned_sentence, True

        if self._is_thinking_sentence(cleaned_sentence):
            logger.info(f"过滤推理句子: {cleaned_sentence[:80]}...")
            return "", False

        return cleaned_sentence, True

    def flush_remaining(self) -> str:
        """在流结束时刷新未闭合句子的剩余内容。"""
        remaining = self.current_sentence.strip()
        self.current_sentence = ""
        return strip_internal_scratchpad_content(clean_json_from_content(remaining)).strip()

    def _is_sentence_boundary(self, char: str) -> bool:
        """检查字符是否是句子边界"""
        return char in "。！？\n"

    def _looks_like_final_answer(self, sentence: str) -> bool:
        return any(pattern.search(sentence) for pattern in FINAL_ANSWER_CUE_PATTERNS)

    def _is_thinking_sentence(self, sentence: str) -> bool:
        """检查句子是否是推理过程句子"""
        sentence = sentence.strip()
        if any(pattern.search(sentence) for pattern in FINAL_ANSWER_CUE_PATTERNS):
            return False
        return any(re.search(pattern, sentence, re.IGNORECASE) for pattern in self.THINKING_PATTERNS)

app = FastAPI(
    title="RuralBrain API",
    description="乡村智慧大脑 - 图像检测对话服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def mount_static_dirs():
    """挂载所有静态文件目录"""
    from service.settings import DETECTION_RESULTS_DIR

    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # 挂载检测结果目录
    for detection_type in ["pest", "cow", "rice"]:
        url_path = f"/{detection_type}_results"
        dir_path = DETECTION_RESULTS_DIR / detection_type
        if dir_path.exists():
            app.mount(url_path, StaticFiles(directory=str(dir_path)), name=detection_type)


mount_static_dirs()

# --------延迟加载机制--------
# 延迟导入 agent，避免启动时加载模型，缩短启动时间
_agent = None
_agent_version = None


def get_agent():
    """延迟加载统一编排 Agent（V2 Skills 架构）"""
    global _agent, _agent_version

    if _agent is None:
        from src.agents.orchestrator_agent_v2 import agent
        _agent = agent
        _agent_version = "orchestrator_v2"
        logger.info("✓ 统一编排 Agent V2 加载完成 - Skills 架构")

    return _agent


def get_agent_version() -> str:
    """
    获取当前使用的 Agent 版本

    Returns:
        "orchestrator" 或其他版本标识
    """
    global _agent_version
    if _agent_version is None:
        # 如果 Agent 还未加载，返回默认版本
        return "orchestrator"
    return _agent_version


@app.on_event("startup")
async def startup_event():
    """启动时预加载模型和知识库"""
    logger.info("RuralBrain 服务启动中...")
    logger.info("Agent 配置: Orchestrator Agent (统一编排)")

    # 自动检查并构建疾病知识库
    await ensure_disease_knowledge_base()

    get_agent()  # 预加载 Orchestrator Agent

    logger.info("RuralBrain 服务启动完成")


async def ensure_disease_knowledge_base():
    """确保疾病知识库已构建，如果不存在则自动构建"""
    from pathlib import Path
    import time

    collection_name = "diseases_knowledge"
    persist_dir = project_root / "knowledge_base" / "diseases" / "chroma_db"
    data_dir = project_root / "src" / "data"
    diseases_dir = data_dir / "diseases"

    # 检查知识库是否存在
    if persist_dir.exists():
        logger.info(f"[OK] 疾病知识库已存在: {persist_dir}")
        return

    logger.info(f"[INFO] 疾病知识库不存在，开始自动构建...")
    logger.info(f"   目标位置: {persist_dir}")
    logger.info(f"   源数据: {diseases_dir}")

    try:
        # 导入必要的模块
        from src.rag.config import get_embeddings_cached
        from src.rag.utils.loaders import MarkdownLoader
        from langchain_chroma import Chroma
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document

        # 检查源数据目录
        if not diseases_dir.exists():
            logger.warning(f"[WARN] 源数据目录不存在: {diseases_dir}")
            logger.warning("   跳过疾病知识库构建")
            return

        # 加载文档
        logger.info(f"[LOAD] 正在加载文档...")
        documents = []

        for animal_type in ["牛", "猪", "羊", "家禽", "其他"]:
            animal_dir = diseases_dir / animal_type
            if not animal_dir.exists():
                continue

            logger.info(f"   处理 {animal_type}/:")

            for file_path in sorted(animal_dir.iterdir()):
                if not file_path.is_file() or file_path.suffix.lower() != '.md':
                    continue

                try:
                    loader = MarkdownLoader(file_path, category="diseases")
                    docs = loader.load()
                    documents.extend(docs)
                except Exception as e:
                    logger.warning(f"      [SKIP] {file_path.name}: {e}")

        logger.info(f"[OK] 已加载 {len(documents)} 个文档片段")

        if not documents:
            logger.warning("[WARN] 未找到任何文档，跳过构建")
            return

        # 分割文档
        logger.info(f"[SPLIT] 正在分割文档...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )

        splits = []
        for doc in documents:
            split_docs = text_splitter.split_text(doc.page_content)
            for i, split in enumerate(split_docs):
                splits.append(Document(
                    page_content=split,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                    }
                ))

        logger.info(f"[OK] 分割为 {len(splits)} 个文本块")

        # 向量化
        logger.info(f"[VECTOR] 正在向量化...")
        start_time = time.time()

        embeddings = get_embeddings_cached()
        persist_dir.mkdir(parents=True, exist_ok=True)

        # 创建向量数据库（不保存引用，只用于触发构建）
        Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(persist_dir),
            collection_name=collection_name,
        )

        elapsed = time.time() - start_time
        logger.info(f"[OK] 向量化完成 (用时 {elapsed:.1f}秒)")
        logger.info(f"[INFO] Collection: {collection_name}")
        logger.info(f"[INFO] 文档块: {len(splits)}")

    except Exception as e:
        logger.error(f"[ERROR] 疾病知识库构建失败: {e}")
        logger.warning("   服务将启动，但疾病预测功能可能不可用")
        import traceback
        traceback.print_exc()


# -------- 意图识别函数 --------
def classify_intent(message: str, has_images: bool = False) -> str:
    """
    分类用户意图

    Args:
        message: 用户消息
        has_images: 是否包含图片

    Returns:
        意图类型: detection/general
    """
    # 规则1: 如果有图片，优先检测
    if has_images:
        return "detection"

    # 规则2: 检测相关关键词
    detection_keywords = [
        "识别", "检测", "害虫", "病害", "大米", "品种", "牛", "奶牛",
        "图片", "照片", "看", "什么", "分析", "诊断", "分类"
    ]

    message_lower = message.lower()

    # 统计关键词匹配
    detection_matches = sum(1 for kw in detection_keywords if kw in message)

    # 如果检测相关关键词较多，返回 detection
    if detection_matches >= 2:
        return "detection"

    # 默认为通用对话（Agent 会根据内容自主决定是否调用规划 skill）
    return "general"


# -------- API 路由定义--------
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "RuralBrain API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/models")
async def get_models():
    """
    获取可用模型列表

    Returns:
        models: 模型列表
        default_model: 默认模型 ID
    """
    models = []
    for model_id, config in AVAILABLE_MODELS.items():
        models.append({
            "id": model_id,
            "name": config["name"],
            "description": config["description"],
            "is_multimodal": config["is_multimodal"],
        })

    return {
        "models": models,
        "default_model": DEFAULT_MODEL_ID,
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_image(files: list[UploadFile] = File(...)):
    """
    上传图片接口（支持单张或多张）
    
    Args:
        files: 上传的图片文件列表（最多10张）
        
    Returns:
        上传响应，包含文件路径列表
    """
    # 限制上传图片数量
    MAX_FILES = 10
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"一次最多上传 {MAX_FILES} 张图片",
        )
    
    try:
        file_paths = []
        
        for file in files:
            # 检查文件大小
            contents = await file.read()
            if len(contents) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件 {file.filename} 大小超过限制 ({MAX_UPLOAD_SIZE / 1024 / 1024}MB)",
                )
            
            # 检查文件扩展名
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件 {file.filename} 格式不支持，仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
                )
            
            # 生成唯一文件名
            filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / filename
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(contents)
            
            file_paths.append(str(file_path))
            logger.info(f"文件上传成功: {filename}")
        
        # 兼容旧版本：如果只有一张图片，同时返回 file_path
        return UploadResponse(
            success=True,
            file_path=file_paths[0] if len(file_paths) == 1 else None,
            file_paths=file_paths,
            message=f"成功上传 {len(file_paths)} 张图片",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}",
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    统一流式对话接口，使用 Orchestrator Agent 智能路由

    Orchestrator Agent 会自动判断用户意图：
    - 有图片 → 调用图像检测
    - 规划相关问题 → 调用规划知识库（规划 skill）
    - 支持多步推理和场景切换

    Args:
        request: 聊天请求，包含消息和可选的图片路径

    Returns:
        SSE 流式响应
    """
    try:
        # 生成或使用线程ID
        thread_id = request.thread_id or str(uuid.uuid4())

        # 支持多图片路径（新版本）或单图片路径（兼容旧版本）
        image_paths = request.image_paths or ([request.image_path] if request.image_path else [])

        # 获取 Orchestrator Agent
        agent = get_agent()
        config = {
            "configurable": {
                "thread_id": thread_id,
                "enable_knowledge_base": request.enable_knowledge_base,
            },
            "recursion_limit": 50,  # 防止递归限制
        }
        # 创建运行时上下文（模型选择）
        model_id = request.model_id or DEFAULT_MODEL_ID
        agent_context = AgentContext(model_id=model_id)

        # 使用多模态消息构建函数
        message_content = build_multimodal_message(
            text=request.message,
            image_paths=image_paths if image_paths else None,
            model_id=model_id,
        )

        # 获取多模态状态
        is_multimodal = AVAILABLE_MODELS.get(model_id, {}).get("is_multimodal", False)
        logger.info(f"调用 Orchestrator Agent [thread_id={thread_id}]: {request.message[:50]}..., "
                    f"图片数量: {len(image_paths)}, 知识库: {request.enable_knowledge_base}, "
                    f"模型: {model_id}, 多模态: {is_multimodal}")

        # 保存知识库开关状态到中间件（供 load_skill 工具使用）
        logger.info(f"准备设置知识库开关: thread_id={thread_id}, enable_knowledge_base={request.enable_knowledge_base}")
        if request.enable_knowledge_base is not None:
            set_kb_switch_state(thread_id, request.enable_knowledge_base)
            logger.info(f"设置知识库开关: thread_id={thread_id}, enabled={request.enable_knowledge_base}")
        else:
            logger.info(f"知识库开关未设置 (None)，跳过状态设置")

        # 联网搜索开关（新增）
        if request.enable_web_search is not None:
            set_web_search_switch_state(thread_id, request.enable_web_search)

        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"

                # 初始化推理过程过滤器
                thinking_filter = ThinkingProcessFilter()

                # 流式处理 agent 响应
                full_content = ""
                content_buffer = []
                BUFFER_SIZE = 1  # 逐字输出，避免卡顿感

                async for event in agent.astream_events(
                    {"messages": [message_content]},
                    config,
                    version="v2",
                    context=agent_context,
                ):
                    kind = event["event"]

                    # 处理流式消息内容（AI 的回答）
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            # 应用推理过程过滤器
                            filtered_content, should_send = thinking_filter.process(content)

                            if should_send and filtered_content:
                                content_buffer.append(filtered_content)
                                # 当缓冲达到大小时发送
                                if len("".join(content_buffer)) >= BUFFER_SIZE:
                                    buffered_content = "".join(content_buffer)
                                    full_content += buffered_content
                                    # 清理 JSON 代码块（移除 ```json ... ``` 部分）
                                    cleaned_content = clean_json_from_content(buffered_content)
                                    cleaned_content = strip_internal_scratchpad_content(cleaned_content)
                                    if cleaned_content:
                                        event_data = {
                                            "type": "content",
                                            "content": cleaned_content,
                                        }
                                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                    content_buffer = []

                    # 处理工具调用结束事件
                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        logger.info(f"工具调用完成: {tool_name}")

                        # 查找对应的结果图片路径（仅检测工具）
                        result_image = None
                        if tool_name == "pest_detection_tool":
                            # 查找最新的害虫检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "pest"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("pest_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/pest_results/{images[0].name}"

                        elif tool_name == "rice_detection_tool":
                            # 查找最新的大米检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "rice"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("rice_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/rice_results/{images[0].name}"

                        elif tool_name == "cow_detection_tool":
                            # 查找最新的牛只检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "cow"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("cow_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/cow_results/{images[0].name}"

                        # 解析工具的结构化输出
                        result_data = None

                        # 获取工具输出内容
                        tool_output = event.get("data")
                        tool_output_text = None

                        if tool_output and isinstance(tool_output, dict):
                            output_msg = tool_output.get("output")
                            if output_msg and hasattr(output_msg, 'content'):
                                tool_output_text = output_msg.content
                            elif isinstance(output_msg, str):
                                tool_output_text = output_msg

                        # 解析联网搜索工具的结构化输出
                        if tool_name == "web_search_tool" and tool_output_text:
                            try:
                                parsed = json.loads(tool_output_text)
                                result_data = {
                                    "ai_summary": parsed.get("ai_summary", ""),
                                    "results": parsed.get("results", []),
                                    "stats": parsed.get("stats", {"total": 0, "news": 0, "web": 0})
                                }
                                logger.info(f"联网搜索结果数据: {result_data['stats']}")
                            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                                logger.warning(f"解析 web_search_tool 输出失败: {e}")

                        # 解析检测工具的结构化输出
                        elif tool_name in ["pest_detection_tool", "rice_detection_tool", "cow_detection_tool"]:
                            result_data = parse_detection_tool_output(tool_output_text or "", tool_name)
                            if result_data:
                                logger.info(f"{tool_name} 结构化数据: {result_data['summary']}")

                        # 解析疾病预测工具的结构化输出
                        elif tool_name == "disease_prediction_tool":
                            # 添加调试日志
                            logger.info(f"疾病预测工具原始输出（前500字符）: {tool_output_text[:500] if tool_output_text else 'None'}")
                            result_data = parse_disease_prediction_output(tool_output_text or "")
                            if result_data:
                                logger.info(f"disease_prediction_tool 结构化数据: {len(result_data['diseases'])} 个疾病预测 - {result_data['diseases'][:2]}")

                            # 清理工具输出文本，移除 JSON 部分，只保留人类可读的报告
                            if tool_output_text:
                                tool_output_text = clean_tool_output_json(tool_output_text)

                        # 解析巡检工具的结构化输出
                        elif tool_name == "farm_inspection_tool":
                            result_data = parse_farm_inspection_output(tool_output_text or "")
                            if result_data:
                                logger.info(f"farm_inspection_tool 结构化数据: {result_data.get('inspection_type', 'unknown')}")

                        # 发送工具调用完成事件
                        # 添加完整的基础 URL（前端通过前端 API 路由访问）
                        tool_event = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "status": "已完成",
                            "result_image": result_image,  # 相对路径，前端会通过代理访问
                            "result_data": result_data,  # 新增：联网搜索的结构化数据
                        }
                        yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"

                # 发送剩余的缓冲内容
                if content_buffer:
                    buffered_content = "".join(content_buffer)
                    full_content += buffered_content
                    # 清理 JSON 代码块（移除 ```json ... ``` 部分）
                    cleaned_content = clean_json_from_content(buffered_content)
                    cleaned_content = strip_internal_scratchpad_content(cleaned_content)
                    if cleaned_content:
                        event_data = {
                            "type": "content",
                            "content": cleaned_content,
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                remaining_content = thinking_filter.flush_remaining()
                if remaining_content:
                    full_content += remaining_content
                    event_data = {
                        "type": "content",
                        "content": remaining_content,
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                full_content = strip_internal_scratchpad_content(clean_json_from_content(full_content))

                # 发送完成事件
                yield f"data: {json.dumps({'type': 'end', 'full_content': full_content}, ensure_ascii=False)}\n\n"

                logger.info(f"对话完成 [thread_id={thread_id}]")

            except Exception as e:
                logger.error(f"对话处理错误: {str(e)}")
                error_data = {
                    "type": "error",
                    "error": str(e),
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        # 使用 StreamingResponse 包装生成器
        return StreamingResponse(
            event_generator(),
            # 设置 SSE 媒体类型
            media_type="text/event-stream",
            # 禁用缓存，防止代理服务器缓冲响应，确保实时性
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"对话请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ==================== 知识库更新 API ====================

@app.post("/api/v1/knowledge/update", response_model=KnowledgeUpdateResponse, tags=["知识库"])
async def update_knowledge_base(request: KnowledgeUpdateRequest):
    """
    更新知识库（线程安全）

    支持两种模式：
    - **增量更新**（默认）：仅处理新增/变更文档，保留现有数据
    - **全量重建**（force_rebuild=True）：清空后重新构建整个知识库

    数据源选项：
    - source: 单个文档路径
    - source_dir: 文档目录（批量处理）
    """
    return await _update_knowledge_base_impl(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "服务器内部错误"},
    )


if __name__ == "__main__":
    import uvicorn
    from service.settings import HOST, PORT
    
    uvicorn.run(
        "service.server:app",
        host=HOST,
        port=PORT,
        reload=True,
    )
