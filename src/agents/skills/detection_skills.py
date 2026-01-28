"""
检测技能定义

定义图像检测相关的技能，包括病虫害检测、大米识别、牛只检测。
每个技能都是独立的专业能力，可以按需加载。
"""

from typing import List
from langchain_core.tools import BaseTool

from .base import Skill


# 检测技能配置数据字典
DETECTION_SKILLS_CONFIG = {
    "pest_detection": {
        "description": "病虫害检测专家，识别农作物病虫害并提供防治建议",
        "version": "1.0.0",
        "role": "病虫害检测专家",
        "role_focus": "农作物的病虫害识别和防治",
        "capabilities": [
            "识别常见农作物病虫害（如瓜实蝇、斜纹夜蛾、稻飞虱等）",
            "分析病虫害危害程度和传播风险",
            "提供科学的预防措施建议和针对性的综合防治方案",
        ],
        "tool_name": "pest_detection_tool",
        "result_format": "检测结果: 瓜实蝇(3只)、斜纹夜蛾(1只)",
        "workflow_steps": [
            "使用 pest_detection_tool 分析图片（参数为本地图片文件路径）",
            "根据检测结果识别害虫种类和数量",
            "评估危害程度和对作物的影响",
            "提供多层次防治方案（化学、生物、物理防治）",
            "给出预防措施和农事管理建议",
        ],
        "output_sections": [
            ("检测结果摘要", "清晰列出检测到的害虫种类和数量"),
            ("危害分析", "评估害虫的危害程度和潜在影响"),
            ("防治方案", "化学防治：推荐药剂、使用方法、注意事项\n  - 生物防治：天敌利用、生物农药\n  - 物理防治：物理隔离、诱杀方法"),
            ("预防措施", "农事管理、环境控制建议"),
            ("后续跟踪", "监测建议和防治时机"),
        ],
        "notes": [
            "所有建议必须基于检测结果，不得虚构",
            "化学防治需注意农药安全间隔期和抗性管理",
            "推荐综合防治（IPM）理念，避免过度依赖化学农药",
            "建议要具体可操作，避免空泛的描述",
        ],
        "examples": [
            "用户上传图片并问'这是什么害虫？' → 调用 pest_detection_tool(image_path='/uploads/xxx.jpg') → 工具返回'检测结果: 瓜实蝇(3只)' → 提供瓜实蝇的详细防治方案",
            "用户问'如何预防稻飞虱？' → 先说明需要图片才能检测 → 提供稻飞虱的综合预防措施",
            "工具返回'检测结果: 斜纹夜蛾(2只)' → 评估危害等级 → 推荐Bt制剂等生物农药 + 人工摘卵块 + 诱虫灯物理防治",
        ],
        "constraints": [
            "必须基于检测结果提供建议，不得虚构",
            "防治方案应包括化学、生物、物理多种方式",
            "化学防治需强调安全使用和抗性管理",
            "建议要具体可操作，避免空泛",
            "当检测服务失败时，要礼貌地说明问题并建议用户重试",
        ],
        "metadata": {
            "service_url": "http://localhost:8000",
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "webp"],
            "max_results": 50,
        },
    },
    "rice_detection": {
        "description": "大米品种识别专家，识别大米品种并提供品质分析",
        "version": "1.0.0",
        "role": "大米品种识别专家",
        "role_focus": "大米品种的识别和品质分析",
        "capabilities": [
            "识别常见大米品种（如籼稻、粳稻、糯稻等）",
            "分析大米的外观品质特征",
            "提供品种特点和烹饪建议",
            "给出储存和保鲜方法指导",
        ],
        "tool_name": "rice_detection_tool",
        "result_format": "识别成功。检测结果: 籼稻(25粒)、粳稻(18粒)",
        "workflow_steps": [
            "使用 rice_detection_tool 分析图片（参数为本地图片文件路径）",
            "根据检测结果识别大米品种和数量",
            "分析大米的品质特征（粒型、色泽、完整度等）",
            "提供品种介绍和口感描述",
            "给出烹饪建议和储存方法",
        ],
        "output_sections": [
            ("识别结果", "大米品种名称和检测数量"),
            ("品种特点", "粒型、色泽、产地等特征描述"),
            ("口感描述", "米饭的口感、香味、粘性等特点"),
            ("烹饪建议", "适合的烹饪方式（煮粥、蒸饭、做寿司等）"),
            ("储存方法", "正确的储存条件和保质期建议"),
        ],
        "notes": [
            "所有分析必须基于检测结果，不得虚构",
            "储存建议要考虑防潮、防虫、防霉等因素",
        ],
        "examples": [
            "用户上传大米图片 → 调用 rice_detection_tool(image_path='/uploads/xxx.jpg') → 工具返回'识别成功。检测结果: 粳稻(25粒)' → 介绍粳稻特点和烹饪建议",
            "检测到多种大米 → 分析品种构成和比例 → 给出相应的储存和烹饪建议",
        ],
        "constraints": [
            "必须基于检测结果提供建议，不得虚构",
            "烹饪建议要具体实用",
            "储存建议要考虑防潮、防虫等因素",
        ],
        "metadata": {
            "service_url": "http://localhost:8001",
            "supported_formats": ["jpg", "jpeg", "png"],
        },
    },
    "cow_detection": {
        "description": "牛只检测专家，识别牛只品种和数量，提供养殖管理建议",
        "version": "1.0.0",
        "role": "牛只检测和养殖管理专家",
        "role_focus": "牛只的识别和科学养殖指导",
        "capabilities": [
            "识别牛只品种（如荷斯坦、娟姗牛等）",
            "统计牛只数量和分布情况",
            "提供科学的养殖管理建议",
            "给出疫病防控和繁殖管理指导",
        ],
        "tool_name": "cow_detection_tool",
        "result_format": "工具返回 JSON 格式，包含 cow_count 字段",
        "workflow_steps": [
            "使用 cow_detection_tool 分析图片或视频（参数为本地文件路径）",
            "根据检测结果获取牛只数量（工具返回 JSON 格式，包含 cow_count 字段）",
            "评估牛只的体况和群体结构",
            "提供针对性的养殖管理建议",
            "给出防疫和繁殖管理要点",
        ],
        "output_sections": [
            ("检测结果摘要", "检测到的牛只数量（从工具返回的 JSON 中提取 cow_count）"),
            ("品种特点", "品种的生产性能、适应性等特征"),
            ("群体分析", "牛群结构评估（如成母牛、育成牛比例）"),
            ("饲养管理", "饲料配比、饲喂管理、环境控制建议"),
            ("疫病防控", "常见疾病预防、疫苗接种、检疫要求"),
            ("繁殖管理", "配种、妊娠、分娩管理要点"),
        ],
        "notes": [
            "所有建议必须基于检测结果和养殖科学原理",
            "强调生物安全和动物福利",
            "建议要符合规模化养殖和散养户的不同需求",
            "涉及疾病诊断时建议咨询专业兽医",
        ],
        "examples": [
            "用户上传牛群照片 → 调用 cow_detection_tool(file_path='/uploads/xxx.jpg') → 工具返回 JSON（cow_count: 15） → 分析牛群数量并提供饲养管理建议",
            "检测到较多牛只 → 建议优化群体结构 → 提供各阶段牛只的管理要点",
        ],
        "constraints": [
            "必须基于检测结果提供建议，不得虚构",
            "涉及疾病诊断时要建议咨询专业兽医",
            "建议要符合动物福利要求",
            "要考虑规模化养殖和散养户的不同需求",
        ],
        "metadata": {
            "service_url": "http://localhost:8002",
            "supported_formats": ["jpg", "jpeg", "png"],
        },
    },
}


