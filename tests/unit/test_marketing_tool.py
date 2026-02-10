"""
营销工具单元测试

测试营销工具的基本功能。
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.tools.marketing_tool import marketing_tool


class TestMarketingTool:
    """测试营销工具"""

    def test_basic_marketing(self):
        """测试基础营销分析"""
        result = marketing_tool.invoke({
            "product_name": "有机大米",
            "product_category": "粮食",
            "target_customers": "城市白领",
            "marketing_goal": "品牌推广"
        })

        assert "有机大米" in result
        assert "营销策略分析报告" in result
        assert "客户画像分析" in result
        assert "营销策略建议" in result

    def test_marketing_with_budget(self):
        """测试带预算的营销分析"""
        result = marketing_tool.invoke({
            "product_name": "有机大米",
            "product_category": "粮食",
            "target_customers": "城市白领",
            "marketing_goal": "销量提升",
            "budget_range": "5000-10000元"
        })

        assert "预算" in result
        assert "预算分配" in result
        assert "5000-10000元" in result

    def test_marketing_with_customer_data(self):
        """测试带客户数据的营销分析"""
        customer_data = '{"age_range": "25-45岁", "income_level": "中高收入"}'

        result = marketing_tool.invoke({
            "product_name": "有机蔬菜",
            "product_category": "蔬菜",
            "target_customers": "注重健康的家庭",
            "marketing_goal": "客户获取",
            "customer_data": customer_data
        })

        assert "25-45岁" in result
        assert "中高收入" in result
        assert "有机蔬菜" in result

    def test_different_marketing_goals(self):
        """测试不同营销目标"""
        goals = ["品牌推广", "销量提升", "客户获取", "复购提升"]

        for goal in goals:
            result = marketing_tool.invoke({
                "product_name": "红富士苹果",
                "product_category": "水果",
                "target_customers": "家庭消费者",
                "marketing_goal": goal
            })

            assert goal in result, f"营销目标 '{goal}' 应该在结果中"
            assert "红富士苹果" in result

    def test_different_product_categories(self):
        """测试不同产品类别"""
        categories = ["粮食", "蔬菜", "水果", "畜牧", "水产"]

        for category in categories:
            result = marketing_tool.invoke({
                "product_name": "测试产品",
                "product_category": category,
                "target_customers": "普通消费者",
                "marketing_goal": "销量提升"
            })

            assert category in result
            assert "营销策略" in result

    def test_rural_marketing_features(self):
        """测试乡村营销特色"""
        result = marketing_tool.invoke({
            "product_name": "土鸡蛋",
            "product_category": "畜牧",
            "target_customers": "城市家庭",
            "marketing_goal": "品牌推广"
        })

        # 检查是否包含乡村营销特色
        assert "乡村营销特色" in result
        assert "信任营销" in result or "故事营销" in result

    def test_error_handling_invalid_json(self):
        """测试无效 JSON 的错误处理"""
        result = marketing_tool.invoke({
            "product_name": "有机大米",
            "product_category": "粮食",
            "target_customers": "城市白领",
            "marketing_goal": "销量提升",
            "customer_data": "{invalid json}"
        })

        # 应该优雅处理错误，仍然返回结果
        assert "有机大米" in result
        assert "营销策略分析报告" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
