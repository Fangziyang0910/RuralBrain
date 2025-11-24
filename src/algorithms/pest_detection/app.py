from flask import Flask, request, jsonify, send_file, send_from_directory
import base64
import cv2
import numpy as np
import torch
from pathlib import Path
import os
from ultralytics import YOLO
import sys
import tempfile
import uuid
import time
import json
import hashlib
import hmac
import base64 as b64
from datetime import datetime
import ssl
import websocket
from urllib.parse import urlparse, urlencode

app = Flask(__name__)

# ===== 配置区域 - 在这里修改参数 =====
# 使用基于脚本位置的路径，避免运行时相对路径错误
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent  # 项目根目录
MODEL_PATH = BASE_DIR / "runs" / "detect" / "A5" / "weights" / "best.pt"
SAVE_DIR = BASE_DIR / "runs" / "appdetect"  # 旧路径保留（若仍需其它数据）
RESULT_IMAGES_DIR = ROOT_DIR / "detection_results"
RESULT_IMAGES_DIR.mkdir(exist_ok=True)
EXAMPLES_DIR = BASE_DIR / "examples"
SHOW_RESULT = False
SAVE_RESULT = True

# 星火大模型API配置
SPARK_APPID = "9bbc4395"
SPARK_API_KEY = "959c4b6da071baff6105875059f5deab"
SPARK_API_SECRET = "NzJjODhmNzAwZjg1NjM3ZjI3M2NhNDFk"
SPARK_DOMAIN = "generalv3.5"
SPARK_URL = "wss://spark-api.xf-yun.com/v3.5/chat"
# ===== 配置区域结束 =====

# 确保保存目录存在
save_dir = Path(SAVE_DIR) / "exp"
save_dir.mkdir(parents=True, exist_ok=True)

# 在Windows上设置控制台编码
if sys.platform == "win32":
    try:
        import ctypes
        # 设置控制台输出编码为UTF-8
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
        # 强制刷新编码设置
        os.system("chcp 65001 > nul")
        print("已设置控制台编码为UTF-8")
    except Exception as e:
        print(f"设置控制台编码失败: {e}")

# 英文到中文类名映射
CLASS_NAME_MAPPING = {
    "Melon fly": "瓜实蝇",
    "Diamondback moth": "小菜蛾",
    "Leafminer fly": "斑潜蝇",
    "Tarsonemid mite": "侧多食跗线螨",
    "Rice whitefly": "稻粉虱（白粉虱）",
    "Litchi fruit borer": "荔枝蒂蛀虫",
    "Litchi stink bug": "荔枝蝽",
    "Eriophyes litchii": "荔枝瘿螨",
    "Sugarcane borer": "甘蔗螟虫",
    "Tea green leafhopper": "茶小绿叶蝉",
    "Apple snail": "福寿螺",
    "Maize weevil": "小象甲",
    "Tobacco whitefly": "烟粉虱",
    "rice leaf roller": "稻纵卷叶螟",
    "paddy stem maggot": "大螟",
    "asiatic rice borer": "二化螟",
    "brown plant hopper": "稻飞虱",
    "corn borer": "玉米螟",
    "army worm": "草地贪夜蛾",
    "aphids": "蚜虫",
    "flea beetle": "黄曲条跳甲",
    "beet army worm": "甜菜夜蛾",
    "Thrips": "蔬菜蓟马",
    "Pieris canidia": "菜青虫",
    "Panonchus citri McGregor": "柑桔红蜘蛛",
    "Phyllocoptes oleiverus ashmead": "柑桔锈蜘蛛",
    "Dacus dorsalis(Hendel)": "桔小实蝇",
    "Prodenia litura": "斜纹夜蛾",
    "Phyllocnistis citrella Stainton": "柑桔潜叶蛾"
}

def get_chinese_name(english_name):
    """获取中文类名，如果没有映射则返回英文名"""
    return CLASS_NAME_MAPPING.get(english_name, english_name)

# 加载模型
print("加载YOLOv8模型...")
device = "cuda" if torch.cuda.is_available() else "cpu"
# 确保向 YOLO 传入字符串路径，并在没有 .to 方法时兼容
model = YOLO(str(MODEL_PATH))
try:
    model = model.to(device)
except Exception:
    # 某些 ultralytics 版本的 YOLO 对象可能不支持 .to()
    pass
names = model.names
print("模型加载完成!")

