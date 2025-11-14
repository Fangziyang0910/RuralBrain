import os
import shutil
import uuid
import datetime
from collections import defaultdict
from flask import Flask, request, jsonify  # 导入 jsonify
from ultralytics import YOLO


# --- 我们在方法二中已经创建好的核心逻辑 ---
# 为了让 app.py 能够独立运行，我们把这些函数也包含进来

def move_folder_contents(src_folder, dest_folder):
    # (此函数内容与 rice_recognizer.py 中的完全一致，直接复用)
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
    # (此函数内容与 rice_recognizer.py 中的完全一致，直接复用)
    char_count = defaultdict(int)
    if not os.path.isdir(folder_path): return {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): char_count[line.strip()[0]] += 1
    return dict(char_count)


# --- Flask 应用初始化 ---
app = Flask(__name__)
# 我们直接在项目根目录操作，简化路径
app.config['UPLOAD_FOLDER'] = '../temp_input'  # API服务器在src下，所以路径要向上级'../'
app.config['RESULT_FOLDER'] = '../res'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)


@app.route('/predict', methods=['POST'])
def predict():
    # 1. 验证输入
    if 'image' not in request.files:
        return jsonify({"error": "请求中必须包含 'image' 文件部分"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "未选择任何文件"}), 400

    task_type = request.form.get('task_type', '品种分类')

    # 2. 根据任务类型选择模型
    if task_type == "品种分类":
        weights_dir = "../weights_fl"
        model_name = "best.pt"
        name_map = {"1": "糯米", "2": "丝苗米", "3": "泰国香米", "4": "五常大米", "5": "珍珠大米"}
    elif task_type == "新旧识别":
        weights_dir = "../weights_xj"
        model_name = "best.pt"
        name_map = {"1": "新米", "2": "旧米"}
    else:
        return jsonify({"error": "无效的任务类型"}), 400

    model_path = os.path.join(weights_dir, model_name)
    if not os.path.exists(model_path):
        return jsonify({"error": f"模型文件未找到: {model_path}"}), 500

    # 3. 保存临时图片并执行预测
    try:
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(temp_path)

        session_id = uuid.uuid4().hex[:8]
        temp_src = os.path.join(app.config['UPLOAD_FOLDER'], f"in_{session_id}")
        os.makedirs(temp_src, exist_ok=True)
        shutil.copy2(temp_path, os.path.join(temp_src, image.filename))

        model = YOLO(model_path)
        model.predict(source=temp_src, imgsz=1920, device='cpu', save=True, save_txt=True, exist_ok=True)

        predict_dir = "../runs/segment/predict"
        if not os.path.isdir(predict_dir):
            raise RuntimeError("未找到YOLO预测输出目录")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_save_dir = os.path.join(app.config['RESULT_FOLDER'], f"result_{ts}_{session_id}")
        move_folder_contents(predict_dir, final_save_dir)

        # 4. 统计并构建 JSON 响应
        labels_dir = os.path.join(final_save_dir, "labels")
        result_counts = count_first_chars_in_txt_files(labels_dir)
        total = sum(result_counts.values())

        # 构建结构化的数据
        analysis_data = []
        for char, count in sorted(result_counts.items(), key=lambda x: x[1], reverse=True):
            analysis_data.append({
                "label": name_map.get(char, "未知"),
                "count": count,
                "percentage": round((count / total) * 100, 2) if total > 0 else 0
            })

        # 清理临时文件
        shutil.rmtree(temp_src)
        if os.path.isdir("./runs"): shutil.rmtree("./runs")

        # 返回最终的 JSON 数据！
        return jsonify({
            "success": True,
            "task_type": task_type,
            "total_count": total,
            "analysis": analysis_data,
            "annotated_image_path": os.path.abspath(os.path.join(final_save_dir, image.filename))
        })

    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500


if __name__ == '__main__':
    # 监听 0.0.0.0 可以让局域网内其他机器也访问，127.0.0.1 只有本机可以
    app.run(debug=True, host='127.0.0.1', port=8081)