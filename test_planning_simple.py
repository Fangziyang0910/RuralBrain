"""
简化的 Planning Agent 测试
测试单个场景，快速验证功能
"""
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, 'src')

from src.agents.planning_agent import agent
import uuid

# 创建对话线程
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# 测试问题（简单事实查询，应该使用快速模式）
user_input = "长宁镇的旅游发展目标是什么？"

print("="*80)
print("Planning Agent 集成测试")
print("="*80)
print(f"\n👤 用户问题：{user_input}")
print("🎯 期望：使用快速模式（执行摘要工具）")
print("\n🤖 Agent 正在思考...\n")

# 记录工具调用
tools_called = []

# Stream 模式
events = agent.stream(
    {"messages": [("user", user_input)]},
    config,
    stream_mode="values"
)

final_response = None
for event in events:
    if "messages" in event:
        for msg in event["messages"]:
            # 记录工具调用
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tools_called.append(tool_name)
                    print(f"   🔧 调用工具：{tool_name}")

            # 获取最终回复
            if msg.type == "ai" and msg.content:
                final_response = msg.content

print("\n" + "="*80)
print("测试结果")
print("="*80)
print(f"\n📊 工具调用统计：")
if tools_called:
    for tool in tools_called:
        print(f"   - {tool}")
else:
    print("   （未调用工具）")

print(f"\n🎓 Agent 回答：")
print("-"*80)
print(final_response)
print("-"*80)

# 分析结果
fast_tools = {"get_executive_summary", "list_chapter_summaries", "get_chapter_summary", "search_key_points"}
deep_tools = {"get_full_document", "get_chapter_by_header", "search_rural_planning_knowledge"}

fast_count = sum(1 for t in tools_called if t in fast_tools)
deep_count = sum(1 for t in tools_called if t in deep_tools)

if fast_count > 0 and deep_count == 0:
    mode = "快速模式 ✅"
elif deep_count > 0:
    mode = "深度模式 ⚠️  (简单问题建议用快速模式)"
else:
    mode = "未知模式 ❌"

print(f"\n📈 模式分析：{mode}")
print(f"   快速工具调用：{fast_count} 次")
print(f"   深度工具调用：{deep_count} 次")
print(f"   回答长度：{len(final_response) if final_response else 0} 字符")
