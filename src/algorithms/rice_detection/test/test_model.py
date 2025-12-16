#!/usr/bin/env python3
"""
模型加载和预测测试脚本
用于验证模型是否正确加载和调用
"""

import sys
import os
from pathlib import Path
import base64
import numpy as np
from PIL import Image
import io

# 计算正确的路径
detector_path = Path(__file__).parent.parent / "detector"
sys.path.insert(0, str(detector_path))

# 切换到工作目录
os.chdir(str(detector_path))

# 导入模块
try:
    from app.services.model_service import RiceService
    from app.core.config import settings
    print("✅ 成功导入服务模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[:3]}")
    sys.exit(1)


def test_model_files():
    """测试模型文件是否存在"""
    print("\n📁 检查模型文件...")
    
    # 检查两个模型路径
    model_paths = [
        settings.WEIGHTS_PATH_FL,
        settings.WEIGHTS_PATH_XJ
    ]
    
    for i, path in enumerate(model_paths, 1):
        path_obj = Path(path)
        print(f"模型{i}路径: {path}")
        print(f"绝对路径: {path_obj.absolute()}")
        
        if path_obj.exists():
            size_mb = path_obj.stat().st_size / (1024 * 1024)
            print(f"✅ 模型文件存在，大小: {size_mb:.2f} MB")
        else:
            print(f"❌ 模型文件不存在！")
            return False
    
    return True


def test_model_loading():
    """测试模型加载"""
    print("\n🧠 测试模型加载...")
    
    try:
        # 创建模型服务实例
        print("正在创建RiceService实例...")
        model_service = RiceService(
            weights_path=settings.WEIGHTS_PATH_FL,
            name_map={}
        )
        
        if model_service.model is not None:
            print("✅ 模型加载成功！")
            print(f"模型类型: {type(model_service.model)}")
            
            # 尝试获取模型信息
            try:
                # YOLOv8模型通常有names属性
                if hasattr(model_service.model, 'names'):
                    print(f"检测类别: {len(model_service.model.names)} 种")
                    print(f"类别名称: {list(model_service.model.names.values())}")
                else:
                    print("⚠️ 无法获取类别信息")
                    
            except Exception as e:
                print(f"⚠️ 获取模型信息失败: {e}")
                
            return True, model_service
        else:
            print("❌ 模型对象为None，加载失败！")
            return False, None
            
    except Exception as e:
        print(f"❌ 模型加载异常: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_model_prediction(model_service):
    """测试模型预测功能"""
    print("\n🔍 测试模型预测...")
    
    # 创建一个简单的测试图片
    try:
        # 创建一个简单的彩色图片
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # 转换为PIL图片
        pil_image = Image.fromarray(test_image)
        
        # 转换为base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        print("✅ 测试图片创建成功")
        
        # 使用模型服务进行预测
        print("正在调用模型预测...")
        result = model_service.predict(img_base64)
        
        if result.get('success'):
            print("✅ 模型预测成功！")
            detections = result.get('detections', [])
            
            if detections:
                print("检测结果:")
                for detection in detections:
                    name = detection.get('name', '未知')
                    count = detection.get('count', 0)
                    print(f"  {name}: {count} 个")
            else:
                print("未检测到目标")
                
            return True
        else:
            print(f"❌ 预测失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 预测测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_image(model_service, image_path):
    """使用真实图片测试"""
    print(f"\n🖼️ 使用真实图片测试: {image_path}")
    
    try:
        if not Path(image_path).exists():
            print(f"❌ 图片文件不存在: {image_path}")
            return False
        
        # 读取图片
        with open(image_path, "rb") as f:
            image_data = f.read()
            img_base64 = base64.b64encode(image_data).decode('utf-8')
        
        print("✅ 图片读取成功，开始预测...")
        
        # 调用预测
        result = model_service.predict(img_base64)
        
        if result.get('success'):
            print("✅ 真实图片预测成功！")
            detections = result.get('detections', [])
            
            if detections:
                print("检测结果:")
                for detection in detections:
                    name = detection.get('name', '未知')
                    count = detection.get('count', 0)
                    print(f"  {name}: {count} 个")
            else:
                print("未检测到目标")
            
            return True
        else:
            print(f"❌ 预测失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 真实图片测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 大米识别模型加载和预测测试")
    print("=" * 60)
    
    print(f"工作目录: {os.getcwd()}")
    print(f"当前Python路径: {sys.path[0]}")
    
    # 1. 测试模型文件
    if not test_model_files():
        print("\n❌ 模型文件检查失败！")
        return False
    
    # 2. 测试模型加载
    load_success, model_service = test_model_loading()
    if not load_success:
        print("\n❌ 模型加载失败！")
        return False
    
    # 3. 测试模型预测（使用简单图片）
    if not test_model_prediction(model_service):
        print("\n⚠️ 简单图片预测测试失败，继续真实图片测试...")
    
    # 4. 使用真实图片测试
    test_image_path = "../../../../tests/resources/rice/1.jpg"
    if Path(test_image_path).exists():
        test_with_real_image(model_service, test_image_path)
    else:
        print(f"\n⚠️ 测试图片不存在: {test_image_path}")
        # 尝试绝对路径
        abs_path = "C:/Users/PC/Documents/GitHub/RuralBrain/tests/resources/rice/1.jpg"
        if Path(abs_path).exists():
            test_with_real_image(model_service, abs_path)
    
    print("\n🎉 所有模型测试完成！")
    return True


if __name__ == "__main__":
    import json
    main()