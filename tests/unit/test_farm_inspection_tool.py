"""农场巡检工具单元测试"""
import pytest
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.tools.farm_inspection_tool import farm_inspection_tool


class TestFarmInspectionTool:
    """测试农场巡检工具"""

    def test_inspect_all(self):
        """测试全范围巡检"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "all"
        })

        data = json.loads(result)
        assert "farm_id" in data
        assert "inspection_time" in data
        assert "data" in data

        # 全范围应包含所有数据类型
        assert "farmlands" in data["data"]
        assert "livestock" in data["data"]
        assert "greenhouses" in data["data"]
        assert "equipment" in data["data"]
        assert "operations" in data["data"]

    def test_inspect_farmland_only(self):
        """测试仅巡检农田"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "farmland"
        })

        data = json.loads(result)
        assert "farmlands" in data["data"]

        # 验证农田数据结构
        farmland = data["data"]["farmlands"][0]
        assert "id" in farmland
        assert "name" in farmland
        assert "crop" in farmland
        assert "soil_moisture" in farmland
        assert "pest_status" in farmland

    def test_inspect_livestock_only(self):
        """测试仅巡检养殖圈"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "livestock"
        })

        data = json.loads(result)
        assert "livestock" in data["data"]

        # 验证养殖圈数据结构
        livestock = data["data"]["livestock"][0]
        assert "id" in livestock
        assert "animal_type" in livestock
        assert "count" in livestock
        assert "health_status" in livestock
        assert "feed_stock" in livestock

    def test_filter_by_area_ids(self):
        """测试按区域ID过滤"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "all",
            "area_ids": ["FL-001", "LS-001"]
        })

        data = json.loads(result)
        assert data.get("filtered") == True
        assert "requested_area_ids" in data

        # 验证返回的数据只包含指定ID
        farmlands = data["data"].get("farmlands", [])
        if farmlands:
            assert all(f["id"] in ["FL-001"] for f in farmlands)

        livestock = data["data"].get("livestock", [])
        if livestock:
            assert all(l["id"] in ["LS-001"] for l in livestock)

    def test_custom_farm_id(self):
        """测试自定义农场ID"""
        result = farm_inspection_tool.invoke({
            "farm_id": "FARM-999",
            "inspection_scope": "equipment"
        })

        data = json.loads(result)
        assert data["farm_id"] == "FARM-999"

    def test_equipment_status(self):
        """测试设备状态数据"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "equipment"
        })

        data = json.loads(result)
        equipment = data["data"]["equipment"]
        assert "power_supply" in equipment
        assert "water_supply" in equipment
        assert "network_status" in equipment
        assert "alerts" in equipment

    def test_operations_data(self):
        """测试作业记录数据"""
        result = farm_inspection_tool.invoke({
            "inspection_scope": "operations"
        })

        data = json.loads(result)
        operations = data["data"]["operations"]
        assert "staff_on_duty" in operations
        assert "ongoing_tasks" in operations
        assert "recent_activities" in operations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
