"""农场巡检工具：收集与整理农场各类信息数据。

对农田、养殖圈、设施设备等进行信息收集与整理，生成结构化数据，
为 Agent 的 LLM 提供充分的决策依据。

支持智能巡检模式：传入巡检图片（监控/无人机拍摄），自动识别场景类型，
并建议后续的检测工具调用链。

支持多模态综合分析：多张巡检照片可传给多模态 LLM 进行综合语义分析。
"""
import json
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage

from ...utils import ModelManager
from ...config import AVAILABLE_MODELS

# 导入场景分类工具
try:
    from .scene_classifier_tool import classify_scene_from_path, get_scene_recommendations, SCENE_TYPES
except ImportError:
    # 如果导入失败，使用降级方案
    SCENE_TYPES = {
        "cattle": {"name": "牛舍"},
        "pig": {"name": "猪舍"},
        "chicken": {"name": "鸡舍"},
        "crop": {"name": "农田"},
        "greenhouse": {"name": "温室"},
        "unknown": {"name": "未知场景"}
    }

    def classify_scene_from_path(image_path: str) -> dict:
        return {"scene_type": "unknown", "confidence": 0.0}

    def get_scene_recommendations(scene_type: str) -> list:
        return []

# 导入图片处理工具
try:
    from .detection_utils import encode_image_to_base64, extract_images_from_messages
except ImportError:
    # 降级方案
    def encode_image_to_base64(image_path: str) -> str:
        with open(image_path, "rb") as f:
            import base64
            return base64.b64encode(f.read()).decode("utf-8")

    def extract_images_from_messages(messages):
        """从消息历史中提取所有图片"""
        images = []
        for msg in messages:
            if hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "image_url":
                            url = block.get("image_url", {})
                            if isinstance(url, dict):
                                url = url.get("url", "")
                                if url.startswith("data:"):
                                    # 解析 base64
                                    mime_type = url.split(":")[1].split(";")[0] if ":" in url else "image/jpeg"
                                    base64_data = url.split(",", 1)[1] if "," in url else ""
                                    images.append({"base64": base64_data, "mime_type": mime_type})
        return images

logger = logging.getLogger(__name__)


# ==================== 常量配置 ====================

MEDIA_TYPES = {
    "monitor": "监控摄像头",
    "drone": "无人机拍摄",
    "manual": "人工拍摄"
}

SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ==================== 辅助函数 ====================

def _is_model_multimodal(model_id: str) -> bool:
    """判断指定模型是否支持多模态

    通过 model_name 匹配，因为 AVAILABLE_MODELS 的 key 是简称
    """
    for config in AVAILABLE_MODELS.values():
        if config.get("model_name") == model_id:
            return config.get("is_multimodal", False)
    return False


# ==================== 传感器数据采集 ====================

# TODO: 后续接入真实数据采集系统时替换此函数
def _collect_actual_sensor_data(farm_id: str, area_type: str) -> dict:
    """从真实传感器/物联网设备采集数据

    预留接口，后续接入时实现：
    - 连接农场物联网平台
    - 读取传感器实时数据
    - 获取设备状态信息

    Args:
        farm_id: 农场ID
        area_type: 区域类型（农田/养殖圈/温室等）

    Returns:
        采集的传感器数据
    """
    # 预留：后续接入真实物联网系统
    pass


