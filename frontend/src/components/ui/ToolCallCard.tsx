"use client";

import React, { useState, useEffect } from "react";
import { ChevronUp, ChevronDown, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/utils/cn";
import { getToolConfig, getToolColorClass, ToolIconConfig } from "@/config/tool-icons";

export interface ToolCall {
  name: string;
  status: "运行中" | "已完成";
  resultImage?: string;
  summary?: string[];
}

interface ToolCallCardProps {
  toolCall: ToolCall;
  index?: number;
}

/**
 * 增强的工具调用卡片组件，带丰富的动画效果
 */
export const ToolCallCard: React.FC<ToolCallCardProps> = ({
  toolCall,
  index = 0
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCompletion, setShowCompletion] = useState(false);
  const [contentHeight, setContentHeight] = useState(0);
  const contentRef = React.useRef<HTMLDivElement>(null);

  // 从配置获取工具图标和颜色
  const config = getToolConfig(toolCall.name);
  const colorClass = getToolColorClass(config.color);

  // 监听状态变化，触发完成动画
  useEffect(() => {
    if (toolCall.status === "已完成" && !showCompletion) {
      setShowCompletion(true);
      // 3秒后移除完成动画类
      const timer = setTimeout(() => setShowCompletion(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [toolCall.status, showCompletion]);

  // 计算展开内容的高度
  useEffect(() => {
    if (isExpanded && contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [isExpanded]);

  // 计算交错延迟
  const staggerDelay = Math.min(index * 100, 400);

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-300 ease-out",
        "p-3.5 sm:p-4 relative overflow-hidden",
        "tool-call-card-enhanced tool-hover-lift",
        colorClass.bg,
        colorClass.border,
        toolCall.status === "运行中" && "tool-running-progress",
        showCompletion && "tool-call-complete"
      )}
      style={{
        animationDelay: `${staggerDelay}ms`
      }}
    >
      {/* 完成庆祝效果 - 彩带 */}
      {showCompletion && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className={cn(
                "tool-confetti",
                i % 2 === 0 ? "bg-green-400" : "bg-gold-400"
              )}
              style={{
                left: `${20 + i * 15}%`,
                animationDelay: `${i * 50}ms`,
                animationDuration: `${600 + i * 50}ms`
              }}
            />
          ))}
        </div>
      )}

      {/* 运行中进度指示器 */}
      {toolCall.status === "运行中" && (
        <div className="tool-progress-indicator" style={{ width: "60%" }} />
      )}

      {/* 工具调用头部 */}
      <div
        className={cn(
          "flex items-center justify-between cursor-pointer group",
          "gap-2 sm:gap-3 relative z-10",
          toolCall.status === "运行中" && "tool-status-running"
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={cn(
          "flex items-center gap-2 sm:gap-3 flex-1 min-w-0"
        )}>
          {/* 工具图标 - 带动画 */}
          <span
            className={cn(
              "text-xl sm:text-2xl flex-shrink-0 tool-icon-animate",
              toolCall.status === "已完成" && "scale-110"
            )}
            role="img"
            aria-label={config.label}
            style={{ animationDelay: `${staggerDelay + 100}ms` }}
          >
            {config.icon}
          </span>

          {/* 工具名称 */}
          <span className={cn(
            "font-semibold truncate text-sm sm:text-base",
            colorClass.text
          )}>
            {config.label}
          </span>

          {/* 状态指示器 - 带动画 */}
          <div className={cn(
            "flex items-center gap-1 sm:gap-1.5 flex-shrink-0"
          )}>
            {toolCall.status === "已完成" ? (
              <>
                <CheckCircle2 className={cn(
                  "text-green-500 w-3.5 h-3.5 sm:w-4 sm:h-4 transition-transform duration-300",
                  showCompletion && "scale-125"
                )} />
                {showCompletion && (
                  <Sparkles className="text-gold-500 w-3.5 h-3.5 sm:w-4 sm:h-4 animate-pulse" />
                )}
              </>
            ) : (
              <div className={cn(
                "relative",
                toolCall.status === "运行中" && "tool-loading-ripple rounded-full"
              )}>
                <Loader2 className={cn(
                  "text-amber-500 animate-spin w-3.5 h-3.5 sm:w-4 sm:h-4"
                )} />
              </div>
            )}
            <span className={cn(
              "rounded-full font-medium text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 status-badge-animate",
              toolCall.status === "已完成"
                ? "bg-green-100 text-green-700"
                : "bg-amber-100 text-amber-700"
            )}>
              {toolCall.status}
            </span>
          </div>
        </div>

        {/* 展开/收起图标 */}
        <div className="flex-shrink-0">
          {isExpanded ? (
            <ChevronUp className={cn(
              "transition-all duration-300 opacity-60 group-hover:opacity-100",
              colorClass.text,
              "w-4 h-4 sm:w-5 sm:h-5",
              isExpanded && "rotate-180"
            )} />
          ) : (
            <ChevronDown className={cn(
              "transition-all duration-300 opacity-60 group-hover:opacity-100",
              colorClass.text,
              "w-4 h-4 sm:w-5 sm:h-5"
            )} />
          )}
        </div>
      </div>

      {/* 展开内容 - 带平滑动画 */}
      {isExpanded && (
        <div
          ref={contentRef}
          className={cn(
            "border-t mt-3 sm:mt-4 pt-3 sm:pt-4 tool-content-expand relative z-10",
            colorClass.border
          )}
          style={{
            maxHeight: isExpanded ? contentHeight : 0,
            transition: "max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1)"
          }}
        >
          {/* 检测结果图片 */}
          {toolCall.resultImage && (
            <div className="mb-3 sm:mb-4">
              <img
                src={toolCall.resultImage}
                alt="工具检测结果"
                className={cn(
                  "w-full rounded-lg shadow-md",
                  "transition-transform duration-300 hover:scale-105",
                  "image-reveal"
                )}
                loading="lazy"
              />
            </div>
          )}

          {/* 工具调用摘要 */}
          {toolCall.summary && toolCall.summary.length > 0 && (
            <div>
              <div className={cn(
                "font-semibold mb-2 uppercase tracking-wide",
                "text-[10px] sm:text-xs",
                colorClass.text,
                "opacity-70"
              )}>
                执行摘要
              </div>
              <ul className="space-y-1 sm:space-y-1.5">
                {toolCall.summary.map((item, idx) => (
                  <li
                    key={idx}
                    className={cn(
                      "flex items-start gap-1.5 sm:gap-2 text-stone-700",
                      "text-xs sm:text-sm transition-all duration-200",
                      "hover:translate-x-1"
                    )}
                    style={{
                      animationDelay: `${idx * 50}ms`
                    }}
                  >
                    <span className={cn("mt-0.5 flex-shrink-0", colorClass.text)}>•</span>
                    <span className="flex-1 break-words">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
