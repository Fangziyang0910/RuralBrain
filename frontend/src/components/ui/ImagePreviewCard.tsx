"use client";

import React from 'react';
import { X } from 'lucide-react';
import { cn } from "@/utils/cn";

interface ImagePreviewCardProps {
  src: string;
  alt: string;
  index?: number;
  total?: number;
  onRemove?: () => void;
  showNumber?: boolean;
}

export const ImagePreviewCard: React.FC<ImagePreviewCardProps> = ({
  src,
  alt,
  index,
  total,
  onRemove,
  showNumber = true,
}) => {
  return (
    <div className={cn(
      "group relative image-preview-card-modern",
      "w-20 h-20 sm:w-24 sm:h-24" // 响应式容器大小
    )}>
      {/* 渐变遮罩层 */}
      <div className="absolute inset-0 bg-gradient-to-br from-paddy-500/0 via-paddy-500/5 to-paddy-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl" />

      {/* 图片 */}
      <img
        src={src}
        alt={alt}
        className={cn(
          "w-full h-full object-cover rounded-2xl shadow-lg",
          "shadow-paddy-500/10",
          "group-hover:shadow-xl group-hover:shadow-paddy-500/20",
          "transition-all duration-500"
        )}
      />

      {/* 删除按钮 - 响应式 */}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className={cn(
            "absolute -top-1.5 -right-1.5 sm:-top-2 sm:-right-2", // 响应式位置
            "bg-white/90 backdrop-blur-md text-stone-700",
            "rounded-full shadow-lg flex items-center justify-center",
            "w-6 h-6 sm:w-7 sm:h-7", // 响应式按钮大小
            "opacity-0 group-hover:opacity-100",
            "-translate-y-1 group-hover:translate-y-0",
            "transition-all duration-300",
            "hover:bg-red-50 hover:text-red-600 hover:scale-110"
          )}
          aria-label="删除图片"
        >
          <X className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </button>
      )}

      {/* 图片序号标签 - 响应式 */}
      {showNumber && index !== undefined && total !== undefined && total > 1 && (
        <div className={cn(
          "absolute bottom-1.5 left-1.5 sm:bottom-2 sm:left-2", // 响应式位置
          "bg-white/90 backdrop-blur-md rounded-full shadow-md",
          "font-semibold text-paddy-700",
          "px-1.5 sm:px-2.5 py-0.5 sm:py-1", // 响应式内边距
          "text-[10px] sm:text-xs" // 响应式字体
        )}>
          {index + 1}/{total}
        </div>
      )}

      {/* 装饰性光晕效果 */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-paddy-400/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
    </div>
  );
};
