"""
测试图像检测功能
"""
import asyncio
import httpx
import json
from pathlib import Path


async def test_detection(image_path: str, question: str, service_name: str):
    """测试图像检测"""
    print(f"\n{'='*60}")
    print(f"🧪 测试：{service_name}")
    print(f"{'='*60}")
    print(f"📝 问题: {question}")
    print(f"📎 图片: {image_path}")

    # 1. 上传图片
    print("\n⏳ 上传图片...")
    async with httpx.AsyncClient() as client:
        files = {"files": open(image_path, "rb")}
        upload_response = await client.post("http://localhost:8080/upload", files=files)

        if upload_response.status_code != 200:
            print(f"❌ 上传失败: {upload_response.status_code}")
            return

        upload_data = upload_response.json()
        image_paths = upload_data["file_paths"]
        print(f"✅ 上传成功: {image_paths}")

    # 2. 发送到 Orchestrator Agent
    print("\n⏳ 发送到 Orchestrator Agent...")
    data = {
        "message": question,
        "image_paths": image_paths,
        "thread_id": "test_detection"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8080/chat/stream",
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
                                tool_calls.append(f"🔧 {tool_name} ({status})")

                            elif event["type"] == "tool_call":
                                tool_name = event.get("tool_name", "unknown")
                                status = event.get("status", "unknown")
                                result_image = event.get("result_image")
                                tool_calls.append(f"🔧 {tool_name} ({status})")
                                if result_image:
                                    tool_calls.append(f"   📎 结果图片: {result_image}")

                            elif event["type"] == "content":
                                content = event["content"]
                                content_parts.append(content)
                                print(content, end="", flush=True)

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

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


async def main():
    base_path = Path("/home/szh/projects/RuralBrain/frontend/public/demo")

    # 测试1：病虫害检测
    pest_image = base_path / "pest-input.jpg"
    if pest_image.exists():
        await test_detection(
            str(pest_image),
            "这是什么害虫？请帮我识别并分析危害程度，提供防治建议。",
            "病虫害检测"
        )
    else:
        print("⚠️ 病虫害示例图片不存在")

    await asyncio.sleep(3)

    # 测试2：大米识别
    rice_image = base_path / "rice-input.jpg"
    if rice_image.exists():
        await test_detection(
            str(rice_image),
            "这是什么品种的大米？有什么特点？",
            "大米品种识别"
        )
    else:
        print("⚠️ 大米示例图片不存在")

    await asyncio.sleep(3)

    # 测试3：先检测后规划的模拟（需要浏览器手动测试）
    print("\n" + "="*60)
    print("🧪 场景：先检测后规划")
    print("="*60)
    print("⚠️ 此场景需要在浏览器中手动测试以保持对话上下文")
    print("   步骤：")
    print("   1. 访问 http://localhost:3000")
    print("   2. 上传病虫害图片，问'这是什么害虫？'")
    print("   3. 追问'有什么生物防治方法？'")
    print("   预期：先调用 pest_detection_tool，后调用 search_knowledge")


if __name__ == "__main__":
    asyncio.run(main())
