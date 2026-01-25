"""
统一编排 Agent (Orchestrator Agent)

作为 RuralBrain 的智能路由和协调中心，负责：
1. 根据用户输入自动判断使用规划咨询还是图像检测
2. 直接调用底层工具，避免嵌套调用
3. 支持多步推理和场景切换
4. 维护统一的对话上下文

使用场景：
- 纯检测：识别病虫害、农作物品种、牛只等
- 纯规划：乡村发展规划、政策咨询、产业建议
- 先检测后规划：识别问题后提供解决方案
- 规划中需要检测：规划过程中需要识别资源
"""

import logging
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from ..utils import ModelManager
from ..config import DEFAULT_PROVIDER

# 直接导入工具（避免通过子 Agent 调用）
from .tools import pest_detection_tool, rice_detection_tool, cow_detection_tool
from src.rag.core.tools import PLANNING_TOOLS

# 配置日志
logger = logging.getLogger(__name__)

# 初始化模型管理器并获取模型实例
model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()


# ========== Orchestrator Agent 配置 ==========

# 收集所有工具（检测工具 + RAG工具）
orchestrator_tools = [
    # 检测工具
    pest_detection_tool,
    rice_detection_tool,
    cow_detection_tool,
    # RAG 规划工具
    *PLANNING_TOOLS,
]

# 系统提示词（简化版，避免重复）
ORCHESTRATOR_SYSTEM_PROMPT = """<role>
你是 RuralBrain 乡村智慧大脑的统一智能助手，专注于农业和乡村发展。
你拥有两大核心能力：图像检测和规划咨询。
</role>

<capabilities>
**图像检测能力**：
- 病虫害检测：识别农作物病虫害并提供防治建议
- 大米识别：识别大米品种（糯米、丝苗米、泰国香米等）
- 牛只检测：识别奶牛、肉牛等

**规划咨询能力**：
- 乡村发展规划（旅游、产业、美丽乡村建设）
- 政策解读（一村一品、乡村振兴、现代农业支持政策）
- 治理模式（合作社、村企联建、党群共建）
- 技术指导（病虫害防治、种植养殖技术）
</capabilities>

<workflow>
## 工作流程

1. **判断意图**
   - 有图片 → 优先使用检测工具（pest_detection_tool/rice_detection_tool/cow_detection_tool）
   - 关键词"检测/识别/是什么" → 使用检测工具
   - 关键词"规划/发展/策略/政策/防治/如何" → 使用 RAG 工具

2. **选择合适的工具**
   - **病虫害**：pest_detection_tool
   - **大米品种**：rice_detection_tool
   - **牛只**：cow_detection_tool
   - **查询知识库**：优先用 search_knowledge 或 search_key_points（快速高效）

3. **直接回答**
   - 调用工具后，**直接基于工具结果回答**
   - 不要重复组织内容，工具返回什么就用什么
   - 使用清晰的结构（1. 2. 3. 或 一、二、三）

4. **场景切换**
   - 支持在同一对话中灵活切换检测和规划
   - 记住之前的对话，保持上下文连续
</workflow>

<constraints>
- **简洁高效**：选择最直接的工具，避免重复调用
- **准确性**：必须基于工具结果，不得虚构
- **不重复**：工具返回的内容直接使用，不要重复说
- **专业性**：保持专业、友好的语气
</constraints>

<examples>
用户: "如何发展乡村旅游业？"
→ 直接调用 search_knowledge(query="乡村旅游业发展") → 基于返回结果直接回答

用户: "这是什么害虫？" + 图片
→ 调用 pest_detection_tool(image_path="...") → "检测到瓜实蝇(3只)，危害程度..."

用户: "有什么生物防治方法？"
→ 调用 search_knowledge(query="瓜实蝇 生物防治") → 直接列出防治方法
</examples>
"""

# 创建 Orchestrator Agent
agent = create_agent(
    model=model,
    tools=orchestrator_tools,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)

logger.info("✓ 统一编排 Agent (Orchestrator) 创建成功")

__all__ = ["agent"]