# 对话历史管理
class DialogueManager:
    def __init__(self):
        self.history = []
        self.detected_objects = {}
        self.system_message_added = False
    
    def set_detections(self, detections):
        self.detected_objects = {}
        for det in detections:
            self.detected_objects[det["name"]] = det["count"]
    
    def get_detection_summary(self):
        if not self.detected_objects:
            return "未检测到任何物体"
        return ", ".join([f"{name}({count})" for name, count in self.detected_objects.items()])
    
    def add_history(self, role, content):
        self.history.append({"role": role, "content": content})
    
    def get_formatted_history(self):
        return self.history.copy()
    
    def reset_detections(self):
        self.detected_objects = {}

    def add_system_message(self, content):
        """添加系统消息（只能作为第一条消息）"""
        if not self.system_message_added and not self.history:
            self.history.append({"role": "system", "content": content})
            self.system_message_added = True
            return True
        return False

# 为每个会话创建对话管理器
session_managers = {}

def get_session_manager(session_id):
    if session_id not in session_managers:
        session_managers[session_id] = DialogueManager()
    return session_managers[session_id]

# 星火大模型API调用
def spark_api_query(manager, user_input=None, max_retries=2):
    """调用星火大模型API，增加重试机制"""
    for attempt in range(max_retries + 1):
        try:
            class WsParam:
                def __init__(self, appid, api_key, api_secret, spark_url):
                    self.appid = appid
                    self.api_key = api_key
                    self.api_secret = api_secret
                    self.host = urlparse(spark_url).netloc
                    self.path = urlparse(spark_url).path
                    self.spark_url = spark_url

                def create_url(self):
                    # 使用UTC时间而不是本地时间
                    now = datetime.utcnow()
                    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    
                    signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
                    signature_sha = hmac.new(
                        self.api_secret.encode('utf-8'),
                        signature_origin.encode('utf-8'),
                        digestmod=hashlib.sha256
                    ).digest()
                    signature_sha_base64 = b64.b64encode(signature_sha).decode()
                    
                    authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
                    authorization = b64.b64encode(authorization_origin.encode()).decode()
                    
                    return f"{self.spark_url}?{urlencode({'authorization': authorization, 'date': date, 'host': self.host})}"

            # 准备对话历史
            messages = manager.get_formatted_history()
            if user_input:
                manager.add_history("user", user_input)
                messages.append({"role": "user", "content": user_input})
            
            # 构建请求
            data = {
                "header": {"app_id": SPARK_APPID, "uid": "1234"},
                "parameter": {"chat": {
                    "domain": SPARK_DOMAIN,
                    "temperature": 0.8,
                    "max_tokens": 2048,
                    "top_k": 5,
                    "auditing": "default"
                }},
                "payload": {"message": {"text": messages}}
            }

            # 创建WebSocket连接
            ws_param = WsParam(SPARK_APPID, SPARK_API_KEY, SPARK_API_SECRET, SPARK_URL)
            ws_url = ws_param.create_url()
            
            response = []
            completed = False
            start_time = time.time()

            def on_message(ws, message):
                nonlocal response, completed
                data = json.loads(message)
                if data['header']['code'] != 0:
                    print(f"API错误: {data['header']['code']}, {data['header']['message']}")
                    completed = True
                    return
                
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                response.append(content)
                
                if status == 2:
                    completed = True
                    ws.close()

            def on_error(ws, error):
                print(f"WebSocket错误: {error}")
                nonlocal completed
                completed = True

            def on_close(ws, close_status_code, close_msg):
                nonlocal completed
                completed = True

            def on_open(ws):
                ws.send(json.dumps(data))

            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # 设置更长的超时时间和ping间隔
            ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=30,  # 增加ping的间隔时间
                ping_timeout=15    # 减少超时时间，确保ping_interval > ping_timeout
            )
            
            # 等待响应完成，延长等待时间
            while not completed:
                if time.time() - start_time > 90:  # 90秒超时
                    raise TimeoutError("API调用超时")
                time.sleep(0.2)  # 减少循环频率
            
            # 添加AI回复到对话历史
            ai_response = "".join(response)
            manager.add_history("assistant", ai_response)
            
            return ai_response
            
        except (TimeoutError, websocket.WebSocketTimeoutException, OSError) as e:
            print(f"第{attempt+1}次尝试失败: {str(e)}")
            if attempt < max_retries:
                print(f"正在重试({attempt+1}/{max_retries})...")
                time.sleep(3)  # 重试前等待
                continue
            else:
                return "对不起，API调用失败，请检查网络连接或稍后再试"
        except Exception as e:
            print(f"第{attempt+1}次尝试失败: {str(e)}")
            if attempt < max_retries:
                print(f"正在重试({attempt+1}/{max_retries})...")
                time.sleep(3)
                continue
            else:
                return "API调用发生错误，请稍后再试"

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/get_examples')
def get_examples():
    """获取示例图片列表"""
    try:
        examples_dir = Path(EXAMPLES_DIR)
        if not examples_dir.exists():
            return jsonify({"success": False, "message": "示例图片目录不存在"}), 404
        
        # 获取所有图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        images = []
        
        for file_path in examples_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                images.append(file_path.name)
        
        # 按文件名排序
        images.sort()
        
        return jsonify({
            "success": True,
            "images": images
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/examples/<filename>')
def serve_example_image(filename):
    """提供示例图片文件访问"""
    try:
        examples_dir = Path(EXAMPLES_DIR)
        return send_from_directory(examples_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/detect', methods=['POST'])
def detect():
    try:
        # 获取请求数据
        data = request.json
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # 处理图像输入
        if 'example_image' in data:
            # 使用示例图片
            example_filename = data['example_image']
            examples_dir = Path(EXAMPLES_DIR)
            temp_path = examples_dir / example_filename
            
            if not temp_path.exists():
                return jsonify({
                    "success": False,
                    "message": f"示例图片 {example_filename} 不存在"
                }), 404
            
            # 读取示例图片
            img = cv2.imread(str(temp_path))
            if img is None:
                return jsonify({
                    "success": False,
                    "message": f"无法读取示例图片 {example_filename}"
                }), 400
                
        elif 'image' in data:
            # 使用上传的图片
            image_data = data['image']
            
            # 将Base64转换为图像
            img_bytes = base64.b64decode(image_data)
            img_np = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            
            # 保存临时文件
            temp_path = save_dir / "temp_image.jpg"
            cv2.imwrite(str(temp_path), img)
        else:
            return jsonify({
                "success": False,
                "message": "缺少图像数据"
            }), 400
        
        # 进行推理
        results = model(temp_path)
        
        # 处理结果
        detections = []
        detected_objects = {}
        
        for result in results:
            # 记录检测到的物体
            for box in result.boxes:
                cls = int(box.cls.item())
                english_name = names[cls]
                chinese_name = get_chinese_name(english_name)
                detected_objects[chinese_name] = detected_objects.get(chinese_name, 0) + 1
            
            # 绘制结果
            im0 = result.orig_img.copy()
            if hasattr(result, "plot"):
                im0 = result.plot()
            else:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = box.conf.item()
                    cls = int(box.cls.item())
                    english_name = names[cls]
                    chinese_name = get_chinese_name(english_name)
                    label = f"{chinese_name} {conf:.2f}"
                    
                    # 绘制边界框
                    color = (0, 255, 0)  # 绿色
                    cv2.rectangle(im0, (x1, y1), (x2, y2), color, 2)
                    
                    # 添加标签
                    cv2.putText(im0, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 保存结果图像到根目录 detection_results
        result_path = str(RESULT_IMAGES_DIR / f"result_{session_id}.jpg")
        cv2.imwrite(result_path, im0)
        
        # 准备检测结果
        for chinese_name, count in detected_objects.items():
            detections.append({
                "name": chinese_name,
                "count": count
            })
        
        # 初始化对话管理器
        manager = get_session_manager(session_id)
        manager.set_detections(detections)
        manager.add_system_message(f"本次检测到的物体: {manager.get_detection_summary()}")
        
        # 获取害虫信息
        for detection in detections:
            try:
                manager.add_history("user", f"请详细介绍{detection['name']}的相关信息")
                response = spark_api_query(manager, None)
                detection["description"] = response
            except Exception as e:
                detection["description"] = f"获取信息失败: {str(e)}"
        
        # 读取结果图像
        with open(result_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 删除临时文件（仅当是上传的图片时）
        if 'image' in data and temp_path.name == "temp_image.jpg":
            try:
                os.unlink(temp_path)
            except:
                pass  # 忽略删除失败的错误
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "result_image": encoded_image,
            "detections": detections
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        question = data['question']
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"success": False, "message": "缺少会话ID"}), 400
        
        manager = get_session_manager(session_id)
        
        # 调用大模型API
        response = spark_api_query(manager, question)
        
        return jsonify({
            "success": True,
            "answer": response
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)