"use client";

import React from "react";
import { Play, ArrowRight } from "lucide-react";

export interface DemoConfig {
  title: string;
  icon: string;
  description: string;
  exampleQuery: string;
  demoImage?: string; // 可选的演示图片路径
}

interface FeatureDemoCardProps {
  config: DemoConfig;
  onClick: (query: string, image?: string) => void;
  disabled?: boolean;
}

export const FeatureDemoCard: React.FC<FeatureDemoCardProps> = ({
  config,
  onClick,
  disabled = false,
}) => {
  return (
    <button
      onClick={() => onClick(config.exampleQuery, config.demoImage)}
      disabled={disabled}
      className={`
        group relative overflow-hidden rounded-2xl p-6
        bg-white border-2 border-stone-200
        hover:border-paddy-400 hover:shadow-xl
        transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed
        text-left w-full
      `}
    >
      {/* 背景渐变装饰 */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-paddy-100/50 to-transparent rounded-bl-full -mr-8 -mt-8 transition-all duration-300 group-hover:from-paddy-200/60" />

      {/* 内容 */}
      <div className="relative">
        {/* 图标 */}
        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-paddy-400 to-paddy-500 flex items-center justify-center text-3xl shadow-md mb-4 group-hover:scale-110 transition-transform duration-300">
          {config.icon}
        </div>

        {/* 标题 */}
        <h3 className="text-lg font-bold text-stone-900 mb-2 group-hover:text-paddy-700 transition-colors">
          {config.title}
        </h3>

        {/* 描述 */}
        <p className="text-sm text-stone-600 mb-4 leading-relaxed">
          {config.description}
        </p>

        {/* 演示按钮 */}
        <div className="flex items-center gap-2 text-sm font-medium text-paddy-600 group-hover:text-paddy-700 transition-colors">
          <span>开始演示</span>
          <Play className="w-4 h-4" />
          <ArrowRight className="w-4 h-4 ml-auto opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
        </div>
      </div>

      {/* 悬停光效 */}
      <div className="absolute inset-0 bg-gradient-to-r from-paddy-500/0 via-paddy-500/5 to-paddy-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out pointer-events-none" />
    </button>
  );
};
