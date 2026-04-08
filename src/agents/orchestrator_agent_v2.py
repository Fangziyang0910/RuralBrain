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
from .tools import load_skill
from .tools.tool_loader import get_tool_loader
from .skills.registry import get_registry
from .middleware.skill_middleware import SkillMiddleware
from .middleware.dynamic_tool_middleware import (
    DynamicToolMiddleware,
    set_dynamic_middleware,
)
from .middleware.model_selection_middleware import model_selection_middleware
from .context import AgentContext
from langchain.agents.middleware import SummarizationMiddleware

logger = logging.getLogger(__name__)

# ---- 初始化 ----

model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()
registry = get_registry()

# ---- 工具 ----

# 严格渐进式披露：初始只注册 load_skill 工具
# 其他工具在 load_skill 时通过 DynamicToolMiddleware 动态注册
orchestrator_tools = [
    load_skill,
]

# 初始化工具加载器
tool_loader = get_tool_loader()

# ---- 系统提示词 ----

ORCHESTRATOR_V2_SYSTEM_PROMPT = """
<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
</role>

<capabilities>
**检测**: 病虫害检测、大米品种识别、牛只检测等农业生产相关识别任务
**规划**: 乡村发展规划、政策解读、技术路线与实施步骤指导
**定价**: 农产品定价、市场行情。分析、成本与收益测算
**营销**: 营销策略设计、客户画像分析、品牌建设与推广建议
**巡检**: 农场巡检数据分析、农田长势评估、养殖过程监控与预警
**疾病预测**: 症状分析、健康风险评估与就医建议辅助
</capabilities>

<workflow>
**第一步：识别意图** - 分析用户需求类型：检测/规划/定价/营销/巡检/疾病预测
**第二步：加载技能** - 根据意图加载相应技能
**第三步：调用工具** - 根据技能指导使用相应工具
**第四步：专业输出** - 按技能定义的格式提供分析结果
**重要**：跳过技能加载会导致分析质量下降。
</workflow>

<knowledge_base_behavior>
**规划技能知识库开关**：
- 规划技能（consult_planning_knowledge）会自动处理知识库开关
- 知识库开启时，技能会注册 RAG 检索工具供调用
- 知识库关闭时，技能会用通用知识回答（不调用 RAG 工具）
- Agent 直接调用 load_skill("consult_planning_knowledge") 即可，无需额外判断
</knowledge_base_behavior>

<output_guidance>
- 基于工具结果提供准确信息
- 知识库无结果时诚实告知
- 分析建议要清晰、具体、可操作
</output_guidance>

<examples>
**检测害虫**（用户上传图片）:
1. load_skill("pest_detection")
2. pest_detection_tool() - 工具自动从对话中提取图片
3. 输出：检测结果、危害分析、防治方案

**疾病预测**（用户上传图片）:
1. load_skill("disease_prediction")
2. disease_prediction_tool(animal_type="猪/牛等", symptoms="根据图片判断") - 工具自动从对话中提取图片
3. 输出：疾病分析、图片识别结果、防控建议

**规划咨询**（知识库开启）:
1. load_skill("consult_planning_knowledge")
2. knowledge_search_tool(query=用户问题内容)
3. 输出：核心建议、政策依据、实施要点

**规划咨询**（知识库关闭）:
1. load_skill("consult_planning_knowledge")
2. 技能会用通用知识回答
3. 输出：基于预训练知识的建议

**定价分析**（用户询问定价）:
1. load_skill("pricing_analysis")
2. pricing_tool(...)
3. 输出：定价建议、分析依据、关键因素

**重要：图片处理说明**
- 检测工具（pest_detection_tool、rice_detection_tool、cow_detection_tool）会自动从用户上传的图片中提取信息
- 疾病预测工具（disease_prediction_tool）同样会自动从对话中提取图片进行分析
- 无需手动传递图片路径参数，工具会自动处理多模态（base64）和非多模态（路径）两种格式
- 用户上传图片后，直接调用对应的检测/疾病预测工具即可

**多模态图片理解**（用户使用 Qwen3.6-Plus 模型）:
- 多模态模型可以直接"看到"用户上传的图片内容
- 可以直接分析图片内容，无需依赖检测工具
- 对于精确检测任务，仍建议调用检测工具获取量化结果
</examples>
"""


# ---- 中间件 ----

# 动态工具注册中间件（必须放在 skill_middleware 之前）
dynamic_tool_middleware = DynamicToolMiddleware(tool_loader=tool_loader)
set_dynamic_middleware(dynamic_tool_middleware)

# 设置 tool_loader 到中间件
dynamic_tool_middleware.set_tool_loader(tool_loader)

# 技能渐进式披露中间件
skill_middleware = SkillMiddleware(registry=registry)

# 摘要中间件
summarization_middleware = SummarizationMiddleware(
    model=model_manager.get_chat_model(),
    trigger=("tokens", 8000),
    keep=("messages", 15),
)

middleware = [model_selection_middleware, dynamic_tool_middleware, skill_middleware, summarization_middleware]

# ---- 创建 Agent ----

agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_V2_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=middleware,
    context_schema=AgentContext,
)

skill_count = len(registry.list_skill_names())
available_tools = tool_loader.get_available_tool_names()
logger.info(
    f"✓ Agent V2 创建成功 - 技能: {skill_count}, "
    f"初始工具: {len(orchestrator_tools)}, "
    f"可用工具: {len(available_tools)}"
)

__all__ = ["agent", "registry", "orchestrator_tools"]
