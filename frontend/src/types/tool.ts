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
 * 单个检测结果
 */
export interface DetectionItem {
  name: string;
  count: number;
  confidence?: number;
}

/**
 * 检测工具结果数据
 */
export interface DetectionData {
  detections: DetectionItem[];
  totalCount: number;
  severity: "low" | "medium" | "high" | "none";
  summary: string;
  suggestions?: string[];
}

/**
 * 单个疾病预测结果
 */
export interface DiseasePrediction {
  name: string;
  probability: number;
  reason: string;
}

/**
 * 疾病预测工具结果数据
 */
export interface DiseasePredictionData {
  diseases: DiseasePrediction[];
  urgency: "high" | "medium" | "low";
  symptoms: string[];
  suggestions: {
    isolation?: string;
    treatment?: string;
    prevention?: string;
  };
  reminder?: string;
}

/**
 * 工具调用事件（扩展后）
 */
export interface ToolCallEventData {
  type: 'tool_call';
  tool_name: string;
  status: '运行中' | '已完成';
  result_image?: string;
  result_data?: WebSearchData | DetectionData | DiseasePredictionData;
}