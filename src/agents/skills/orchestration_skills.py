"""
编排技能定义

定义智能路由和场景切换相关的技能。
"""
from typing import List
from langchain_core.tools import BaseTool
from .base import Skill


def create_intent_recognition_skill() -> Skill:
    """
    意图识别技能

    功能：
    - 识别用户意图类型（检测/规划/混合）
    - 根据关键词和上下文判断场景
    - 引导 Agent 使用合适的工具/技能
    """
    return Skill(
        name="intent_recognition",
        description="意图识别专家，判断用户需要检测服务还是规划咨询",
        category="orchestration",
        version="1.0.0",
        system_prompt="""你是意图识别专家，负责分析用户输入并判断用户意图类型。

## 核心能力
- 识别检测意图：图片、识别、检测、是什么等
- 识别规划意图：规划、发展、政策、如何、策略等
- 识别混合意图：检测后咨询、规划中需要检测

## 判断流程
1. **检查是否包含图片**：有图片 → 优先检测意图
2. **关键词分析**：
   - 检测关键词：检测、识别、品种、害虫、是什么、这是什么
   - 规划关键词：规划、发展、政策、如何、策略、防治、方案、建议
3. **上下文分析**：结合对话历史判断场景转换
4. **意图分类**：
   - pure_detection：纯检测
   - pure_planning：纯规划
   - detection_then_planning：先检测后规划
   - planning_with_detection：规划中需要检测

## 输出格式
- 意图类型：明确标识
- 推荐技能：列出应该使用的技能名称
- 置信度：高/中/低
""",
        tools=[],  # 不绑定具体工具，仅提供指导
        examples=[
            "用户上传图片 + '这是什么？' → 意图：pure_detection → 推荐：pest_detection/rice_detection/cow_detection",
            "用户问'如何发展旅游？' → 意图：pure_planning → 推荐：consult_planning_knowledge",
            "用户先问'识别病虫害'，再问'如何防治？' → 意图：detection_then_planning → 场景切换",
        ],
        constraints=[
            "必须基于用户输入和上下文判断",
            "不执行实际检测或规划，仅提供意图分析",
            "考虑多轮对话的上下文连续性",
        ],
    )


def create_scenario_switching_skill() -> Skill:
    """
    场景切换技能

    功能：
    - 管理检测和规划之间的场景切换
    - 维护对话上下文连续性
    - 提供场景转换的平滑过渡
    """
    return Skill(
        name="scenario_switching",
        description="场景切换专家，管理检测和规划场景的平滑转换",
        category="orchestration",
        version="1.0.0",
        system_prompt="""你是场景切换专家，负责管理多轮对话中的场景转换。

## 核心能力
- 检测场景切换时机
- 保持上下文连续性
- 提供平滑的过渡引导
- 避免突兀的场景跳跃

## 常见场景转换模式
1. **检测 → 规划**：
   - 用户先识别病虫害，再询问防治方法
   - 策略：先完成检测，再基于检测结果调用规划技能

2. **规划 → 检测**：
   - 用户在规划咨询中需要识别资源
   - 策略：暂停规划，执行检测，再继续规划

3. **混合场景**：
   - 单轮对话中同时需要检测和规划
   - 策略：分步执行，明确说明步骤

## 输出格式
- 当前场景：标识当前处于哪个场景
- 切换建议：是否需要切换场景
- 过渡语句：提供自然的过渡表达
- 上下文摘要：总结之前对话的关键信息
""",
        tools=[],
        examples=[
            "场景1：用户问'这是什么害虫？' → 场景：detection → 执行检测",
            "场景2：用户追问'有什么生物防治方法？' → 场景切换：detection → planning → 过渡：'根据刚才的检测结果，我来查询生物防治方法'",
        ],
        constraints=[
            "必须保持对话上下文连续性",
            "避免突兀的场景切换",
            "清晰说明当前所处的场景",
        ],
    )


def create_all_orchestration_skills() -> List[Skill]:
    """
    创建所有编排技能

    Returns:
        所有编排技能列表
    """
    return [
        create_intent_recognition_skill(),
        create_scenario_switching_skill(),
    ]
