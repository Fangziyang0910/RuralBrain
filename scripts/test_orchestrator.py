"""
Orchestrator Agent 集成测试脚本

测试场景：
1. 纯规划 - 如何发展乡村旅游业？
2. 纯检测 - 上传病虫害图片识别
3. 先检测后规划 - 识别病虫害后询问防治方法
4. 规划中需要检测 - 规划咨询中需要识别资源
5. 上下文连续性 - 多轮对话测试
"""

import asyncio
import httpx
import json
from pathlib import Path


class OrchestratorTester:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
        self.thread_id = "test_orchestrator"

    async def test_scenario(self, name: str, message: str, image_path: str = None):
        """测试单个场景"""
        print(f"\n{'='*60}")
        print(f"🧪 测试场景：{name}")
        print(f"{'='*60}")
        print(f"📝 用户输入: {message}")
        if image_path:
            print(f"📎 图片路径: {image_path}")

        # 准备请求数据
        data = {
            "message": message,
            "thread_id": self.thread_id,
        }

        # 如果有图片，先上传
        if image_path:
            print("\n⏳ 上传图片...")
            async with httpx.AsyncClient() as client:
                files = {"files": open(image_path, "rb")}
                upload_response = await client.post(f"{self.base_url}/upload", files=files)
                if upload_response.status_code != 200:
                    print(f"❌ 图片上传失败: {upload_response.status_code}")
                    return
                upload_data = upload_response.json()
                data["image_paths"] = upload_data["file_paths"]
                print(f"✅ 图片上传成功")

        # 发送聊天请求
        print("\n⏳ 发送消息到 Orchestrator Agent...")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/stream",
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status_code != 200:
                        print(f"❌ 请求失败: {response.status_code}")
                        return

                    print("\n📊 Agent 响应：\n")

                    tool_calls = []
                    content_parts = []

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])

                                if event["type"] == "tool":
                                    tool_name = event.get("tool_name", "unknown")
                                    status = event.get("status", "unknown")
                                    tool_calls.append(f"🔧 工具调用: {tool_name} ({status})")

                                elif event["type"] == "tool_call":
                                    tool_name = event.get("tool_name", "unknown")
                                    status = event.get("status", "unknown")
                                    result_image = event.get("result_image")
                                    tool_calls.append(f"🔧 工具调用: {tool_name} ({status})")
                                    if result_image:
                                        tool_calls.append(f"   📎 结果图片: {result_image}")

                                elif event["type"] == "content":
                                    content = event["content"]
                                    content_parts.append(content)
                                    print(content, end="", flush=True)

                                elif event["type"] == "sources":
                                    sources = event.get("sources", [])
                                    if sources:
                                        print(f"\n\n📚 知识库来源 ({len(sources)} 条):")
                                        for source in sources[:3]:  # 只显示前3条
                                            print(f"   - {source.get('source', 'unknown')}: {source.get('title', 'unknown')}")

                                elif event["type"] == "end":
                                    full_content = event.get("full_content", "")
                                    print(f"\n\n✅ 响应完成 (总长度: {len(full_content)} 字符)")

                            except Exception as e:
                                print(f"\n⚠️ 解析事件失败: {e}")

                    # 打印工具调用摘要
                    if tool_calls:
                        print(f"\n\n🔧 工具调用摘要:")
                        for call in tool_calls:
                            print(f"  {call}")

                    return True

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试场景"""
        print("🚀 开始 Orchestrator Agent 集成测试")
        print("="*60)

        # 场景1：纯规划
        await self.test_scenario(
            "场景1：纯规划 - 乡村旅游发展",
            "如何发展乡村旅游业？请给出具体的建议和策略。"
        )

        await asyncio.sleep(2)  # 等待2秒

        # 场景2：纯检测 - 病虫害
        pest_image = Path("/home/szh/projects/RuralBrain/frontend/public/demo/pest-input.jpg")
        if pest_image.exists():
            await self.test_scenario(
                "场景2：纯检测 - 病虫害识别",
                "这是什么害虫？请帮我识别并分析危害。",
                str(pest_image)
            )
        else:
            print("⚠️ 病虫害示例图片不存在，跳过场景2")

        await asyncio.sleep(2)

        # 场景3：纯检测 - 大米品种
        rice_image = Path("/home/szh/projects/RuralBrain/frontend/public/demo/rice-input.jpg")
        if rice_image.exists():
            await self.test_scenario(
                "场景3：纯检测 - 大米品种识别",
                "这是什么品种的大米？",
                str(rice_image)
            )
        else:
            print("⚠️ 大米示例图片不存在，跳过场景3")

        await asyncio.sleep(2)

        # 场景4：纯检测 - 牛只
        cow_image = Path("/home/szh/projects/RuralBrain/frontend/public/demo/cow-input.jpg")
        if cow_image.exists():
            await self.test_scenario(
                "场景4：纯检测 - 牛只识别",
                "这是奶牛还是肉牛？有多少头？",
                str(cow_image)
            )
        else:
            print("⚠️ 牛只示例图片不存在，跳过场景4")

        await asyncio.sleep(2)

        # 场景5：先检测后规划（需要模拟，使用新thread_id）
        print("\n" + "="*60)
        print("🧪 场景5：先检测后规划 - 识别病虫害后询问防治方法")
        print("="*60)
        print("⚠️ 此场景需要手动在浏览器中测试，因为需要保持对话上下文")
        print("   步骤：")
        print("   1. 上传病虫害图片，问'这是什么害虫？'")
        print("   2. 追问'有什么生物防治方法？'")
        print("   预期：先调用检测工具，后调用RAG工具查询防治方案")

        await asyncio.sleep(2)

        # 场景6：规划咨询
        await self.test_scenario(
            "场景6：规划咨询 - 一村一品政策",
            "一村一品政策是什么？如何申请？有什么支持措施？"
        )

        await asyncio.sleep(2)

        # 场景7：技术指导
        await self.test_scenario(
            "场景7：技术指导 - 病虫害防治",
            "瓜实蝇有什么综合防治方法？请提供化学、生物、物理等多种方案。"
        )

        print("\n" + "="*60)
        print("🎉 所有测试场景完成！")
        print("="*60)


async def main():
    tester = OrchestratorTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
