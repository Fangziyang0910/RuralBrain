"use client";

import React from 'react';
import { cn } from '@/utils/cn';

interface ConfidenceGaugeProps {
  confidence: number;  // 0-1
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

/**
 * 置信度颜色映射
 */
function getConfidenceConfig(confidence: number) {
  if (confidence >= 0.8) {
    return { color: "#22c55e", label: "高置信", bg: "bg-emerald-50", text: "text-emerald-600" };
  }
  if (confidence >= 0.5) {
    return { color: "#f59e0b", label: "中等", bg: "bg-amber-50", text: "text-amber-600" };
  }
  return { color: "#ef4444", label: "低置信", bg: "bg-red-50", text: "text-red-600" };
}

/**
 * 置信度仪表盘组件
 * 使用 SVG 绘制圆形仪表盘，展示置信度百分比
 */
export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({
  confidence,
  size = "md",
  showLabel = true,
}) => {
  const percent = Math.round(confidence * 100);
  const config = getConfidenceConfig(confidence);

  // 尺寸映射
  const sizeMap = {
    sm: { dimension: 48, fontSize: "text-xs", labelSize: "text-[10px]" },
    md: { dimension: 72, fontSize: "text-sm", labelSize: "text-xs" },
    lg: { dimension: 96, fontSize: "text-base", labelSize: "text-xs" },
  };

  const { dimension, fontSize, labelSize } = sizeMap[size];

  // SVG path for circular arc
  const pathD = "M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831";

  return (
    <div
      className="relative flex flex-col items-center justify-center"
      style={{ width: dimension, height: dimension }}
    >
      {/* SVG 圆形仪表盘 */}
      <svg
        className="w-full h-full transform -rotate-90"
        viewBox="0 0 36 36"
      >
        {/* 背景圆 */}
        <path
          d={pathD}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="3"
        />
        {/* 进度圆 */}
        <path
          d={pathD}
          fill="none"
          stroke={config.color}
          strokeWidth="3"
          strokeDasharray={`${percent}, 100`}
          className="transition-all duration-1000 ease-out"
          strokeLinecap="round"
        />
      </svg>

      {/* 中心文字 */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={cn("font-bold", fontSize)}
          style={{ color: config.color }}
        >
          {percent}%
        </span>
        {showLabel && (
          <span className={cn("text-stone-500", labelSize)}>
            {config.label}
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * 置信度分布条形图组件
 * 用于展示多个检测目标的置信度分布
 */
export const ConfidenceDistributionChart: React.FC<{
  detections: Array<{ class_name: string; confidence: number }>;
}> = ({ detections }) => {
  const colors = ["#22c55e", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6"];

  return (
    <div className="space-y-2">
      {detections.map((det, idx) => {
        const percent = Math.round(det.confidence * 100);
        const color = getConfidenceConfig(det.confidence).color;

        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-stone-700 truncate max-w-[120px]">
                {det.class_name}
              </span>
              <span className="font-bold text-stone-900">{percent}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out relative"
                style={{ width: `${percent}%`, backgroundColor: color }}
              >
                {/* 脉冲动画效果 */}
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * 平均置信度展示组件
 */
export const AverageConfidenceDisplay: React.FC<{
  avgConfidence: number;
  count: number;
}> = ({ avgConfidence, count }) => {
  const config = getConfidenceConfig(avgConfidence);
  const percent = Math.round(avgConfidence * 100);

  return (
    <div className="flex items-center gap-4">
      {/* 仪表盘 */}
      <ConfidenceGauge confidence={avgConfidence} size="md" />

      {/* 右侧信息 */}
      <div className="flex-1">
        <div className="text-xs text-stone-500 mb-1">平均置信度</div>
        <div className={cn("font-bold text-xl", config.text)}>
          {percent}%
        </div>
        <div className="text-xs text-stone-500 mt-1">
          共 {count} 个检测目标
        </div>
      </div>
    </div>
  );
};

export default ConfidenceGauge;