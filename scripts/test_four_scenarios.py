"""
四个核心场景测试脚本
1. 纯规划场景
2. 纯图像场景
3. 先规划后图像
4. 先图像后规划
"""

import asyncio
import httpx
import json
from pathlib import Path


class ScenarioTester:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url

    async def test_single_message(self, name: str, message: str, image_path: str = None, thread_id: str = None):
        """测试单条消息"""
        print(f"\n{'='*70}")
        print(f"🧪 {name}")
        print(f"{'='*70}")
        print(f"📝 用户输入: {message}")
        if image_path:
            print(f"📎 图片路径: {image_path}")
        if thread_id:
            print(f"🔗 Thread ID: {thread_id}")

        # 准备请求数据
        data = {
            "message": message,
            "thread_id": thread_id or "test_scenario",
        }

        # 如果有图片，先上传
        if image_path:
            print("\n⏳ 上传图片...")
            async with httpx.AsyncClient() as client:
                files = {"files": open(image_path, "rb")}
                upload_response = await client.post(f"{self.base_url}/upload", files=files)
                if upload_response.status_code != 200:
                    print(f"❌ 图片上传失败: {upload_response.status_code}")
                    return False, None
                upload_data = upload_response.json()
                data["image_paths"] = upload_data["file_paths"]
                print(f"✅ 图片上传成功")

        # 发送聊天请求
        print("\n⏳ 发送消息...")

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
                        return False, thread_id

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
                                    tool_calls.append(f"🔧 {tool_name} ({status})")

                                elif event["type"] == "tool_call":
                                    tool_name = event.get("tool_name", "unknown")
                                    status = event.get("status", "unknown")
                                    tool_calls.append(f"🔧 {tool_name} ({status})")

                                elif event["type"] == "content":
                                    content = event.get("content", "")
                                    content_parts.append(content)
                                    print(content, end="", flush=True)

                                elif event["type"] == "sources":
                                    sources = event.get("sources", [])
                                    if sources:
                                        print(f"\n\n📚 知识库来源 ({len(sources)} 条):")
                                        for source in sources[:3]:
                                            print(f"   - {source.get('source', 'unknown')}")

                                elif event["type"] == "end":
                                    print(f"\n\n✅ 响应完成")

                            except Exception as e:
                                print(f"\n⚠️ 解析事件失败: {e}")

                    # 打印工具调用摘要
                    if tool_calls:
                        print(f"\n\n🔧 工具调用记录:")
                        for call in tool_calls:
                            print(f"  {call}")

                    return True, thread_id

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False, thread_id

    async def run_tests(self):
        """运行四个核心场景测试"""
        print("\n" + "🚀"*35)
        print("开始四个核心场景测试")
        print("🚀"*35)

        # 场景1：纯规划
        success, _ = await self.test_single_message(
            "场景1：纯规划 - 乡村旅游发展",
            "如何发展乡村旅游业？请给出具体的建议和策略。"
        )
        await asyncio.sleep(3)

        # 场景2：纯图像 - 病虫害识别
        pest_image = Path("frontend/my-app/public/demo/pest-input.jpg")
        if pest_image.exists():
            success, _ = await self.test_single_message(
                "场景2：纯图像 - 病虫害识别",
                "这是什么害虫？请帮我识别并分析危害。",
                str(pest_image),
                thread_id="scenario2"
            )
        else:
            print("⚠️ 病虫害示例图片不存在，跳过场景2")
        await asyncio.sleep(3)

        # 场景3：先规划后图像（使用相同 thread_id 保持上下文）
        print("\n" + "🎯"*35)
        print("场景3：先规划后图像（多轮对话）")
        print("🎯"*35)

        thread_id = "scenario3_planning_then_image"

        # 第1轮：规划咨询
        success, _ = await self.test_single_message(
            "场景3-第1轮：规划咨询 - 瓜实蝇防治",
            "瓜实蝇有什么综合防治方法？",
            thread_id=thread_id
        )
        await asyncio.sleep(2)

        # 第2轮：图像识别（基于之前的规划上下文）
        if pest_image.exists():
            success, _ = await self.test_single_message(
                "场景3-第2轮：图像识别 - 上传受害虫害图片",
                "我在地里发现了这种虫子，请确认是否是瓜实蝇？",
                str(pest_image),
                thread_id=thread_id
            )

        await asyncio.sleep(3)

        # 场景4：先图像后规划（使用相同 thread_id 保持上下文）
        print("\n" + "🎯"*35)
        print("场景4：先图像后规划（多轮对话）")
        print("🎯"*35)

        thread_id = "scenario4_image_then_planning"

        # 第1轮：图像识别
        if pest_image.exists():
            success, _ = await self.test_single_message(
                "场景4-第1轮：图像识别 - 发现病虫害",
                "这是什么害虫？",
                str(pest_image),
                thread_id=thread_id
            )
        await asyncio.sleep(2)

        # 第2轮：规划咨询（基于识别结果）
        success, _ = await self.test_single_message(
            "场景4-第2轮：规划咨询 - 询问防治方案",
            "针对这种害虫，有什么生物防治方法？",
            thread_id=thread_id
        )

        print("\n" + "="*70)
        print("🎉 四个核心场景测试完成！")
        print("="*70)


async def main():
    tester = ScenarioTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
