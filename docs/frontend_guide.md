# RuralBrain 前端展示系统

## 📋 项目简介

这是 RuralBrain 的前端展示系统，提供简洁现代的对话界面，支持图像上传和智能对话。

## 🎯 功能特性

- ✅ 简洁现代的对话界面（类似 ChatGPT/DeepSeek）
- ✅ 支持多图片上传（单次最多 10 张）
- ✅ 流式输出对话内容，实时展示 AI 思考过程
- ✅ 集成害虫识别、大米品种识别、牛只识别功能
- ✅ Markdown 渲染支持（含代码高亮、表格等）
- ✅ 内置 Demo 演示页面，展示完整对话场景
- ✅ 工具调用可视化，实时展示检测结果图片

## 🏗️ 项目结构

```
RuralBrain/
├── service/                     # 后端服务层
│   ├── server.py               # FastAPI 服务器
│   ├── schemas.py              # 数据模型
│   └── settings.py             # 配置文件
├── frontend/                   # 前端应用
│   └── my-app/                # Next.js 应用
│       ├── src/
│       │   ├── app/           # 页面路由
│       │   │   ├── page.tsx   # 主页（对话界面）
│       │   │   └── demo/      # Demo 演示页面
│       │   ├── components/    # React 组件
│       │   │   ├── ChatMessageBubble.tsx  # 消息气泡组件
│       │   │   ├── ChatWindow.tsx         # 聊天窗口组件
│       │   │   └── ui/                    # UI 基础组件
│       │   └── utils/         # 工具函数
│       ├── public/            # 静态资源
│       │   └── demo/          # Demo 页面图片资源
│       ├── next.config.mjs    # Next.js 配置
│       └── package.json       # 依赖配置
├── uploads/                    # 用户上传图片目录
├── pest_detection_results/     # 害虫检测结果目录
├── cow_detection_results/      # 牛只检测结果目录
├── rice_detection_results/     # 大米检测结果目录
├── run_server.py              # 后端启动脚本
└── run_frontend.bat/ps1       # 前端启动脚本
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.13+
- Node.js 18+
- uv (Python 包管理器)

### 2. 启动后端服务

```bash
# 使用 uv 启动（推荐）
uv run run_server.py

# 或使用 Python
python run_server.py
```

后端服务将在 `http://localhost:8080` 启动

### 3. 启动前端服务

**Windows (PowerShell):**
```powershell
.\run_frontend.ps1
```

**Windows (CMD):**
```cmd
run_frontend.bat
```

**手动启动:**
```bash
cd frontend/my-app
npm install  # 首次运行需要安装依赖
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

### 4. 访问应用

**主对话界面:**
打开浏览器访问: `http://localhost:3000`

**Demo 演示页面:**
访问: `http://localhost:3000/demo`
查看完整的三种检测功能演示（害虫、大米、牛只识别）

## 📖 使用说明

### 基本对话

1. 在输入框中输入问题
2. 按 Enter 发送，Shift+Enter 换行
3. 等待 AI 助手流式回复
4. 可以查看 AI 调用的工具和检测结果

### 图片识别

**单图上传:**
1. 点击上传按钮选择图片
2. 输入相关问题（如"帮我识别这张图片中的害虫"）
3. 发送消息
4. AI 会自动判断并调用相应的识别工具

**多图上传:**
1. 点击上传按钮，按住 Ctrl 或 Shift 选择多张图片（最多 10 张）
2. 或者多次点击上传按钮添加图片
3. 可以单独删除某张图片，或点击"清空全部"删除所有图片
4. 输入问题并发送，AI 会批量处理所有图片

### 支持的识别类型

- **害虫识别**: 上传农作物病虫害图片，识别害虫种类、数量并提供防治建议
- **大米品种识别**: 上传大米图片，识别品种、颗粒数量并提供储存建议
- **牛只识别**: 上传牛的图片，检测牛只数量、位置并提供养殖建议

### 查看演示

访问 `/demo` 页面可以查看：
- 三种检测功能的完整对话示例
- 输入图片和检测结果的对比展示
- 工具调用过程的可视化
- 专业的分析和建议内容

## 🔧 技术栈

### 后端
- FastAPI: Web 框架
- LangChain: AI Agent 框架
- LangGraph: Agent 工作流
- Uvicorn: ASGI 服务器

### 前端
- Next.js 14: React 框架（App Router）
- TypeScript: 类型安全
- TailwindCSS: 样式框架
- React Markdown: Markdown 渲染
- remark-gfm: GitHub 风格 Markdown 支持（表格、删除线等）
- Lucide React: 图标库
- Radix UI: 无障碍 UI 组件基础

## 🎨 界面特色

### 主对话界面 (`/`)
- 清爽简洁的对话界面，类似主流 AI 助手
- 流畅的流式输出效果，实时展示 AI 回复
- 支持多图片预览和批量展示
- Markdown 格式完整渲染（代码块、表格、列表等）
- 工具调用卡片，可展开/收起查看检测详情
- 检测结果图片实时展示
- 响应式设计，适配移动端

### Demo 演示页面 (`/demo`)
- 完整的使用场景展示
- 三种检测功能的典型对话流程
- 输入输出对比展示
- 专业的分析和建议示例
- 可展开/收起的工具调用详情

## 🔍 API 接口

### 上传单张图片
```http
POST /upload
Content-Type: multipart/form-data

Request:
- file: 图片文件（支持 jpg, jpeg, png, bmp, webp）
- 最大 10MB

Response:
{
  "success": true,
  "file_path": "uploads/xxx.jpg",
  "message": "上传成功"
}
```

