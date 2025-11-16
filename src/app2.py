# 最终修正版的 app2.py

import os
import shutil
import uuid
import datetime
from collections import defaultdict
from flask import Flask, request, jsonify
from ultralytics import YOLO
import traceback

# --- 1. 使用绝对路径，让应用健壮 ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_ROOT)

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join(PROJECT_ROOT, 'temp_input')
app.config['RESULT_FOLDER'] = os.path.join(PROJECT_ROOT, 'res')
WEIGHTS_DIR = os.path.join(PROJECT_ROOT, 'weights_fl')
# 我们将所有YOLO的临时输出都统一放到这个目录下
RUNS_DIR = os.path.join(PROJECT_ROOT, 'temp_runs') 

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)


# ... (move_folder_contents 和 count_first_chars_in_txt_files 函数保持不变) ...
def move_folder_contents(src_folder, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    for item in os.listdir(src_folder):
        src_item = os.path.join(src_folder, item)
        dest_item = os.path.join(dest_folder, item)
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
    if not os.path.isdir(folder_path): return {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): char_count[line.strip()[0]] += 1
    return dict(char_count)


@app.route('/predict', methods=['POST'])
def predict():
    # 为了防止上次运行失败的残留，先清理一下临时运行目录
    if os.path.isdir(RUNS_DIR):
        shutil.rmtree(RUNS_DIR)
    os.makedirs(RUNS_DIR)

    try:
        if 'image' not in request.files:
            return jsonify({"error": "请求中必须包含 'image' 文件部分"}), 400
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "未选择任何文件"}), 400
        task_type = request.form.get('task_type', '品种分类')

        if task_type == "品种分类":
            model_name = "best.pt"
            name_map = {"1": "糯米", "2": "丝苗米", "3": "泰国香米", "4": "五常大米", "5": "珍珠大米"}
        else:
            return jsonify({"error": "无效的任务类型"}), 400

        model_path = os.path.join(WEIGHTS_DIR, model_name)
        if not os.path.exists(model_path):
            return jsonify({"error": f"模型文件未找到: {model_path}"}), 500

        unique_filename = f"{uuid.uuid4().hex[:8]}_{image_file.filename}"
        temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(temp_image_path)

        # --- 2. 强制指定YOLO的输出目录 (最关键的修复) ---
        session_id = uuid.uuid4().hex[:8]
        # 我们不再关心YOLO是什么任务类型，强制它把结果输出到我们指定的 project 和 name
        predict_output_dir_name = f"predict_output_{session_id}"

        model = YOLO(model_path)
        model.predict(
            source=temp_image_path,
            imgsz=1920,
            device='cpu',
            save=True,
            save_txt=True,
            exist_ok=True,
            project=RUNS_DIR,               # 指定项目目录
            name=predict_output_dir_name    # 指定本次运行的目录名
        )

        # --- 3. 直接定位到我们指定的输出目录，不再猜测 ---
        predict_dir = os.path.join(RUNS_DIR, predict_output_dir_name)
        if not os.path.isdir(predict_dir):
             raise RuntimeError(f"YOLO预测输出目录未成功创建: {predict_dir}")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_save_dir = os.path.join(app.config['RESULT_FOLDER'], f"result_{ts}_{session_id}")
        move_folder_contents(predict_dir, final_save_dir)

        labels_dir = os.path.join(final_save_dir, "labels")
        result_counts = count_first_chars_in_txt_files(labels_dir)
        total = sum(result_counts.values())

        analysis_data = []
        for char, count in sorted(result_counts.items(), key=lambda x: x[1], reverse=True):
            analysis_data.append({
                "label": name_map.get(char, "未知"),
                "count": count,
                "percentage": round((count / total) * 100, 2) if total > 0 else 0
            })

        os.remove(temp_image_path)
        shutil.rmtree(RUNS_DIR) # 清理本次请求的临时目录

        return jsonify({
            "success": True,
            "task_type": task_type,
            "total_count": total,
            "analysis": analysis_data,
            "annotated_image_path": os.path.abspath(os.path.join(final_save_dir, unique_filename))
        })

    except Exception as e:
        print("\n--- ERROR IN /predict ENDPOINT ---")
        traceback.print_exc()
        print("----------------------------------\n")
        return jsonify({"error": "处理请求时发生内部错误", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)