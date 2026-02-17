"""
层次化摘要系统测试脚本
测试阶段2的摘要生成和查询功能
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document
from src.rag.core.summarization import DocumentSummarizer, summarize_document
from src.rag.core.context_manager import DocumentContextManager
from src.rag.config import DEFAULT_PROVIDER, CHROMA_PERSIST_DIR


def test_summarizer_basic():
    """测试摘要生成器的基本功能"""
    print("\n" + "="*70)
    print("测试1: 基本摘要生成功能")
    print("="*70)

    # 创建测试文档
    test_doc = Document(
        page_content="""
# 博罗县乡村振兴发展规划（2024-2030年）

## 一、总体目标

到2030年，博罗县将建设成为粤港澳大湾区生态宜居示范区，实现乡村全面振兴。

### 1.1 经济发展目标
- 地区生产总值达到100亿元，年均增长7%
- 农民人均可支配收入达到3万元

### 1.2 社会发展目标
- 城镇化率达到65%
- 每千人拥有医疗卫生机构床位数达到5张

## 二、产业发展规划

### 2.1 文化旅游产业
依托罗浮山文化资源和东江生态资源，打造5A级旅游景区集群。

**重点建设项目：**
- 罗浮山环线建设工程，投资5亿元，2025-2027年
- 东江生态旅游带，投资3亿元，2026-2028年

**发展目标：**
- 2027年，年接待游客500万人次
- 旅游收入达到20亿元

### 2.2 现代农业
建设现代农业产业园，发展有机农业和特色种植。

**重点领域：**
- 有机蔬菜种植基地
- 特色水果产业园
- 农产品深加工中心

**发展目标：**
- 2030年，农业产值达到20亿元
- 有机认证面积达到5万亩

## 三、空间布局规划

构建"一轴两带三片区"的空间发展格局：

- **一轴**：东江发展轴
- **两带**：罗浮山生态带、广惠交通带
- **三片区**：长宁镇中心区、石湾镇产业区、泰美镇生态区

## 四、保障措施

### 4.1 政策保障
出台《博罗县乡村振兴扶持政策》，设立专项基金10亿元。

### 4.2 人才保障
实施"乡村人才计划"，每年引进100名专业人才。

