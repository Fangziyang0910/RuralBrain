"use client";

import React, { useState } from 'react';
import { X, Crosshair, Maximize2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import { DetailedDetection } from '@/types/tool';

interface AnnotatedImageProps {
  src: string;              // 原图或标注图 URL
  detections: DetailedDetection[];
  imageWidth: number;
  imageHeight: number;
  onBoxClick?: (detection: DetailedDetection) => void;
}

/**
 * 置信度颜色映射
 * 高置信度(≥80%)绿色、中等(50-80%)黄色、低(<50%)红色
 */
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "#22c55e";  // 绿色 - 高置信度
  if (confidence >= 0.5) return "#f59e0b";  // 黄色 - 中等
  return "#ef4444";                          // 红色 - 低置信度
}

/**
 * 置信度标签
 */
function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return "高置信";
  if (confidence >= 0.5) return "中等";
  return "低置信";
}

/**
 * 检测详情面板组件
 */
function DetectionDetailPanel({
  detection,
  onClose,
}: {
  detection: DetailedDetection;
  onClose: () => void;
}) {
  const confidencePercent = Math.round(detection.confidence * 100);
  const color = getConfidenceColor(detection.confidence);
  const label = getConfidenceLabel(detection.confidence);

  return (
    <div className={cn(
      "absolute bottom-4 left-4 right-4",
      "bg-white/95 backdrop-blur-md",
      "rounded-xl shadow-lg border",
      "p-4 animate-slide-up"
    )}>
      {/* 关闭按钮 */}
      <button
        onClick={onClose}
        className="absolute top-2 right-2 p-1 rounded-full hover:bg-gray-100"
      >
        <X className="w-4 h-4 text-gray-500" />
      </button>

      {/* 标题 */}
      <div className="flex items-center gap-2 mb-3">
        <Crosshair className="w-5 h-5" style={{ color }} />
        <span className="font-bold text-stone-900">{detection.class_name}</span>
        <span className={cn(
          "px-2 py-0.5 rounded-full text-xs font-medium",
          confidencePercent >= 80 ? "bg-emerald-100 text-emerald-700" :
          confidencePercent >= 50 ? "bg-amber-100 text-amber-700" :
          "bg-red-100 text-red-700"
        )}>
          {label}
        </span>
      </div>

      {/* 置信度进度条 */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-stone-500">置信度</span>
          <span className="font-bold" style={{ color }}>{confidencePercent}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${confidencePercent}%`, backgroundColor: color }}
          />
        </div>
      </div>

      {/* 位置和大小信息 */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-stone-50 rounded-lg p-2">
          <div className="text-stone-500 mb-1">位置</div>
          <div className="font-medium text-stone-700">
            ({Math.round(detection.center[0])}, {Math.round(detection.center[1])})
          </div>
        </div>
        <div className="bg-stone-50 rounded-lg p-2">
          <div className="text-stone-500 mb-1">大小</div>
          <div className="font-medium text-stone-700">
            {Math.round(detection.size.width)} × {Math.round(detection.size.height)}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 标注图片组件
 * 在图片上使用 SVG 绘制检测标注框，支持交互（悬停、点击）
 */
export const AnnotatedImage: React.FC<AnnotatedImageProps> = ({
  src,
  detections,
  imageWidth,
  imageHeight,
  onBoxClick,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [showAllLabels, setShowAllLabels] = useState(false);

  // 如果没有检测数据或图片尺寸无效，只显示图片
  if (!detections || detections.length === 0 || imageWidth <= 0 || imageHeight <= 0) {
    return (
      <div className="relative rounded-xl overflow-hidden">
        <img src={src} alt="检测结果" className="w-full h-auto" />
      </div>
    );
  }

  return (
    <div className="relative rounded-xl overflow-hidden group">
      {/* 图片 */}
      <img
        src={src}
        alt="检测结果"
        className="w-full h-auto"
        onClick={() => setSelectedIndex(null)}
      />

      {/* SVG 标注框 overlay */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox={`0 0 ${imageWidth} ${imageHeight}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {detections.map((det, idx) => {
          const [x1, y1, x2, y2] = det.bbox;
          const color = getConfidenceColor(det.confidence);
          const isHovered = hoveredIndex === idx;
          const isSelected = selectedIndex === idx;

          return (
            <g
              key={idx}
              className="pointer-events-auto"
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedIndex(idx);
                onBoxClick?.(det);
              }}
            >
              {/* 标注框 */}
              <rect
                x={x1}
                y={y1}
                width={x2 - x1}
                height={y2 - y1}
                fill="none"
                stroke={color}
                strokeWidth={isHovered || isSelected ? 3 : 2}
                strokeDasharray={det.confidence < 0.5 ? "4 2" : "none"}
                className="transition-all duration-200 cursor-pointer"
                rx={2}
              />

              {/* 角标记 */}
              {(isHovered || isSelected) && (
                <>
                  {/* 左上角 */}
                  <circle cx={x1} cy={y1} r={4} fill={color} />
                  {/* 右上角 */}
                  <circle cx={x2} cy={y1} r={4} fill={color} />
                  {/* 左下角 */}
                  <circle cx={x1} cy={y2} r={4} fill={color} />
                  {/* 右下角 */}
                  <circle cx={x2} cy={y2} r={4} fill={color} />
                </>
              )}

              {/* 标签（悬停、选中或全局显示时） */}
              {(isHovered || isSelected || showAllLabels) && (
                <g>
                  {/* 标签背景 */}
                  <rect
                    x={x1}
                    y={Math.max(0, y1 - 24)}
                    width={90}
                    height={20}
                    fill={color}
                    rx={4}
                  />
                  {/* 标签文字 */}
                  <text
                    x={x1 + 6}
                    y={Math.max(12, y1 - 12)}
                    fill="white"
                    fontSize="11"
                    fontWeight="600"
                    fontFamily="system-ui"
                  >
                    {det.class_name} {Math.round(det.confidence * 100)}%
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* 控制按钮：显示/隐藏所有标签 */}
      {detections.length > 0 && (
        <button
          onClick={() => setShowAllLabels(!showAllLabels)}
          className={cn(
            "absolute top-3 right-3",
            "flex items-center gap-1",
            "px-2 py-1 rounded-lg",
            "bg-white/90 backdrop-blur-sm shadow",
            "text-xs font-medium text-stone-700",
            "hover:bg-white transition-colors"
          )}
        >
          <Maximize2 className="w-3 h-3" />
          {showAllLabels ? "隐藏标签" : "显示所有"}
        </button>
      )}

      {/* 检测数量统计 */}
      <div className={cn(
        "absolute top-3 left-3",
        "px-2 py-1 rounded-lg",
        "bg-white/90 backdrop-blur-sm shadow",
        "text-xs font-medium text-stone-700"
      )}>
        共 {detections.length} 个目标
      </div>

      {/* 选中详情面板 */}
      {selectedIndex !== null && detections[selectedIndex] && (
        <DetectionDetailPanel
          detection={detections[selectedIndex]}
          onClose={() => setSelectedIndex(null)}
        />
      )}
    </div>
  );
};

export default AnnotatedImage;