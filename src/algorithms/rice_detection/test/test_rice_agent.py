#!/usr/bin/env python3
"""
大米识别Agent测试脚本
用于测试rice_detection_agent的对话功能
"""

import sys
import os
from pathlib import Path
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置正确的路径
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 到RuralBrain根目录
agents_path = project_root / "agents"

# 确保agents模块能被导入
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(agents_path))

# 检查环境变量
print(f"DEEPSEEK_API_KEY 是否设置: {'DEEPSEEK_API_KEY' in os.environ}")
if 'DEEPSEEK_API_KEY' in os.environ:
    print(f"API密钥长度: {len(os.environ['DEEPSEEK_API_KEY'])} 字符")

def test_agent_import():
    """测试Agent模块导入"""
    print("📦 测试Agent模块导入...")
    
    try:
        # 尝试不同的导入方式
        try:
            from agents.rice_detection_agent import agent
            print("✅ 成功导入agents.rice_detection_agent")
            return True, agent
        except ImportError as e1:
            print(f"尝试agents.rice_detection_agent失败: {e1}")
            try:
                import rice_detection_agent
                agent = rice_detection_agent.agent
                print("✅ 成功导入rice_detection_agent")
                return True, agent
            except ImportError as e2:
                print(f"尝试rice_detection_agent失败: {e2}")
                print(f"当前路径: {sys.path}")
                return False, None
    except Exception as e:
        print(f"❌ 导入异常: {e}")
        return False, None

def test_agent_conversation(agent, image_path):
    """测试Agent对话功能，包括记忆和追问"""
    print(f"\n💬 测试Agent对话功能...")
    print(f"使用图片: {image_path}")
    
    try:
        # 第一步：识别大米图片
        print("\n【第一轮对话 - 识别大米】")
        user_message1 = f"请帮我识别这张大米图片的品种: {image_path}"
        print(f"用户: {user_message1}")
        
        # 构建消息
        messages = [
            {"role": "user", "content": user_message1}
        ]
        
        # 调用Agent的invoke方法，添加必要的配置
        config = {"configurable": {"thread_id": "test_thread_1"}}
        response1 = agent.invoke({"messages": messages}, config=config)
        
        print("\nAgent回复:")
        if response1 and response1.get("messages"):
            last_message = response1["messages"][-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
            else:
                print(str(last_message))
        else:
            print("无回复内容")
        
        # 第二步：测试记忆功能 - 询问刚才识别的是什么
        print("\n【第二轮对话 - 测试记忆功能】")
        user_message2 = "刚才识别的是什么大米？"
        print(f"用户: {user_message2}")
        
        # 使用上次的对话历史继续
        messages.append({"role": "assistant", "content": str(last_message.content) if hasattr(last_message, 'content') else str(last_message)})
        messages.append({"role": "user", "content": user_message2})
        
        response2 = agent.invoke({"messages": messages}, config=config)
        
        print("\nAgent回复:")
        if response2 and response2.get("messages"):
            last_message = response2["messages"][-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
            else:
                print(str(last_message))
        
        # 第三步：追问详细信息
        print("\n【第三轮对话 - 追问详细信息】")
        user_message3 = "这种大米适合煮粥吗？"
        print(f"用户: {user_message3}")
        
        messages.append({"role": "assistant", "content": str(last_message.content) if hasattr(last_message, 'content') else str(last_message)})
        messages.append({"role": "user", "content": user_message3})
        
        response3 = agent.invoke({"messages": messages}, config=config)
        
        print("\nAgent回复:")
        if response3 and response3.get("messages"):
            last_message = response3["messages"][-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
            else:
                print(str(last_message))
        
        return True
        
    except Exception as e:
        print(f"❌ Agent对话测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_with_direct_tool():
    """直接测试Agent的工具调用"""
    print("\n🔧 直接测试工具调用...")
    
    try:
        from tools.rice_detection_tool import rice_detection_tool
        
        # 使用测试图片
        test_image = "C:/Users/PC/Documents/GitHub/RuralBrain/tests/resources/rice/1.jpg"
        
        if not Path(test_image).exists():
            print(f"❌ 测试图片不存在: {test_image}")
            return False
            
        print(f"调用工具识别: {test_image}")
        result = rice_detection_tool.invoke(test_image)
        
        print("工具返回结果:")
        print(result)
        
        return True
        
    except Exception as e:
        print(f"❌ 工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🤖 大米识别Agent对话测试")
    print("=" * 60)
    
    print(f"项目根目录: {project_root}")
    print(f"Agents路径: {agents_path}")
    print(f"Python路径: {sys.path[:2]}")
    
    # 1. 测试Agent导入
    import_success, agent = test_agent_import()
    if not import_success:
        print("\n❌ Agent导入失败，测试终止！")
        return False
    
    # 2. 直接测试工具
    test_agent_with_direct_tool()
    
    # 3. 测试Agent对话
    test_image = "C:/Users/PC/Documents/GitHub/RuralBrain/tests/resources/rice/1.jpg"
    if Path(test_image).exists():
        test_agent_conversation(agent, test_image)
    else:
        print(f"\n⚠️ 测试图片不存在: {test_image}")
        # 尝试相对路径
        rel_image = "../../../../tests/resources/rice/1.jpg"
        if Path(rel_image).exists():
            test_agent_conversation(agent, rel_image)
        else:
            print("❌ 找不到测试图片，对话测试跳过")
    
    print("\n🎉 Agent测试完成！")
    return True

if __name__ == "__main__":
    main()