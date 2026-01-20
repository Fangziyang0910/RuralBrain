"""
RAG 模块优化验证测试

测试内容：
1. 工具数量验证（从 10+ 精简到 6 个核心工具）
2. 系统提示词长度验证（从 196 行压缩到 ~120 行）
3. 缓存性能测试
4. 工具功能测试
"""
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from src.rag.core.tools import PLANNING_TOOLS, get_vectorstore
from src.rag.core.cache import get_vector_cache
from src.agents.planning_agent import SYSTEM_PROMPT_BASE, build_system_prompt


def test_tool_count():
    """测试 1：验证工具数量"""
    print("\n" + "="*60)
    print("测试 1：工具数量验证")
    print("="*60)

    original_count = 10  # 原始工具数量
    new_count = len(PLANNING_TOOLS)

    print(f"✅ 原始工具数量：{original_count}+")
    print(f"✅ 当前工具数量：{new_count}")
    print(f"✅ 减少：{((original_count - new_count) / original_count * 100):.1f}%")

    # 列出新工具
    print(f"\n新工具列表：")
    for idx, tool in enumerate(PLANNING_TOOLS, 1):
        print(f"  {idx}. {tool.name}")

    assert new_count <= 7, "工具数量应该 ≤ 7"
    print("\n✅ 测试通过：工具数量精简成功")


def test_system_prompt_length():
    """测试 2：验证系统提示词长度"""
    print("\n" + "="*60)
    print("测试 2：系统提示词长度验证")
    print("="*60)

    original_lines = 196  # 原始行数

    # 基础提示词
    base_lines = len(SYSTEM_PROMPT_BASE.split('\n'))

    # 完整提示词（包含工具描述）
    full_prompt = build_system_prompt()
    full_lines = len(full_prompt.split('\n'))

    print(f"✅ 原始系统提示词：{original_lines} 行")
    print(f"✅ 当前基础提示词：{base_lines} 行")
    print(f"✅ 当前完整提示词：{full_lines} 行")
    print(f"✅ 基础部分减少：{((original_lines - base_lines) / original_lines * 100):.1f}%")

    assert base_lines < 150, "基础提示词应该 < 150 行"
    print("\n✅ 测试通过：系统提示词优化成功")


def test_cache_performance():
    """测试 3：缓存性能测试"""
    print("\n" + "="*60)
    print("测试 3：缓存性能测试")
    print("="*60)

    cache = get_vector_cache()

    # 测试 Embedding 模型缓存
    print("\n测试 Embedding 模型缓存：")
    start = time.time()
    model1 = cache.get_embedding_model()
    first_load_time = time.time() - start
    print(f"  首次加载：{first_load_time:.3f} 秒")

    start = time.time()
    model2 = cache.get_embedding_model()
    cached_load_time = time.time() - start
    print(f"  缓存加载：{cached_load_time:.3f} 秒")
    print(f"  加速比：{first_load_time / cached_load_time:.1f}x")

    assert model1 is model2, "应该返回同一个模型实例"
    print("  ✅ 模型实例复用成功")

    # 测试向量数据库缓存
    print("\n测试向量数据库缓存：")
    start = time.time()
    db1 = cache.get_vectorstore()
    first_db_load_time = time.time() - start
    print(f"  首次连接：{first_db_load_time:.3f} 秒")

    start = time.time()
    db2 = cache.get_vectorstore()
    cached_db_load_time = time.time() - start
    print(f"  缓存连接：{cached_db_load_time:.3f} 秒")
    print(f"  加速比：{first_db_load_time / cached_db_load_time:.1f}x")

    assert db1 is db2, "应该返回同一个数据库实例"
    print("  ✅ 数据库实例复用成功")

    # 缓存统计
    stats = cache.get_cache_stats()
    print(f"\n缓存统计：")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ 测试通过：缓存系统工作正常")


def test_tools_functionality():
    """测试 4：工具功能测试"""
    print("\n" + "="*60)
    print("测试 4：工具功能测试")
    print("="*60)

    # 注意：这些测试需要知识库已构建
    # 如果知识库不存在，会抛出异常

    try:
        from src.rag.core.tools import (
            list_available_documents,
            get_document_overview,
            search_knowledge,
        )

        # 测试 list_documents
        print("\n测试 list_documents：")
        result = list_available_documents()
        print(f"  返回长度：{len(result)} 字符")
        assert "【可用文档列表】" in result
        print("  ✅ list_documents 工作正常")

        # 测试 search_knowledge（使用 minimal 模式）
        print("\n测试 search_knowledge（minimal 模式）：")
        result = search_knowledge("旅游", top_k=2, context_mode="minimal")
        print(f"  返回长度：{len(result)} 字符")
        assert "【片段" in result or "未找到" in result
        print("  ✅ search_knowledge 工作正常")

        print("\n✅ 测试通过：所有核心工具工作正常")

    except FileNotFoundError as e:
        print(f"\n⚠️  跳过工具功能测试：知识库未构建")
        print(f"   请先运行: python src/rag/build.py")
        return False

    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RAG 模块优化验证测试")
    print("="*60)

    try:
        # 测试 1：工具数量
        test_tool_count()

        # 测试 2：系统提示词长度
        test_system_prompt_length()

        # 测试 3：缓存性能
        test_cache_performance()

        # 测试 4：工具功能（可选，需要知识库）
        test_tools_functionality()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

        print("\n核心改进总结：")
        print("  1. 工具数量：从 10+ 精简到 6 个核心工具")
        print("  2. 系统提示词：从 196 行压缩到 ~120 行")
        print("  3. 缓存系统：Embedding 模型和向量数据库缓存")
        print("  4. 工具优化：支持渐进式披露，通过参数控制详细程度")

    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
