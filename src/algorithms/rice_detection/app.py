import os
import shutil
import uuid
import datetime
import base64  # 新增：用于处理base64编码
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

    temp_image_path = None # 初始化变量以便 finally 清理

    try:
        # --- 修改点 1: 接收 JSON 数据而不是文件流 ---
        data = request.get_json()
        if not data or 'image_base64' not in data:
            return jsonify({"success": False, "message": "请求体必须是JSON且包含 'image_base64' 字段"}), 400
        
        image_base64 = data['image_base64']
        task_type = data.get('task_type', '品种分类')

        # --- 修改点 2: 解码 Base64 并保存为临时文件 ---
        try:
            image_data = base64.b64decode(image_base64)
        except Exception:
            return jsonify({"success": False, "message": "无效的 Base64 字符串"}), 400

        # 生成唯一文件名 (默认为 .jpg，方便YOLO处理)
        unique_filename = f"{uuid.uuid4().hex[:8]}.jpg"
        temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        with open(temp_image_path, "wb") as f:
            f.write(image_data)

        # --- 逻辑保持不变: 模型配置 ---
        if task_type == "品种分类":
            model_name = "best.pt"
            name_map = {"1": "糯米", "2": "丝苗米", "3": "泰国香米", "4": "五常大米", "5": "珍珠大米"}
        else:
            return jsonify({"success": False, "message": "无效的任务类型"}), 400

        model_path = os.path.join(WEIGHTS_DIR, model_name)
        if not os.path.exists(model_path):
            return jsonify({"success": False, "message": f"模型文件未找到: {model_path}"}), 500

        # --- 逻辑保持不变: YOLO预测 ---
        session_id = uuid.uuid4().hex[:8]
        predict_output_dir_name = f"predict_output_{session_id}"

        model = YOLO(model_path)
        model.predict(
            source=temp_image_path,
            imgsz=1920,
            device='cpu',
            save=True,
            save_txt=True,
            exist_ok=True,
            project=RUNS_DIR,
            name=predict_output_dir_name
        )

        # --- 逻辑保持不变: 结果处理 ---
        predict_dir = os.path.join(RUNS_DIR, predict_output_dir_name)
        if not os.path.isdir(predict_dir):
             raise RuntimeError(f"YOLO预测输出目录未成功创建: {predict_dir}")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_save_dir = os.path.join(app.config['RESULT_FOLDER'], f"result_{ts}_{session_id}")
        move_folder_contents(predict_dir, final_save_dir)

        labels_dir = os.path.join(final_save_dir, "labels")
        result_counts = count_first_chars_in_txt_files(labels_dir)
        
        # --- 修改点 3: 构建符合新规范的 detections 列表 ---
        detections = []
        # 按数量排序
        for char, count in sorted(result_counts.items(), key=lambda x: x[1], reverse=True):
            detections.append({
                "name": name_map.get(char, "未知"),
                "count": count
            })

        # --- 修改点 4: 读取结果图片并编码为 Base64 ---
        result_image_path = os.path.join(final_save_dir, unique_filename)
        result_image_base64 = ""
        
        if os.path.exists(result_image_path):
            with open(result_image_path, "rb") as img_f:
                result_image_base64 = base64.b64encode(img_f.read()).decode('utf-8')
        else:
            # 如果没有生成图片（极少数情况），可以留空或报错
            print(f"Warning: Result image not found at {result_image_path}")

        # 清理临时运行目录 (temp_image_path会在finally中清理)
        shutil.rmtree(RUNS_DIR) 

        # --- 修改点 5: 返回符合新规范的 JSON ---
        return jsonify({
            "success": True,
            "detections": detections,
            "result_image": result_image_base64
        })

    except Exception as e:
        print("\n--- ERROR IN /predict ENDPOINT ---")
        traceback.print_exc()
        print("----------------------------------\n")
        return jsonify({"success": False, "message": f"处理请求时发生内部错误: {str(e)}"}), 500
    
    finally:
        # 确保清理上传的临时图片
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception:
                pass

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)