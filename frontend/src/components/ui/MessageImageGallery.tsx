"use client";

import React, { useState } from 'react';
import { Maximize2 } from 'lucide-react';

interface MessageImageGalleryProps {
  images: string[];
  alt?: string;
}

export const MessageImageGallery: React.FC<MessageImageGalleryProps> = ({
  images,
  alt = "上传的图片",
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (images.length === 1) {
    // 单张图片 - 使用固定宽度确保不会溢出
    // 考虑布局：容器padding(24px) + 头像(36px) + gap(12px) + 安全边距(20px) = 92px
    return (
      <div className="relative group image-single-modern max-w-[120px] xs:max-w-[140px] sm:max-w-[180px] md:max-w-[280px]">
        <div className="absolute inset-0 bg-gradient-to-br from-paddy-500/20 via-gold-500/10 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 blur-xl" />
        <img
          src={images[0]}
          alt={alt}
          className="relative w-full h-auto max-h-[120px] xs:max-h-[140px] sm:max-h-[180px] md:max-h-[250px] object-contain rounded-3xl shadow-2xl shadow-paddy-500/20 group-hover:shadow-paddy-500/30 transition-all duration-500"
        />
        {/* 装饰性边框 */}
        <div className="absolute -inset-0.5 rounded-3xl bg-gradient-to-br from-paddy-400/30 via-gold-400/20 to-paddy-600/30 opacity-0 group-hover:opacity-100 transition-opacity duration-700 -z-10" />
      </div>
    );
  }

  if (images.length === 2) {
    // 两张图片 - 并排展示，使用固定宽度确保不溢出
    return (
      <div className="grid grid-cols-2 gap-1.5 sm:gap-2 max-w-[110px] xs:max-w-[130px] sm:max-w-[160px] md:max-w-[240px]">
        {images.map((img, index) => (
          <div
            key={index}
            className="relative group image-double-modern"
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${
              index === 0 ? 'from-paddy-500/20' : 'from-gold-500/20'
            } via-transparent to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`}>
              <div className="absolute inset-0 bg-gradient-to-tr from-paddy-400/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-2xl" />
            </div>
            <img
              src={img}
              alt={`${alt} ${index + 1}`}
              className="relative w-full h-14 xs:h-16 sm:h-20 md:h-24 object-cover rounded-2xl shadow-lg shadow-stone-500/10 group-hover:shadow-xl group-hover:shadow-paddy-500/20 transition-all duration-500 group-hover:scale-105"
            />
            {/* 图片编号 */}
            <div className="absolute top-2 left-2 px-2 py-0.5 bg-white/90 backdrop-blur-md rounded-full shadow-md text-[10px] sm:text-[10px] sm:text-xs font-bold text-paddy-700">
              {index + 1}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // 多张图片 - 网格布局，使用固定宽度确保不溢出
  const gridCols = images.length >= 4 ? 'grid-cols-3' : 'grid-cols-2';

  return (
    <div className={`grid ${gridCols} gap-1.5 sm:gap-2 max-w-[110px] xs:max-w-[130px] sm:max-w-[160px] md:max-w-[260px]`}>
      {images.map((img, index) => (
        <div
          key={index}
          className={`relative group image-grid-modern ${
            index === 0 && images.length >= 3 ? 'col-span-2 row-span-2' : ''
          }`}
          onMouseEnter={() => setHoveredIndex(index)}
          onMouseLeave={() => setHoveredIndex(null)}
        >
          {/* 背景装饰 */}
          <div className="absolute inset-0 bg-gradient-to-br from-paddy-500/15 via-transparent to-gold-500/10 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute inset-0 bg-gradient-to-tr from-paddy-400/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-2xl" />

          {/* 图片 */}
          <img
            src={img}
            alt={`${alt} ${index + 1}`}
            className={`relative w-full object-cover rounded-2xl shadow-lg shadow-stone-500/10 group-hover:shadow-xl group-hover:shadow-paddy-500/20 transition-all duration-500 ${
              index === 0 && images.length >= 3 ? 'h-20 xs:h-24 sm:h-28 md:h-40' : 'h-12 xs:h-14 sm:h-16 md:h-20'
            } group-hover:scale-105`}
          />

          {/* 图片编号 */}
          <div className="absolute top-1.5 left-1.5 px-2 py-0.5 bg-white/90 backdrop-blur-md rounded-full shadow-md text-[10px] sm:text-[10px] sm:text-xs font-bold text-paddy-700">
            {index + 1}
          </div>

          {/* 悬停时显示的查看按钮 */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="w-10 h-10 bg-white/90 backdrop-blur-md rounded-full shadow-lg flex items-center justify-center transform scale-0 group-hover:scale-100 transition-transform duration-300">
              <Maximize2 className="w-5 h-5 text-paddy-600" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
