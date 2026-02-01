"""简洁的文件缓存管理：容量限制 + LRU 自动清理"""
from pathlib import Path
from typing import List


def get_dir_size(directory: Path) -> int:
    """计算目录总大小（字节）

    Args:
        directory: 要计算的目录

    Returns:
        目录总大小（字节）
    """
    if not directory.exists():
        return 0
    return sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())


def cleanup_lru(directory: Path, max_size: int) -> None:
    """LRU 清理：删除最旧的文件直到容量满足要求

    Args:
        directory: 要清理的目录
        max_size: 最大允许容量（字节）
    """
    if not directory.exists():
        return

    current_size = get_dir_size(directory)
    if current_size <= max_size:
        return  # 容量足够，无需清理

    # 获取所有文件并按修改时间排序（旧的在前）
    files: List[Path] = sorted(
        directory.rglob('*'),
        key=lambda f: f.stat().st_mtime
    )

    # 删除旧文件直到容量满足要求
    for file_path in files:
        if file_path.is_file():
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                current_size -= file_size

                if current_size <= max_size:
                    break  # 容量已满足
            except Exception:
                continue  # 忽略删除失败的文件
