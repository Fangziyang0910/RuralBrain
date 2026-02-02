# 乡村智慧数字化门户

## 🚀 快速运行

1. **直接打开**：双击 `static/portal.html` 即可在浏览器中预览。
2. **通过服务打开**（推荐）：

   ```bash
   python -m http.server 8000
   ```

   然后访问 `http://localhost:8000/portal.html`。

## 🔗 如何接入网址

接入网址非常简单，只需要修改 `portal.html` 文件末尾的配置对象。

1. 用编辑器（如 VS Code）打开 [portal.html](portal.html)。
2. 搜索关键字 `const config`（大约在文件第 700 行之后）。
3. 将对应的占位符替换为你真实的跳转地址：

```javascript
// 修改这段代码
const config = {
    brain: 'https://您的乡村智慧大脑网址', 
    wai: 'https://您的乡村经营智能体WAI网址',
    plan: 'https://您的乡村智能规划智能体网址'
};
```
