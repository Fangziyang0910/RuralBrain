"use client";

import React from "react";

interface LoadingDotsProps {
  size?: "sm" | "md" | "lg";
  color?: string;
  className?: string;
}

/**
 * LoadingDots - 专业的加载动画组件
 *
 * 基于跳跳点动画（Bouncing Dots）
 * 符合现代 UI/UX 最佳实践
 */
export const LoadingDots: React.FC<LoadingDotsProps> = ({
  size = "md",
  color = "#10b981",
  className = "",
}) => {
  const sizeMap = {
    sm: "w-1.5 h-1.5",
    md: "w-2 h-2",
    lg: "w-2.5 h-2.5",
  };

  return (
    <div className={`loading-dots ${className}`} aria-label="加载中">
      <div
        className={`loading-dot ${sizeMap[size]}`}
        style={{ backgroundColor: color }}
      />
      <div
        className={`loading-dot ${sizeMap[size]}`}
        style={{ backgroundColor: color }}
      />
      <div
        className={`loading-dot ${sizeMap[size]}`}
        style={{ backgroundColor: color }}
      />
    </div>
  );
};

export default LoadingDots;
