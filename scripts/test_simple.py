"""
简单的图像检测测试
"""
import asyncio
import httpx


async def test_pest_detection():
    """测试病虫害检测"""
    print("🧪 测试病虫害检测")

    # 1. 上传图片
    image_path = "/home/szh/projects/RuralBrain/frontend/my-app/public/demo/pest-input.jpg"
    print(f"\n⏳ 上传图片: {image_path}")

    async with httpx.AsyncClient() as client:
        with open(image_path, "rb") as f:
            files = {"files": f}
            upload_response = await client.post("http://localhost:8080/upload", files=files)

            if upload_response.status_code != 200:
                print(f"❌ 上传失败: {upload_response.status_code} - {upload_response.text}")
                return

            upload_data = upload_response.json()
            image_paths = upload_data["file_paths"]
            print(f"✅ 上传成功: {image_paths}")

    # 2. 直接调用检测服务（绕过 Agent）
    print("\n⏳ 直接调用检测服务...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        detect_response = await client.post(
            "http://localhost:8001/detect",
            json={"image_base64": ""}  # 简化测试
        )

        print(f"检测服务响应: {detect_response.status_code}")

    # 3. 通过 Orchestrator Agent（使用简单问题）
    print("\n⏳ 通过 Orchestrator Agent（简单问题）...")
    data = {
        "message": "这是什么害虫？",
        "image_paths": image_paths,
        "thread_id": "test_simple"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8080/chat/stream",
                json=data
            ) as response:
                if response.status_code != 200:
                    print(f"❌ Agent 请求失败: {response.status_code}")
                    return

                print("\n📊 Agent 响应：")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            event = json.loads(line[6:])
                            if event["type"] == "content":
                                print(event["content"], end="", flush=True)
                            elif event["type"] == "end":
                                print("\n\n✅ 完成")
                        except:
                            pass

    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_pest_detection())