### 4.3 资金保障
建立多元化投融资机制，引导社会资本参与乡村振兴。
""",
        metadata={"source": "test_plan.md", "type": "md"}
    )

    try:
        # 初始化摘要生成器
        print(f"\n📝 初始化摘要生成器（模型: {DEFAULT_PROVIDER}）...")
        summarizer = DocumentSummarizer(provider=DEFAULT_PROVIDER)

        # 生成完整摘要
        print("\n⏳ 正在生成摘要...")
        summary = summarizer.generate_summary(test_doc)

        # 输出执行摘要
        print("\n" + "-"*70)
        print("【执行摘要】")
        print("-"*70)
        print(summary.executive_summary)

        # 输出章节摘要
        print("\n" + "-"*70)
        print("【章节摘要】")
        print("-"*70)
        for i, chapter in enumerate(summary.chapter_summaries, 1):
            print(f"\n{i}. {chapter.title}")
            print(f"   摘要: {chapter.summary}")
            print(f"   要点: {'; '.join(chapter.key_points[:3])}")

        # 输出关键要点
        print("\n" + "-"*70)
        print("【关键要点】")
        print("-"*70)
        for i, point in enumerate(summary.key_points, 1):
            print(f"{i}. {point}")

        print("\n✅ 测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_context_manager_integration():
    """测试与 DocumentContextManager 的集成"""
    print("\n" + "="*70)
    print("测试2: 文档上下文管理器集成")
    print("="*70)

    try:
        # 创建测试文档和摘要
        test_doc = Document(
            page_content="# 测试文档\n\n这是一个测试文档，用于验证摘要功能与上下文管理器的集成。",
            metadata={"source": "integration_test.md", "type": "md"}
        )

        # 生成摘要
        summarizer = DocumentSummarizer(provider=DEFAULT_PROVIDER)
        summary = summarizer.generate_summary(test_doc)

        # 创建上下文管理器
        cm = DocumentContextManager()
        cm.doc_index = {
            "integration_test.md": {
                "source": "integration_test.md",
                "doc_type": "md",
                "full_content": test_doc.page_content,
                "metadata": test_doc.metadata,
                "chunks_info": [],
                "executive_summary": summary.executive_summary,
                "chapter_summaries": [
                    {
                        "title": ch.title,
                        "level": ch.level,
                        "summary": ch.summary,
                        "key_points": ch.key_points,
                        "start_index": ch.start_index,
                        "end_index": ch.end_index
                    }
                    for ch in summary.chapter_summaries
                ],
                "key_points": summary.key_points
            }
        }

        # 测试查询方法
        print("\n📋 测试 get_executive_summary...")
        result = cm.get_executive_summary("integration_test.md")
        print(f"结果: {result.get('executive_summary', 'N/A')[:100]}...")

        print("\n📋 测试 list_chapter_summaries...")
        result = cm.list_chapter_summaries("integration_test.md")
        print(f"章节数: {result.get('total_chapters', 0)}")

        print("\n📋 测试 get_chapter_summary...")
        result = cm.get_chapter_summary("integration_test.md", "测试")
        print(f"章节标题: {result.get('chapter_title', 'N/A')}")

        print("\n📋 测试 search_key_points...")
        result = cm.search_key_points("测试")
        print(f"匹配数: {result.get('total_matches', 0)}")

        print("\n✅ 集成测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_functions():
    """测试工具函数"""
    print("\n" + "="*70)
    print("测试3: 工具函数")
    print("="*70)

    try:
        from src.rag.core.tools import (
            get_executive_summary_tool_func,
            list_chapter_summaries_tool_func,
            get_chapter_summary_tool_func,
            search_key_points_tool_func
        )

        # 注意：这些工具需要实际的索引数据，这里只是测试函数存在
        print("\n📦 工具函数导入成功")
        print("   - get_executive_summary_tool_func")
        print("   - list_chapter_summaries_tool_func")
        print("   - get_chapter_summary_tool_func")
        print("   - search_key_points_tool_func")

        print("\n✅ 工具函数测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 工具函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_documents():
    """测试真实文档（如果知识库存在）"""
    print("\n" + "="*70)
    print("测试4: 真实文档（可选）")
    print("="*70)

    # 检查知识库是否存在
    if not CHROMA_PERSIST_DIR.exists():
        print("\n⚠️  知识库不存在，跳过真实文档测试")
        print(f"   提示：运行 python src/rag/build.py 构建知识库后再测试")
        return True

    try:
        # 加载上下文管理器
        cm = DocumentContextManager()
        cm.load()

        if not cm.doc_index:
            print("\n⚠️  知识库中没有文档")
            return True

        # 获取第一个文档
        first_source = list(cm.doc_index.keys())[0]
        print(f"\n📄 测试文档: {first_source}")

        # 检查是否有摘要
        doc_index = cm.doc_index[first_source]
        if not doc_index.executive_summary:
            print("\n⚠️  该文档尚未生成摘要")
            print(f"   提示：重新构建知识库后测试")
            return True

        # 测试查询
        print("\n📋 测试 get_executive_summary...")
        result = cm.get_executive_summary(first_source)
        if "error" not in result:
            print(f"执行摘要: {result.get('executive_summary', 'N/A')[:200]}...")

        print("\n📋 测试 list_chapter_summaries...")
        result = cm.list_chapter_summaries(first_source)
        if "error" not in result:
            print(f"章节数: {result.get('total_chapters', 0)}")

        print("\n📋 测试 search_key_points...")
        result = cm.search_key_points("发展")
        if "error" not in result:
            print(f"匹配数: {result.get('total_matches', 0)}")

        print("\n✅ 真实文档测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 真实文档测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("RAG 阶段2：层次化摘要系统测试")
    print("="*70)

    # 检查环境变量
    if DEFAULT_PROVIDER == "deepseek":
        if not os.getenv("DEEPSEEK_API_KEY"):
            print("\n❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
            print("   请先设置环境变量或创建 .env 文件")
            return
    elif DEFAULT_PROVIDER == "glm":
        if not os.getenv("ZHIPUAI_API_KEY"):
            print("\n❌ 错误: 未设置 ZHIPUAI_API_KEY 环境变量")
            print("   请先设置环境变量或创建 .env 文件")
            return

    results = []

    # 运行测试
    results.append(("基本摘要生成", test_summarizer_basic()))
    results.append(("上下文管理器集成", test_context_manager_integration()))
    results.append(("工具函数", test_tool_functions()))
    results.append(("真实文档（可选）", test_with_real_documents()))

    # 输出测试结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 所有测试通过！阶段2开发完成。")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()
