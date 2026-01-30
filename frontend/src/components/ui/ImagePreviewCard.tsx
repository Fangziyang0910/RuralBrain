"use client";

import React from 'react';
import { X } from 'lucide-react';

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
    <div className="group relative image-preview-card-modern">
      {/* 渐变遮罩层 */}
      <div className="absolute inset-0 bg-gradient-to-br from-paddy-500/0 via-paddy-500/5 to-paddy-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl" />

      {/* 图片 */}
      <img
        src={src}
        alt={alt}
        className="w-full h-24 sm:h-32 object-cover rounded-2xl shadow-lg shadow-paddy-500/10 group-hover:shadow-xl group-hover:shadow-paddy-500/20 transition-all duration-500"
      />

      {/* 删除按钮 */}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="absolute -top-2 -right-2 w-7 h-7 bg-white/90 backdrop-blur-md text-stone-700 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 -translate-y-1 group-hover:translate-y-0 transition-all duration-300 hover:bg-red-50 hover:text-red-600 hover:scale-110"
          aria-label="删除图片"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      {/* 图片序号标签 */}
      {showNumber && index !== undefined && total !== undefined && total > 1 && (
        <div className="absolute bottom-2 left-2 px-2.5 py-1 bg-white/90 backdrop-blur-md rounded-full shadow-md text-xs font-semibold text-paddy-700">
          {index + 1}/{total}
        </div>
      )}

      {/* 装饰性光晕效果 */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-paddy-400/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
    </div>
  );
};