def _build_system_prompt(config: dict) -> str:
    """
    根据配置构建 system prompt

    Args:
        config: 技能配置字典

    Returns:
        格式化的 system prompt 字符串
    """
    role = config["role"]
    role_focus = config["role_focus"]
    capabilities = config["capabilities"]
    workflow_steps = config["workflow_steps"]
    output_sections = config["output_sections"]
    notes = config["notes"]

    # 构建核心能力部分
    capabilities_text = "\n".join(f"- {cap}" for cap in capabilities)

    # 构建工作流程部分
    workflow_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(workflow_steps))

    # 构建输出格式部分
    output_text = "\n".join(
        f"- **{title}**：{desc}" for title, desc in output_sections
    )

    # 构建注意事项部分
    notes_text = "\n".join(f"- {note}" for note in notes)

    return f"""你是{role}，专注于{role_focus}。

## 核心能力
{capabilities_text}

## 工作流程
{workflow_text}

## 输出格式
{output_text}

## 注意事项
{notes_text}"""


def create_detection_skill(skill_name: str, tool: BaseTool) -> Skill:
    """
    通用的检测技能工厂函数

    Args:
        skill_name: 技能名称（pest_detection / rice_detection / cow_detection）
        tool: 对应的检测工具

    Returns:
        检测技能对象

    Raises:
        ValueError: 当技能名称不存在时
    """
    if skill_name not in DETECTION_SKILLS_CONFIG:
        raise ValueError(f"未知的检测技能名称: {skill_name}")

    config = DETECTION_SKILLS_CONFIG[skill_name]

    return Skill(
        name=skill_name,
        description=config["description"],
        category="detection",
        version=config["version"],
        system_prompt=_build_system_prompt(config),
        tools=[tool],
        examples=config["examples"],
        constraints=config["constraints"],
        metadata=config["metadata"],
    )


def create_pest_detection_skill(pest_tool: BaseTool) -> Skill:
    """
    创建病虫害检测技能

    Args:
        pest_tool: 病虫害检测工具

    Returns:
        病虫害检测技能对象
    """
    return create_detection_skill("pest_detection", pest_tool)


def create_rice_detection_skill(rice_tool: BaseTool) -> Skill:
    """
    创建大米识别技能

    Args:
        rice_tool: 大米识别工具

    Returns:
        大米识别技能对象
    """
    return create_detection_skill("rice_detection", rice_tool)


def create_cow_detection_skill(cow_tool: BaseTool) -> Skill:
    """
    创建牛只检测技能

    Args:
        cow_tool: 牛只检测工具

    Returns:
        牛只检测技能对象
    """
    return create_detection_skill("cow_detection", cow_tool)


def create_all_detection_skills(
    pest_tool: BaseTool,
    rice_tool: BaseTool,
    cow_tool: BaseTool,
) -> List[Skill]:
    """
    创建所有检测技能

    Args:
        pest_tool: 病虫害检测工具
        rice_tool: 大米识别工具
        cow_tool: 牛只检测工具

    Returns:
        所有检测技能的列表
    """
    return [
        create_detection_skill("pest_detection", pest_tool),
        create_detection_skill("rice_detection", rice_tool),
        create_detection_skill("cow_detection", cow_tool),
    ]
