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
## 任务背景和工具选择

理解用户意图，根据需求选择合适的工具：
- **有图片** → 优先使用检测工具（pest_detection_tool / rice_detection_tool / cow_detection_tool）
- **关键词"规划/发展/政策"** → 使用规划咨询工具（planning_consult）
- **关键词"定价/价格/多少钱"** → 使用定价工具（pricing_tool）
- **关键词"营销/推广/销售/客户/销量"** → 使用营销工具（marketing_tool）
- **关键词"农场/农田/养殖/设备"** → 使用巡检工具（farm_inspection_tool）
- **关键词"疾病/症状/生病/发热/咳嗽/拉稀"** → 使用疾病预测工具（disease_prediction_tool）

**技能加载**：如需详细了解如何处理特定类型的请求，可使用 load_skill 工具加载技能详细指导。
</task_context>

<workflow>
## 工作流程

1. **理解用户意图和需求**
2. **根据需求选择合适的工具**（或加载详细技能指导）
3. **调用工具获取结果**
4. **基于工具结果，为用户提供清晰、有用的分析和建议**
</workflow>

<output_guidance>
## 输出内容要求

- 基于工具结果提供准确、有用的信息
- 当知识库无结果时，诚实告知用户
- 分析和建议要清晰、具体、可操作
- 可以自由组织回答的表达方式，无需遵循特定格式
</output_guidance>

<examples>
### 示例场景

**用户询问规划问题：**
用户: "长宁镇发展前景如何？"
→ 调用 planning_consult(query="长宁镇发展前景")
→ 基于返回结果，为用户提供详细的发展前景分析

**用户上传图片检测害虫：**
用户: "这是什么害虫？" + 图片
→ 调用 pest_detection_tool(image_path="...")
→ 基于检测结果，提供害虫识别结果和防治建议

**用户询问定价问题：**
用户: "我的一等有机大米成本3.5元/斤，应该卖多少钱？"
→ 调用 pricing_tool(product_name="有机大米", product_category="粮食", cost_price=3.5, quality_grade="一等")
→ 基于工具返回的分析报告，给出定价建议和策略选择
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