### 批量上传图片
```http
POST /upload/batch
Content-Type: multipart/form-data

Request:
- files: 多个图片文件（最多 10 张）

Response:
{
  "success": true,
  "file_paths": ["uploads/1.jpg", "uploads/2.jpg"],
  "message": "成功上传 2 张图片"
}
```

### 流式对话
```http
POST /chat/stream
Content-Type: application/json

Body:
{
  "message": "用户消息",
  "image_paths": ["可选的图片路径列表"],  // 支持多图片
  "thread_id": "可选的对话线程ID"
}

Response: text/event-stream (SSE)
事件类型:
- message: AI 回复内容（流式）
- tool_call: 工具调用信息
- error: 错误信息
- end: 对话结束
```

### 静态资源访问
```http
# 用户上传的图片
GET /uploads/{filename}

# 害虫检测结果
GET /pest_results/{filename}

# 牛只检测结果
GET /cow_results/{filename}

# 大米检测结果
GET /rice_results/{filename}
```

## 📝 开发说明

### 核心组件

**ChatMessageBubble** (`src/components/ChatMessageBubble.tsx`)
- 消息气泡组件，支持用户和 AI 消息
- 集成 Markdown 渲染
- 工具调用可视化展示
- 图片预览功能

**ChatWindow** (`src/components/ChatWindow.tsx`)
- 完整的聊天窗口组件（可复用）
- 消息输入和发送
- 图片上传管理
- 自动滚动和响应式布局

### 配置文件

**next.config.mjs**
配置了 API 代理和静态资源路径映射：
```javascript
rewrites: [
  { source: '/api/:path*', destination: 'http://localhost:8080/:path*' },
  { source: '/pest_results/:path*', destination: 'http://localhost:8080/pest_results/:path*' },
  { source: '/cow_results/:path*', destination: 'http://localhost:8080/cow_results/:path*' },
  { source: '/rice_results/:path*', destination: 'http://localhost:8080/rice_results/:path*' },
]
```

**service/settings.py**
后端配置：
```python
HOST = "127.0.0.1"
PORT = 8080
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
```

### 添加新功能

1. **后端添加新路由**: 在 `service/server.py` 中添加
2. **前端创建新组件**: 在 `src/components/` 中创建
3. **添加新页面**: 在 `src/app/` 中创建目录和 `page.tsx`
4. **集成新检测服务**: 
   - 在 `src/agents/tools/` 中创建新工具
   - 在对应 agent 中注册工具
   - 在 `server.py` 中添加静态资源映射

### 调试技巧

- **后端日志**: 查看终端输出，使用 `logger.info()` 添加日志
- **前端调试**: 
  - 浏览器开发者工具 Console
  - React DevTools 查看组件状态
  - Network 面板查看 API 请求
- **API 测试**: 访问 `http://localhost:8080/docs` 查看 Swagger 文档
- **SSE 调试**: 使用浏览器 Network 面板的 EventStream 过滤器

### 开发最佳实践

1. **代码风格**: 遵循 Python Zen 哲学和 TypeScript 最佳实践
2. **组件化**: 保持组件职责单一，提高复用性
3. **类型安全**: 充分利用 TypeScript 类型系统
4. **错误处理**: 前后端都要做好异常捕获和用户提示
5. **性能优化**: 
   - 图片压缩后再上传
   - 使用 React.memo 避免不必要的重渲染
   - 后端使用流式输出提升响应速度

## 🐛 常见问题

### 端口被占用

修改 `service/settings.py` 中的 `PORT` 配置，或设置环境变量:
```bash
export PORT=8081  # Linux/Mac
set PORT=8081     # Windows CMD
$env:PORT=8081   # Windows PowerShell
```

### 图片上传失败

- 检查图片大小是否超过 10MB
- 确认图片格式是否支持 (jpg, jpeg, png, bmp, webp)
- 检查 `uploads/` 目录是否有写入权限
- 多图上传时确保总数不超过 10 张

### 前端无法连接后端

1. 检查后端服务是否已启动: `http://localhost:8080/docs`
2. 检查 `next.config.mjs` 中的代理配置
3. 查看浏览器控制台的网络错误信息
4. 确认防火墙没有阻止本地端口

### 检测结果图片无法显示

1. 检查对应的结果目录是否存在且有读取权限
2. 确认 `server.py` 中已正确挂载静态文件目录
3. 查看浏览器控制台是否有 404 错误
4. 检查图片路径是否正确（应为相对路径）

### 流式输出卡住或中断

1. 检查后端日志是否有错误
2. 确认 AI 模型服务是否正常（检查 API Key）
3. 查看网络连接是否稳定
4. 尝试刷新页面重新开始对话

### Demo 页面图片不显示

确保 `frontend/my-app/public/demo/` 目录下有以下图片：
- `pest-input.jpg` / `pest-output.jpg`
- `rice-input.jpg` / `rice-output.jpg`
- `cow-input.jpg` / `cow-output.jpg`

### 开发时修改代码不生效

- 前端: Next.js 开发服务器会自动热重载，如果不生效可以重启 `npm run dev`
- 后端: 需要手动重启 `run_server.py`
- 清除浏览器缓存: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)

## 🔗 相关文档

- [项目总览](../PROJECT_OVERVIEW.md)
- [模型管理文档](model_management.md)
- [多图上传指南](multi_image_upload_guide.md)
- [场景 Demo 说明](场景demo.md)
- [Docker 部署指南](../docker-compose.all.yml)

## 💡 技术支持

如遇到其他问题，请：
1. 查看后端终端日志
2. 检查浏览器控制台错误信息
3. 访问 `/docs` 查看 API 文档
4. 参考项目 GitHub Issues