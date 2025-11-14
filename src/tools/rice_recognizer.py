import os
import shutil
import uuid
import datetime
from collections import defaultdict
from ultralytics import YOLO
import pandas as pd


# --- 从原代码剥离的辅助函数 ---

def move_folder_contents(src_folder, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    for item in os.listdir(src_folder):
        src_item = os.path.join(src_folder, item)
        dest_item = os.path.join(dest_folder, item)
        # 简单处理，直接覆盖
        if os.path.exists(dest_item):
            if os.path.isdir(dest_item):
                shutil.rmtree(dest_item)
            else:
                os.remove(dest_item)
        shutil.move(src_item, dest_item)
    try:
        os.rmdir(src_folder)
    except OSError:
        pass


def count_first_chars_in_txt_files(folder_path):
    char_count = defaultdict(int)
    if not os.path.isdir(folder_path):
        return {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        first_char = line[0]
                        char_count[first_char] += 1
    return dict(char_count)


# --- 封装后的核心识别函数 ---

def recognize_rice_from_image(image_path: str, task_type: str = "品种分类") -> dict:
    """
    对单张大米图片进行识别和统计。

    Args:
        image_path (str): 需要识别的本地图片文件的绝对路径。
        task_type (str): 任务类型，可选 "品种分类" 或 "新旧识别"。

    Returns:
        dict: 包含识别结果的字典，包括文字摘要和标注后图片的路径。
    """
    if not os.path.exists(image_path):
        return {"error": f"图片文件未找到: {image_path}"}

    # 根据任务类型选择模型
    if task_type == "品种分类":
        weights_dir = "weights_fl"
        model_name = "best.pt"
        name_map = {
            "1": "糯米", "2": "丝苗米", "3": "泰国香米",
            "4": "五常大米", "5": "珍珠大米"
        }
    elif task_type == "新旧识别":
        weights_dir = "weights_xj"
        model_name = "best.pt"
        name_map = {"1": "新米", "2": "旧米"}
    else:
        return {"error": "无效的任务类型，请选择 '品种分类' 或 '新旧识别'"}

    model_path = os.path.join(weights_dir, model_name)
    if not os.path.exists(model_path):
        return {"error": f"模型文件未找到: {model_path}"}

    try:
        # 1. 准备临时输入目录
        temp_root = "./temp_input"
        os.makedirs(temp_root, exist_ok=True)
        session_id = uuid.uuid4().hex[:8]
        temp_src = os.path.join(temp_root, f"in_{session_id}")
        os.makedirs(temp_src, exist_ok=True)

        basename = os.path.basename(image_path)
        temp_img_path = os.path.join(temp_src, basename)
        shutil.copy2(image_path, temp_img_path)

        # 2. 加载模型并执行预测
        model = YOLO(model_path)
        model.predict(
            source=temp_src, imgsz=1920, device='cpu', agnostic_nms=True,
            save=True, line_width=6, save_txt=True, exist_ok=True
        )

        # 3. 结果整理
        predict_dir = "./runs/segment/predict"
        if not os.path.isdir(predict_dir):
            raise RuntimeError("未找到YOLO的预测输出目录")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_save_dir = os.path.join("./res", f"result_{ts}_{session_id}")
        move_folder_contents(predict_dir, final_save_dir)

        # 4. 统计与格式化输出
        labels_dir = os.path.join(final_save_dir, "labels")
        result_counts = count_first_chars_in_txt_files(labels_dir)
        total = sum(result_counts.values())

        summary_lines = [f"图像 {basename} 的大米 {task_type} 结果分析:"]
        sorted_result = sorted(result_counts.items(), key=lambda x: x[1], reverse=True)

        for char, count in sorted_result:
            percentage = (count / total) * 100 if total > 0 else 0
            label_name = name_map.get(char, f"未知类别({char})")
            summary_lines.append(f"- {label_name}: {count} 个, 占比 {percentage:.2f}%")

        summary_lines.append(f"总计: {total} 个。")

        summary_text = "\n".join(summary_lines)
        annotated_image_path = os.path.join(final_save_dir, basename)

        return {
            "summary": summary_text,
            "annotated_image_path": annotated_image_path
        }

    except Exception as e:
        # 清理临时文件
        if 'temp_src' in locals() and os.path.exists(temp_src):
            shutil.rmtree(temp_src)
        return {"error": f"处理图片时发生未知错误: {e}"}
    finally:
        # 清理runs目录，避免下次运行冲突
        predict_dir = "./runs/segment/predict"
        if os.path.isdir(predict_dir):
            shutil.rmtree(os.path.dirname(predict_dir))