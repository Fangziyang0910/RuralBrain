"""
V1/V2 Agent 多轮对话对比测试

测试多轮对话场景下 V2 的 Progressive Disclosure 优势
"""
import os
import sys
import requests
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def find_test_images():
    """查找测试图片"""
    test_resources_dir = Path("tests/resources")

    # 递归搜索所有子目录
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    test_images = []

    for ext in image_extensions:
        test_images.extend(list(test_resources_dir.rglob(f"*{ext}")))

    # 按类型分组
    images_by_type = {
        "pest": [],
        "rice": [],
        "cow": []
    }

    for img in test_images:
        path_lower = str(img).lower()
        if "pest" in path_lower or "害虫" in path_lower or "虫" in path_lower:
            images_by_type["pest"].append(img)
        elif "rice" in path_lower or "大米" in path_lower or "稻" in path_lower:
            images_by_type["rice"].append(img)
        elif "cow" in path_lower or "牛" in path_lower or "cattle" in path_lower:
            images_by_type["cow"].append(img)

    return images_by_type


def run_multi_round_test(version, images_by_type, thread_id):
    """运行多轮对话测试"""
    print(f"\n{'='*60}")
    print(f"测试 {version.upper()} Agent - 多轮对话")
    print(f"{'='*60}")

    # 定义多轮对话场景
    scenarios = [
        {
            "round": 1,
            "message": "你好，我想了解一下农业图像识别系统。",
            "image": None,
            "description": "初始问候（不涉及具体检测）"
        },
        {
            "round": 2,
            "message": "这是我的稻田图片，能帮我识别一下品种吗？",
            "image": images_by_type["rice"][0] if images_by_type["rice"] else None,
            "description": "大米品种识别"
        },
        {
            "round": 3,
            "message": "我还有一张害虫图片，能帮我看看是什么害虫吗？",
            "image": images_by_type["pest"][0] if images_by_type["pest"] else None,
            "description": "病虫害检测"
        },
        {
            "round": 4,
            "message": "最后，我还有一张牛群的图片，能帮我数一下有多少头牛吗？",
            "image": images_by_type["cow"][0] if images_by_type["cow"] else None,
            "description": "牛只检测"
        },
        {
            "round": 5,
            "message": "总结一下你刚才帮我识别的内容。",
            "image": None,
            "description": "总结回顾"
        }
    ]

    results = {
        "rounds": [],
        "total_time": 0,
        "total_tokens": 0,
        "total_length": 0,
        "tool_calls": []
    }

    for scenario in scenarios:
        print(f"\n--- 第 {scenario['round']} 轮: {scenario['description']} ---")

        # 构建请求
        api_request = {
            "message": scenario["message"],
            "thread_id": thread_id
        }

        if scenario["image"]:
            api_request["image_paths"] = [str(scenario["image"])]
            print(f"图片: {scenario['image'].name}")

        print(f"消息: {scenario['message']}")

        # 发送请求
        try:
            start_time = time.time()

            response = requests.post(
                "http://localhost:8080/chat/stream",
                json=api_request,
                stream=True,
                timeout=60
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                # 收集响应内容
                full_content = ""
                round_tool_calls = []

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            data = line[6:]
                            try:
                                import json
                                event = json.loads(data)
                                if event.get("type") == "content":
                                    full_content += event.get("content", "")
                                elif event.get("type") == "tool_call":
                                    tool_name = event.get("tool_name", "unknown")
                                    round_tool_calls.append(tool_name)
                                    print(f"  [工具调用] {tool_name}")
                                elif event.get("type") == "end":
                                    pass
                            except:
                                pass

                # 估算 token
                token_count = int(len(full_content) * 1.5)

                print(f"  [响应时间] {elapsed_time:.2f}秒")
                print(f"  [估算 Token] {token_count}")
                print(f"  [响应长度] {len(full_content)}字符")
                print(f"  [响应预览] {full_content[:100]}...")

                # 记录结果
                results["rounds"].append({
                    "round": scenario["round"],
                    "description": scenario["description"],
                    "time": elapsed_time,
                    "tokens": token_count,
                    "length": len(full_content),
                    "tool_calls": round_tool_calls
                })

                results["total_time"] += elapsed_time
                results["total_tokens"] += token_count
                results["total_length"] += len(full_content)
                results["tool_calls"].extend(round_tool_calls)

            else:
                print(f"  [ERROR] 请求失败: {response.status_code}")

        except Exception as e:
            print(f"  [ERROR] 测试失败: {e}")

    return results


def print_multi_round_comparison(v1_results, v2_results):
    """打印多轮对话对比结果"""
    print(f"\n{'='*60}")
    print("多轮对话对比总结")
    print(f"{'='*60}")

    if not v1_results or not v2_results:
        print("[ERROR] 测试数据不完整，无法对比")
        return

    # 总体对比
    print(f"\n总体对比:")
    print(f"  总轮数: {len(v1_results['rounds'])} 轮")
    print(f"  V1 - 总时间: {v1_results['total_time']:.2f}秒, 总Token: {v1_results['total_tokens']}, 总字符: {v1_results['total_length']}")
    print(f"  V2 - 总时间: {v2_results['total_time']:.2f}秒, 总Token: {v2_results['total_tokens']}, 总字符: {v2_results['total_length']}")

    # 计算差异
    time_diff = ((v2_results['total_time'] - v1_results['total_time']) / v1_results['total_time']) * 100
    token_diff = ((v2_results['total_tokens'] - v1_results['total_tokens']) / v1_results['total_tokens']) * 100

    print(f"\n差异分析:")
    print(f"  响应时间: {time_diff:+.1f}% ({'V2 更快' if time_diff < 0 else 'V2 更慢'})")
    print(f"  Token 消耗: {token_diff:+.1f}% ({'V2 节省' if token_diff < 0 else 'V2 更多'})")
    print(f"  Token 节省: {v1_results['total_tokens'] - v2_results['total_tokens']} tokens")

    # 逐轮对比
    print(f"\n逐轮对比:")
    print("{'轮次':<6} {'场景':<20} {'V1时间':<10} {'V2时间':<10} {'V1 Token':<10} {'V2 Token':<10} {'Token差异'}<10}")
    print("-" * 90)

    for i in range(len(v1_results['rounds'])):
        v1_round = v1_results['rounds'][i]
        v2_round = v2_results['rounds'][i]

        v1_time = f"{v1_round['time']:.2f}s"
        v2_time = f"{v2_round['time']:.2f}s"
        v1_tokens = v1_round['tokens']
        v2_tokens = v2_round['tokens']
        token_diff = v1_tokens - v2_tokens
        token_diff_str = f"{token_diff:+d}" if token_diff != 0 else "0"

        print(f"{v1_round['round']:<6} {v1_round['description']:<20} {v1_time:<10} {v2_time:<10} {v1_tokens:<10} {v2_tokens:<10} {token_diff_str:<10}")

    # Progressive Disclosure 分析
    print(f"\nProgressive Disclosure 分析:")
    print(f"  V1: 每轮都发送完整的 82 行提示词 (~{v1_results['total_tokens'] // 5} tokens/轮)")
    print(f"  V2: 初始发送简短提示词,按需加载技能详情 (~{v2_results['total_tokens'] // 5} tokens/轮)")

    if token_diff < 0:
        savings_percent = abs(token_diff) / v1_results['total_tokens'] * 100
        print(f"  结论: V2 在多轮对话中节省了 {savings_percent:.1f}% 的 Token")
        print(f"  优势: 随着对话轮次增加,V2 的累积优势会越来越明显")
    else:
        print(f"  结论: 当前测试场景下 V2 未能体现 Token 节省优势")
        print(f"  可能原因: 对话轮次较少,或未触发 load_skill 机制")

    # 建议
    print(f"\n建议:")
    if token_diff < 0 and abs(token_diff) > 100:
        print("  ✓ V2 在多轮对话中表现更优，推荐使用 V2")
    elif abs(token_diff) < 50:
        print("  ! V1 和 V2 性能接近，可以根据其他因素选择")
        print("    - 开发阶段: V2 更易调试和修改")
        print("    - 生产环境: V1 更稳定成熟")
    else:
        print("  ✓ V1 在当前场景下更优，建议继续使用 V1")

    print(f"\n提示:")
    print(f"  - 要准确统计 Token 消耗，可在 .env 中设置 LANGSMITH_TRACING=true")
    print(f"  - V2 的优势主要体现在复杂场景和长期对话中")
    print(f"  - V2 的架构更易于扩展和维护")


def main():
    """主函数"""
    print("=" * 60)
    print("V1/V2 Agent 多轮对话对比测试")
    print("=" * 60)
    print("\n此测试需要:")
    print("1. 检测服务运行在 8001/8081/8002 端口")
    print("2. 后端服务器已启动")
    print("3. tests/resources/ 目录下有测试图片")
    print()

    # 查找测试图片
    images_by_type = find_test_images()

    if not any(images_by_type.values()):
        print("[ERROR] 未找到任何测试图片")
        print("请确保 tests/resources/ 目录下有测试图片（pests/, rice/, cows/）")
        return

    print(f"[INFO] 找到测试图片:")
    print(f"  - 病虫害: {len(images_by_type['pest'])} 张")
    print(f"  - 大米: {len(images_by_type['rice'])} 张")
    print(f"  - 牛只: {len(images_by_type['cow'])} 张")
    print()

    # 检查服务器状态
    try:
        response = requests.get("http://localhost:8080/health", timeout=2)
        if response.status_code != 200:
            print("[ERROR] 后端服务未就绪")
            print("请先启动后端服务: uv run python run_server.py")
            return
        print("[OK] 后端服务已就绪")
    except:
        print("[ERROR] 无法连接到后端服务")
        print("请先启动后端服务: uv run python run_server.py")
        return

    # 测试 V1
    print("\n" + "=" * 60)
    print("准备测试 V1 Agent")
    print("=" * 60)

    # 切换到 V1
    env_path = Path(".env")
    env_content = env_path.read_text(encoding="utf-8")
    env_content = env_content.replace("AGENT_VERSION=v2", "AGENT_VERSION=v1")
    env_path.write_text(env_content, encoding="utf-8")

    print("\n[提示] 已切换到 V1。开始多轮对话测试...")
    time.sleep(1)  # 等待配置生效

    v1_thread_id = f"multi_round_v1_{int(time.time())}"
    v1_results = run_multi_round_test("v1", images_by_type, v1_thread_id)

    print(f"\n[提示] V1 测试完成。现在切换到 V2...")
    time.sleep(1)

    # 测试 V2
    print("\n" + "=" * 60)
    print("准备测试 V2 Agent")
    print("=" * 60)

    # 切换到 V2
    env_content = env_path.read_text(encoding="utf-8")
    env_content = env_content.replace("AGENT_VERSION=v1", "AGENT_VERSION=v2")
    env_path.write_text(env_content, encoding="utf-8")

    print("\n[提示] 已切换到 V2。开始多轮对话测试...")
    time.sleep(1)  # 等待配置生效

    v2_thread_id = f"multi_round_v2_{int(time.time())}"
    v2_results = run_multi_round_test("v2", images_by_type, v2_thread_id)

    # 打印对比结果
    print_multi_round_comparison(v1_results, v2_results)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
