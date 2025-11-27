#!/usr/bin/env python3
"""
FastAPI API测试客户端
用于测试FastAPI API的各种功能
"""

import os
import sys
import json
import requests
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """测试健康检查接口"""
    print("测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print("-" * 50)
    return response.status_code == 200

def test_root():
    """测试根路径接口"""
    print("测试根路径接口...")
    response = requests.get(f"{BASE_URL}/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print("-" * 50)
    return response.status_code == 200

def test_image_detection():
    """测试图像检测接口"""
    print("测试图像检测接口...")
    
    # 查找测试图像
    test_image_path = None
    possible_paths = [
        "train14/train_batch0.jpg",
        "train14/train_batch1.jpg",
        "train14/train_batch2.jpg",
        "uploads/train_batch0.jpg",
        "uploads/train_batch2.jpg"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            test_image_path = path
            break
    
    if not test_image_path:
        print("未找到测试图像，跳过图像检测测试")
        return False
    
    print(f"使用测试图像: {test_image_path}")
    
    # 准备文件上传
    with open(test_image_path, "rb") as f:
        files = {"file": (os.path.basename(test_image_path), f, "image/jpeg")}
        data = {"confidence_threshold": 0.5, "return_image": False}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/detection/image",
            files=files,
            data=data
        )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print("-" * 50)
    return response.status_code == 200

def test_agent_chat():
    """测试Agent对话接口"""
    print("测试Agent对话接口...")
    
    # 查找测试图像
    test_image_path = None
    possible_paths = [
        "train14/train_batch0.jpg",
        "train14/train_batch1.jpg",
        "train14/train_batch2.jpg",
        "uploads/train_batch0.jpg",
        "uploads/train_batch2.jpg"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            test_image_path = path
            break
    
    # 测试简单对话
    data = {
        "message": "你好，我想了解一下牛的养殖知识",
        "thread_id": "test_session_123"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/agent/chat",
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    # 如果有测试图像，测试带图像的对话
    if test_image_path:
        print("\n测试带图像的对话...")
        data_with_image = {
            "message": "请分析这张图片中的牛只情况",
            "thread_id": "test_session_123",
            "image_path": test_image_path
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/agent/chat",
            json=data_with_image
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    
    print("-" * 50)
    return response.status_code == 200

def test_api_docs():
    """测试API文档接口"""
    print("测试API文档接口...")
    
    # 测试Swagger UI
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Swagger UI状态码: {response.status_code}")
    
    # 测试ReDoc
    response = requests.get(f"{BASE_URL}/redoc")
    print(f"ReDoc状态码: {response.status_code}")
    
    # 测试OpenAPI JSON
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"OpenAPI JSON状态码: {response.status_code}")
    if response.status_code == 200:
        openapi_data = response.json()
        print(f"API标题: {openapi_data.get('info', {}).get('title')}")
        print(f"API版本: {openapi_data.get('info', {}).get('version')}")
        print(f"可用端点数量: {len(openapi_data.get('paths', {}))}")
    
    print("-" * 50)
    return True

def main():
    """主测试函数"""
    print("FastAPI API测试客户端")
    print("=" * 50)
    
    # 检查API服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到API服务 {BASE_URL}")
        print("请确保FastAPI服务正在运行:")
        print("python tests/test_fastapi_basic.py")
        return
    except requests.exceptions.Timeout:
        print(f"错误: 连接API服务超时 {BASE_URL}")
        return
    
    # 运行测试
    test_results = []
    
    test_results.append(("健康检查", test_health_check()))
    test_results.append(("根路径", test_root()))
    test_results.append(("API文档", test_api_docs()))
    test_results.append(("图像检测", test_image_detection()))
    test_results.append(("Agent对话", test_agent_chat()))
    
    # 打印测试结果摘要
    print("\n测试结果摘要:")
    print("=" * 50)
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(test_results)} 测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败，请检查日志")

if __name__ == "__main__":
    main()