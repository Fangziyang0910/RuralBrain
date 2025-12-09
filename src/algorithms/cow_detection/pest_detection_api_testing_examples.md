# Pest Detection API测试Agent功能示例

## 概述

本文档提供了使用Pest Detection API文档测试agent功能的具体示例和最佳实践。这些示例可以帮助理解和评估AI agent的功能健全性。

## API文档访问与测试

### 1. 访问API文档

启动Pest Detection服务后，可通过以下URL访问API文档：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 2. 核心测试端点

#### 2.1 害虫检测接口 (/detect)

**功能测试：**
1. 上传包含害虫的图像
2. 验证返回的检测结果
3. 检查标注图像的准确性

**测试步骤：**
1. 在API文档页面找到POST /detect端点
2. 点击"Try it out"按钮
3. 准备测试图像的base64编码
4. 执行请求并分析响应

**示例请求：**
```json
{
  "image_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
}
```

**预期响应：**
```json
{
  "success": true,
  "detections": [
    {
      "name": "瓜实蝇",
      "count": 2
    },
    {
      "name": "蚜虫",
      "count": 1
    }
  ],
  "result_image": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
}
```

#### 2.2 支持的害虫类型接口 (/supported-pests)

**功能测试：**
1. 验证返回的害虫类型列表完整性
2. 检查害虫类型的中英文名称映射
3. 确认与实际检测能力一致

**测试步骤：**
1. 在API文档页面找到GET /supported-pests端点
2. 点击"Try it out"按钮
3. 执行请求并分析响应

**预期响应：**
```json
{
  "pests": [
    {
      "id": 0,
      "name": "瓜实蝇",
      "name_en": "Bactrocera cucurbitae"
    },
    {
      "id": 1,
      "name": "蚜虫",
      "name_en": "Aphid"
    }
    // ... 更多害虫类型
  ],
  "total": 29
}
```

#### 2.3 健康检查接口 (/health/detailed)

**功能测试：**
1. 验证服务运行状态
2. 检查模型加载状态
3. 确认依赖库可用性

**测试步骤：**
1. 在API文档页面找到GET /health/detailed端点
2. 点击"Try it out"按钮
3. 执行请求并分析响应

**预期响应：**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "dependencies": {
    "torch": "1.9.0",
    "ultralytics": "8.0.0",
    "PIL": "8.3.2"
  },
  "file_system": {
    "model_file_exists": true,
    "class_file_exists": true
  }
}
```

## Agent功能测试场景

### 1. 基本功能测试

**场景1：正常害虫检测**
- 目的：验证基本的害虫检测功能
- 步骤：上传包含害虫的图像，检查检测结果
- 预期：正确识别害虫类型和数量

**场景2：无害虫图像**
- 目的：验证对无害虫图像的处理
- 步骤：上传不包含害虫的图像，检查检测结果
- 预期：返回空检测结果或"未检测到害虫"

**场景3：多害虫图像**
- 目的：验证对多种害虫的检测能力
- 步骤：上传包含多种害虫的图像，检查检测结果
- 预期：正确识别所有害虫类型和数量

### 2. 边界条件测试

**场景1：低质量图像**
- 目的：验证对低质量图像的处理能力
- 步骤：上传模糊、低分辨率的图像，检查检测结果
- 预期：给出适当的提示或处理结果

**场景2：超大图像**
- 目的：验证对大尺寸图像的处理能力
- 步骤：上传高分辨率大尺寸图像，检查处理时间和结果
- 预期：在合理时间内返回结果

**场景3：非标准格式**
- 目的：验证对非标准图像格式的处理
- 步骤：上传非标准格式图像，检查错误处理
- 预期：返回适当的错误信息

### 3. 异常处理测试

**场景1：无效base64编码**
- 目的：验证对无效base64编码的处理
- 步骤：发送无效的base64编码，检查错误处理
- 预期：返回400错误和详细错误信息

**场景2：空请求**
- 目的：验证对空请求的处理
- 步骤：发送空请求体，检查错误处理
- 预期：返回422错误和详细错误信息

**场景3：服务不可用**
- 目的：验证服务不可用时的处理
- 步骤：停止服务后发送请求，检查错误处理
- 预期：返回连接错误或超时

## Agent工具集成测试

### 1. 使用pest_detection_tool测试

```python
# 测试代码示例
from src.agents.tools.pest_detection_tool import pest_detection_tool

# 测试基本功能
def test_basic_detection():
    image_path = "test_images/pest_1.jpg"
    result = pest_detection_tool(image_path)
    print(f"检测结果: {result}")
    
    # 验证结果格式
    assert "检测到" in result or "未检测到" in result
    assert "害虫" in result

# 测试错误处理
def test_error_handling():
    try:
        # 测试不存在的文件
        result = pest_detection_tool("non_existent_file.jpg")
        print(f"错误处理结果: {result}")
    except Exception as e:
        print(f"捕获到异常: {e}")
```

### 2. 使用LangChain Agent测试

```python
# 测试代码示例
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from src.agents.tools.pest_detection_tool import pest_detection_tool

# 创建工具
tools = [
    Tool(
        name="Pest Detection",
        func=pest_detection_tool,
        description="分析图片中的害虫种类和数量"
    )
]

