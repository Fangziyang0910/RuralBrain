"use client";

import React from "react";
import { cn } from "@/utils/cn";
import { LucideIcon } from "lucide-react";

interface ToggleButtonProps {
  /** 是否启用 */
  enabled: boolean;
  /** 点击切换时的回调 */
  onToggle: () => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 按钮标签文字 */
  label: string;
  /** 图标组件 */
  icon?: LucideIcon;
  /** 启用状态的配色主题 */
  activeTheme?: "earth" | "sky" | "harvest";
  /** 尺寸 */
  size?: "sm" | "md" | "lg";
  /** 额外的 className */
  className?: string;
}

/**
 * 现代化开关按钮组件
 *
 * 设计特点：
 * - Glass morphism 效果
 * - 流畅的状态切换动画
 * - SVG 图标（符合 UI/UX Pro Max 规范）
 * - 触摸目标 ≥ 44x44pt
 * - 清晰的启用/禁用状态区分
 */
export function ToggleButton({
  enabled,
  onToggle,
  disabled = false,
  label,
  icon,
  activeTheme = "earth",
  size = "md",
  className,
}: ToggleButtonProps) {
  // 主题配色
  const themes = {
    earth: {
      active: {
        bg: "bg-gradient-to-r from-earth-500/20 to-earth-600/10",
        border: "border-earth-400",
        text: "text-earth-700",
        iconColor: "text-earth-600",
        glow: "shadow-[0_0_20px_rgba(34,197,94,0.15)]",
      },
      inactive: {
        bg: "bg-white/80",
        border: "border-earth-200",
        text: "text-stone-500",
        iconColor: "text-stone-400",
      },
    },
    sky: {
      active: {
        bg: "bg-gradient-to-r from-sky-500/20 to-sky-600/10",
        border: "border-sky-400",
        text: "text-sky-700",
        iconColor: "text-sky-600",
        glow: "shadow-[0_0_20px_rgba(14,165,233,0.15)]",
      },
      inactive: {
        bg: "bg-white/80",
        border: "border-sky-200",
        text: "text-stone-500",
        iconColor: "text-stone-400",
      },
    },
    harvest: {
      active: {
        bg: "bg-gradient-to-r from-harvest-500/20 to-harvest-600/10",
        border: "border-harvest-400",
        text: "text-harvest-700",
        iconColor: "text-harvest-600",
        glow: "shadow-[0_0_20px_rgba(234,179,8,0.15)]",
      },
      inactive: {
        bg: "bg-white/80",
        border: "border-harvest-200",
        text: "text-stone-500",
        iconColor: "text-stone-400",
      },
    },
  };

  // 尺寸配置
  const sizes = {
    sm: {
      button: "px-3 py-1.5 gap-1.5",
      text: "text-xs",
      icon: "w-3.5 h-3.5",
      indicator: "w-4 h-2.5",
    },
    md: {
      button: "px-4 py-2.5 gap-2",
      text: "text-sm",
      icon: "w-4 h-4",
      indicator: "w-5 h-3",
    },
    lg: {
      button: "px-5 py-3 gap-2.5",
      text: "text-base",
      icon: "w-5 h-5",
      indicator: "w-6 h-3.5",
    },
  };

  const theme = themes[activeTheme];
  const sizeConfig = sizes[size];
  const IconComponent = icon;

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={cn(
        // 基础样式
        "inline-flex items-center justify-center",
        "rounded-full font-medium",
        "border-2 backdrop-blur-sm",
        "transition-all duration-200 ease-out",
        // 触摸目标最小尺寸
        "min-h-[44px]",
        // 禁用状态
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
        // 状态样式
        enabled
          ? cn(
              theme.active.bg,
              theme.active.border,
              theme.active.text,
              theme.active.glow,
              "shadow-md hover:shadow-lg"
            )
          : cn(
              theme.inactive.bg,
              theme.inactive.border,
              theme.inactive.text,
              "shadow-sm hover:shadow-md hover:bg-white/90"
            ),
        // 尺寸
        sizeConfig.button,
        // 悬停效果
        "hover:scale-[1.02] active:scale-[0.98]",
        // 焦点样式
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        enabled
          ? `focus-visible:ring-${activeTheme === "earth" ? "earth" : activeTheme === "sky" ? "sky" : "harvest"}-400`
          : "focus-visible:ring-stone-300",
        className
      )}
      aria-pressed={enabled}
      aria-label={`${label} ${enabled ? "已启用" : "已禁用"}`}
    >
      {/* 图标 */}
      {IconComponent && (
        <IconComponent
          className={cn(
            sizeConfig.icon,
            "transition-all duration-200",
            enabled ? theme.active.iconColor : theme.inactive.iconColor,
            enabled && "animate-pulse-once"
          )}
        />
      )}

      {/* 标签文字 */}
      <span className={cn(sizeConfig.text, "font-semibold tracking-wide")}>
        {label}
      </span>

      {/* 状态指示器 - 胶囊开关 */}
      <div
        className={cn(
          "relative rounded-full transition-all duration-300 ease-out",
          sizeConfig.indicator,
          enabled
            ? cn(
                "bg-gradient-to-r",
                activeTheme === "earth" && "from-earth-500 to-earth-600",
                activeTheme === "sky" && "from-sky-500 to-sky-600",
                activeTheme === "harvest" && "from-harvest-500 to-harvest-600"
              )
            : "bg-stone-200"
        )}
      >
        {/* 滑动圆点 */}
        <div
          className={cn(
            "absolute top-1/2 -translate-y-1/2 rounded-full bg-white shadow-sm",
            "transition-all duration-300 ease-out",
            activeTheme === "earth" && sizeConfig.indicator.includes("w-4") ? "w-2.5 h-2.5" : "w-2 h-2",
            activeTheme === "sky" && sizeConfig.indicator.includes("w-4") ? "w-2.5 h-2.5" : "w-2 h-2",
            activeTheme === "harvest" && sizeConfig.indicator.includes("w-4") ? "w-2.5 h-2.5" : "w-2 h-2",
            enabled
              ? sizeConfig.indicator.includes("w-4")
                ? "left-[calc(100%-10px)]"
                : sizeConfig.indicator.includes("w-5")
                ? "left-[calc(100%-12px)]"
                : "left-[calc(100%-14px)]"
              : "left-1"
          )}
        />
      </div>
    </button>
  );
}

// 动画样式需要在 globals.css 中添加