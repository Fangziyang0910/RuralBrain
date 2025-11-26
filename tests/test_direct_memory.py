"""直接测试agent的memory功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_agent_memory():
    """直接测试agent的memory功能"""
    print("=== 直接测试agent memory功能 ===")
    
    # 先检查必要的导入
    try:
        from src.agents.cow_detection_agent import chat_with_agent
        print("✓ 成功导入chat_with_agent函数")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return
    
    # 测试简单的对话
    try:
        print("\n测试1: 简单对话")
        response = chat_with_agent("你好", "test_thread_1")
        print(f"助手回复: {response}")
        print("✓ 简单对话测试通过")
    except Exception as e:
        print(f"✗ 简单对话测试失败: {e}")
        return
    
    # 测试memory功能
    try:
        print("\n测试2: memory功能测试")
        thread_id = "memory_test_thread"
        
        # 第一轮对话
        response1 = chat_with_agent("我叫李四，我想养牛", thread_id)
        print(f"第一轮回复: {response1}")
        
        # 第二轮对话（测试是否记住名字）
        response2 = chat_with_agent("你记得我的名字吗？", thread_id)
        print(f"第二轮回复: {response2}")
        
        # 检查是否包含记忆内容
        if "李四" in response2:
            print("✓ memory功能正常 - 助手记住了用户名")
        else:
            print("⚠ memory功能可能有问题 - 助手没有记住用户名")
            
    except Exception as e:
        print(f"✗ memory功能测试失败: {e}")
        return
    
    # 测试thread隔离性
    try:
        print("\n测试3: thread隔离性测试")
        
        # 用户A的对话
        response_a1 = chat_with_agent("我是用户A，喜欢黄牛", "user_a")
        print(f"用户A第一轮: {response_a1}")
        
        # 用户B的对话（应该独立）
        response_b1 = chat_with_agent("你记得我是谁吗？", "user_b") 
        print(f"用户B第一轮: {response_b1}")
        
        # 用户A继续对话（应该记住历史）
        response_a2 = chat_with_agent("我刚才说了我喜欢什么牛？", "user_a")
        print(f"用户A第二轮: {response_a2}")
        
        # 检查隔离性
        if "黄牛" in response_a2 and "黄牛" not in response_b1:
            print("✓ thread隔离性正常")
        else:
            print("⚠ thread隔离性可能有问题")
            
    except Exception as e:
        print(f"✗ thread隔离性测试失败: {e}")
        return

if __name__ == "__main__":
    print("开始直接测试agent memory功能...\n")
    test_agent_memory()
    print("\n=== 测试完成 ===")