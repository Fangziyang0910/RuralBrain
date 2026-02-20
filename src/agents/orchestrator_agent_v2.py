"""
统一编排 Agent V2 (Orchestrator Agent V2)

采用 LangChain Skills 架构模式：
1. Progressive Disclosure：只在系统提示词中包含技能简短描述
2. 按需加载：通过 load_skill 工具获取技能完整内容
3. 技能组织：检测技能、规划技能、编排技能
4. 中间件支持：SkillMiddleware（支持动态工具注册）

使用场景：
- 纯检测：识别病虫害、农作物品种、牛只等
- 纯规划：乡村发展规划、政策咨询、产业建议
- 先检测后规划：识别问题后提供解决方案
- 规划中需要检测：规划过程中需要识别资源
"""
import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from ..utils import ModelManager
from .tools import (
    pest_detection_tool,
    rice_detection_tool,
    cow_detection_tool,
    pricing_tool,
    marketing_tool,
    farm_inspection_tool,
    disease_prediction_tool,
    load_skill,
)
from .tools.planning_service_tool import planning_consult
from .skills.registry import get_registry
from .middleware.skill_middleware import SkillMiddleware
from langchain.agents.middleware import SummarizationMiddleware

logger = logging.getLogger(__name__)

# ========== 初始化模型 ==========

model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()


# ========== 技能组织 ==========

# 获取技能注册中心
registry = get_registry()


# ========== 工具收集 ==========

# 收集所有工具（检测3 + 定价1 + 营销1 + 巡检1 + 疾病预测1 + 规划1 + 技能加载1 = 9个工具）
orchestrator_tools = [
    # 检测工具
    pest_detection_tool,
    rice_detection_tool,
    cow_detection_tool,
    # 定价和营销工具
    pricing_tool,
    marketing_tool,
    # 巡检工具
    farm_inspection_tool,
    # 疾病预测工具
    disease_prediction_tool,
    # 规划咨询工具（通过 HTTP 调用独立 RAG 服务）
    planning_consult,
    # 技能加载工具
    load_skill,
]


# ========== 系统提示词 ==========

ORCHESTRATOR_V2_SYSTEM_PROMPT = """<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
你拥有五大核心能力：图像检测、规划咨询、智能定价、精准营销和农场巡检。
</role>

<capabilities>
- **检测能力**：病虫害检测、大米品种识别、牛只检测
- **规划能力**：乡村发展规划、政策解读、技术指导
- **定价能力**：农产品定价、市场分析、价格优化
- **营销能力**：营销策略、客户分析、品牌推广、销量提升
- **巡检能力**：农场数据收集、农田状况、养殖状态、设备监控
- **疾病预测能力**：畜禽疾病预测、症状分析、健康评估
</capabilities>

<task_context>
## 任务背景和工作流程

你必须遵循"技能优先"的工作流程，确保提供专业、准确的分析：

### 第一步：识别用户意图
分析用户的需求类型：检测、规划、定价、营销、巡检、疾病预测

### 第二步：加载专业技能（必需）
根据用户意图，**必须先使用** load_skill 工具加载对应技能的详细指导：
- 上传图片识别害虫 → load_skill("pest_detection")
- 上传图片识别大米品种 → load_skill("rice_detection")
- 上传图片检测牛只 → load_skill("cow_detection")
- 询问规划/发展/政策 → load_skill("consult_planning_knowledge")
- 询问定价/价格 → load_skill("pricing_analysis")
- 询问营销/销售 → load_skill("marketing_strategy")
- 询问农场/农田/养殖 → load_skill("farm_inspection")
- 询问疾病/症状 → load_skill("disease_prediction")

### 第三步：执行专业技能
根据技能指导调用相应的工具，并按照技能中定义的输出格式提供专业分析

**重要**：不要跳过技能加载直接调用工具。技能包含了专业的工作流程、输出格式和质量要求，是提供专业服务的基础。
</task_context>

<workflow>
## 标准工作流程总结

1. **识别意图** → 分析用户需求类型
2. **加载技能** → 调用 load_skill 获取专业指导
3. **调用工具** → 根据技能指导使用相应工具
4. **专业输出** → 按技能定义的格式提供分析结果
</workflow>

<output_guidance>
## 输出内容要求

- 基于工具结果提供准确、有用的信息
- 当知识库无结果时，诚实告知用户
- 分析和建议要清晰、具体、可操作
- 可以自由组织回答的表达方式，无需遵循特定格式
</output_guidance>

<examples>
### 示例场景（展示完整工作流程）

**用户上传图片检测害虫：**
用户: "这是什么害虫？" + 图片
→ 1. 调用 load_skill("pest_detection") 获取病虫害检测的专业指导
→ 2. 根据技能指导，调用 pest_detection_tool(image_path="...") 进行检测
→ 3. 按照技能定义的输出格式，提供检测结果摘要、危害分析、防治方案和预防措施

**用户询问规划问题：**
用户: "长宁镇发展前景如何？"
→ 1. 调用 load_skill("consult_planning_knowledge") 获取规划咨询的专业指导
→ 2. 根据技能指导选择合适的 RAG 工具查询知识库
→ 3. 按照技能定义的输出格式，提供核心建议、政策依据、参考案例和实施要点

**用户询问定价问题：**
用户: "我的一等有机大米成本3.5元/斤，应该卖多少钱？"
→ 1. 调用 load_skill("pricing_analysis") 获取定价分析的专业指导
→ 2. 根据技能指导，调用 pricing_tool(...) 获取定价分析报告
→ 3. 按照技能定义的输出格式，提供定价建议、分析依据、关键因素、竞争优势和风险提示
"""


# ========== 中间件配置 ==========

# 技能中间件：实现 Progressive Disclosure，直接使用注册中心
skill_middleware = SkillMiddleware(registry=registry)

# 总结中间件：长对话历史自动总结（LangChain 官方推荐最佳实践）
summarization_middleware = SummarizationMiddleware(
    # 使用与主模型一致的配置进行总结
    model=model_manager.get_chat_model(),
    # 触发条件: 当对话超过 8000 tokens 时自动触发
    trigger=("tokens", 8000),
    # 保留策略: 保留最近的 15 条消息,对更早的消息进行总结
    keep=("messages", 15),
)

# 中间件列表
middleware = [skill_middleware, summarization_middleware]


# ========== 创建 Agent ==========

agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
)

skill_count = len(registry.list_skill_names())
logger.info(
    f"✓ 统一编排 Agent V2 (Orchestrator V2) 创建成功 - "
    f"采用 Skills 架构，技能数量: {skill_count}, 工具数量: {len(orchestrator_tools)}"
)

__all__ = ["agent", "registry", "orchestrator_tools"]
