/**
 * 工具图标和颜色配置
 * 用于前端工具调用可视化展示
 */

export interface ToolIconConfig {
  icon: string; // emoji 图标
  color: string; // Tailwind 颜色类
  label: string; // 中文标签
  category: "detection" | "business" | "inspection" | "planning" | "search";
}

/**
 * 工具图标映射
 * key: 工具名称（与后端 tool_name 一致）
 */
export const toolIcons: Record<string, ToolIconConfig> = {
  // 检测类工具
  pest_detection_tool: {
    icon: "🐛",
    color: "green",
    label: "病虫害识别",
    category: "detection",
  },
  rice_detection_tool: {
    icon: "🍚",
    color: "amber",
    label: "大米品种识别",
    category: "detection",
  },
  cow_detection_tool: {
    icon: "🐄",
    color: "brown",
    label: "牛只检测",
    category: "detection",
  },
  plant_disease_detection_tool: {
    icon: "🌿",
    color: "emerald",
    label: "植物病害识别",
    category: "detection",
  },

  // 商业类工具
  pricing_tool: {
    icon: "💰",
    color: "yellow",
    label: "定价分析",
    category: "business",
  },
  marketing_tool: {
    icon: "📈",
    color: "blue",
    label: "营销策略",
    category: "business",
  },

  // 巡检类工具
  farm_inspection_tool: {
    icon: "🔍",
    color: "indigo",
    label: "农场巡检",
    category: "inspection",
  },
  scene_classifier_tool: {
    icon: "🏞️",
    color: "teal",
    label: "场景分类",
    category: "inspection",
  },
  disease_prediction_tool: {
    icon: "🏥",
    color: "red",
    label: "疾病预测",
    category: "inspection",
  },

  // 规划类工具（RAG）
  document_list_tool: {
    icon: "📚",
    color: "sky",
    label: "文档列表",
    category: "planning",
  },
  document_overview_tool: {
    icon: "📋",
    color: "sky",
    label: "文档概览",
    category: "planning",
  },
  knowledge_search_tool: {
    icon: "🔎",
    color: "sky",
    label: "知识检索",
    category: "planning",
  },
  key_points_search_tool: {
    icon: "📌",
    color: "sky",
    label: "要点搜索",
    category: "planning",
  },

  // 搜索类工具
  web_search_tool: {
    icon: "🌐",
    color: "purple",
    label: "联网搜索",
    category: "search",
  },

  // 技能加载工具
  load_skill: {
    icon: "⚡",
    color: "orange",
    label: "加载技能",
    category: "planning",
  },
};

/**
 * 获取工具配置
 * @param toolName 工具名称
 * @returns 工具配置，如果不存在则返回默认配置
 */
export function getToolConfig(toolName: string): ToolIconConfig {
  return (
    toolIcons[toolName] || {
      icon: "🔧",
      color: "gray",
      label: toolName.replace(/_tool$/, "").replace(/_/g, " "),
      category: "business" as const,
    }
  );
}

/**
 * 获取工具颜色样式类
 * @param color 颜色名称
 * @returns Tailwind 样式类
 */
export function getToolColorClass(color: string): {
  bg: string;
  text: string;
  border: string;
} {
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    green: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
    amber: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
    brown: { bg: "bg-amber-50", text: "text-amber-800", border: "border-amber-200" },
    emerald: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
    yellow: { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" },
    blue: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
    indigo: { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-200" },
    teal: { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-200" },
    red: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
    sky: { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-200" },
    purple: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
    orange: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
    gray: { bg: "bg-gray-50", text: "text-gray-700", border: "border-gray-200" },
  };

  return colorMap[color] || colorMap.gray;
}