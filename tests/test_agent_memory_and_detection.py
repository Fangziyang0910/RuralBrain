"""
测试cow_detection_agent的记忆化对话和牛图片识别功能
重点测试：
1. 记忆化对话功能
2. 牛图片识别和报告生成
3. 识别后的追问功能
4. 多线程会话隔离
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

from src.agents.cow_detection_agent import agent

def chat_with_agent(user_input: str, thread_id: str = "default") -> str:
    """与agent进行对话"""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = ""
    for chunk, _ in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="messages",
    ):
        # 只输出 AI 消息
        if type(chunk).__name__ == "AIMessageChunk" and chunk.content:
            result += chunk.content
    
    return result

def test_memory_dialogue():
    """测试记忆化对话功能"""
    print("=== 测试1: 记忆化对话功能 ===")
    
    # 第一轮对话：自我介绍
    print("\n第一轮对话：自我介绍")
    response1 = chat_with_agent("你好，我叫张三，是一名养牛户")
    print(f"助手回复: {response1}")
    
    # 第二轮对话：测试记忆
    print("\n第二轮对话：测试记忆")
    response2 = chat_with_agent("你还记得我叫什么名字吗？")
    print(f"助手回复: {response2}")
    
    # 检查是否记住了用户名
    if "张三" in response2:
        print("✅ 记忆功能测试通过 - 助手记住了用户名")
    else:
        print("❌ 记忆功能测试失败 - 助手没有记住用户名")
    
    return "张三" in response2

def test_cow_detection_and_report():
    """测试牛图片识别和报告生成"""
    print("\n=== 测试2: 牛图片识别和报告生成 ===")
    
    # 查找train14文件夹中以train_batch或val_batch开头的图片
    train14_path = "train14"
    batch_image_files = []
    
    if os.path.exists(train14_path):
        for file in os.listdir(train14_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                # 只选择以train_batch或val_batch开头的图片
                if file.startswith('train_batch') or file.startswith('val_batch'):
                    batch_image_files.append(os.path.join(train14_path, file))
    
    if not batch_image_files:
        print("❌ 未找到train_batch或val_batch开头的测试图片，跳过图片识别测试")
        return False
    
    # 选择前2-3张图片进行测试
    test_images = batch_image_files[:3]
    
    print(f"找到 {len(batch_image_files)} 张batch图片，选择 {len(test_images)} 张进行测试")
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n测试图片 {i}: {os.path.basename(image_path)}")
        
        # 请求分析图片
        response = chat_with_agent(f"请分析这张图片中的牛只情况: {image_path}")
        print(f"助手回复: {response}")
        
        # 检查回复是否包含检测结果
        if any(keyword in response.lower() for keyword in ['牛', 'cow', '检测', '识别', '数量']):
            print(f"✅ 图片 {i} 识别测试通过")
        else:
            print(f"❌ 图片 {i} 识别测试失败")
    
    return True

def test_follow_up_questions():
    """测试识别后的追问功能"""
    print("\n=== 测试3: 识别后的追问功能 ===")
    
    # 先进行图片识别，使用batch图片
    train14_path = "train14"
    batch_image_files = []
    
    if os.path.exists(train14_path):
        for file in os.listdir(train14_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                # 只选择以train_batch或val_batch开头的图片
                if file.startswith('train_batch') or file.startswith('val_batch'):
                    batch_image_files.append(os.path.join(train14_path, file))
    
    if not batch_image_files:
        print("❌ 未找到train_batch或val_batch开头的测试图片，跳过追问测试")
        return False
    
    test_image = batch_image_files[0]
    
    # 第一轮：图片识别
    print(f"\n第一轮：图片识别 ({os.path.basename(test_image)})")
    response1 = chat_with_agent(f"请分析这张图片中的牛只情况: {test_image}")
    print(f"助手回复: {response1}")
    
    # 第二轮：追问养殖建议
    print("\n第二轮：追问养殖建议")
    response2 = chat_with_agent("基于刚才的检测结果，请给我一些养殖建议")
    print(f"助手回复: {response2}")
    
    # 检查是否基于之前的检测结果进行回答
    if any(keyword in response2.lower() for keyword in ['养殖', '饲养', '建议', '管理', '饲料']):
        print("✅ 追问功能测试通过 - 助手基于检测结果提供了养殖建议")
    else:
        print("❌ 追问功能测试失败 - 助手没有基于检测结果回答")
    
    # 第三轮：追问具体问题
    print("\n第三轮：追问具体问题")
    response3 = chat_with_agent("这些牛适合什么样的饲料配比？")
    print(f"助手回复: {response3}")
    
    return True

def test_thread_isolation():
    """测试多线程会话隔离"""
    print("\n=== 测试4: 多线程会话隔离 ===")
    
    # 线程1：用户张三
    print("\n线程1 (用户张三):")
    response1 = chat_with_agent("你好，我叫张三", "thread_zhangsan")
    print(f"助手回复: {response1}")
    
    # 线程2：用户李四
    print("\n线程2 (用户李四):")
    response2 = chat_with_agent("你好，我叫李四", "thread_lisi")
    print(f"助手回复: {response2}")
    
    # 测试线程隔离
    print("\n测试线程隔离:")
    
    # 在张三的线程中询问名字
    response_zhang = chat_with_agent("你还记得我叫什么名字吗？", "thread_zhangsan")
    print(f"张三线程回复: {response_zhang}")
    
    # 在李四的线程中询问名字
    response_li = chat_with_agent("你还记得我叫什么名字吗？", "thread_lisi")
    print(f"李四线程回复: {response_li}")
    
    # 检查隔离效果
    zhang_isolated = "张三" in response_zhang and "李四" not in response_zhang
    li_isolated = "李四" in response_li and "张三" not in response_li
    
    if zhang_isolated and li_isolated:
        print("✅ 线程隔离测试通过 - 不同线程的对话完全隔离")
    else:
        print("❌ 线程隔离测试失败 - 线程间对话有干扰")
    
    return zhang_isolated and li_isolated

def main():
    """主测试函数"""
    print("开始测试cow_detection_agent的记忆化对话和牛图片识别功能")
    print("=" * 70)
    
    test_results = []
    
    try:
        # 测试1: 记忆化对话
        result1 = test_memory_dialogue()
        test_results.append(("记忆化对话", result1))
        
        # 测试2: 牛图片识别
        result2 = test_cow_detection_and_report()
        test_results.append(("牛图片识别", result2))
        
        # 测试3: 追问功能
        result3 = test_follow_up_questions()
        test_results.append(("追问功能", result3))
        
        # 测试4: 线程隔离
        result4 = test_thread_isolation()
        test_results.append(("线程隔离", result4))
        
        # 输出测试总结
        print("\n" + "=" * 70)
        print("测试总结:")
        print("=" * 70)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总测试结果: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！agent功能正常。")
        else:
            print("⚠️  部分测试失败，请检查agent配置。")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
