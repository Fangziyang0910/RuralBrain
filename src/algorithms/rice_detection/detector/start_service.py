# 服务启动脚本
import subprocess
import sys
from pathlib import Path

# 将当前目录添加到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    # 启动服务
    subprocess.run([sys.executable, "-m", "app.main"])