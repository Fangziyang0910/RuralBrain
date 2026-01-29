"""
统一编排 Agent V2 (Orchestrator Agent V2)

采用 LangChain Skills 架构模式：
1. Progressive Disclosure：只在系统提示词中包含技能简短描述
2. 按需加载：通过 load_skill 工具获取技能完整内容
3. 技能组织：检测技能、规划技能、编排技能
4. 中间件支持：SkillMiddleware

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
from .tools import pest_detection_tool, rice_detection_tool, cow_detection_tool, pricing_tool, farm_inspection_tool
from src.rag.core.tools import PLANNING_TOOLS
from .skills.detection_skills import create_all_detection_skills
from .skills.planning_skills import create_all_planning_skills
from .skills.pricing_skills import create_all_pricing_skills
from .skills.farm_inspection_skills import create_all_farm_inspection_skills
from .skills.orchestration_skills import create_all_orchestration_skills
from .skills.base import Skill
from .middleware.skill_middleware import SkillMiddleware

logger = logging.getLogger(__name__)

# ========== 初始化模型 ==========

model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()


# ========== 技能组织 ==========

# 创建检测技能
detection_skills = create_all_detection_skills(
    pest_tool=pest_detection_tool,
    rice_tool=rice_detection_tool,
    cow_tool=cow_detection_tool,
)

# 创建规划技能（使用 search_knowledge 作为代表工具）
from src.rag.core.tools import search_knowledge

planning_skills = create_all_planning_skills(
    consult_tool=search_knowledge,
)

# 创建定价技能
pricing_skills = create_all_pricing_skills(
    pricing_tool=pricing_tool,
)

# 创建农场巡检技能
farm_inspection_skills = create_all_farm_inspection_skills(
    farm_inspection_tool=farm_inspection_tool,
)

# 创建编排技能
orchestration_skills = create_all_orchestration_skills()

# 合并所有技能（检测3 + 规划1 + 定价1 + 巡检1 + 编排2 = 8）
all_skills: List[Skill] = detection_skills + planning_skills + pricing_skills + farm_inspection_skills + orchestration_skills


# ========== 工具收集 ==========

# 收集所有工具（检测3 + 定价1 + 巡检1 + RAG 6 = 11个工具）
orchestrator_tools = [
    # 检测工具
    pest_detection_tool,
    rice_detection_tool,
    cow_detection_tool,
    # 定价工具
    pricing_tool,
    # 巡检工具
    farm_inspection_tool,
    # RAG 规划工具（所有 6 个）
    *PLANNING_TOOLS,
]


# ========== 系统提示词 ==========

ORCHESTRATOR_V2_SYSTEM_PROMPT = """<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
你拥有四大核心能力：图像检测、规划咨询、智能定价和农场巡检。
</role>

<capabilities>
通过技能系统，你可以动态加载专业能力：
- **检测能力**：病虫害检测、大米品种识别、牛只检测
- **规划能力**：乡村发展规划、政策解读、技术指导
- **定价能力**：农产品定价、市场分析、价格优化
- **巡检能力**：农场数据收集、农田状况、养殖状态、设备监控
- **编排能力**：意图识别、场景切换、上下文管理
</capabilities>

<workflow>
## 工作流程

1. **理解用户意图**
   - 如果需要详细了解如何处理特定类型的请求，使用 load_skill 工具加载技能详细指导
   - 可加载技能：pest_detection, rice_detection, cow_detection, consult_planning_knowledge, pricing_analysis, farm_inspection, intent_recognition, scenario_switching

2. **选择合适的工具**
   - **有图片** → 优先使用检测工具（pest_detection_tool/rice_detection_tool/cow_detection_tool）
   - **关键词"规划/发展/政策"** → 使用 RAG 工具（search_knowledge, search_key_points 等）
   - **关键词"定价/价格/多少钱"** → 使用定价工具（pricing_tool）
   - **关键词"农场/农田/养殖/设备"** → 使用巡检工具（farm_inspection_tool）
   - **不确定** → 加载 intent_recognition 技能获取指导

3. **多轮对话管理**
   - 保持上下文连续性
   - 场景切换时使用 load_skill("scenario_switching") 获取指导
   - 基于之前对话内容提供连贯的回答

4. **直接回答**
   - 调用工具后，直接基于工具结果回答
   - 不要重复组织内容，工具返回什么就用什么
</workflow>

<constraints>
- **必须使用工具**：所有回答都必须基于工具调用结果
- **按需加载技能**：使用 load_skill 工具获取技能详细指导
- **保持专业性**：提供准确、专业、友好的回答
- **场景切换平滑**：多轮对话中保持上下文连续性
</constraints>

<examples>
用户: "如何发展乡村旅游业？"
→ 调用 search_knowledge(query="乡村旅游业发展") → 基于返回结果直接回答

用户: "这是什么害虫？" + 图片
→ 调用 pest_detection_tool(image_path="...") → "检测到瓜实蝇(3只)，危害程度..."

用户: "有什么生物防治方法？"（上下文：之前检测到瓜实蝇）
→ 调用 search_knowledge(query="瓜实蝇 生物防治") → 直接列出防治方法
</examples>
"""


# ========== 中间件配置 ==========

# 技能中间件：实现 Progressive Disclosure
skill_middleware = SkillMiddleware(skills=all_skills)

# 中间件列表
middleware = [skill_middleware]


# ========== 创建 Agent ==========

agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
)

logger.info(
    f"✓ 统一编排 Agent V2 (Orchestrator V2) 创建成功 - "
    f"采用 Skills 架构，技能数量: {len(all_skills)}, 工具数量: {len(orchestrator_tools)}"
)

__all__ = ["agent", "all_skills", "orchestrator_tools"]
