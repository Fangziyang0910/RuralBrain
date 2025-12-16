#!/usr/bin/env python3
"""
大米识别服务测试脚本
用于测试FastAPI服务是否正常工作
"""

import base64
import requests
import json
from pathlib import Path


def test_rice_detection_service():
    """测试大米识别服务"""
    
    # FastAPI服务地址
    base_url = "http://127.0.0.1:8081"
    
    # 测试图片路径 - 使用绝对路径
    test_images = [
        "C:/Users/PC/Documents/GitHub/RuralBrain/tests/resources/rice/1.jpg",
        "C:/Users/PC/Documents/GitHub/RuralBrain/tests/resources/rice/2.jpg"
    ]
    
    print("🧪 开始测试大米识别服务...")
    print(f"📍 服务地址: {base_url}")
    
    # 1. 测试健康检查接口
    print("\n1️⃣ 测试健康检查接口...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            print(f"✅ 健康检查通过: {health_response.json()}")
        else:
            print(f"❌ 健康检查失败: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 测试根路径
    print("\n2️⃣ 测试根路径...")
    try:
        root_response = requests.get(f"{base_url}/", timeout=10)
        if root_response.status_code == 200:
            print(f"✅ 根路径正常: {root_response.json()}")
        else:
            print(f"❌ 根路径异常: {root_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 根路径异常: {e}")
        return False
    
    # 3. 测试图片识别接口
    print("\n3️⃣ 测试图片识别接口...")
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n📸 测试图片 {i}: {image_path}")
        
        # 检查图片是否存在
        if not Path(image_path).exists():
            print(f"❌ 图片不存在: {image_path}")
            continue
        
        try:
            # 读取图片并转换为base64
            with open(image_path, "rb") as f:
                image_data = f.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
            
            # 准备请求数据
            payload = {
                "image_base64": base64_string
            }
            
            # 发送识别请求
            print("🔍 正在识别...")
            response = requests.post(
                f"{base_url}/predict",
                json=payload,
                timeout=30  # 识别可能需要一些时间
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 识别成功!")
                    print(f"📊 检测结果: {len(result.get('detections', []))} 个目标")
                    
                    # 显示检测详情
                    detections = result.get('detections', [])
                    for j, detection in enumerate(detections):
                        name = detection.get('name', '未知')
                        count = detection.get('count', 0)
                        print(f"   🎯 {name}: {count} 个")
                else:
                    print(f"❌ 识别失败: {result.get('message', '未知错误')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"📄 错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    print("\n🎉 所有测试完成！")
    return True


def test_api_docs():
    """测试API文档"""
    print("\n📚 测试API文档...")
    
    base_url = "http://127.0.0.1:8081"
    
    try:
        docs_response = requests.get(f"{base_url}/docs", timeout=10)
        if docs_response.status_code == 200:
            print("✅ API文档可访问")
            return True
        else:
            print(f"❌ API文档访问失败: {docs_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API文档访问异常: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🌾 大米识别服务测试工具")
    print("=" * 50)
    
    # 确保服务正在运行
    print("\n⏳ 请确保FastAPI服务正在运行...")
    print("   如果未运行，请在另一个终端执行:")
    print("   uvicorn src.algorithms.rice_detection.detector.app.main:app --reload --port 8081")
    
    input("\n按回车键开始测试...")
    
    # 运行测试
    success = test_rice_detection_service()
    
    if success:
        print("\n🎊 测试通过！服务运行正常。")
    else:
        print("\n💥 测试失败！请检查服务状态和配置。")