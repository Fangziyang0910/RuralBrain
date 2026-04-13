"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, Sparkles, Image, Check } from "lucide-react";
import { cn } from "@/utils/cn";

// 模型类型定义
interface Model {
  id: string;
  name: string;
  description: string;
  is_multimodal: boolean;
}

interface ModelSelectorProps {
  models: Model[];
  selectedModelId: string;
  onSelect: (modelId: string) => void;
  disabled?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModelId,
  onSelect,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedModel = models.find(m => m.id === selectedModelId);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 键盘导航
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case "Enter":
      case "Space":
        e.preventDefault();
        setIsOpen(!isOpen);
        break;
      case "Escape":
        setIsOpen(false);
        break;
      case "ArrowDown":
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          const currentIndex = models.findIndex(m => m.id === selectedModelId);
          const nextIndex = Math.min(currentIndex + 1, models.length - 1);
          onSelect(models[nextIndex].id);
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (isOpen) {
          const currentIndex = models.findIndex(m => m.id === selectedModelId);
          const prevIndex = Math.max(currentIndex - 1, 0);
          onSelect(models[prevIndex].id);
        }
        break;
    }
  };

  const handleSelect = (modelId: string) => {
    onSelect(modelId);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      {/* 触发按钮 */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          "model-selector-trigger",
          "flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2",
          "rounded-organic-full font-medium",
          "border-2 bg-white",
          "transition-all duration-300 ease-out",
          "focus:outline-none focus:ring-2 focus:ring-earth-400/30",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          isOpen
            ? "border-earth-400 shadow-organic bg-earth-50"
            : "border-earth-200 hover:border-earth-300 hover:shadow-natural shadow-natural"
        )}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        {/* 模型图标 */}
        <div className={cn(
          "w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center",
          "bg-gradient-to-br from-earth-400 to-earth-600 text-white",
          "shadow-sm transition-transform duration-300",
          isOpen && "scale-110"
        )}>
          <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </div>

        {/* 当前模型名称 */}
        <span className="text-sm sm:text-base text-earth-700 font-semibold">
          {selectedModel?.name || "选择模型"}
        </span>

        {/* 多模态徽章 */}
        {selectedModel?.is_multimodal && (
          <span className={cn(
            "inline-flex items-center gap-1 px-1.5 py-0.5 sm:px-2 sm:py-1",
            "rounded-full text-xs font-medium",
            "bg-sky-100 text-sky-700 border border-sky-200",
            "transition-all duration-200",
            "animate-pulse-once"
          )}>
            <Image className="w-3 h-3" />
            <span className="hidden sm:inline">多模态</span>
          </span>
        )}

        {/* 下拉箭头 */}
        <ChevronDown className={cn(
          "w-4 h-4 sm:w-5 sm:h-5 text-earth-500",
          "transition-transform duration-300 ease-out",
          isOpen && "rotate-180"
        )} />
      </button>

      {/* 下拉面板 */}
      {isOpen && (
        <div
          className={cn(
            "model-selector-dropdown",
            "absolute top-full left-0 mt-2 min-w-[200px] sm:min-w-[280px]",
            "bg-white rounded-organic-xl border-2 border-earth-100",
            "shadow-organic-lg overflow-hidden",
            "z-50",
            "animate-dropdown-enter"
          )}
          role="listbox"
        >
          {/* 标题 */}
          <div className={cn(
            "px-3 py-2 sm:px-4 sm:py-2.5",
            "bg-gradient-to-r from-earth-50 to-harvest-50",
            "border-b-2 border-earth-100",
            "text-xs sm:text-sm font-semibold text-earth-700"
          )}>
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-earth-500" />
              选择 AI 模型
            </span>
          </div>

          {/* 模型列表 */}
          <div className="py-1 sm:py-1.5">
            {models.map((model, index) => (
              <button
                key={model.id}
                type="button"
                onClick={() => handleSelect(model.id)}
                className={cn(
                  "model-option",
                  "w-full px-3 py-2.5 sm:px-4 sm:py-3",
                  "flex items-center gap-2 sm:gap-3",
                  "transition-all duration-200 ease-out",
                  "hover:bg-earth-50",
                  "focus:outline-none focus:bg-earth-50",
                  selectedModelId === model.id
                    ? "bg-earth-100/70 border-l-4 border-earth-500"
                    : "border-l-4 border-transparent",
                  // 入场动画延迟
                  `animate-option-enter delay-${index * 50}`
                )}
                role="option"
                aria-selected={selectedModelId === model.id}
              >
                {/* 模型图标 */}
                <div className={cn(
                  "w-8 h-8 sm:w-10 sm:h-10 rounded-organic-md flex items-center justify-center",
                  "transition-all duration-200",
                  selectedModelId === model.id
                    ? "bg-gradient-to-br from-earth-500 to-earth-600 text-white shadow-organic"
                    : "bg-earth-100 text-earth-600"
                )}>
                  <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                </div>

                {/* 模型信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 sm:gap-2">
                    <span className={cn(
                      "text-sm sm:text-base font-semibold truncate",
                      selectedModelId === model.id ? "text-earth-800" : "text-earth-700"
                    )}>
                      {model.name}
                    </span>
                    {/* 多模态标识 */}
                    {model.is_multimodal && (
                      <span className={cn(
                        "inline-flex items-center gap-0.5 px-1 py-0.5",
                        "rounded-full text-[10px] sm:text-xs font-medium",
                        selectedModelId === model.id
                          ? "bg-earth-200/70 text-earth-700"
                          : "bg-sky-100 text-sky-700"
                      )}>
                        <Image className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                        <span className="hidden sm:inline">多模态</span>
                      </span>
                    )}
                  </div>
                  <p className={cn(
                    "text-xs sm:text-sm truncate mt-0.5",
                    selectedModelId === model.id ? "text-earth-600" : "text-earth-500"
                  )}>
                    {model.description}
                  </p>
                </div>

                {/* 选中标记 */}
                {selectedModelId === model.id && (
                  <div className={cn(
                    "w-5 h-5 sm:w-6 sm:h-6 rounded-full",
                    "bg-gradient-to-br from-earth-500 to-earth-600",
                    "flex items-center justify-center text-white",
                    "animate-check-enter"
                  )}>
                    <Check className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* 底部提示 */}
          <div className={cn(
            "px-3 py-2 sm:px-4 sm:py-2.5",
            "bg-earth-50 border-t-2 border-earth-100",
            "text-xs text-earth-500"
          )}>
            <span className="flex items-center gap-1">
              <Image className="w-3 h-3 text-sky-500" />
              多模态模型支持图片识别
            </span>
          </div>
        </div>
      )}
    </div>
  );
};