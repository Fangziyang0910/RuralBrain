"""
技能加载工具

包含 load_skill 工具，用于按需加载技能完整内容。
"""
from langchain_core.tools import tool


@tool
def load_skill(skill_name: str) -> str:
    """加载技能的完整内容。

    当需要详细了解如何处理特定类型的请求时，使用此工具获取专业技能的详细工作流程、输出格式和专业要求。

    可用技能：
    - pest_detection: 病虫害检测专家，识别农作物病虫害并提供防治建议
    - rice_detection: 大米品种识别专家，识别大米品种并提供品质分析
    - cow_detection: 牛只检测专家，识别牛只品种和数量，提供养殖管理建议
    - consult_planning_knowledge: 规划咨询专家，查询乡村发展、政策、产业规划等知识库信息
    - pricing_analysis: 定价分析专家，为农产品提供全面的定价因素分析和建议
    - marketing_strategy: 营销策略专家，为农产品提供营销策略、客户分析和品牌推广建议
    - farm_inspection: 农场巡检专家，收集农场数据、分析农田状况、监控养殖状态和设备
    - disease_prediction: 疾病预测专家，分析畜禽疾病症状、预测疾病风险、提供健康评估

    Args:
        skill_name: 要加载的技能名称（必须是上述列表中的一个）

    Returns:
        技能的完整内容（包含详细的工作流程、输出格式和专业要求）
    """
    from ..skills.registry import get_registry
    registry = get_registry()

    try:
        content = registry.load_content(skill_name)
        return f"已加载技能: {skill_name}\n\n{content}"
    except ValueError:
        available = ", ".join(registry.list_skill_names())
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"


__all__ = ["load_skill"]
