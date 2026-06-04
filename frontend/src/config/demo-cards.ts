export interface DemoCardConfig {
  skill: string;
  title: string;
  icon: string;
  description: string;
  demo_input: {
    text: string;
    image?: string;
  };
  category?: "detection" | "business" | "inspection" | "planning";
  variant?: "default" | "compact";
}

export interface AutoDemoStep {
  id:
    | "opening"
    | "knowledge-base"
    | "planning"
    | "pricing"
    | "detection"
    | "cow-detection"
    | "rice-detection"
    | "disease-detection"
    | "disease-knowledge";
  title: string;
  text: string;
  image?: string;
  enableKnowledgeBase?: boolean;
  enableWebSearch?: boolean;
}

const detectionDemoCards: DemoCardConfig[] = [
  {
    skill: "pest_detection",
    title: "病虫害检测",
    icon: "🐛",
    description: "智能识别农作物病虫害，分析危害程度并提供科学防治方案",
    demo_input: {
      text: "请帮我检测这张图片中的病虫害，并给出防治建议",
      image: "/demo/pest-input.jpg",
    },
    category: "detection",
    variant: "default",
  },
  {
    skill: "rice_detection",
    title: "大米品种识别",
    icon: "🍚",
    description: "识别大米品种，分析品质特征，提供烹饪建议和储存方法",
    demo_input: {
      text: "请帮我识别这张图片中的大米品种",
      image: "/demo/rice-input.jpg",
    },
    category: "detection",
    variant: "default",
  },
  {
    skill: "cow_detection",
    title: "奶牛检测",
    icon: "🐄",
    description: "识别牛只品种和数量，提供养殖管理、疫病防控和繁殖建议",
    demo_input: {
      text: "请帮我数一下这张图片中有多少头牛",
      image: "/demo/cow-input.jpg",
    },
    category: "detection",
    variant: "default",
  },
  {
    skill: "disease_prediction",
    title: "疾病预测",
    icon: "🏥",
    description: "智能预测畜禽疾病，基于患处图片和症状提供专业分析建议",
    demo_input: {
      text: "请帮我看一下图片中的牛患了什么病",
      image: "/demo/disease-input.jpg",
    },
    category: "detection",
    variant: "default",
  },
];

const businessDemoCards: DemoCardConfig[] = [
  {
    skill: "pricing_analysis",
    title: "定价分析",
    icon: "💰",
    description: "农产品定价建议，分析成本、市场和竞争因素",
    demo_input: {
      text: "我想为有机大米定价，成本约8元/斤，请帮我分析合理定价",
    },
    category: "business",
    variant: "compact",
  },
  {
    skill: "marketing_strategy",
    title: "营销策略",
    icon: "📈",
    description: "农产品营销方案，分析市场渠道和品牌推广策略",
    demo_input: {
      text: "我想推广家乡的土特产，请帮我制定一个线上线下结合的营销方案",
    },
    category: "business",
    variant: "compact",
  },
  {
    skill: "farm_inspection",
    title: "农场巡检",
    icon: "🔍",
    description: "智能巡检农场，识别场景并分析作物和养殖状况",
    demo_input: {
      text: "请帮我分析这张巡检图片，识别场景并提供管理建议",
      image: "/demo/cow-input.jpg",
    },
    category: "inspection",
    variant: "compact",
  },
];

const planningDemoCards: DemoCardConfig[] = [
  {
    skill: "consult_planning_knowledge",
    title: "规划政策查询",
    icon: "📋",
    description: "基于知识库查询乡村振兴政策和规划案例参考",
    demo_input: {
      text: "请帮我查询乡村振兴相关的扶持政策",
    },
    category: "planning",
    variant: "compact",
  },
  {
    skill: "consult_planning_knowledge",
    title: "发展案例参考",
    icon: "🏘️",
    description: "检索乡村发展规划成功案例，提供经验参考",
    demo_input: {
      text: "我想了解乡村产业发展的成功案例，特别是特色农业方向",
    },
    category: "planning",
    variant: "compact",
  },
  {
    skill: "consult_planning_knowledge",
    title: "知识库概览",
    icon: "📚",
    description: "查看知识库中可用的文档资源",
    demo_input: {
      text: "请列出知识库中所有可用的文档",
    },
    category: "planning",
    variant: "compact",
  },
];

export const allDemoCards = [...detectionDemoCards, ...businessDemoCards, ...planningDemoCards];

export const layer2DetectionCards: DemoCardConfig[] = [
  detectionDemoCards[0],
  detectionDemoCards[3],
];

export const layer3SalesCards: DemoCardConfig[] = [
  businessDemoCards[0],
  businessDemoCards[1],
];

export const layer4PlanningCards: DemoCardConfig[] = [
  {
    skill: "consult_planning_knowledge",
    title: "规划咨询",
    icon: "📋",
    description: "查询乡村振兴政策扶持与产业发展成功案例参考",
    demo_input: {
      text: "我想发展乡村特色产业，请帮我查询相关政策扶持和成功案例参考",
    },
    category: "planning",
    variant: "compact",
  },
];

export const otherCards: DemoCardConfig[] = [
  detectionDemoCards[2],
  detectionDemoCards[1],
  businessDemoCards[2],
];

export function getAutoDemoScript(): AutoDemoStep[] {
  return [
    {
      id: "opening",
      title: "开场介绍",
      text: "你好，请先用一句话介绍一下你能为乡村治理和产业发展提供哪些帮助。",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "knowledge-base",
      title: "知识库问答",
      text: "请基于知识库，概括 2026 年和乡村全面振兴相关的重点政策方向。",
      enableKnowledgeBase: true,
      enableWebSearch: false,
    },
    {
      id: "planning",
      title: "规划咨询",
      text: "我想发展乡村特色产业，请结合政策扶持和成功案例给我一个简要建议。",
      enableKnowledgeBase: true,
      enableWebSearch: false,
    },
    {
      id: "pricing",
      title: "定价分析",
      text: "我想为有机大米定价，成本约 8 元/斤，请帮我分析合理定价。",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "detection",
      title: "图像检测",
      text: "请帮我检测这张图片中的病虫害，并给出防治建议。",
      image: "/demo/pest-input.jpg",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "cow-detection",
      title: "奶牛检测",
      text: "请帮我数一下这张图片中有多少头牛，并简要说明养殖管理建议。",
      image: "/demo/cow-input.jpg",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "rice-detection",
      title: "大米识别",
      text: "请帮我识别这张图片中的大米品种，并简要说明品质特点与食用建议。",
      image: "/demo/rice-input.jpg",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "disease-detection",
      title: "疾病检测",
      text: "请帮我看一下图片中的牛可能患了什么病，并给出初步处理建议。",
      image: "/demo/disease-input.jpg",
      enableKnowledgeBase: false,
      enableWebSearch: false,
    },
    {
      id: "disease-knowledge",
      title: "疾病知识库问答",
      text: "请基于疾病知识库，概括牛常见疾病的判断依据、初步处理建议，以及哪些情况需要尽快联系兽医。",
      enableKnowledgeBase: true,
      enableWebSearch: false,
    },
  ];
}

export { detectionDemoCards, businessDemoCards, planningDemoCards };
