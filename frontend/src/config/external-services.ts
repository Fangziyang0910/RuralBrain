/**
 * 外部服务配置
 * 用于前端外部服务入口卡片
 */

export interface ExternalServiceConfig {
  id: string;
  title: string;
  icon: string;
  description: string;
  url: string; // 外部服务地址
}

/**
 * 外部服务列表配置
 * 使用占位 URL，后续可通过环境变量配置真实地址
 */
export const externalServices: ExternalServiceConfig[] = [
  {
    id: "management",
    title: "乡村经营服务",
    icon: "🏘️",
    description: "乡村经营管理、产业对接、资源整合等综合服务",
    url: process.env.NEXT_PUBLIC_MANAGEMENT_URL || "http://localhost:3002",
  },
  {
    id: "planning",
    title: "规划方案服务",
    icon: "📋",
    description: "乡村发展规划、产业布局、项目申报等专业方案",
    url: process.env.NEXT_PUBLIC_PLANNING_URL || "http://localhost:3003",
  },
  {
    id: "legal",
    title: "法律助手服务",
    icon: "⚖️",
    description: "农村法律咨询、合同审查、权益维护等法律服务",
    url: process.env.NEXT_PUBLIC_LEGAL_URL || "http://localhost:3004",
  },
  {
    id: "tourism",
    title: "文旅服务",
    icon: "🗺️",
    description: "乡村旅游规划、景点推荐、路线导航、文化导览等服务",
    url: process.env.NEXT_PUBLIC_TOURISM_URL || "http://localhost:5173",
  },
];

/**
 * 获取服务状态（可选实现）
 * 用于显示服务可用性指示灯
 */
export async function checkServiceStatus(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { method: "HEAD", mode: "no-cors" });
    return true; // no-cors 模式无法判断状态，默认返回 true
  } catch {
    return false;
  }
}

/**
 * ========== 四层架构分组配置 ==========
 */

// 第一层：经营规划服务入口（乡村经营智能体 + 乡村规划智能体 + 文旅服务）
export const layer1ExternalServices: ExternalServiceConfig[] = [
  {
    id: "management",
    title: "乡村经营智能体",
    icon: "🏘️",
    description: "乡村经营管理、产业对接、资源整合等综合服务",
    url: process.env.NEXT_PUBLIC_MANAGEMENT_URL || "http://localhost:3002",
  },
  {
    id: "planning",
    title: "乡村规划智能体",
    icon: "📋",
    description: "乡村发展规划、产业布局、项目申报等专业方案",
    url: process.env.NEXT_PUBLIC_PLANNING_URL || "http://localhost:3003",
  },
  {
    id: "tourism",
    title: "文旅服务",
    icon: "🗺️",
    description: "乡村旅游规划、景点推荐、路线导航、文化导览等服务",
    url: process.env.NEXT_PUBLIC_TOURISM_URL || "http://localhost:5173",
  },
];

// 第四层：法律咨询服务（外部服务）
export const layer4LegalService: ExternalServiceConfig = {
  id: "legal",
  title: "法律咨询",
  icon: "⚖️",
  description: "农村法律咨询、合同审查、权益维护等法律服务",
  url: process.env.NEXT_PUBLIC_LEGAL_URL || "http://localhost:3004",
};