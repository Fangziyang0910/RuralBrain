"""智能定价工具单元测试"""
import pytest
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.tools.pricing_tool import pricing_tool


class TestPricingTool:
    """测试定价工具"""

    def test_basic_pricing(self):
        """测试基础定价功能"""
        result = pricing_tool.invoke({
            "product_name": "有机大米",
            "product_category": "粮食",
            "cost_price": 3.5,
            "quality_grade": "一等"
        })

        assert result is not None
        assert "有机大米" in result
        assert "定价因素分析报告" in result
        assert "¥" in result
        assert "成本价格" in result

    def test_pricing_with_market_data(self):
        """测试带市场数据的定价"""
        market_data = {
            "supply_level": "充足",
            "demand_level": "旺盛",
            "seasonality": "旺季",
            "competitor_price_range": [4.0, 6.0]
        }

        result = pricing_tool.invoke({
            "product_name": "夏季荔枝",
            "product_category": "水果",
            "cost_price": 2.0,
            "quality_grade": "一等",
            "market_data": json.dumps(market_data)
        })

        assert "夏季荔枝" in result
        assert "市场状况分析" in result
        assert "竞争状况分析" in result

    def test_different_quality_grades(self):
        """测试不同品质等级"""
        qualities = ["优等", "一等", "中等", "三等"]

        for quality in qualities:
            result = pricing_tool.invoke({
                "product_name": "苹果",
                "product_category": "水果",
                "cost_price": 3.0,
                "quality_grade": quality
            })

            assert "苹果" in result
            assert quality in result

    def test_error_handling_invalid_json(self):
        """测试无效 JSON 的错误处理"""
        result = pricing_tool.invoke({
            "product_name": "测试产品",
            "product_category": "粮食",
            "cost_price": 2.0,
            "quality_grade": "一等",
            "market_data": "invalid json"
        })

        # 应该返回错误信息或使用默认分析
        assert result is not None

    def test_premium_pricing(self):
        """测试溢价定价策略（优等品质）"""
        result = pricing_tool.invoke({
            "product_name": "有机大米",
            "product_category": "粮食",
            "cost_price": 5.0,
            "quality_grade": "优等"
        })

        assert "优等" in result
        assert "溢价" in result or "高溢价" in result

    def test_cost_oriented_low_cost(self):
        """测试低成本产品的成本导向定价"""
        result = pricing_tool.invoke({
            "product_name": "普通小麦",
            "product_category": "粮食",
            "cost_price": 1.5,
            "quality_grade": "中等"
        })

        assert "普通小麦" in result
        assert "1.5" in result or "1.50" in result

    def test_competition_pricing(self):
        """测试竞争导向定价"""
        market_data = {
            "competitor_price_range": [4.0, 6.0]
        }

        result = pricing_tool.invoke({
            "product_name": "苹果",
            "product_category": "水果",
            "cost_price": 3.0,
            "quality_grade": "一等",
            "market_data": json.dumps(market_data)
        })

        assert "竞争" in result
        assert "竞争对手" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
