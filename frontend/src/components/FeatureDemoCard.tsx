"use client";

import React from "react";
import { Play, ArrowRight } from "lucide-react";
import type { DemoCardConfig } from "@/config/demo-cards";

export interface DemoConfig {
  title: string;
  icon: string;
  description: string;
  exampleQuery: string;
  demoImage?: string; // 可选的演示图片路径
  category?: "detection" | "business" | "inspection" | "planning"; // 功能分类
}

/**
 * 将新接口 DemoCardConfig 转换为内部 DemoConfig 格式
 * 用于适配计划文档 5.11 章节的配置结构
 */
export function adaptDemoCard(card: DemoCardConfig): DemoConfig {
  return {
    title: card.title,
    icon: card.icon,
    description: card.description,
    exampleQuery: card.demo_input.text,
    demoImage: card.demo_input.image,
    category: card.category,
  };
}

interface FeatureDemoCardProps {
  config: DemoConfig;
  onClick: (query: string, image?: string) => void;
  disabled?: boolean;
  variant?: "default" | "compact"; // 卡片样式变体
}

export const FeatureDemoCard: React.FC<FeatureDemoCardProps> = ({
  config,
  onClick,
  disabled = false,
  variant = "default",
}) => {
  // 根据 variant 决定样式 - Organic Biophilic 设计
  const isCompact = variant === "compact";
  const paddingClass = isCompact ? "p-4" : "p-5";
  const iconSizeClass = isCompact ? "w-10 h-10 text-2xl" : "w-12 h-12 text-2xl";
  const titleSizeClass = isCompact ? "text-base" : "text-lg";
  const descSizeClass = isCompact ? "text-xs mb-3" : "text-sm mb-3";
  const decorSizeClass = isCompact ? "w-20 h-20 -mr-4 -mt-4" : "w-28 h-28 -mr-6 -mt-6";

  return (
    <button
      onClick={() => onClick(config.exampleQuery, config.demoImage)}
      disabled={disabled}
      className={`
        group relative overflow-hidden rounded-organic-xl ${paddingClass}
        bg-white border-2 border-earth-100
        hover:border-earth-400 hover:shadow-organic-md
        transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed
        text-left w-full
      `}
    >
      {/* 背景渐变装饰 - 有机风格 */}
      <div className={`absolute top-0 right-0 ${decorSizeClass} bg-gradient-to-br from-earth-100/60 to-transparent rounded-bl-full transition-all duration-300 group-hover:from-earth-200/70`} />

      {/* 内容 */}
      <div className="relative">
        {/* 图标 - 有机曲线设计 */}
        <div className={`${iconSizeClass} rounded-organic-lg bg-gradient-to-br from-earth-400 to-earth-600 flex items-center justify-center shadow-organic mb-3 group-hover:scale-110 group-hover:shadow-organic-md transition-all duration-300`}>
          {config.icon}
        </div>

        {/* 标题 */}
        <h3 className={`${titleSizeClass} font-bold text-earth-900 mb-1.5 group-hover:text-earth-700 transition-colors`}>
          {config.title}
        </h3>

        {/* 描述 */}
        <p className={`${descSizeClass} text-earth-600 leading-relaxed`}>
          {config.description}
        </p>

        {/* 演示按钮 - 有机风格 */}
        <div className="flex items-center gap-2 text-sm font-medium text-earth-600 group-hover:text-earth-700 transition-colors">
          <span>{config.demoImage ? "开始演示" : "开始咨询"}</span>
          <Play className="w-4 h-4" />
          <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
        </div>
      </div>

      {/* 悬停光效 - 有机渐变 */}
      <div className="absolute inset-0 bg-gradient-to-r from-earth-500/0 via-earth-500/5 to-earth-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out pointer-events-none" />
    </button>
  );
};
