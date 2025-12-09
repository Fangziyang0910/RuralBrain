#!/usr/bin/env python3
"""
测试cow_detection FastAPI服务的脚本
"""

import os
import sys
import base64
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 服务配置
API_BASE_URL = "http://127.0.0.1:8002"
TEST_IMAGES_DIR = Path(__file__).parent.parent.parent.parent.parent / "tests" / "resources" / "cows"

def encode_image_to_base64(image_path):
    """将图像文件编码为base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def test_health_check():
    """测试健康检查端点"""
    print("测试健康检查端点...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {str(e)}")
        return False

def test_detailed_health_check():
    """测试详细健康检查端点"""
    print("\n测试详细健康检查端点...")
    try:
        response = requests.get(f"{API_BASE_URL}/health/detailed")
        if response.status_code == 200:
            print("✅ 详细健康检查通过")
            health_data = response.json()
            print(f"服务状态: {health_data.get('status')}")
            return True
        else:
            print(f"❌ 详细健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 详细健康检查异常: {str(e)}")
        return False

def test_supported_cows():
    """测试支持的牛只类型端点"""
    print("\n测试支持的牛只类型端点...")
    try:
        response = requests.get(f"{API_BASE_URL}/supported-cows")
        if response.status_code == 200:
            print("✅ 获取支持的牛只类型成功")
            data = response.json()
            print(f"支持的牛只类型数量: {data.get('total_count', 0)}")
            return True
        else:
            print(f"❌ 获取支持的牛只类型失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取支持的牛只类型异常: {str(e)}")
        return False

def test_cow_detection(image_path):
    """测试牛只检测端点"""
    print(f"\n测试牛只检测，图像: {image_path.name}...")
    try:
        # 编码图像
        image_b64 = encode_image_to_base64(image_path)
        
        # 发送请求
        payload = {"image_base64": image_b64}
        response = requests.post(
            f"{API_BASE_URL}/detect",
            json=payload,
            timeout=30  # 设置超时时间为30秒
        )
        
        if response.status_code == 200:
            print("✅ 检测请求成功")
            result = response.json()
            
            if result.get("success"):
                detections = result.get("detections", [])
                print(f"检测到 {len(detections)} 种牛只")
                for detection in detections:
                    print(f"- {detection.get('name', '未知')}: {detection.get('count', 0)}个")
                return True
            else:
                print(f"❌ 检测失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 检测请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 检测异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始测试cow_detection FastAPI服务...")
    print(f"API基础URL: {API_BASE_URL}")
    print(f"测试图像目录: {TEST_IMAGES_DIR}")
    
    # 检查测试图像目录是否存在
    if not TEST_IMAGES_DIR.exists():
        print(f"❌ 测试图像目录不存在: {TEST_IMAGES_DIR}")
        return
    
    # 获取测试图像列表
    test_images = list(TEST_IMAGES_DIR.glob("*.jpg"))[:3]  # 只测试前3张图像
    if not test_images:
        print(f"❌ 在目录 {TEST_IMAGES_DIR} 中没有找到测试图像")
        return
    
    print(f"找到 {len(test_images)} 张测试图像")
    
    # 测试各个端点
    results = {}
    
    # 测试健康检查
    results["health_check"] = test_health_check()
    
    # 测试详细健康检查
    results["detailed_health_check"] = test_detailed_health_check()
    
    # 测试支持的牛只类型
    results["supported_cows"] = test_supported_cows()
    
    # 测试牛只检测
    detection_results = []
    for image_path in test_images:
        result = test_cow_detection(image_path)
        detection_results.append(result)
    
    results["cow_detection"] = all(detection_results) if detection_results else False
    
    # 打印测试结果总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    overall_success = all(results.values())
    print(f"\n总体结果: {'✅ 所有测试通过' if overall_success else '❌ 部分测试失败'}")
    
    if not overall_success:
        print("\n请检查:")
        "1. cow_detection服务是否已启动"
        "2. 服务端口是否正确 (默认8000)"
        "3. 模型文件是否已正确加载"

if __name__ == "__main__":
    main()