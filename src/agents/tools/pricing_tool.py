"""
智能定价工具：为农产品定价提供结构化的市场分析信息。

该工具收集和整理产品成本、品质、市场等信息，为 Agent 的 LLM
提供充分的决策依据，让 LLM 自己进行定价分析和推理。
"""
import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def pricing_tool(
    product_name: str,
    product_category: str,
    cost_price: float,
    quality_grade: str = "中等",
    market_data: Optional[str] = None
) -> str:
    """
    分析农产品定价的影响因素，为定价决策提供信息支持。

    该工具会收集和整理以下信息：
    - 产品基本信息（名称、分类、成本、品质）
    - 成本结构和利润空间分析
    - 市场供需状况
    - 竞争对手价格参考
    - 季节性因素影响
    - 品质溢价空间

    **工具的作用：**
    该工具不直接给出定价建议，而是整理和分析影响定价的各种因素，
    让 Agent 的 LLM 基于这些信息进行专业的定价分析和推理。

    **参数说明：**
    - product_name: 农产品名称，如"有机大米"、"红富士苹果"
    - product_category: 产品分类（粮食/蔬菜/水果/畜牧/水产）
    - cost_price: 成本价格（元/斤或元/公斤），必须 >= 0
    - quality_grade: 品质等级（优等/一等/中等/三等），默认"中等"
    - market_data: 可选的市场数据 JSON 字符串，包含供需、竞争、季节等信息

    **市场数据格式（JSON）：**
    ```json
    {
      "supply_level": "充足|紧张|一般",
      "demand_level": "旺盛|疲软|一般",
      "seasonality": "旺季|淡季|平稳",
      "competitor_price_range": [最低价, 最高价],
      "market_trend": "上涨|下跌|稳定"
    }
    ```

    **返回信息：**
    返回结构化的定价因素分析报告，包含：
    - 成本分析（基础成本、品质加成空间）
    - 市场分析（供需状况、价格趋势）
    - 竞争分析（竞争对手价格区间）
    - 品质分析（品质等级对应的溢价能力）
    - 季节性分析（当前季节对价格的影响）
    - 建议的定价策略方向

    **使用示例：**
    >>> analyze_pricing_factors("有机大米", "粮食", 3.5, "一等")
    返回：详细的因素分析报告

    >>> analyze_pricing_factors(
    ...     "夏季荔枝", "水果", 2.0, "一等",
    ...     market_data='{"supply_level": "充足", "demand_level": "旺盛", "seasonality": "旺季"}'
    ... )
    返回：包含旺季供需分析的详细报告

    Args:
        product_name: 产品名称
        product_category: 产品分类
        cost_price: 成本价格
        quality_grade: 品质等级，默认"中等"
        market_data: 市场数据 JSON 字符串（可选）

    Returns:
        结构化的定价因素分析报告
    """
    try:
        logger.info(f"分析定价因素: {product_name} (成本: ¥{cost_price}, 品质: {quality_grade})")

        # 解析市场数据
        parsed_market_data = None
        if market_data:
            try:
                parsed_market_data = json.loads(market_data)
            except json.JSONDecodeError:
                logger.warning(f"市场数据 JSON 解析失败，将使用默认分析: {market_data}")
                parsed_market_data = None

        # ========== 成本分析 ==========
        cost_analysis = []
        cost_analysis.append(f"**基础成本分析**")
        cost_analysis.append(f"- 成本价格: ¥{cost_price:.2f}")
        cost_analysis.append(f"- 品质等级: {quality_grade}")

        # 品质溢价空间
        quality_premium = {
            "优等": (0.50, 0.80, "高溢价空间"),
            "一等": (0.40, 0.60, "中高溢价空间"),
            "中等": (0.30, 0.50, "中等溢价空间"),
            "三等": (0.20, 0.35, "有限溢价空间")
        }
        premium_min, premium_max, premium_desc = quality_premium.get(quality_grade, (0.30, 0.50, "中等溢价空间"))
        price_min = cost_price * (1 + premium_min)
        price_max = cost_price * (1 + premium_max)

        cost_analysis.append(f"- 品质溢价能力: {premium_desc}")
        cost_analysis.append(f"- 建议价格区间: ¥{price_min:.2f} - ¥{price_max:.2f}")
        cost_analysis.append(f"- 最低保本价（20%利润率）: ¥{cost_price * 1.2:.2f}")

        # ========== 市场分析 ==========
        market_analysis = []
        market_analysis.append(f"**市场状况分析**")

        if parsed_market_data:
            if "supply_level" in parsed_market_data:
                supply = parsed_market_data["supply_level"]
                supply_impact = {
                    "充足": "供应充足，价格上行压力大",
                    "紧张": "供应紧张，价格上涨空间大",
                    "一般": "供应正常，价格相对稳定"
                }
                market_analysis.append(f"- 供应状况: {supply} - {supply_impact.get(supply, '')}")

            if "demand_level" in parsed_market_data:
                demand = parsed_market_data["demand_level"]
                demand_impact = {
                    "旺盛": "需求旺盛，可适当提价",
                    "疲软": "需求疲软，建议保持竞争力",
                    "一般": "需求正常，按常规定价"
                }
                market_analysis.append(f"- 需求状况: {demand} - {demand_impact.get(demand, '')}")

            if "market_trend" in parsed_market_data:
                trend = parsed_market_data["market_trend"]
                trend_advice = {
                    "上涨": "价格上涨趋势中，建议略高于常规定价",
                    "下跌": "价格下跌趋势中，建议保持竞争力",
                    "稳定": "价格稳定，按常规策略定价"
                }
                market_analysis.append(f"- 价格趋势: {trend} - {trend_advice.get(trend, '')}")

            if "seasonality" in parsed_market_data:
                season = parsed_market_data["seasonality"]
                season_impact = {
                    "旺季": "旺季需求大，价格可适当上调",
                    "淡季": "淡季需求弱，建议保持低价促销",
                    "平稳": "季节性不明显，按常规定价"
                }
                market_analysis.append(f"- 季节性: {season} - {season_impact.get(season, '')}")
        else:
            market_analysis.append("- 市场数据: 未提供具体市场数据，建议根据实际情况分析")
            market_analysis.append("- 建议: 收集市场供需、竞争、季节性信息以获得更准确的分析")

        # ========== 竞争分析 ==========
        competition_analysis = []
        competition_analysis.append(f"**竞争状况分析**")

        if parsed_market_data and "competitor_price_range" in parsed_market_data:
            comp_min, comp_max = parsed_market_data["competitor_price_range"]
            competition_analysis.append(f"- 竞争对手价格区间: ¥{comp_min:.2f} - ¥{comp_max:.2f}")
            competition_analysis.append(f"- 市场平均价: ¥{((comp_min + comp_max) / 2):.2f}")

            # 竞争定位建议
            if cost_price < comp_min:
                competition_analysis.append(f"- 成本优势明显，可选择低价策略或品质溢价")
            elif cost_price > comp_max:
                competition_analysis.append(f"- 成本较高，必须强调品质差异化，采用溢价定价")
            else:
                competition_analysis.append(f"- 成本处于竞争区间，可通过品质和差异化定位")
        else:
            competition_analysis.append("- 竞争对手价格: 未提供，建议调研市场价格")
            competition_analysis.append("- 定价策略: 可参考品质和成本选择合适定位")

        # ========== 定价策略建议 ==========
        strategy_analysis = []
        strategy_analysis.append(f"**定价策略建议**")

        # 根据品质和成本推荐策略
        if quality_grade in ["优等", "一等"]:
            strategy_analysis.append("- 推荐策略: 溢价定价或差异化定价")
            strategy_analysis.append(f"  理由: {quality_grade}品质具备溢价能力")
            strategy_analysis.append(f"  建议价格: ¥{price_max * 0.85:.2f} - ¥{price_max:.2f}（中高端定位）")
        elif cost_price < 5.0:
            strategy_analysis.append("- 推荐策略: 成本导向或市场导向")
            strategy_analysis.append("  理由: 成本较低，可通过合理定价获得销量优势")
            strategy_analysis.append(f"  建议价格: ¥{cost_price * 1.3:.2f} - ¥{cost_price * 1.5:.2f}（性价比定位）")
        else:
            strategy_analysis.append("- 推荐策略: 竞争导向或品质导向")
            strategy_analysis.append("  理由: 成本较高，需要通过品质或差异化提升竞争力")
            strategy_analysis.append(f"  建议价格: ¥{cost_price * 1.4:.2f} - ¥{cost_price * 1.6:.2f}（中端定位）")

        # ========== 组装完整报告 ==========
        report_sections = []
        report_sections.append(f"【定价因素分析报告】")
        report_sections.append(f"产品: {product_name} | 分类: {product_category}")
        report_sections.append(f"")

        report_sections.extend(cost_analysis)
        report_sections.append(f"")
        report_sections.extend(market_analysis)
        report_sections.append(f"")
        report_sections.extend(competition_analysis)
        report_sections.append(f"")
        report_sections.extend(strategy_analysis)
        report_sections.append(f"")

        report_sections.append(f"**综合建议**")
        report_sections.append(f"基于以上分析，建议综合考虑以下因素进行定价决策：")
        report_sections.append(f"1. 成本基础: ¥{cost_price:.2f}，确保合理利润空间")
        report_sections.append(f"2. 品质定位: {quality_grade}品质，{premium_desc}")
        report_sections.append(f"3. 市场状况: 根据供需和季节性调整")
        report_sections.append(f"4. 竞争策略: 参考市场定位，选择合适的价格区间")
        report_sections.append(f"5. 风险提示: 密切关注市场变化，适时调整价格")

        final_report = "\n".join(report_sections)

        logger.info(f"定价因素分析完成: {product_name}")
        return final_report

    except Exception as e:
        error_msg = f"定价因素分析失败: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# 为工具添加标签，供中间件使用
pricing_tool.tags = ["pricing", "analysis", "market"]

# 导出
__all__ = ["pricing_tool"]
