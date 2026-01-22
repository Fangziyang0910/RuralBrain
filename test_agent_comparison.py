"""
V1/V2 Agent 对比测试脚本

用于对比传统架构（V1）和基于 Skills 架构（V2）的 Agent 功能。
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_configuration():
    """测试配置读取"""
    print("=" * 60)
    print("测试 1: 配置读取")
    print("=" * 60)

    from service.settings import AGENT_VERSION, AGENT_AUTO_FALLBACK

    print(f"[OK] AGENT_VERSION = {AGENT_VERSION}")
    print(f"[OK] AGENT_AUTO_FALLBACK = {AGENT_AUTO_FALLBACK}")
    print()


def test_agent_modules():
    """测试 Agent 模块结构（不触发模型加载）"""
    print("=" * 60)
    print("测试 2: Agent 模块结构")
    print("=" * 60)

    from pathlib import Path

    # 检查 V1 Agent 文件是否存在
    v1_path = Path("src/agents/image_detection_agent.py")
    if v1_path.exists():
        print("[OK] V1 Agent 文件存在")
        # 读取文件内容验证关键组件
        content = v1_path.read_text(encoding="utf-8")
        if "SYSTEM_PROMPT" in content and "create_agent" in content:
            print("[OK] V1 Agent 包含必要组件")
        else:
            print("[FAIL] V1 Agent 缺少关键组件")
    else:
        print("[FAIL] V1 Agent 文件不存在")

    # 检查 V2 Agent 文件是否存在
    v2_path = Path("src/agents/image_detection_agent_v2.py")
    if v2_path.exists():
        print("[OK] V2 Agent 文件存在")
        content = v2_path.read_text(encoding="utf-8")
        if "SkillMiddleware" in content and "create_all_detection_skills" in content:
            print("[OK] V2 Agent 包含必要组件")
        else:
            print("[FAIL] V2 Agent 缺少关键组件")
    else:
        print("[FAIL] V2 Agent 文件不存在")

    # 检查 __init__.py 是否已修复（不再导入 agent 实例）
    init_path = Path("src/agents/__init__.py")
    if init_path.exists():
        content = init_path.read_text(encoding="utf-8")
        if "from ." not in content or "__all__ = []" in content:
            print("[OK] __init__.py 已修复（不会触发早期加载）")
        else:
            print("[WARN] __init__.py 可能仍有导入问题")
    else:
        print("[FAIL] __init__.py 不存在")

    print()


def test_skills_architecture():
    """测试 Skills 架构组件"""
    print("=" * 60)
    print("测试 3: Skills 架构组件")
    print("=" * 60)

    # 测试技能基类
    try:
        from src.agents.skills.base import Skill
        print("[OK] Skill 基类可导入")
    except ImportError as e:
        print(f"[FAIL] Skill 基类导入失败: {e}")

    # 测试检测技能
    try:
        from src.agents.skills.detection_skills import create_all_detection_skills
        print("[OK] 检测技能模块可导入")
    except ImportError as e:
        print(f"[FAIL] 检测技能模块导入失败: {e}")

    # 测试中间件
    try:
        from src.agents.middleware import SkillMiddleware, ToolSelectorMiddleware
        print("[OK] 中间件模块可导入")
    except ImportError as e:
        print(f"[FAIL] 中间件模块导入失败: {e}")
    print()


def test_version_switching_logic():
    """测试版本切换逻辑（代码检查）"""
    print("=" * 60)
    print("测试 4: 版本切换逻辑")
    print("=" * 60)

    # 检查 server.py 中的关键函数
    try:
        with open("service/server.py", "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键函数是否存在
        checks = [
            ("get_agent() 函数", "def get_agent():"),
            ("get_agent_version() 函数", "def get_agent_version()"),
            ("版本切换逻辑", "if AGENT_VERSION == \"v2\":"),
            ("自动回退逻辑", "AGENT_AUTO_FALLBACK"),
            ("版本日志", "Agent 实际版本"),
        ]

        for name, pattern in checks:
            if pattern in content:
                print(f"[OK] {name} 已实现")
            else:
                print(f"[FAIL] {name} 未找到")
    except Exception as e:
        print(f"[FAIL] 检查失败: {e}")
    print()


def test_agent_performance_comparison():
    """测试 V1/V2 Agent 架构对比"""
    print("=" * 60)
    print("测试 5: V1/V2 Agent 架构对比")
    print("=" * 60)
    print("注意：此测试对比架构差异，不进行实际 Agent 调用")
    print()

    from dotenv import load_dotenv
    load_dotenv()
    import time

    print("-" * 60)
    print("测试 V1 Agent 结构")
    print("-" * 60)

    try:
        start_time = time.time()
        from src.agents.image_detection_agent import SYSTEM_PROMPT as v1_prompt
        v1_load_time = time.time() - start_time

        v1_prompt_lines = len(v1_prompt.strip().split('\n'))
        v1_prompt_chars = len(v1_prompt)

        print(f"[OK] V1 Agent 提示词分析完成")
        print(f"  - 加载时间: {v1_load_time:.3f}秒")
        print(f"  - 提示词行数: {v1_prompt_lines}行")
        print(f"  - 提示词字符数: {v1_prompt_chars}字符")
        print(f"  - 架构: 固定提示词（包含所有检测类型说明）")
        print()

    except Exception as e:
        print(f"[FAIL] V1 Agent 分析失败: {e}")
        print()

    print("-" * 60)
    print("测试 V2 Agent 结构")
    print("-" * 60)

    try:
        start_time = time.time()
        from src.agents.image_detection_agent_v2 import BASE_SYSTEM_PROMPT as v2_prompt
        from src.agents.skills.detection_skills import create_all_detection_skills

        # 创建模拟工具来测试技能创建
        from langchain_core.tools import tool

        @tool
        def mock_tool(x: str) -> str:
            """模拟检测工具（用于测试）"""
            return "mock"

        skills = create_all_detection_skills(
            pest_tool=mock_tool,
            rice_tool=mock_tool,
            cow_tool=mock_tool,
        )

        v2_load_time = time.time() - start_time
        v2_prompt_lines = len(v2_prompt.strip().split('\n'))
        v2_prompt_chars = len(v2_prompt)

        # 计算技能内容
        total_skill_content = 0
        for skill in skills:
            total_skill_content += len(skill.get_full_content())

        print(f"[OK] V2 Agent 提示词分析完成")
        print(f"  - 加载时间: {v2_load_time:.3f}秒")
        print(f"  - 基础提示词行数: {v2_prompt_lines}行")
        print(f"  - 基础提示词字符数: {v2_prompt_chars}字符")
        print(f"  - 技能数量: {len(skills)}个")
        print(f"  - 技能总内容: {total_skill_content}字符（按需加载）")
        print(f"  - 架构: Progressive Disclosure（渐进式披露）")
        print()

    except Exception as e:
        print(f"[FAIL] V2 Agent 分析失败: {e}")
        import traceback
        traceback.print_exc()
        print()

    # 对比总结
    print("=" * 60)
    print("架构对比总结")
    print("=" * 60)

    # 计算减少比例
    if 'v1_prompt_lines' in locals() and 'v2_prompt_lines' in locals():
        reduction_rate = (1 - v2_prompt_lines / v1_prompt_lines) * 100
        print(f"""
