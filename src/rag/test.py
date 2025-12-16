import sys
import os

# 把项目根目录加入 python 路径，确保能 import src 下的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.rag.tool import retrieve_planning_info

def console_test():
    print("========================================")
    print("📚 乡村规划知识库 - 独立测试模式")
    print("========================================")
    print("正在初始化检索模型，请稍候...")
    
    # 预热一下（随便查个空的），让模型先加载进内存
    retrieve_planning_info("test")
    print("✅ 模型加载完毕！可以开始提问了。")
    print("输入 'q' 或 'exit' 退出。")
    print("----------------------------------------")

    while True:
        query = input("\n🙋 请输入问题 (比如: 罗浮山有什么战略定位?): ").strip()
        
        if query.lower() in ['q', 'exit', 'quit']:
            print("👋 测试结束")
            break
        
        if not query:
            continue

        print(f"🔍 正在检索: {query} ...")
        
        # 调用我们在 tool.py 里写的核心函数
        answer = retrieve_planning_info(query)
        
        print("\n🤖 [检索结果]:")
        print("-" * 20)
        print(answer)
        print("-" * 20)

if __name__ == "__main__":
    console_test()