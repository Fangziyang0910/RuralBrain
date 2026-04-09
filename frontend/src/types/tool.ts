/**
 * 工具调用相关类型定义
 */

/**
 * 联网搜索单条结果
 */
export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
  type: 'news' | 'web';
  published_date?: string;
}

/**
 * 联网搜索结果数据
 */
export interface WebSearchData {
  ai_summary: string;
  results: WebSearchResult[];
  stats: {
    total: number;
    news: number;
    web: number;
  };
}

/**
 * 工具调用事件（扩展后）
 */
export interface ToolCallEventData {
  type: 'tool_call';
  tool_name: string;
  status: '运行中' | '已完成';
  result_image?: string;
  result_data?: WebSearchData;  // 联网搜索的结构化数据
}