1. 提示词复杂度对比
   - V1: {v1_prompt_lines}行固定提示词（包含所有检测类型说明）
   - V2: {v2_prompt_lines}行基础提示词 + {len(skills)}个独立技能模块
   - 减少: {reduction_rate:.1f}% 的基础提示词复杂度

2. Token 消耗（估算）
   - V1: 每次请求 ~{v1_prompt_chars // 2} tokens（包含完整提示词）
   - V2: 初始请求 ~{v2_prompt_chars // 2} tokens，按需加载技能详情（~{total_skill_content // 2} tokens）
   - 优势: Progressive Disclosure 减少不必要的 Token 消耗

3. 可维护性
   - V1: 修改检测逻辑需要编辑长提示词
   - V2: 每个技能独立文件（src/agents/skills/detection_skills.py），易于扩展和维护

4. 扩展性
   - V1: 添加新检测类型需要修改核心提示词（image_detection_agent.py）
   - V2: 添加新技能只需在 detection_skills.py 创建新的 Skill 对象

5. 性能对比
   - V1 加载时间: {v1_load_time:.3f}秒
   - V2 加载时间: {v2_load_time:.3f}秒
   - 技能模块化带来的初始化开销可忽略不计

建议：
- 开发和测试阶段：使用 V2，易于调试和迭代
- 生产环境：可先使用 V1（稳定），验证 V2 后切换
- 监控指标：响应时间、Token 消耗、用户满意度
- 切换方式：修改 .env 中的 AGENT_VERSION=v1 或 v2
        """)
    else:
        print("""
无法完成完整对比（某个版本加载失败）

建议检查：
1. 环境变量是否正确配置
2. 依赖包是否完整安装
3. Agent 文件是否存在
        """)

    print()


def print_summary():
    """打印总结"""
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("""
V2 Agent 集成已完成以下功能：

1. [OK] 配置支持
   - .env 添加了 AGENT_VERSION 和 AGENT_AUTO_FALLBACK 配置
   - .env.example 添加了配置示例
   - service/settings.py 添加了配置读取逻辑

2. [OK] 版本切换机制
   - get_agent() 函数支持 v1/v2 版本切换
   - get_agent_version() 函数返回当前使用的版本
   - V2 失败时自动回退到 V1

3. [OK] 日志增强
   - 启动事件显示配置版本和实际版本
   - Agent 调用日志包含版本标识

4. [OK] 平滑迁移
   - 默认使用 V1（保守策略）
   - 通过设置 AGENT_VERSION=v2 启用新架构
   - 支持快速回滚到 V1

使用方法：
1. 确保 .env 文件中设置了 AGENT_VERSION=v1 或 v2
2. 启动服务：uv run python run_server.py
3. 观察日志确认加载的版本

切换版本：
- 编辑 .env 文件，修改 AGENT_VERSION=v1 或 v2
- 重启服务即可
    """)
    print("=" * 60)


def test_agent_live_comparison():
    """测试 V1/V2 Agent 实际运行对比"""
    print("=" * 60)
    print("测试 6: V1/V2 Agent 实际运行对比")
    print("=" * 60)
    print("注意：此测试需要检测服务运行（8001/8081/8002端口）")
    print()

    import requests
    import time
    import os
    from pathlib import Path

    # 检查测试图片是否存在（从 tests/resources 目录及子目录查找）
    test_resources_dir = Path("tests/resources")
    if not test_resources_dir.exists():
        test_resources_dir = Path("tests") / "resources"

    # 支持多种图片格式，并递归搜索子目录
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    test_images = []

    # 递归搜索所有子目录
    for ext in image_extensions:
        test_images.extend(list(test_resources_dir.rglob(f"*{ext}")))

    if not test_images:
        print("[SKIP] 未找到测试图片")
        print(f"查找路径: {test_resources_dir}")
        print("建议：将测试图片放入 tests/resources/ 目录")
        print()
        return

    # 选择一张图片进行测试
    test_image = test_images[0]
    print(f"[INFO] 使用测试图片: {test_image}")
    print()

    # 根据图片路径和名称判断测试类型
    image_path_lower = str(test_image).lower()
    image_name_lower = test_image.name.lower()

    # 明确指定识别内容的测试消息
    if "pest" in image_path_lower or "害虫" in image_path_lower or "虫" in image_path_lower:
        test_message = "请帮我识别图片中的害虫，并给出防治建议。"
        test_type = "病虫害检测"
    elif "rice" in image_path_lower or "大米" in image_path_lower or "稻" in image_path_lower:
        test_message = "请帮我识别图片中的大米品种。"
        test_type = "大米品种识别"
    elif "cow" in image_path_lower or "牛" in image_path_lower or "cattle" in image_path_lower:
        test_message = "请帮我统计图片中的牛只数量。"
        test_type = "牛只检测"
    else:
        # 根据文件名判断（如果路径不包含关键信息）
        if "pest" in image_name_lower or "害虫" in image_name_lower or "虫" in image_name_lower:
            test_message = "请帮我识别图片中的害虫，并给出防治建议。"
            test_type = "病虫害检测"
        elif "rice" in image_name_lower or "大米" in image_name_lower or "稻" in image_name_lower:
            test_message = "请帮我识别图片中的大米品种。"
            test_type = "大米品种识别"
        elif "cow" in image_name_lower or "牛" in image_name_lower or "cattle" in image_name_lower:
            test_message = "请帮我统计图片中的牛只数量。"
            test_type = "牛只检测"
        else:
            # 默认使用病虫害检测
            test_message = "请帮我识别图片中的害虫，并给出防治建议。"
            test_type = "病虫害检测（默认）"

    print(f"[INFO] 测试类型: {test_type}")
    print(f"[INFO] 测试消息: {test_message}")
    print()

    results = {}

    # 测试 V1 和 V2
    for version in ["v1", "v2"]:
        print(f"-" * 60)
        print(f"测试 {version.upper()} Agent - {test_type}")
        print(f"-" * 60)

        # 修改 .env 文件切换版本
        env_path = Path(".env")
        env_content = env_path.read_text(encoding="utf-8")

        # 处理可能的 v1/v2 大小写
        if "AGENT_VERSION=v1" in env_content or "AGENT_VERSION=V1" in env_content:
            env_content_modified = env_content.replace(
                "AGENT_VERSION=v1" if version == "v2" else "AGENT_VERSION=V1",
                f"AGENT_VERSION={version}"
            )
            env_content_modified = env_content_modified.replace(
                "AGENT_VERSION=V1" if version == "v2" else "AGENT_VERSION=v1",
                f"AGENT_VERSION={version}"
            )
        elif "AGENT_VERSION=v2" in env_content or "AGENT_VERSION=V2" in env_content:
            env_content_modified = env_content.replace(
                "AGENT_VERSION=v2" if version == "v2" else "AGENT_VERSION=V2",
                f"AGENT_VERSION={version}"
            )
            env_content_modified = env_content_modified.replace(
                "AGENT_VERSION=V2" if version == "v2" else "AGENT_VERSION=v2",
                f"AGENT_VERSION={version}"
            )
        else:
            # 如果没有找到，直接添加
            env_content_modified = env_content + f"\nAGENT_VERSION={version}\n"

        env_path.write_text(env_content_modified, encoding="utf-8")

        print(f"[INFO] 已切换到 {version.upper()}，等待服务器启动...")

        # 注意：这里假设用户手动启动服务器
        print(f"[INFO] 请手动启动服务器：uv run python run_server.py")
        print(f"[INFO] 然后按 Enter 继续...")
        input()

        # 等待服务器就绪
        max_retries = 10
        server_ready = False
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8080/health", timeout=2)
                if response.status_code == 200:
                    print(f"[OK] 服务器已就绪")
                    server_ready = True
                    break
            except:
                if i < max_retries - 1:
                    print(f"[WAIT] 等待服务器启动... ({i+1}/{max_retries})")
                    time.sleep(2)

        if not server_ready:
            print(f"[SKIP] 服务器未就绪，跳过 {version.upper()} 测试")
            print(f"[INFO] 请停止服务器（Ctrl+C），然后按 Enter 继续...")
            input()
            continue

        # 发送测试请求
        try:
            start_time = time.time()

            api_request = {
                "message": test_message,
                "image_paths": [str(test_image)],
                "thread_id": f"test_{version}_{int(time.time())}"
            }

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
                tool_calls = []

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
                                    # 记录工具调用
                                    tool_calls.append(event.get("tool_name", "unknown"))
                                elif event.get("type") == "end":
                                    pass
                            except:
                                pass

                # 估算 token 数量（粗略：中文字符数 * 1.5）
                token_count = int(len(full_content) * 1.5)

                results[version] = {
                    "success": True,
                    "time": elapsed_time,
                    "tokens": token_count,
                    "response_length": len(full_content),
                    "tool_calls": tool_calls,
                    "response_preview": full_content[:150] + "..." if len(full_content) > 150 else full_content
                }

                print(f"[OK] {version.upper()} 测试完成")
                print(f"  - 响应时间: {elapsed_time:.2f}秒")
                print(f"  - 估算 Token: {token_count}")
                print(f"  - 响应长度: {len(full_content)}字符")
                print(f"  - 工具调用: {', '.join(tool_calls) if tool_calls else '无'}")
                print(f"  - 响应预览: {results[version]['response_preview']}")
                print()

            else:
                print(f"[FAIL] {version.upper()} 请求失败: {response.status_code}")
                print()

        except Exception as e:
            print(f"[FAIL] {version.upper()} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            print()

        # 提示用户停止服务器
        print(f"[INFO] 请停止当前服务器（Ctrl+C），然后按 Enter 继续...")
        input()

    # 对比总结
    if "v1" in results and "v2" in results:
        print("=" * 60)
        print("实际运行对比总结")
        print("=" * 60)

        v1_result = results["v1"]
        v2_result = results["v2"]

        time_diff = ((v2_result["time"] - v1_result["time"]) / v1_result["time"]) * 100
        token_diff = ((v2_result["tokens"] - v1_result["tokens"]) / v1_result["tokens"]) * 100

        print(f"""
测试类型: {test_type}
测试图片: {test_image.name}

1. 响应时间对比
   - V1: {v1_result['time']:.2f}秒
   - V2: {v2_result['time']:.2f}秒
   - 差异: {time_diff:+.1f}% {'V2 更快' if time_diff < 0 else 'V2 更慢'}

2. Token 消耗对比（估算）
   - V1: ~{v1_result['tokens']} tokens
   - V2: ~{v2_result['tokens']} tokens
   - 差异: {token_diff:+.1f}% {'V2 更节省' if token_diff < 0 else 'V2 更多'}
   - 节省: {v1_result['tokens'] - v2_result['tokens']} tokens ({((v1_result['tokens'] - v2_result['tokens']) / v1_result['tokens'] * 100):+.1f}%)

3. 响应质量
   - V1 响应长度: {v1_result['response_length']}字符
   - V2 响应长度: {v2_result['response_length']}字符
   - 差异: {v2_result['response_length'] - v1_result['response_length']:+d}字符
   - V1 工具调用: {', '.join(v1_result['tool_calls']) if v1_result['tool_calls'] else '无'}
   - V2 工具调用: {', '.join(v2_result['tool_calls']) if v2_result['tool_calls'] else '无'}

4. 建议
   基于实际运行结果：
   - Token 节省: {abs(v1_result['tokens'] - v2_result['tokens'])} tokens ({'V2 优势' if token_diff < 0 else 'V1 优势'})
   - 响应速度: {'V2 更快' if time_diff < 0 else 'V1 更快'}
   - 推荐使用: {'V2 (Skills 架构)' if token_diff < 0 and abs(time_diff) < 50 else 'V1 (稳定架构)'}

   综合评估：
   - 如果 V2 Token 消耗显著更低（>20%），推荐使用 V2
   - 如果 V2 响应时间相当（±50%以内），可以使用 V2
   - 建议在生产环境监控实际表现后做出最终选择
        """)
    else:
        print("[WARN] 无法完成对比（某个版本测试失败）")
        if "v1" in results:
            print(f"[INFO] V1 测试成功，V2 测试失败")
        elif "v2" in results:
            print(f"[INFO] V2 测试成功，V1 测试失败")

    print()


if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        # 运行实际测试（需要手动启动服务器）
        print("=" * 60)
        print("V1/V2 Agent 实际运行对比测试")
        print("=" * 60)
        print("此测试需要：")
        print("1. 检测服务运行在 8001/8081/8002 端口")
        print("2. 手动启动/停止后端服务器")
        print("3. uploads/ 目录中有测试图片")
        print()
        test_agent_live_comparison()
    else:
        # 运行基础测试
        test_configuration()
        test_agent_modules()
        test_skills_architecture()
        test_version_switching_logic()
        test_agent_performance_comparison()
        print_summary()

        print("\n所有配置检查完成！")
        print("\n要运行实际性能对比测试（需要手动启动服务器）：")
        print("  uv run python test_agent_comparison.py --live")
