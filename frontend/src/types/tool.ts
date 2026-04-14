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
 * 场景分类信息
 */
export interface SceneClassification {
  primary_scene: string;
  primary_scene_type: string;
  all_scenes: SceneInfo[];
}

/**
 * 单个场景信息
 */
export interface SceneInfo {
  index: number;
  scene_type: string;
  scene_name: string;
  confidence: number;
}

/**
 * 推荐工具信息
 */
export interface RecommendedTool {
  tool: string;
  reason: string;
}

/**
 * 多模态分析结果
 */
export interface MultimodalAnalysis {
  enabled: boolean;
  report: string;
}

/**
 * 巡检工具结果数据
 */
export interface InspectionData {
  inspection_type: string;
  inspection_time: string;
  farm_id: string;
  media_type?: string;
  media_type_name?: string;
  image_count?: number;
  scene_classification?: SceneClassification;
  recommended_tools?: RecommendedTool[];
  multimodal_analysis?: MultimodalAnalysis;
  suggested_actions?: string[];
  sensor_data?: Record<string, any>;
}

/**
 * 工具调用事件（扩展后）
 */
export interface ToolCallEventData {
  type: 'tool_call';
  tool_name: string;
  status: '运行中' | '已完成';
  result_image?: string;
  result_data?: WebSearchData | DetectionData | DiseasePredictionData | InspectionData;
}