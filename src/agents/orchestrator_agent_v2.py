"""
统一编排 Agent V2 - Skills 架构

采用 Progressive Disclosure：只在提示词中包含技能简述，按需加载完整内容。
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

# ---- 初始化 ----

model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()
registry = get_registry()

# ---- 工具 ----

orchestrator_tools = [
    pest_detection_tool,
    rice_detection_tool,
    cow_detection_tool,
    pricing_tool,
    marketing_tool,
    farm_inspection_tool,
    disease_prediction_tool,
    planning_consult,
    load_skill,
]

# ---- 系统提示词 ----

ORCHESTRATOR_V2_SYSTEM_PROMPT = """<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
</role>

<capabilities>
**检测**: 病虫害、大米品种、牛只
**规划**: 发展规划、政策解读、技术指导
**定价**: 农产品定价、市场分析
**营销**: 营销策略、客户分析、品牌推广
**巡检**: 农场数据、农田状况、养殖监控
**疾病预测**: 症状分析、健康评估
</capabilities>

<workflow>
## 工作流程（必须遵守）

**第一步：识别意图** - 分析用户需求类型：检测/规划/定价/营销/巡检/疾病预测

**第二步：加载技能（必需）** - 先调用 load_skill 获取专业指导：
- 检测害虫 → load_skill("pest_detection")
- 识别大米 → load_skill("rice_detection")
- 检测牛只 → load_skill("cow_detection")
- 规划咨询 → load_skill("consult_planning_knowledge")
- 定价分析 → load_skill("pricing_analysis")
- 营销策略 → load_skill("marketing_strategy")
- 农场巡检 → load_skill("farm_inspection")
- 疾病预测 → load_skill("disease_prediction")

**第三步：调用工具** - 根据技能指导使用相应工具

**第四步：专业输出** - 按技能定义的格式提供分析结果

**重要**：跳过技能加载会导致分析质量下降。
</workflow>

<output_guidance>
## 输出要求

- 基于工具结果提供准确信息
- 知识库无结果时诚实告知
- 分析建议要清晰、具体、可操作
</output_guidance>

<examples>
### 示例

**检测害虫**（用户上传图片）:
1. load_skill("pest_detection")
2. pest_detection_tool(image_path="...")
3. 输出：检测结果、危害分析、防治方案

**规划咨询**（用户询问发展前景）:
1. load_skill("consult_planning_knowledge")
2. 调用 RAG 工具查询知识库
3. 输出：核心建议、政策依据、实施要点

**定价分析**（用户询问定价）:
1. load_skill("pricing_analysis")
2. pricing_tool(...)
3. 输出：定价建议、分析依据、关键因素
"""


# ---- 中间件 ----

skill_middleware = SkillMiddleware(registry=registry)

summarization_middleware = SummarizationMiddleware(
    model=model_manager.get_chat_model(),
    trigger=("tokens", 8000),
    keep=("messages", 15),
)

middleware = [skill_middleware, summarization_middleware]

# ---- 创建 Agent ----

agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
)

skill_count = len(registry.list_skill_names())
logger.info(
    f"✓ Agent V2 创建成功 - 技能: {skill_count}, 工具: {len(orchestrator_tools)}"
)

__all__ = ["agent", "registry", "orchestrator_tools"]