# 初始化agent
llm = OpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

# 测试agent功能
def test_agent_functionality():
    query = "请分析这张图片中的害虫情况：test_images/pest_1.jpg"
    result = agent.run(query)
    print(f"Agent分析结果: {result}")
    
    # 验证agent理解能力
    assert "害虫" in result
    assert "分析" in result or "检测" in result
```

## 性能测试

### 1. 响应时间测试

```python
import time
import requests
import base64

def test_response_time():
    # 准备测试图像
    with open("test_images/pest_1.jpg", "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode()
    
    # 测试多次请求的响应时间
    times = []
    for i in range(10):
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8001/detect",
            json={"image_base64": image_base64}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        times.append(response_time)
        
        print(f"请求 {i+1} 响应时间: {response_time:.2f}秒")
    
    # 计算平均响应时间
    avg_time = sum(times) / len(times)
    print(f"平均响应时间: {avg_time:.2f}秒")
```

### 2. 并发请求测试

```python
import threading
import requests
import base64

def test_concurrent_requests():
    # 准备测试图像
    with open("test_images/pest_1.jpg", "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode()
    
    # 定义请求函数
    def send_request():
        response = requests.post(
            "http://localhost:8001/detect",
            json={"image_base64": image_base64}
        )
        print(f"响应状态码: {response.status_code}")
    
    # 创建并启动多个线程
    threads = []
    for i in range(5):
        thread = threading.Thread(target=send_request)
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print("并发请求测试完成")
```

## 测试结果分析

### 1. 功能健全性评估

基于API文档测试结果，可以从以下方面评估agent功能健全性：

- **准确性**：检测结果是否准确
- **完整性**：是否覆盖所有支持的害虫类型
- **稳定性**：在不同条件下是否稳定工作
- **可用性**：错误信息是否清晰有用

### 2. 性能评估

- **响应时间**：是否在可接受范围内
- **并发能力**：是否能处理多个并发请求
- **资源使用**：内存和CPU使用是否合理

### 3. 用户体验评估

- **文档质量**：API文档是否清晰完整
- **错误处理**：错误信息是否友好
- **易用性**：是否容易集成和使用

## 测试自动化

### 1. 自动化测试脚本

```python
import requests
import base64
import json
import os

class PestDetectionTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
    
    def test_detection_endpoint(self, image_path):
        """测试检测端点"""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode()
            
            response = requests.post(
                f"{self.base_url}/detect",
                json={"image_base64": image_base64}
            )
            
            result = {
                "test": "detection_endpoint",
                "image": os.path.basename(image_path),
                "status_code": response.status_code,
                "success": response.json().get("success", False),
                "detections": response.json().get("detections", [])
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "test": "detection_endpoint",
                "image": os.path.basename(image_path),
                "error": str(e)
            }
            self.test_results.append(error_result)
            return error_result
    
    def test_supported_pests(self):
        """测试支持的害虫类型端点"""
        try:
            response = requests.get(f"{self.base_url}/supported-pests")
            result = {
                "test": "supported_pests",
                "status_code": response.status_code,
                "total_pests": response.json().get("total", 0)
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "test": "supported_pests",
                "error": str(e)
            }
            self.test_results.append(error_result)
            return error_result
    
    def test_health_check(self):
        """测试健康检查端点"""
        try:
            response = requests.get(f"{self.base_url}/health/detailed")
            result = {
                "test": "health_check",
                "status_code": response.status_code,
                "status": response.json().get("status", "unknown")
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "test": "health_check",
                "error": str(e)
            }
            self.test_results.append(error_result)
            return error_result
    
    def run_all_tests(self, test_images_dir):
        """运行所有测试"""
        # 测试健康检查
        self.test_health_check()
        
        # 测试支持的害虫类型
        self.test_supported_pests()
        
        # 测试检测功能
        for image_file in os.listdir(test_images_dir):
            if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(test_images_dir, image_file)
                self.test_detection_endpoint(image_path)
        
        # 保存测试结果
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        return self.test_results

# 使用示例
if __name__ == "__main__":
    tester = PestDetectionTester()
    results = tester.run_all_tests("test_images")
    print(f"测试完成，共执行 {len(results)} 个测试")
```

### 2. 持续集成测试

可以将上述测试脚本集成到CI/CD管道中，实现自动化测试：

```yaml
# .github/workflows/test.yml
name: Pest Detection API Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Start API service
      run: |
        python -m uvicorn src.algorithms.pest_detection.detector.app.main:app --host 0.0.0.0 --port 8001 &
        sleep 30
    
    - name: Run API tests
      run: |
        python test_pest_detection_api.py
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: test_results.json
```

## 总结

通过Pest Detection的API文档测试agent功能的方法包括：

1. **使用交互式API文档**：直接在Swagger UI中测试各个端点
2. **编写自动化测试脚本**：创建全面的测试套件验证功能
3. **集成到CI/CD流程**：实现持续自动化测试
4. **性能和并发测试**：评估系统在负载下的表现
5. **错误处理测试**：验证异常情况下的系统行为

这些测试方法确保了agent功能的健全性，为Cow Detection等类似系统提供了宝贵的参考。通过全面的测试，可以及早发现和解决问题，提高系统的可靠性和用户体验。