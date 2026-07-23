/**
 * Markdown 后处理清理工具
 * 用于清理 ReactMarkdown 渲染后仍然残留的 markdown 格式
 */

/**
 * 修复流式拼接后容易贴连在一起的 Markdown 语法。
 *
 * 这里保留 Markdown 标记本身，只补足必要的换行/空格，让 ReactMarkdown
 * 能继续负责语义渲染。
 */
export function normalizeMarkdownForRendering(text: string): string {
  if (!text || typeof text !== 'string') {
    return text;
  }

  let normalized = text.replace(/\r\n?/g, '\n');

  // 流式拼接或模型输出常把块级语法贴在上一句后面。
  normalized = normalized.replace(/([^\n-])(-{3,})(?=#{1,6}\s*\S)/g, '$1\n\n$2\n\n');
  normalized = normalized.replace(/([^\n\s#])(?=#{1,6}(?:\s+#{1,6}\s+|\s*[^\s#]))/g, '$1\n\n');
  normalized = normalized.replace(/([^\n])(?=(?:\d+[\.)]|[-–—])[ \t]+\S)/g, '$1\n');

  const lines = normalized.split('\n').map((line) => {
    let nextLine = line.replace(/[ \t]+$/g, '');

    // ## # 标题、### ## 标题 -> ## 标题
    nextLine = nextLine.replace(/^(\s*)(#{1,6})\s+#{1,6}\s+(.+)$/, '$1$2 $3');

    // ####标题 -> #### 标题
    nextLine = nextLine.replace(/^(\s*)(#{1,6})([^\s#].*)$/, '$1$2 $3');

    return nextLine;
  });

  normalized = lines.join('\n');
  normalized = normalized.replace(/(^|\n)(#{1,6}\s+[^\n]+)\n(?!\n)/g, '$1$2\n\n');
  normalized = normalized.replace(/\n{3,}/g, '\n\n');

  return normalized.trim();
}

/**
 * 清理文本中残留的 Markdown 格式标记
 */
export function cleanupMarkdownRemnants(text: string): string {
  if (!text || typeof text !== 'string') {
    return text;
  }

  let cleaned = text;

  // 1. 清理残留的标题标记（### 或 #### 等）
  // 匹配行首的 ### 或 #### 后跟文本
  cleaned = cleaned.replace(/^(#{3,6})\s+(.+)$/gm, (match, hashes, content) => {
    // 如果这行没有被正确渲染为标题，则移除 # 号
    return content;
  });

  // 1b. 处理“标题/分隔线/列表”被连在一起的情况，例如 ---### 文本 或 ####可能的疾病
  cleaned = cleaned.replace(/#{3,6}\s*/g, '\n');
  cleaned = cleaned.replace(/-{3,}/g, '\n\n');
  cleaned = cleaned.replace(/(?<!\n)(\d+\.\s+|[-–—]\s+)(?=\S)/g, '\n$1');
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  // 2. 清理残留的加粗标记 **文本**
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1');

  // 3. 清理残留的斜体标记 *文本*
  cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1');

  // 4. 清理残留的代码标记 `文本`
  cleaned = cleaned.replace(/`([^`]+)`/g, '$1');

  // 5. 清理残留的分隔线标记 ---
  cleaned = cleaned.replace(/^---+$/gm, '────────');

  // 6. 清理残留的列表标记 - 开头的 -
  cleaned = cleaned.replace(/^[-–—]\s+(.+)$/gm, '• $1');

  // 7. 清理残留的数字列表标记
  cleaned = cleaned.replace(/^\d+\.\s+(.+)$/gm, '$1');

  // 7b. 将“列表项前缀”与正文粘连的情况拆成换行，避免堆在一起
  cleaned = cleaned.replace(/(?<!\n)(\d+\.\s+|[-–—]\s+)(?=\S)/g, '\n$1');
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  // 8. 清理混合格式，如 **text** 和 *text* 连在一起
  cleaned = cleaned.replace(/\*\*[^\*]+\*\*/g, (match) => {
    return match.replace(/\*\*/g, '');
  });

  // 9. 清理括号中的斜体，如 (*text*)
  cleaned = cleaned.replace(/\(\*([^*]+)\*\)/g, '($1)');

  // 10. 清理多余的空行
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  return cleaned;
}

/**
 * 检查文本中是否还有残留的 markdown 格式
 */
export function hasMarkdownRemnants(text: string): boolean {
  if (!text || typeof text !== 'string') {
    return false;
  }

  // 检查常见的残留模式
  const patterns = [
    /#{3,6}\s*\S+/,           // ### 标题
    /^#{3,6}\S+/gm,           // 贴连标题，如####可能的疾病
    /\*\*[^*]+\*\*/,         // **加粗**
    /`[^`]+`/,                 // `代码`
    /^---+\s*\S*$/gm,        // --- 分隔线/贴连标题
    /^\d+\.\s+\S+/gm,       // 1. 数字列表
    /^[-–—]\s+\S+/gm,        // - 项目列表
    /(^|\n)(?:\d+\.\s+|[-–—]\s+)(?=\S)/, // 列表前缀紧跟正文
  ];

  return patterns.some(pattern => pattern.test(text));
}

/**
 * 清理HTML中的markdown残留（用于ReactMarkdown渲染后的HTML字符串）
 */
export function cleanupMarkdownInHTML(html: string): string {
  if (!html || typeof html !== 'string') {
    return html;
  }

  let cleaned = html;

  // 清理文本节点中的残留markdown
  // 这个主要用于检查ReactMarkdown渲染后的HTML

  return cleaned;
}
