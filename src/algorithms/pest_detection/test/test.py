import base64
import requests
import json
import os
from PIL import Image
import io
from datetime import datetime

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 读取图片并转换为base64编码
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"读取图片失败: {e}")
        return None

# 2. 准备请求数据 - 使用相对路径
image_path = os.path.join(SCRIPT_DIR, "images", "5.jpg")
print(f"使用图片路径: {image_path}")
# 检查文件是否存在
if not os.path.exists(image_path):
    print(f"错误: 图片文件不存在 - {image_path}")
    # 尝试使用其他图片
    alt_path = os.path.join(SCRIPT_DIR, "images", "1.jpg")
    print(f"尝试使用替代路径: {alt_path}")
    image_path = alt_path
base64_image = image_to_base64(image_path)

if base64_image is None:
    print("无法继续，图片转换失败。")
else:
    payload = {
        "image_base64": base64_image
    }
    
    # 3. 发送请求到API
    url = "http://localhost:8001/detect"
    print(f"发送请求到: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)  # 添加超时设置
        
        # 4. 处理响应
        print(f"收到响应，状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n检测结果:")
                print(f"成功状态: {result.get('success', False)}")
                print(f"消息: {result.get('message', '')}")
                
                # 打印响应中所有可用的键
                print(f"\n响应包含的字段: {list(result.keys())}")
                
                if result.get('success', False) and 'detections' in result:
                    detections = result['detections']
                    print(f"\n检测到 {len(detections)} 个目标:")
                    for idx, detection in enumerate(detections):
                        print(f"  {idx + 1}. 类别: {detection.get('name', '未知')}")
                        print(f"     数量: {detection.get('count', 0)}")
                elif 'detections' in result:
                    print(f"\n检测结果 (尽管success为False):")
                    if result['detections'] is not None:
                        print(f"检测到 {len(result['detections'])} 个目标")
                    else:
                        print("detections字段为None")
                else:
                    print("\n未检测到目标或结果格式不包含detections字段")
                
                # 保存JSON结果
                try:
                    # 创建jsonresult目录（使用相对路径）
                    json_output_dir = os.path.join(SCRIPT_DIR, "jsonresult")
                    if not os.path.exists(json_output_dir):
                        os.makedirs(json_output_dir)
                    
                    # 生成JSON文件名（使用时间戳避免重复）
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = f"detection_result_{timestamp}.json"
                    json_path = os.path.join(json_output_dir, json_filename)
                    
                    # 保存JSON结果
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"\nJSON结果已保存至: {json_path}")
                
                except Exception as e:
                    print(f"保存JSON结果失败: {e}")
                
                # 保存返回的标注图像
                if 'result_image' in result and result['result_image']:
                    try:
                        # 解码base64图像
                        img_data = base64.b64decode(result['result_image'])
                        img = Image.open(io.BytesIO(img_data))
                        
                        # 创建output_images目录（使用相对路径）
                        output_dir = os.path.join(SCRIPT_DIR, "output_images")
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        # 生成图像文件名（使用时间戳）
                        img_filename = f"result_{timestamp}.jpg"
                        output_path = os.path.join(output_dir, img_filename)
                        img.save(output_path)
                        print(f"标注图像已保存至: {output_path}")
                    except Exception as e:
                        print(f"保存图像失败: {e}")
                else:
                    print("\n响应中未包含有效图像数据")
                    
            except json.JSONDecodeError:
                print("无法解析响应为JSON格式")
                print(f"响应内容: {response.text}")
        else:
            print(f"请求失败: {response.status_code}")
            try:
                error_info = response.json()
                print(f"错误信息: {error_info}")
                
                # 保存错误响应的JSON
                try:
                    json_output_dir = os.path.join(SCRIPT_DIR, "jsonresult")
                    if not os.path.exists(json_output_dir):
                        os.makedirs(json_output_dir)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = f"error_result_{timestamp}.json"
                    json_path = os.path.join(json_output_dir, json_filename)
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(error_info, f, ensure_ascii=False, indent=2)
                    print(f"错误JSON结果已保存至: {json_path}")
                except Exception as e:
                    print(f"保存错误JSON结果失败: {e}")
                    
            except:
                print(f"响应内容: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("连接错误: 无法连接到服务器。请确保API服务正在运行。")
    except requests.exceptions.Timeout:
        print("请求超时: 服务器响应时间过长")
    except Exception as e:
        print(f"请求过程中发生错误: {e}")

print("\n测试完成")