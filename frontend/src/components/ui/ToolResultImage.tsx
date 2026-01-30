"use client";

import React from 'react';
import { Scan, Sparkles } from 'lucide-react';

interface ToolResultImageProps {
  src: string;
  alt?: string;
  toolName?: string;
}

export const ToolResultImage: React.FC<ToolResultImageProps> = ({
  src,
  alt = "检测结果",
  toolName,
}) => {
  return (
    <div className="relative group tool-result-image-container">
      {/* 背景装饰层 */}
      <div className="absolute -inset-1 bg-gradient-to-br from-paddy-400 via-sky-400 to-gold-400 rounded-3xl opacity-20 group-hover:opacity-40 blur-xl transition-opacity duration-700" />
      <div className="absolute -inset-0.5 bg-gradient-to-br from-paddy-500/30 via-sky-500/20 to-gold-500/30 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* 主容器 */}
      <div className="relative bg-white rounded-3xl shadow-2xl shadow-paddy-500/20 overflow-hidden">
        {/* 顶部装饰条 */}
        <div className="h-1.5 bg-gradient-to-r from-paddy-500 via-sky-500 to-gold-500" />

        {/* 工具名称标签 */}
        {toolName && (
          <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 bg-white/95 backdrop-blur-md rounded-full shadow-lg border border-paddy-100 z-10">
            <Sparkles className="w-3.5 h-3.5 text-paddy-600" />
            <span className="text-xs font-semibold text-paddy-700">{toolName}</span>
          </div>
        )}

        {/* 检测标记 */}
        <div className="absolute top-3 right-3 flex items-center gap-2 px-3 py-1.5 bg-paddy-500/95 backdrop-blur-md rounded-full shadow-lg z-10">
          <Scan className="w-3.5 h-3.5 text-white" />
          <span className="text-xs font-semibold text-white">检测结果</span>
        </div>

        {/* 图片 */}
        <div className="relative">
          <img
            src={src}
            alt={alt}
            className="w-full h-auto rounded-t-2xl"
          />

          {/* 悬停时的渐变遮罩 */}
          <div className="absolute inset-0 bg-gradient-to-t from-paddy-900/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-t-2xl" />
        </div>

        {/* 底部装饰 */}
        <div className="px-5 py-3 bg-gradient-to-r from-paddy-50 to-sky-50 border-t border-paddy-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-paddy-500 animate-pulse" />
              <span className="text-xs font-medium text-stone-600">AI 智能检测完成</span>
            </div>
            <div className="text-xs text-stone-500">
              点击查看详情
            </div>
          </div>
        </div>
      </div>

      {/* 装饰性光点 */}
      <div className="absolute -top-2 -right-2 w-4 h-4 bg-gold-400 rounded-full opacity-60 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />
      <div className="absolute -bottom-2 -left-2 w-3 h-3 bg-sky-400 rounded-full opacity-60 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />
    </div>
  );
};
