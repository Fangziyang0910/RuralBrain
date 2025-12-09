#!/usr/bin/env python3
"""
测试牛只检测API的详细检测功能
"""

import requests
import base64
import json
import os
from pathlib import Path

def test_detailed_detection():
    """测试详细检测API"""
    
    # API端点
    base_url = "http://localhost:8002"
    detailed_endpoint = f"{base_url}/detect-detailed"
    regular_endpoint = f"{base_url}/detect"
    
    # 查找测试图像
    project_root = Path(__file__).parent.parent.parent.parent.parent
    test_image_paths = [
        project_root / "tests/resources/cows/1.jpg",
        project_root / "tests/resources/cows/2.jpg",
        project_root / "tests/resources/cows/3.jpg",
    ]
    
    test_image_path = None
    for path in test_image_paths:
        if path.exists():
            test_image_path = path
            break
    
    if not test_image_path:
        print("未找到测试图像，跳过测试")
        return
    
    print(f"使用测试图像: {test_image_path}")
    
    # 读取图像并转换为base64
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode()
    
    # 测试常规检测API
    print("\n=== 测试常规检测API ===")
    try:
        response = requests.post(
            regular_endpoint,
            json={"image_base64": image_b64},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 常规检测API调用成功")
            print(f"检测到 {len(result.get('detections', []))} 种牛只")
            for detection in result.get('detections', []):
                print(f"- {detection['name']}: {detection['count']}个")
        else:
            print(f"❌ 常规检测API调用失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 常规检测API调用异常: {str(e)}")
    
    # 测试详细检测API
    print("\n=== 测试详细检测API ===")
    try:
        response = requests.post(
            detailed_endpoint,
            json={"image_base64": image_b64},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 详细检测API调用成功")
            print(f"检测到 {len(result.get('detections', []))} 种牛只")
            for detection in result.get('detections', []):
                print(f"- {detection['name']}: {detection['count']}个")
            
            # 显示详细信息
            print("\n详细信息:")
            image_info = result.get('image_info', {})
            print(f"图像尺寸: {image_info.get('width')}x{image_info.get('height')}")
            print(f"检测到的牛只总数: {image_info.get('total_cows')}")
            
            detailed_detections = result.get('detailed_detections', [])
            print(f"\n详细检测信息 ({len(detailed_detections)}个牛只):")
            for i, detection in enumerate(detailed_detections):
                print(f"\n牛只 #{i+1}:")
                print(f"- 类别: {detection.get('class_name')}")
                print(f"- 置信度: {detection.get('confidence'):.2f}")
                print(f"- 边界框: {detection.get('bbox')}")
                print(f"- 中心点: {detection.get('center')}")
                
                size = detection.get('size', {})
                print(f"- 大小: 宽度={size.get('width'):.1f}px, 高度={size.get('height'):.1f}px, 面积={size.get('area'):.1f}px²")
                
                rel_pos = detection.get('relative_position', {})
                print(f"- 相对位置: x={rel_pos.get('x'):.2f}, y={rel_pos.get('y'):.2f}")
            
            # 保存结果图像
            result_image_b64 = result.get('result_image', '')
            if result_image_b64:
                result_image_data = base64.b64decode(result_image_b64)
                result_path = Path(__file__).parent / "detection_result.jpg"
                with open(result_path, 'wb') as f:
                    f.write(result_image_data)
                print(f"\n结果图像已保存到: {result_path}")
            
        else:
            print(f"❌ 详细检测API调用失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 详细检测API调用异常: {str(e)}")

if __name__ == "__main__":
    test_detailed_detection()