def _generate_mock_farm_data(farm_id: Optional[str] = None, inspection_scope: Optional[str] = None) -> dict:
    """生成模拟农场巡检数据（临时占位实现）

    后续会被真实数据采集系统替换，这里只是占位实现。
    """
    farm_id = farm_id or "FARM-001"
    scope = inspection_scope or "all"

    result = {
        "farm_id": farm_id,
        "inspection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {}
    }

    # 农田信息
    if scope in ["all", "farmland"]:
        result["data"]["farmlands"] = [
            {
                "id": "FL-001",
                "name": "A区水稻田",
                "area": 50,
                "crop": "水稻",
                "growth_stage": "分蘖期",
                "planting_date": "2024-05-15",
                "soil_moisture": 65,
                "soil_ph": 6.5,
                "temperature": 28,
                "humidity": 75,
                "pest_status": "无异常",
                "irrigation_status": "正常",
                "equipment_status": {
                    "irrigation_system": "运行中",
                    "monitoring_sensors": "在线"
                }
            },
            {
                "id": "FL-002",
                "name": "B区玉米地",
                "area": 30,
                "crop": "玉米",
                "growth_stage": "拔节期",
                "planting_date": "2024-06-01",
                "soil_moisture": 58,
                "soil_ph": 6.8,
                "temperature": 27,
                "humidity": 70,
                "pest_status": "发现少量蚜虫",
                "irrigation_status": "需灌溉",
                "equipment_status": {
                    "irrigation_system": "待启动",
                    "monitoring_sensors": "在线"
                }
            }
        ]

    # 养殖圈信息
    if scope in ["all", "livestock"]:
        result["data"]["livestock"] = [
            {
                "id": "LS-001",
                "name": "1号牛舍",
                "animal_type": "牛",
                "count": 45,
                "capacity": 50,
                "health_status": "正常",
                "temperature": 22,
                "humidity": 65,
                "ventilation": "良好",
                "feed_stock": {
                    "forage": "充足（约3天）",
                    "concentrate": "充足（约5天）",
                    "water": "正常"
                },
                "equipment_status": {
                    "feeding_system": "运行中",
                    "ventilation_fans": "运行中",
                    "water_dispensers": "正常"
                },
                "abnormal_count": 0,
                "recent_health_records": []
            },
            {
                "id": "LS-002",
                "name": "2号猪舍",
                "animal_type": "猪",
                "count": 120,
                "capacity": 150,
                "health_status": "2头食欲不振",
                "temperature": 24,
                "humidity": 70,
                "ventilation": "一般",
                "feed_stock": {
                    "forage": "充足（约2天）",
                    "concentrate": "充足（约4天）",
                    "water": "正常"
                },
                "equipment_status": {
                    "feeding_system": "运行中",
                    "ventilation_fans": "1台待修",
                    "water_dispensers": "正常"
                },
                "abnormal_count": 2,
                "recent_health_records": [
                    {"date": "2024-07-20", "issue": "2头猪食欲不振，已隔离观察"}
                ]
            }
        ]

    # 温室大棚信息
    if scope in ["all", "greenhouse"]:
        result["data"]["greenhouses"] = [
            {
                "id": "GH-001",
                "name": "1号蔬菜大棚",
                "crop": "番茄",
                "area": 2000,
                "growth_stage": "结果期",
                "planting_date": "2024-04-10",
                "temperature": 26,
                "humidity": 75,
                "co2_level": 450,
                "light_intensity": 85,
                "irrigation_status": "滴灌运行中",
                "equipment_status": {
                    "temperature_control": "自动",
                    "ventilation": "运行中",
                    "shading_system": "收起",
                    "irrigation": "运行中"
                }
            }
        ]

    # 设施设备状态
    if scope in ["all", "equipment"]:
        result["data"]["equipment"] = {
            "power_supply": "正常",
            "water_supply": "正常",
            "network_status": "在线",
            "alert_count": 1,
            "alerts": [
                {
                    "id": "ALT-001",
                    "level": "warning",
                    "equipment": "2号猪舍通风扇",
                    "issue": "1台通风扇运行异常，需检修",
                    "time": "2024-07-21 08:30"
                }
            ]
        }

    # 人员与作业记录
    if scope in ["all", "operations"]:
        result["data"]["operations"] = {
            "staff_on_duty": 8,
            "ongoing_tasks": [
                {"task": "A区水稻田灌溉", "operator": "张三", "status": "进行中"},
                {"task": "2号猪舍设备检修", "operator": "李四", "status": "待开始"},
                {"task": "温室病虫害巡查", "operator": "王五", "status": "已完成"}
            ],
            "recent_activities": [
                {"time": "07:00", "activity": "晨间巡检完成", "operator": "值班员"},
                {"time": "08:00", "activity": "牛群喂料完成", "operator": "张三"},
                {"time": "09:00", "activity": "温室采摘完成", "operator": "王五"}
            ]
        }

    return result


