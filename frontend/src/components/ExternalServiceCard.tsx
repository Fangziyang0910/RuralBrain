"use client";

import React from "react";
import { ExternalLink, ArrowRight } from "lucide-react";
import type { ExternalServiceConfig } from "@/config/external-services";

interface ExternalServiceCardProps {
  config: ExternalServiceConfig;
  onClick?: (url: string) => void;
}

/**
 * 外部服务入口卡片
 * 用于跳转到外部服务（乡村经营、规划方案、法律助手）
 */
export const ExternalServiceCard: React.FC<ExternalServiceCardProps> = ({
  config,
  onClick,
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(config.url);
    } else {
      // 默认行为：在新标签页打开外部服务
      window.open(config.url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <button
      onClick={handleClick}
      className="
        group relative overflow-hidden rounded-2xl p-5
        bg-white border-2 border-stone-200
        hover:border-blue-400 hover:shadow-xl
        transition-all duration-300 ease-out
        text-left w-full
      "
    >
      {/* 背景渐变装饰 */}
      <div className="absolute top-0 right-0 w-28 h-28 bg-gradient-to-br from-blue-100/50 to-transparent rounded-bl-full -mr-6 -mt-6 transition-all duration-300 group-hover:from-blue-200/60" />

      {/* 内容 */}
      <div className="relative">
        {/* 图标 */}
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center text-2xl shadow-md mb-3 group-hover:scale-110 transition-transform duration-300">
          {config.icon}
        </div>

        {/* 标题 */}
        <h3 className="text-base font-bold text-stone-900 mb-1.5 group-hover:text-blue-700 transition-colors">
          {config.title}
        </h3>

        {/* 描述 */}
        <p className="text-sm text-stone-600 mb-3 leading-relaxed">
          {config.description}
        </p>

        {/* 跳转提示 */}
        <div className="flex items-center gap-2 text-sm font-medium text-blue-600 group-hover:text-blue-700 transition-colors">
          <ExternalLink className="w-4 h-4" />
          <span>点击访问</span>
          <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
        </div>
      </div>

      {/* 悬停光效 */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out pointer-events-none" />
    </button>
  );
};