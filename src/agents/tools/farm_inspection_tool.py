"""农场巡检工具：收集与整理农场各类信息数据。

对农田、养殖圈、设施设备等进行信息收集与整理，生成结构化数据，
为 Agent 的 LLM 提供充分的决策依据。
"""
import json
from typing import Optional, List
from datetime import datetime
from langchain_core.tools import tool


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
    # iot_client = connect_iot_platform(farm_id)
    # sensor_data = iot_client.get_sensor_data(area_type)
    # return sensor_data
    pass


def _generate_mock_farm_data(farm_id: Optional[str] = None, inspection_scope: Optional[str] = None) -> dict:
    """生成模拟农场巡检数据（临时占位实现）

    后续会被真实数据采集系统替换，这里只是占位实现。
    """
    farm_id = farm_id or "FARM-001"

    # 根据巡检范围返回相应数据
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
                "area": 50,  # 亩
                "crop": "水稻",
                "growth_stage": "分蘖期",
                "planting_date": "2024-05-15",
                "soil_moisture": 65,  # %
                "soil_ph": 6.5,
                "temperature": 28,  # °C
                "humidity": 75,  # %
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
                "temperature": 22,  # 舍内温度
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
            },
            {
                "id": "LS-003",
                "name": "鸡舍A",
                "animal_type": "鸡",
                "count": 500,
                "capacity": 500,
                "health_status": "正常",
                "temperature": 25,
                "humidity": 60,
                "ventilation": "良好",
                "feed_stock": {
                    "forage": "充足（约1天）",
                    "concentrate": "充足（约3天）",
                    "water": "正常"
                },
                "equipment_status": {
                    "feeding_system": "自动运行中",
                    "ventilation_fans": "运行中",
                    "water_dispensers": "正常",
                    "egg_collector": "运行中"
                },
                "abnormal_count": 0,
                "recent_health_records": []
            }
        ]

    # 温室大棚信息
    if scope in ["all", "greenhouse"]:
        result["data"]["greenhouses"] = [
            {
                "id": "GH-001",
                "name": "1号蔬菜大棚",
                "crop": "番茄",
                "area": 2000,  # 平方米
                "growth_stage": "结果期",
                "planting_date": "2024-04-10",
                "temperature": 26,
                "humidity": 75,
                "co2_level": 450,  # ppm
                "light_intensity": 85,  # %
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


@tool
def farm_inspection_tool(
    farm_id: Optional[str] = None,
    inspection_scope: Optional[str] = None,
    area_ids: Optional[List[str]] = None
) -> str:
    """收集农场巡检数据，生成结构化信息。

    对农田、养殖圈、设施设备等信息进行采集与整理，为决策提供数据支持。

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

    Returns:
        JSON格式的结构化数据，包含：
        - farmlands: 农田信息（作物长势、土壤墒情、病虫害等）
        - livestock: 养殖圈信息（数量、健康状态、环境参数等）
        - greenhouses: 温室信息（环境参数、设备状态等）
        - equipment: 设施设备状态
        - operations: 人员与作业记录
    """
    try:
        # TODO: 后续切换到真实数据采集
        # result = _collect_actual_sensor_data(farm_id, inspection_scope)

        # 当前使用模拟数据
        result = _generate_mock_farm_data(farm_id, inspection_scope)

        # 如果指定了区域ID，过滤数据
        if area_ids:
            filtered_data = {}

            for category, items in result["data"].items():
                if isinstance(items, list):
                    filtered_items = [item for item in items if item.get("id") in area_ids]
                    if filtered_items:
                        filtered_data[category] = filtered_items
                else:
                    filtered_data[category] = items

            result["data"] = filtered_data
            result["filtered"] = True
            result["requested_area_ids"] = area_ids

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


if __name__ == "__main__":
    # 测试工具
    test_cases = [
        {"inspection_scope": "farmland"},
        {"inspection_scope": "livestock"},
        {"inspection_scope": "all", "area_ids": ["FL-001", "LS-001"]},
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n=== 测试用例 {i} ===")
        result = farm_inspection_tool.invoke(case)
        print(result)


# 为工具添加标签，供 ToolSelectorMiddleware 使用
farm_inspection_tool.tags = ["inspection", "farm", "monitoring"]