# ==================== 多模态 LLM 综合分析 ====================

def _analyze_inspection_with_llm(
    image_sources: List[str | dict],
    scene_results: List[dict],
    media_type: str
) -> dict:
    """使用多模态 LLM 综合分析多张巡检照片

    Args:
        image_sources: 图片来源列表（路径或 base64 字典）
        scene_results: 场景分类结果列表
        media_type: 媒体类型

    Returns:
        分析结果字典
    """
    try:
        # 初始化模型管理器
        model_manager = ModelManager.from_env()
        model = model_manager.get_chat_model(temperature=0.3)
        model_id = model_manager.config.get("default_model", "")

        # 判断是否支持多模态
        supports_multimodal = _is_model_multimodal(model_id)

        # 构建场景分类摘要
        scene_summary_parts = []
        for i, scene_result in enumerate(scene_results, 1):
            scene_type = scene_result.get("scene_type", "unknown")
            confidence = scene_result.get("confidence", 0.0)
            scene_info = SCENE_TYPES.get(scene_type, SCENE_TYPES["unknown"])
            scene_summary_parts.append(
                f"图片{i}：{scene_info.get('name', '未知场景')}（置信度：{confidence:.1%}）"
            )

        scene_summary = "\n".join(scene_summary_parts)

        # 构建媒体类型说明
        media_type_name = MEDIA_TYPES.get(media_type, media_type)

        # 构建提示词
        prompt = f"""你是一位专业的农场巡检员，请综合分析以下巡检照片。

## 巡检信息
- 拍摄方式：{media_type_name}
- 照片数量：{len(image_sources)}张

## 场景识别结果（AI辅助）
{scene_summary}

## 分析要求
请仔细观察每一张照片，综合分析以下方面：

### 养殖场景（牛舍/猪舍/鸡舍）
- 动物数量和健康状况
- 有无异常行为、精神萎靡、食欲不振
- 环境条件：温度、湿度、通风、卫生状况
- 设备状态：喂料系统、饮水系统、通风设备
- 饲料储备情况

### 种植场景（农田/温室）
- 作物长势和生长阶段
- 有无病虫害迹象（叶片斑点、虫害、枯萎）
- 土壤墒情（干旱、积水）
- 设施状态：灌溉系统、温室设备、遮阳系统

### 设施设备
- 运行状态是否正常
- 有无损坏或故障
- 安全隐患检查

## 输出格式
请输出一份结构清晰的巡检报告：

---
### 📋 农场巡检综合报告

#### 🎯 巡检概览
- 拍摄场景：[总结各照片的场景类型]
- 整体状况：[正常/需关注/异常]

#### 📸 逐张分析
**图片1** [场景类型]
- 观察到的情况：[详细描述]
- 发现的问题：[如有]

**图片2** [场景类型]
...

#### ⚠️ 发现的问题
1. [问题描述] - [紧急程度：高/中/低]
2. ...

#### ✅ 建议措施
1. [具体建议]
2. ...

#### 🔧 建议调用的检测工具
[根据发现的问题，建议使用哪些专业检测工具]

---
注意：
- 即使没有明显问题，也要描述观察到的情况
- 建议措施要具体、可操作
- 紧急程度根据问题影响范围判断"""

        # 构建消息
        if supports_multimodal and image_sources:
            # 构建多模态消息
            content_blocks = [{"type": "text", "text": prompt}]

            for i, image_source in enumerate(image_sources, 1):
                try:
                    if isinstance(image_source, dict):
                        # base64 格式
                        mime_type = image_source.get("mime_type", "image/jpeg")
                        base64_data = image_source.get("base64", "")
                        content_blocks.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                        })
                        logger.info(f"添加第{i}张图片（base64）到多模态消息")
                    elif isinstance(image_source, str):
                        # 路径格式，需要读取并编码
                        image_base64 = encode_image_to_base64(image_source)
                        import mimetypes
                        mime_type, _ = mimetypes.guess_type(image_source)
                        if mime_type is None:
                            mime_type = "image/jpeg"
                        content_blocks.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
                        })
                        logger.info(f"添加第{i}张图片（路径）到多模态消息: {image_source}")
                except Exception as e:
                    logger.error(f"第{i}张图片编码失败: {e}")
                    # 降级：在文本中说明
                    content_blocks[0]["text"] += f"\n\n[第{i}张图片读取失败]"

            message = HumanMessage(content=content_blocks)
        else:
            # 纯文本消息（不支持多模态或没有图片）
            message = HumanMessage(content=prompt)

        # 调用模型
        response = model.invoke([message])
        report_text = response.content.strip().replace("```", "").strip()

        return {
            "success": True,
            "report": report_text,
            "model_used": model_id,
            "supports_multimodal": supports_multimodal,
            "image_count": len(image_sources),
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        logger.error(f"LLM 综合分析失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "report": f"### ⚠️ 分析失败\n\n综合分析工具遇到错误：{str(e)}\n\n请稍后重试或进行人工巡检。"
        }


# ==================== 智能巡检分析 ====================

def _perform_smart_inspection(media_path: str, media_type: str) -> dict:
    """执行智能巡检分析

    Args:
        media_path: 媒体文件路径
        media_type: 媒体类型（monitor/drone/manual）

    Returns:
        智能分析结果
    """
    # 验证文件
    path = Path(media_path)
    if not path.exists():
        return {
            "success": False,
            "error": "文件不存在"
        }

    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        return {
            "success": False,
            "error": f"不支持的图片格式: {path.suffix}"
        }

    # 调用场景分类
    scene_result = classify_scene_from_path(media_path)
    scene_type = scene_result.get("scene_type", "unknown")
    confidence = scene_result.get("confidence", 0.0)

    # 获取推荐工具
    recommended_tools = get_scene_recommendations(scene_type)
    scene_info = SCENE_TYPES.get(scene_type, SCENE_TYPES["unknown"])

    return {
        "success": True,
        "media_type": media_type,
        "media_type_name": MEDIA_TYPES.get(media_type, media_type),
        "scene_type": scene_type,
        "scene_name": scene_info.get("name", "未知场景"),
        "confidence": confidence,
        "recommended_tools": recommended_tools,
        "next_actions": _generate_action_suggestions(scene_type, recommended_tools)
    }


def _generate_action_suggestions(scene_type: str, tools: list) -> list[str]:
    """生成后续行动建议

    Args:
        scene_type: 场景类型
        tools: 推荐工具列表

    Returns:
        行动建议列表
    """
    if scene_type == "cattle":
        return [
            "1. 调用 cow_detection_tool 统计牛只数量，确认是否有遗漏",
            "2. 观察牛只精神状态，如有异常调用 disease_prediction_tool 分析",
            "3. 检查舍内环境参数（温度、湿度、通风）"
        ]
    elif scene_type == "pig":
        return [
            "1. 观察猪只精神状态和食欲",
            "2. 如有异常症状，调用 disease_prediction_tool 分析疾病",
            "3. 检查舍内环境参数和饲料储备"
        ]
    elif scene_type == "chicken":
        return [
            "1. 观察家禽活动状态和羽毛情况",
            "2. 如有异常症状，调用 disease_prediction_tool 分析",
            "3. 检查产蛋情况和饲料消耗"
        ]
    elif scene_type == "crop":
        return [
            "1. 调用 pest_detection_tool 检测是否有害虫",
            "2. 调用 plant_disease_detection_tool 检测是否有病害",
            "3. 观察作物长势和土壤墒情"
        ]
    elif scene_type == "greenhouse":
        return [
            "1. 检查温室内环境参数（温度、湿度、CO2）",
            "2. 调用 pest_detection_tool 和 plant_disease_detection_tool 检测病虫害",
            "3. 检查灌溉系统和设备运行状态"
        ]
    else:
        return [
            "1. 无法自动识别场景类型，建议人工确认",
            "2. 可根据实际场景调用相应的检测工具"
        ]


# ==================== 主工具 ====================

@tool
def farm_inspection_tool(
    runtime: ToolRuntime,
    farm_id: Optional[str] = None,
    inspection_scope: Optional[str] = None,
    area_ids: Optional[List[str]] = None,
    media_path: Optional[str] = None,
    media_paths: Optional[List[str]] = None,
    media_type: Optional[str] = None,
    smart_analysis: Optional[bool] = True,
    enable_multimodal: Optional[bool] = True
) -> str:
    """收集农场巡检数据，生成结构化信息。

    **支持智能巡检模式**：传入巡检图片（监控/无人机拍摄），自动识别场景类型
    并建议后续的检测工具调用链。

    **支持多模态综合分析**：多张巡检照片可传给多模态 LLM 进行综合语义分析，
    生成更详细的巡检报告。

    **传统巡检模式**：返回农田、养殖圈、温室、设备等传感器数据。

    Args:
        runtime: LangGraph 工具运行时，用于访问消息历史
        farm_id: 农场ID，如 FARM-001，可选
        inspection_scope: 巡检范围，可选值：
            - all: 全部巡检（默认）
            - farmland: 仅农田
            - livestock: 仅养殖圈
            - greenhouse: 仅温室
            - equipment: 仅设施设备
            - operations: 仅作业记录
        area_ids: 指定巡检的区域ID列表，如 ["FL-001", "LS-001"]，可选
        media_path: 巡检媒体文件路径（单张图片），可选。提供此参数时启用智能巡检模式
        media_paths: 巡检媒体文件路径列表（多张图片），可选
        media_type: 媒体采集类型，可选值：
            - monitor: 监控摄像头（默认）
            - drone: 无人机拍摄
            - manual: 人工拍摄
        smart_analysis: 是否启用智能分析（默认 True）
        enable_multimodal: 是否启用多模态综合分析（默认 True，需要多模态模型支持）

    Returns:
        JSON格式的结构化数据：
        - 智能巡检模式：返回场景识别结果和建议的工具调用列表
        - 多模态分析模式：返回 LLM 综合分析的巡检报告
        - 传统模式：返回传感器数据（农田、养殖圈、温室、设备等）

    Examples:
        智能巡检（单张图片）：
        >>> farm_inspection_tool(media_path="inspection.jpg", media_type="drone")

        多模态综合分析（多张图片）：
        >>> farm_inspection_tool(media_paths=["photo1.jpg", "photo2.jpg"], enable_multimodal=True)

        传统巡检：
        >>> farm_inspection_tool(inspection_scope="livestock")
    """
    try:
        result = {
            "inspection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "farm_id": farm_id or "FARM-001"
        }

        # ========== 处理图片输入 ==========
        image_sources = []
        media_type = media_type or "monitor"

        # 1. 手动指定的多图片
        if media_paths:
            image_sources = media_paths
            logger.info(f"使用手动指定的多张图片: {len(media_paths)}张")
        # 2. 手动指定的单图片
        elif media_path:
            image_sources = [media_path]
            logger.info(f"使用手动指定的单张图片: {media_path}")
        # 3. 自动从消息历史提取
        else:
            try:
                messages = runtime.state.get("messages", [])
                extracted_images = extract_images_from_messages(messages)
                if extracted_images:
                    image_sources = extracted_images
                    logger.info(f"从消息历史提取到 {len(extracted_images)}张图片")
            except Exception as e:
                logger.warning(f"从消息历史提取图片失败: {e}")

        # ========== 智能巡检模式（有图片）==========
        if image_sources:
            # 对每张图片进行场景分类
            scene_results = []
            for i, img_source in enumerate(image_sources, 1):
                # 处理图片来源（支持 base64 字典或路径）
                img_path = img_source if isinstance(img_source, str) else None

                # 如果是 base64，先保存为临时文件用于场景分类
                if img_path is None and isinstance(img_source, dict):
                    # 对于 base64 图片，场景分类可能需要跳过或使用其他方法
                    # 这里简化处理：标记为未知场景
                    scene_results.append({
                        "scene_type": "unknown",
                        "confidence": 0.0,
                        "index": i
                    })
                    logger.info(f"图片{i}（base64）跳过场景分类")
                elif img_path:
                    # 执行场景分类
                    scene_result = classify_scene_from_path(img_path)
                    scene_result["index"] = i
                    scene_results.append(scene_result)
                    logger.info(f"图片{i}场景分类: {scene_result.get('scene_type', 'unknown')}")

            # 获取推荐工具（基于第一张图片的场景）
            primary_scene = scene_results[0].get("scene_type", "unknown") if scene_results else "unknown"
            recommended_tools = get_scene_recommendations(primary_scene)
            scene_info = SCENE_TYPES.get(primary_scene, SCENE_TYPES["unknown"])

            # 执行多模态综合分析（如果启用且支持）
            llm_report = None
            if enable_multimodal:
                llm_result = _analyze_inspection_with_llm(image_sources, scene_results, media_type)
                if llm_result.get("success"):
                    llm_report = llm_result.get("report")

            # 构建结果
            result.update({
                "inspection_type": "多图智能巡检",
                "image_count": len(image_sources),
                "media_type": media_type,
                "media_type_name": MEDIA_TYPES.get(media_type, media_type),
                "scene_classification": {
                    "primary_scene": scene_info.get("name", "未知场景"),
                    "primary_scene_type": primary_scene,
                    "all_scenes": [
                        {
                            "index": s.get("index"),
                            "scene_type": s.get("scene_type"),
                            "scene_name": SCENE_TYPES.get(s.get("scene_type"), {}).get("name", "未知场景"),
                            "confidence": s.get("confidence", 0.0)
                        }
                        for s in scene_results
                    ]
                },
                "recommended_tools": [
                    {
                        "tool": t["tool"],
                        "reason": t["reason"]
                    }
                    for t in recommended_tools
                ],
                "multimodal_analysis": {
                    "enabled": enable_multimodal,
                    "report": llm_report
                } if llm_report else None
            })

            # 如果没有多模态报告，添加传统的行动建议
            if not llm_report:
                result["suggested_actions"] = _generate_action_suggestions(primary_scene, recommended_tools)

            # 如果同时请求了传感器数据，也一并返回
            if inspection_scope:
                sensor_data = _generate_mock_farm_data(farm_id, inspection_scope)
                result["sensor_data"] = sensor_data.get("data", {})

            return json.dumps(result, ensure_ascii=False, indent=2)

        # ========== 传统巡检模式 ==========
        else:
            result["inspection_type"] = "传感器巡检"

            # 收集传感器数据
            sensor_data = _generate_mock_farm_data(farm_id, inspection_scope)

            # 如果指定了区域ID，过滤数据
            if area_ids:
                filtered_data = {}
                for category, items in sensor_data["data"].items():
                    if isinstance(items, list):
                        filtered_items = [item for item in items if item.get("id") in area_ids]
                        if filtered_items:
                            filtered_data[category] = filtered_items
                    else:
                        filtered_data[category] = items
                sensor_data["data"] = filtered_data
                result["filtered"] = True
                result["requested_area_ids"] = area_ids

            result["data"] = sensor_data["data"]
            return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


__all__ = ["farm_inspection_tool"]
farm_inspection_tool.tags = ["inspection", "farm", "smart"]


if __name__ == "__main__":
    # 测试工具
    import tempfile

    print("\n" + "="*60)
    print("测试 1: 传统巡检模式")
    print("="*60)
    result = farm_inspection_tool.invoke({"inspection_scope": "livestock"})
    print(result)

    print("\n" + "="*60)
    print("测试 2: 智能巡检模式（模拟牛舍）")
    print("="*60)

    # 创建模拟测试图片
    with tempfile.NamedTemporaryFile(suffix="_cow.jpg", delete=False) as f:
        test_path = f.name
        f.write(b"fake_image_data")

    result = farm_inspection_tool.invoke({
        "media_path": test_path,
        "media_type": "monitor"
    })
    print(result)

    # 清理
    Path(test_path).unlink(missing_ok=True)
