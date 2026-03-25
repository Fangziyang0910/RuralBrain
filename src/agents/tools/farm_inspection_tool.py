"""农场巡检工具：收集与整理农场各类信息数据。

对农田、养殖圈、设施设备等进行信息收集与整理，生成结构化数据，
为 Agent 的 LLM 提供充分的决策依据。

支持智能巡检模式：传入巡检图片（监控/无人机拍摄），自动识别场景类型，
并建议后续的检测工具调用链。
"""
import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool

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


# ==================== 常量配置 ====================

MEDIA_TYPES = {
    "monitor": "监控摄像头",
    "drone": "无人机拍摄",
    "manual": "人工拍摄"
}

SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


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
    farm_id: Optional[str] = None,
    inspection_scope: Optional[str] = None,
    area_ids: Optional[List[str]] = None,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None,
    smart_analysis: Optional[bool] = True
) -> str:
    """收集农场巡检数据，生成结构化信息。

    **支持智能巡检模式**：传入巡检图片（监控/无人机拍摄），自动识别场景类型
    并建议后续的检测工具调用链。

    **传统巡检模式**：返回农田、养殖圈、温室、设备等传感器数据。

    Args:
        farm_id: 农场ID，如 FARM-001，可选
        inspection_scope: 巡检范围，可选值：
            - all: 全部巡检（默认）
            - farmland: 仅农田
            - livestock: 仅养殖圈
            - greenhouse: 仅温室
            - equipment: 仅设施设备
            - operations: 仅作业记录
        area_ids: 指定巡检的区域ID列表，如 ["FL-001", "LS-001"]，可选
        media_path: 巡检媒体文件路径（图片），可选。提供此参数时启用智能巡检模式
        media_type: 媒体采集类型，可选值：
            - monitor: 监控摄像头（默认）
            - drone: 无人机拍摄
            - manual: 人工拍摄
        smart_analysis: 是否启用智能分析（默认 True）

    Returns:
        JSON格式的结构化数据：
        - 智能巡检模式：返回场景识别结果和建议的工具调用列表
        - 传统模式：返回传感器数据（农田、养殖圈、温室、设备等）

    Examples:
        智能巡检：
        >>> farm_inspection_tool(media_path="inspection.jpg", media_type="drone")

        传统巡检：
        >>> farm_inspection_tool(inspection_scope="livestock")
    """
    try:
        result = {
            "inspection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "farm_id": farm_id or "FARM-001"
        }

        # ========== 智能巡检模式 ==========
        if media_path:
            media_type = media_type or "monitor"

            # 执行智能分析
            smart_result = _perform_smart_inspection(media_path, media_type)

            if not smart_result.get("success"):
                return json.dumps({
                    "inspection_type": "智能巡检",
                    "success": False,
                    "error": smart_result.get("error"),
                    "media_path": media_path
                }, ensure_ascii=False, indent=2)

            # 合并结果
            result.update({
                "inspection_type": "智能巡检",
                "media_info": {
                    "path": media_path,
                    "type": media_type,
                    "type_name": smart_result["media_type_name"]
                },
                "scene_classification": {
                    "scene_type": smart_result["scene_type"],
                    "scene_name": smart_result["scene_name"],
                    "confidence": smart_result["confidence"]
                },
                "recommended_tools": [
                    {
                        "tool": t["tool"],
                        "reason": t["reason"]
                    }
                    for t in smart_result["recommended_tools"]
                ],
                "suggested_actions": smart_result["next_actions"]
            })

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
