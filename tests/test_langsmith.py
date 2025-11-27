"""测试LangSmith集成"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

# 导入agent
from src.agents.cow_detection_agent import agent

def test_langsmith_integration():
    """测试LangSmith集成是否正常工作"""
    
    # 检查环境变量
    langchain_tracing = os.getenv("LANGCHAIN_TRACING_V2")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    langchain_project = os.getenv("LANGCHAIN_PROJECT")
    
    print(f"LANGCHAIN_TRACING_V2: {langchain_tracing}")
    print(f"LANGCHAIN_API_KEY: {'已设置' if langchain_api_key else '未设置'}")
    print(f"LANGCHAIN_PROJECT: {langchain_project}")
    
    if langchain_tracing != "true":
        print("\n错误: LangSmith追踪未启用!")
        print("请在.env文件中设置LANGCHAIN_TRACING_V2=true")
        return False
    
    if not langchain_api_key or langchain_api_key == "your_langsmith_api_key_here":
        print("\n错误: LangSmith API密钥未设置或使用了示例密钥!")
        print("请在.env文件中设置正确的LANGCHAIN_API_KEY")
        return False
    
    print("\n✅ LangSmith配置检查通过!")
    
    # 测试agent调用
    print("\n正在测试agent调用...")
    try:
        # 创建一个简单的测试消息
        messages = [{"role": "user", "content": "你好，请介绍一下你的功能"}]
        
        # 调用agent - 添加必需的配置参数
        config = {"configurable": {"thread_id": "test-thread-1"}}
        response = agent.invoke({"messages": messages}, config=config)
        
        print("✅ Agent调用成功!")
        print(f"响应: {response['messages'][-1].content}")
        
        print("\n📊 请在LangSmith控制台中查看追踪数据:")
        print(f"项目名称: {langchain_project}")
        print("网址: https://smith.langchain.com/")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent调用失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_langsmith_integration()