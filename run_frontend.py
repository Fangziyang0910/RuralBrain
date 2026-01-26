"""
RuralBrain 前端服务启动脚本

跨平台兼容的前端启动脚本，支持 Windows、Linux 和 macOS
"""
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text: str) -> None:
    """打印标题"""
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()


def print_success(text: str) -> None:
    """打印成功信息"""
    print(f"[OK] {text}")


def print_error(text: str) -> None:
    """打印错误信息"""
    print(f"[ERROR] {text}")


def check_nodejs() -> str:
    """检查 Node.js 和 npm 是否安装，返回 npm 可执行文件路径"""
    print("检查环境...")

    # 检查 Node.js
    node_exec = shutil.which("node")
    if not node_exec:
        print_error("未找到 Node.js")
        print("\n请先安装 Node.js:")
        print("  - 访问 https://nodejs.org/")
        print("  - 下载并安装 LTS 版本")
        print("\n安装后重新运行此脚本。")
        sys.exit(1)

    # 检查 npm
    npm_exec = shutil.which("npm")
    if not npm_exec:
        print_error("未找到 npm")
        print("\nnpm 通常随 Node.js 一起安装，请重新安装 Node.js。")
        sys.exit(1)

    # 显示版本信息
    try:
        result = subprocess.run(
            [node_exec, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        node_version = result.stdout.strip()
        print_success(f"Node.js {node_version}")

        result = subprocess.run(
            [npm_exec, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        npm_version = result.stdout.strip()
        print_success(f"npm {npm_version}")
    except subprocess.CalledProcessError:
        print_error("无法获取 Node.js/npm 版本信息")
        sys.exit(1)

    print()
    return npm_exec


def get_frontend_dir() -> Path:
    """获取前端目录路径"""
    frontend_dir = Path(__file__).parent / "frontend" / "my-app"

    if not frontend_dir.exists():
        print_error("前端目录不存在")
        print(f"\n预期路径: {frontend_dir}")
        print("请确认项目结构完整。")
        sys.exit(1)

    if not (frontend_dir / "package.json").exists():
        print_error("前端目录中未找到 package.json")
        print(f"\n路径: {frontend_dir}")
        print("请确认这是一个有效的 Next.js 项目。")
        sys.exit(1)

    return frontend_dir


def install_dependencies(npm_exec: str, frontend_dir: Path) -> None:
    """安装前端依赖"""
    print("正在安装依赖...")
    print("这可能需要几分钟，请耐心等待...\n")

    try:
        subprocess.run(
            [npm_exec, "install"],
            cwd=frontend_dir,
            check=True
        )
        print()
        print_success("依赖安装完成")
        print()
    except subprocess.CalledProcessError:
        print()
        print_error("依赖安装失败")
        print("\n请检查:")
        print("  - 网络连接是否正常")
        print("  - npm 源配置是否正确")
        print(f"\n尝试手动运行: cd {frontend_dir} && npm install")
        sys.exit(1)


def start_frontend() -> None:
    """启动前端开发服务器"""
    print_header("RuralBrain 前端服务启动中...")

    # 检查环境
    npm_exec = check_nodejs()

    # 获取前端目录
    frontend_dir = get_frontend_dir()

    # 检查依赖
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        install_dependencies(npm_exec, frontend_dir)
    else:
        print_success("依赖已安装")
        print()

    # 启动服务
    print("启动前端开发服务器...")
    print_success("访问地址: http://localhost:3000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    print()

    try:
        # 直接运行，让输出直接显示在终端
        subprocess.run([npm_exec, "run", "dev"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print()
        print()
        print("[INFO] 前端服务已停止")
    except subprocess.CalledProcessError:
        print()
        print_error("前端服务启动失败")
        print("\n请检查:")
        print("  - 端口 3000 是否被占用")
        print("  - 查看上方错误信息")
        print(f"\n尝试手动运行: cd {frontend_dir} && npm run dev")
        sys.exit(1)


if __name__ == "__main__":
    try:
        start_frontend()
    except Exception as e:
        print()
        print_error(f"发生未知错误: {e}")
        sys.exit(1)
