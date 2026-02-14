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
from .tools import pest_detection_tool, rice_detection_tool, cow_detection_tool, pricing_tool, marketing_tool, farm_inspection_tool, disease_prediction_tool
from .tools.planning_service_tool import planning_consult
from .skills.detection_skills import create_all_detection_skills
from .skills.planning_skills import create_all_planning_skills
from .skills.pricing_skills import create_all_pricing_skills
from .skills.marketing_skills import create_all_marketing_skills
from .skills.farm_inspection_skills import create_all_farm_inspection_skills
from .skills.disease_prediction_skills import create_all_disease_prediction_skills
from .skills.orchestration_skills import create_all_orchestration_skills
from .skills.base import Skill
from .middleware.skill_middleware import SkillMiddleware
from langchain.agents.middleware import SummarizationMiddleware

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

# 创建规划技能（使用 HTTP 客户端工具调用独立 RAG 服务）
planning_skills = create_all_planning_skills(
    consult_tool=planning_consult,
)

# 创建定价技能
pricing_skills = create_all_pricing_skills(
    pricing_tool=pricing_tool,
)

# 创建营销技能
marketing_skills = create_all_marketing_skills(
    marketing_tool=marketing_tool,
)

# 创建农场巡检技能
farm_inspection_skills = create_all_farm_inspection_skills(
    farm_inspection_tool=farm_inspection_tool,
)

# 创建疾病预测技能
disease_prediction_skills = create_all_disease_prediction_skills(
    disease_prediction_tool=disease_prediction_tool,
)

# 创建编排技能
orchestration_skills = create_all_orchestration_skills()

# 合并所有技能（检测3 + 规划1 + 定价1 + 营销1 + 巡检1 + 疾病预测1 + 编排2 = 10）
all_skills: List[Skill] = detection_skills + planning_skills + pricing_skills + marketing_skills + farm_inspection_skills + disease_prediction_skills + orchestration_skills


# ========== 工具收集 ==========

# 收集所有工具（检测3 + 定价1 + 营销1 + 巡检1 + 疾病预测1 + 规划1 = 8个工具）
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

<critical_rules>
## 关键规则（必须遵守）

1. **静默调用工具** - 在调用任何工具之前，绝对不要输出任何文字！
   - 禁止说"让我来查询"、"我来搜索"、"我尝试"等
   - 禁止说"首先"、"然后"、"接下来"等过渡语
   - 工具调用期间保持完全静默，直到获得所有结果

2. **一次性输出** - 只有在所有工具调用完成后，才开始输出最终回答
   - 先完成所有必要的工具调用
   - 然后直接输出完整的答案
   - 不要在工具调用过程中输出任何内容

3. **单次搜索** - 规划咨询问题只搜索一次
   - 用最直接的关键词搜索一次
   - 如果无结果，诚实告知用户
   - 绝对不要尝试多个不同关键词
</critical_rules>

<workflow>
## 工作流程

1. **理解用户意图**
   - 如果需要详细了解如何处理特定类型的请求，使用 load_skill 工具加载技能详细指导
   - 可加载技能：pest_detection, rice_detection, cow_detection, consult_planning_knowledge, pricing_analysis, marketing_strategy, farm_inspection, disease_prediction, intent_recognition, scenario_switching

2. **选择合适的工具**
   - **有图片** → 优先使用检测工具（pest_detection_tool/rice_detection_tool/cow_detection_tool）
   - **关键词"规划/发展/政策"** → 使用 RAG 工具（knowledge_search_tool 等）
   - **关键词"定价/价格/多少钱"** → 使用定价工具（pricing_tool）
   - **关键词"营销/推广/销售/客户/销量"** → 使用营销工具（marketing_tool）
   - **关键词"农场/农田/养殖/设备"** → 使用巡检工具（farm_inspection_tool）
   - **关键词"疾病/症状/生病/发热/咳嗽/拉稀"** → 使用疾病预测工具（disease_prediction_tool）
   - **不确定** → 加载 intent_recognition 技能获取指导
3. **获得结果后**
   - 基于工具返回的结果，直接输出完整回答
   - 从"您好"或直接从答案内容开始
   - 不要说"根据查询结果"、"经过搜索"等
</workflow>

<constraints>
- **绝对静默**：工具调用前/中不许说任何话
- **单次调用**：每个问题只调用 1 个工具（最多 2 个）
- **直接输出**：获得结果后立即输出答案，不要铺垫
- **诚实回答**：知识库无结果时明确告知
</constraints>

<examples>
用户: "长宁镇发展前景如何？"
→ （静默）调用 knowledge_search_tool("长宁镇发展前景")
→ （获得结果后）直接输出："长宁镇的发展前景主要体现在..."

用户: "这是什么害虫？" + 图片
→ （静默）调用 pest_detection_tool(image_path="...")
→ （获得结果后）直接输出："检测到瓜实蝇(3只)，危害程度..."

错误示例（禁止）：
用户: "长宁镇发展前景如何？"
→ "让我来查询一下..." ← 禁止！
→ "我来搜索相关信息..." ← 禁止！
→ "根据我的查询..." ← 禁止！
"""


# ========== 中间件配置 ==========

# 技能中间件：实现 Progressive Disclosure
skill_middleware = SkillMiddleware(skills=all_skills)

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

logger.info(
    f"✓ 统一编排 Agent V2 (Orchestrator V2) 创建成功 - "
    f"采用 Skills 架构，技能数量: {len(all_skills)}, 工具数量: {len(orchestrator_tools)}"
)

__all__ = ["agent", "all_skills", "orchestrator_tools"]
