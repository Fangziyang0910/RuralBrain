# 多图片上传功能使用指南

## 📋 功能概述

RuralBrain 现已支持一次性上传多张图片进行智能检测，提升了批量处理效率。

## ✨ 新特性

### 用户功能
- ✅ **批量选择**：一次可选择最多 10 张图片
- ✅ **实时预览**：选择后立即显示所有图片缩略图
- ✅ **灵活删除**：可以单独删除某张图片或一键清空
- ✅ **批量上传**：所有图片一次性上传到服务器
- ✅ **智能分析**：AI 能同时分析多张图片并给出综合结果

### 技术改进
- ✅ **后端支持**：上传接口支持批量文件处理
- ✅ **数据模型**：更新为支持多图片路径列表
- ✅ **前端优化**：优化的UI展示多图片网格布局
- ✅ **向后兼容**：保持对单图片上传的兼容性

## 🎯 使用方法

### 1. 选择多张图片

点击上传按钮后：
- 按住 `Ctrl` (Windows) 或 `Cmd` (Mac) 可以多选图片
- 或者框选多张图片
- 最多可选择 10 张图片

### 2. 预览和管理

选择后会看到：
- 所有图片的缩略图预览（网格布局）
- 每张图片右上角有删除按钮
- 如果选择了多张，会显示"清除全部"按钮

### 3. 发送分析

- 输入问题描述或直接发送
- 系统会批量上传所有图片
- AI 会同时分析所有图片并给出结果

## 🔧 技术细节

### 后端改动

#### 1. 数据模型 (service/schemas.py)
```python
class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    file_path: Optional[str] = None  # 单文件（兼容）
    file_paths: Optional[List[str]] = None  # 多文件（新）
    message: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    image_path: Optional[str] = None  # 单图片（兼容）
    image_paths: Optional[List[str]] = None  # 多图片（新）
    thread_id: Optional[str] = None
```

#### 2. 上传接口 (service/server.py)
```python
@app.post("/upload")
async def upload_image(files: list[UploadFile] = File(...)):
    """
    上传图片接口（支持单张或多张）
    - 最多支持 10 张图片
    - 返回所有文件路径列表
    """
    MAX_FILES = 10
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"一次最多上传 {MAX_FILES} 张图片")
    
    # ... 批量处理逻辑
```

### 前端改动

#### 1. 状态管理 (frontend/my-app/src/app/page.tsx)
```typescript
// 从单图片改为数组
const [selectedImages, setSelectedImages] = useState<File[]>([]);
const [imagePreviews, setImagePreviews] = useState<string[]>([]);
```

#### 2. 多图选择和预览
```typescript
// 文件输入支持 multiple
<input type="file" accept="image/*" multiple />

// 网格布局显示预览
<div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
  {imagePreviews.map((preview, index) => (...))}
</div>
```

#### 3. 批量上传
```typescript
// FormData 添加多个文件
images.forEach(image => {
  formData.append("files", image);
});
```

### 消息类型更新 (ChatMessageBubble.tsx)
```typescript
export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  image?: string;      // 兼容单图
  images?: string[];   // 支持多图
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
};
```

## 📊 限制说明

- **数量限制**：最多 10 张图片/次
- **大小限制**：每张图片最大 10MB
- **格式支持**：jpg, jpeg, png, bmp, webp

## 🔄 向后兼容性

系统保持了对旧版单图片上传的完全兼容：
- 后端同时支持 `image_path` 和 `image_paths` 字段
- 前端消息同时支持 `image` 和 `images` 属性
- 单图片上传时，依然返回 `file_path` 字段

## 🐛 故障排查

### 上传失败
- 检查图片数量是否超过 10 张
- 检查单个图片大小是否超过 10MB
- 检查文件格式是否支持

### 预览不显示
- 清除浏览器缓存
- 检查浏览器控制台是否有错误

### AI 分析异常
- 确保后端服务正常运行
- 检查图片内容是否清晰可识别

## 📝 更新日志

**v0.2.0** (2025-12-18)
- ✨ 新增多图片批量上传功能
- ✨ 新增图片预览网格布局
- ✨ 新增单独删除和批量清空功能
- 🔧 优化后端上传接口性能
- 🔧 改进数据模型支持多图片
- 📝 保持向后兼容性

## 💡 使用建议

1. **批量检测**：将同类型的图片一起上传，AI 能给出更全面的分析
2. **合理数量**：虽然支持 10 张，但 3-5 张通常最佳
3. **清晰度**：确保图片清晰，光线充足
4. **类型一致**：建议同一批次上传同类型图片（全是牛、全是害虫等）

## 🎉 示例场景

### 场景 1：批量牛只检测
上传 5 张不同角度的牛只图片，AI 会：
- 分别识别每张图片中的牛只数量
- 给出总体统计信息
- 提供每张图片的检测结果图

### 场景 2：多害虫识别
上传多张害虫图片，AI 会：
- 识别所有害虫种类
- 统计每种害虫出现的次数
- 提供综合防治建议

### 场景 3：大米品种对比
上传不同品种的大米图片，AI 会：
- 识别各个品种
- 对比品种特征
- 提供质量评估

## 🔗 相关文档

- [前端开发指南](./frontend_guide.md)
- [API 接口文档](../README.md)
- [模型管理文档](./model_management.md)
