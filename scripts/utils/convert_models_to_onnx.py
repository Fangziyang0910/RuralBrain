#!/usr/bin/env python3
"""
YOLO PT 模型转 ONNX 格式转换脚本

功能：
- 将病虫害、大米、奶牛检测模型从 PT 格式转换为 ONNX 格式
- ONNX Runtime 依赖更小，推理更快，适合生产部署

使用方法：
    uv run python scripts/utils/convert_models_to_onnx.py
"""
from pathlib import Path
from ultralytics import YOLO
import sys

# 模型配置
MODELS_TO_CONVERT = [
    ("pest/best.pt", "pest"),
    ("rice/weights_fl/best.pt", "rice"),
    ("cow/yolov8n.pt", "cow"),
]


def convert_model(pt_path: Path, output_dir: Path, model_name: str) -> bool:
    """转换单个 PT 模型到 ONNX"""
    print(f"\n{'='*60}")
    print(f"转换 {model_name} 模型")
    print(f"{'='*60}")

    if not pt_path.exists():
        print(f" 模型文件不存在: {pt_path}")
        return False

    # 显示原始模型大小
    original_size_mb = pt_path.stat().st_size / (1024 * 1024)
    print(f" 原始模型: {pt_path} ({original_size_mb:.1f}MB)")

    # 加载 PT 模型
    print(f" 加载模型...")
    model = YOLO(str(pt_path))

    # 导出为 ONNX
    onnx_path = output_dir / f"{pt_path.stem}.onnx"
    print(f" 导出 ONNX: {onnx_path}")

    try:
        model.export(
            format='onnx',
            imgsz=640,
            opset=12,
            simplify=True,
            dynamic=False,
        )

        # 移动导出的 ONNX 文件到目标目录
        exported_onnx = pt_path.parent / f"{pt_path.stem}.onnx"
        if exported_onnx.exists() and str(exported_onnx) != str(onnx_path):
            exported_onnx.rename(onnx_path)

        # 检查文件大小
        size_mb = onnx_path.stat().st_size / (1024 * 1024)
        print(f" 转换成功: {onnx_path} ({size_mb:.1f}MB)")
        print(f" 大小变化: {original_size_mb:.1f}MB -> {size_mb:.1f}MB ({(size_mb/original_size_mb-1)*100:+.1f}%)")
        return True

    except Exception as e:
        print(f" 转换失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("RuralBrain YOLO 模型转 ONNX 工具")
    print("="*60)

    # 获取模型目录
    models_dir = Path(__file__).parent.parent.parent / "src" / "algorithms" / "detection" / "models"

    if not models_dir.exists():
        print(f"错误: 模型目录不存在: {models_dir}")
        return 1

    results = {}

    for model_rel_path, model_name in MODELS_TO_CONVERT:
        pt_path = models_dir / model_rel_path
        output_dir = pt_path.parent

        # 检查是否已存在 ONNX 文件
        onnx_path = output_dir / f"{pt_path.stem}.onnx"
        if onnx_path.exists():
            print(f"\n {model_name} ONNX 文件已存在，跳过")
            results[model_name] = "skipped"
            continue

        success = convert_model(pt_path, output_dir, model_name)
        results[model_name] = "success" if success else "failed"

    # 总结
    print(f"\n{'='*60}")
    print("转换总结")
    print(f"{'='*60}")
    for model, status in results.items():
        emoji = "" if status == "success" else " " if status == "skipped" else ""
        print(f"{emoji} {model}: {status}")

    # 检查是否全部成功
    if all(s in ["success", "skipped"] for s in results.values()):
        print("\n 所有模型转换完成！")
        print("\n下一步:")
        print("1. 检查 ONNX 模型文件")
        print("2. 修改 src/algorithms/detection/config.py 中的模型路径")
        print("3. 修改 pyproject.toml，将 torch 替换为 onnxruntime")
        print("4. 重建 Docker 镜像测试")
        return 0
    else:
        print("\n 部分模型转换失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
