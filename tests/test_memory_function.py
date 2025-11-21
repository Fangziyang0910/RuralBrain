"""测试cow_detection_agent的memory功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.cow_detection_agent import chat_with_agent

def test_memory_with_image():
    """测试图片识别后的追问功能"""
    print("=== 测试1: 图片识别后的追问功能 ===")
    
    # 使用train14文件夹中的测试图片
    test_image = "train14/train_batch0.jpg"
    thread_id = "test_user_001"
    
    # 第一轮对话：图片识别
    print("第一轮对话：图片识别")
    response1 = chat_with_agent(f"请分析这张图片中的牛只：{test_image}", thread_id)
    print(f"助手回复: {response1}")
    print("-" * 50)
    
    # 第二轮对话：追问相关信息（测试memory）
    print("第二轮对话：追问牛只品种特点")
    response2 = chat_with_agent("这些牛是什么品种？有什么特点？", thread_id)
    print(f"助手回复: {response2}")
    print("-" * 50)
    
    # 第三轮对话：继续追问（测试memory是否连贯）
    print("第三轮对话：追问养殖建议")
    response3 = chat_with_agent("对于这种牛，你有什么养殖建议？", thread_id)
    print(f"助手回复: {response3}")
    print("-" * 50)

def test_different_threads():
    """测试不同thread_id的隔离性"""
    print("\n=== 测试2: 不同thread_id的隔离性 ===")
    
    test_image = "train14/train_batch1.jpg"
    
    # 用户1的对话
    print("用户1对话：")
    response1 = chat_with_agent(f"分析这张图片：{test_image}", "user_001")
    print(f"用户1助手回复: {response1[:100]}...")
    
    # 用户2的对话（应该独立）
    print("用户2对话：")
    response2 = chat_with_agent("刚才我们聊了什么？", "user_002")
    print(f"用户2助手回复: {response2}")
    
    # 用户1继续对话（应该记住历史）
    print("用户1继续对话：")
    response3 = chat_with_agent("刚才检测到了多少头牛？", "user_001")
    print(f"用户1助手回复: {response3}")

def test_memory_persistence():
    """测试memory的持久性"""
    print("\n=== 测试3: memory持久性测试 ===")
    
    thread_id = "persistence_test"
    test_image = "train14/train_batch2.jpg"
    
    # 第一次对话
    print("第一次对话：")
    response1 = chat_with_agent(f"请分析这张图片：{test_image}", thread_id)
    print(f"第一次回复: {response1[:100]}...")
    
    # 第二次对话（应该记住第一次的内容）
    print("第二次对话：")
    response2 = chat_with_agent("刚才检测的结果是什么？", thread_id)
    print(f"第二次回复: {response2}")

if __name__ == "__main__":
    print("开始测试cow_detection_agent的memory功能...\n")
    
    try:
        # 检查测试图片是否存在
        required_images = [
            "train14/train_batch0.jpg",
            "train14/train_batch1.jpg", 
            "train14/train_batch2.jpg"
        ]
        
        missing_images = []
        for img in required_images:
            if not os.path.exists(img):
                missing_images.append(img)
        
        if missing_images:
            print(f"警告：以下测试图片不存在: {missing_images}")
            print("将使用模拟数据进行测试...")
        
        # 运行测试
        test_memory_with_image()
        test_different_threads()
        test_memory_persistence()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()