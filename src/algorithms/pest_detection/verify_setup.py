"""
害虫检测模块验证脚本

运行此脚本验证重构后的模块是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试所有关键模块的导入"""
    print("=" * 60)
    print("🧪 测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from src.algorithms.pest_detection.detector.app.core.config import settings
        print("✅ 配置模块导入成功")
        print(f"   - 项目名: {settings.PROJECT_NAME}")
        print(f"   - 模型路径: {settings.MODEL_PATH}")
        print(f"   - 端口: {settings.PORT}")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    try:
        from src.algorithms.pest_detection.detector.app.services.model_service import model_service
        print("✅ 模型服务导入成功")
    except Exception as e:
        print(f"❌ 模型服务导入失败: {e}")
        return False
    
    try:
        from src.algorithms.pest_detection.detector.app.api.routes import router
        print("✅ API路由导入成功")
    except Exception as e:
        print(f"❌ API路由导入失败: {e}")
        return False
    
    try:
        from src.algorithms.pest_detection.detector.app.main import app
        print("✅ FastAPI应用导入成功")
    except Exception as e:
        print(f"❌ FastAPI应用导入失败: {e}")
        return False
    
    return True


def test_file_paths():
    """测试关键文件是否存在"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 文件路径")
    print("=" * 60)
    
    from src.algorithms.pest_detection.detector.app.core.config import settings
    
    model_path = Path(settings.MODEL_PATH)
    classes_path = Path(settings.CLASSES_PATH)
    
    if model_path.exists():
        print(f"✅ 模型文件存在: {model_path}")
        print(f"   - 大小: {model_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"⚠️  模型文件不存在: {model_path}")
        print("   请确保模型文件已正确放置")
    
    if classes_path.exists():
        print(f"✅ 类别文件存在: {classes_path}")
        with open(classes_path, 'r', encoding='utf-8') as f:
            classes = [line.strip() for line in f if line.strip()]
        print(f"   - 类别数量: {len(classes)}")
    else:
        print(f"⚠️  类别文件不存在: {classes_path}")
    
    return True


def test_api_routes():
    """测试API路由配置"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: API路由")
    print("=" * 60)
    
    try:
        from src.algorithms.pest_detection.detector.app.main import app
        
        routes = [route.path for route in app.routes]
        print(f"✅ 发现 {len(routes)} 个路由:")
        for route in routes:
            print(f"   - {route}")
        
        # 检查关键路由
        required_routes = ["/", "/health", "/detect"]
        for route in required_routes:
            if any(route in r for r in routes):
                print(f"✅ 关键路由存在: {route}")
            else:
                print(f"⚠️  关键路由缺失: {route}")
        
        return True
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False


def test_dependencies():
    """测试关键依赖是否安装"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 依赖包")
    print("=" * 60)
    
    dependencies = {
        'fastapi': 'FastAPI框架',
        'uvicorn': 'ASGI服务器',
        'pydantic': '数据验证',
        'pydantic_settings': '配置管理',
        'torch': 'PyTorch',
        'ultralytics': 'YOLOv8',
        'cv2': 'OpenCV',
        'numpy': 'NumPy'
    }
    
    all_ok = True
    for package, description in dependencies.items():
        try:
            if package == 'cv2':
                import cv2
            else:
                __import__(package)
            print(f"✅ {description} ({package})")
        except ImportError:
            print(f"❌ {description} ({package}) - 未安装")
            all_ok = False
    
    return all_ok


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🔍 害虫检测模块验证")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("文件路径", test_file_paths()))
    results.append(("API路由", test_api_routes()))
    results.append(("依赖包", test_dependencies()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！模块已正确配置")
        print("\n下一步:")
        print("  运行服务: python -m src.algorithms.pest_detection.detector.start_service")
        print("  访问文档: http://localhost:8001/docs")
    else:
        print("⚠️  部分测试未通过，请检查上述错误")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
