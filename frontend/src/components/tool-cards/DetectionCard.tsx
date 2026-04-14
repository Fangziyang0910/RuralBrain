"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, Info, PieChart, Beef, TrendingUp } from "lucide-react";
import { cn } from "@/utils/cn";
import { ConfidenceDistributionChart, AverageConfidenceDisplay } from "@/components/ui/ConfidenceGauge";
import { EnhancedDetectionData } from "@/types/tool";

/**
 * 单个检测结果
 */
interface Detection {
  name: string;
  count: number;
  confidence?: number;
}

/**
 * 检测工具结构化数据
 */
export interface DetectionCardData {
  detections: Detection[];
  totalCount: number;
  severity: "low" | "medium" | "high" | "none";
  summary: string;
  suggestions?: string[];
}

/**
 * 检测显示模式
 * - pest: 病虫害检测，使用严重程度
 * - count: 数量统计（牛只检测），显示数量仪表盘
 * - identify: 品种识别（大米检测），显示识别结果
 */
type DetectionMode = "pest" | "count" | "identify";

/**
 * 根据工具名称判断检测模式
 */
function getDetectionMode(toolName: string): DetectionMode {
  if (toolName.includes("病虫害") || toolName.includes("pest")) {
    return "pest";
  }
  if (toolName.includes("牛只") || toolName.includes("奶牛") || toolName.includes("cow") || toolName.includes("牛")) {
    return "count";
  }
  if (toolName.includes("大米") || toolName.includes("rice") || toolName.includes("品种")) {
    return "identify";
  }
  // 默认使用 pest 模式
  return "pest";
}

interface DetectionCardProps {
  data: DetectionCardData | EnhancedDetectionData;
  toolName: string;
}

/**
 * 严重程度仪表盘组件（病虫害检测专用）
 */
function SeverityGauge({ severity, totalCount }: { severity: DetectionCardData["severity"]; totalCount: number }) {
  const getSeverityColor = (s: DetectionCardData["severity"]) => {
    switch (s) {
      case "none": return { color: "#22c55e", label: "无", percent: 0 };
      case "low": return { color: "#3b82f6", label: "轻微", percent: 25 };
      case "medium": return { color: "#f59e0b", label: "中等", percent: 60 };
      case "high": return { color: "#ef4444", label: "严重", percent: 100 };
      default: return { color: "#9ca3af", label: "未知", percent: 0 };
    }
  };

  const { color, label, percent } = getSeverityColor(severity);

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-20 h-20">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={`${percent}, 100`}
            className="transition-all duration-1000 ease-out"
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className="text-lg font-bold" style={{ color }}>
            {label}
          </span>
        </div>
      </div>
      <div className="flex-1">
        <div className="text-xs text-stone-500 mb-1">检测数量</div>
        <div className="text-2xl font-bold text-stone-900">{totalCount}</div>
      </div>
    </div>
  );
}

/**
 * 数量统计仪表盘组件（牛只检测专用）
 */
function CountGauge({ totalCount, avgConfidence }: { totalCount: number; avgConfidence?: number }) {
  // 根据数量显示不同的颜色和状态
  const getCountDisplay = (count: number) => {
    if (count === 0) return { color: "#9ca3af", label: "未检测到", bg: "bg-gray-50" };
    if (count >= 20) return { color: "#22c55e", label: "数量充足", bg: "bg-emerald-50" };
    if (count >= 10) return { color: "#3b82f6", label: "数量正常", bg: "bg-blue-50" };
    return { color: "#f59e0b", label: "数量较少", bg: "bg-amber-50" };
  };

  const { color, label } = getCountDisplay(totalCount);
  const confidencePercent = avgConfidence ? Math.round(avgConfidence * 100) : 0;

  return (
    <div className="flex items-center gap-4">
      {/* 数量圆形展示 */}
      <div className="relative w-24 h-24">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          {/* 外圈 */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="6"
          />
          {/* 数量指示（基于数量百分比） */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={`${Math.min(totalCount, 30) / 30 * 251.2}, 251.2`}
            className="transition-all duration-1000 ease-out"
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
          />
          {/* 内圈显示数量 */}
          <text
            x="50"
            y="45"
            textAnchor="middle"
            className="text-3xl font-bold"
            style={{ fill: color }}
          >
            {totalCount}
          </text>
          <text
            x="50"
            y="65"
            textAnchor="middle"
            className="text-xs font-medium"
            style={{ fill: '#78716c' }}
          >
            头
          </text>
        </svg>
      </div>

      {/* 详细信息 */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <Beef className="w-4 h-4" style={{ color }} />
          <span className="font-bold text-stone-900">{label}</span>
        </div>
        {avgConfidence && avgConfidence > 0 && (
          <div className="flex items-center gap-2 text-xs text-stone-500">
            <TrendingUp className="w-3 h-3" />
            <span>平均置信度: {confidencePercent}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 品种识别仪表盘组件（大米检测专用）
 * 显示所有检测到的品种列表
 */
function IdentifyGauge({ detections }: { detections: Detection[] }) {
  const color = "#3b82f6"; // 品种识别使用蓝色
  const totalCount = detections.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="flex items-start gap-4">
      {/* 识别结果圆形展示 */}
      <div className="relative w-20 h-20 flex-shrink-0">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          {/* 外圈 */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="6"
          />
          {/* 识别成功指示 */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray="251.2"
            className="transition-all duration-1000 ease-out"
          />
          {/* 中心显示总数 */}
          <text
            x="50"
            y="40"
            textAnchor="middle"
            className="text-xl font-bold"
            style={{ fill: color }}
          >
            {totalCount}
          </text>
          <text
            x="50"
            y="55"
            textAnchor="middle"
            className="text-xs"
            style={{ fill: '#78716c' }}
          >
            粒
          </text>
          <text
            x="50"
            y="70"
            textAnchor="middle"
            className="text-xs"
            style={{ fill: '#78716c' }}
          >
            {detections.length}种
          </text>
        </svg>
      </div>

      {/* 品种列表 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">🌾</span>
          <span className="text-xs text-stone-500">识别结果</span>
        </div>
        {detections.length > 0 ? (
          <div className="space-y-1.5">
            {detections.map((det, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <span className="font-medium text-stone-900 truncate">{det.name}</span>
                <span className="text-xs text-stone-500">{det.count}粒</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-stone-500">未识别到品种</div>
        )}
      </div>
    </div>
  );
}

/**
 * 检测分布条形图组件
 */
function DistributionChart({ detections, mode }: { detections: Detection[]; mode: DetectionMode }) {
  const maxCount = Math.max(...detections.map(d => d.count), 1);
  const colors = mode === "count"
    ? ["#22c55e", "#3b82f6", "#8b5cf6", "#f59e0b", "#ec4899"]  // 牛只检测：绿色系
    : mode === "identify"
    ? ["#3b82f6", "#8b5cf6", "#22c55e", "#f59e0b", "#ec4899"]  // 品种识别：蓝色系
    : ["#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6", "#22c55e"]; // 病虫害：红色系

  return (
    <div className="space-y-2.5">
      {detections.map((detection, idx) => {
        const percentage = (detection.count / maxCount) * 100;
        const showConfidence = mode === "identify" && detection.confidence;
        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-stone-700 w-24 truncate">{detection.name}</span>
              <div className="flex items-center gap-2">
                <span className="font-bold text-stone-900">{detection.count}</span>
                {showConfidence && (
                  <span className="text-xs text-stone-500">({Math.round(detection.confidence! * 100)}%)</span>
                )}
              </div>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${percentage}%`,
                  backgroundColor: colors[idx % colors.length],
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * 检测工具专用卡片组件
 */
export const DetectionCard: React.FC<DetectionCardProps> = ({
  data,
  toolName,
}) => {
  // 判断检测模式
  const mode = getDetectionMode(toolName);

  // 根据模式获取显示配置
  const getModeConfig = (m: DetectionMode) => {
    switch (m) {
      case "count":
        return {
          icon: Beef,
          headerLabel: "牛只检测",
          color: "text-emerald-600",
          bg: "bg-emerald-50",
          border: "border-emerald-200",
        };
      case "identify":
        return {
          icon: Info,
          headerLabel: "品种识别",
          color: "text-blue-600",
          bg: "bg-blue-50",
          border: "border-blue-200",
        };
      default:
        // pest 模式根据 severity 动态配置
        return getSeverityConfig(data.severity);
    }
  };

  const getSeverityConfig = (severity: DetectionCardData["severity"]) => {
    switch (severity) {
      case "none":
        return {
          icon: CheckCircle2,
          headerLabel: "未检测到",
          color: "text-green-600",
          bg: "bg-green-50",
          border: "border-green-200",
        };
      case "low":
        return {
          icon: Info,
          headerLabel: "轻微",
          color: "text-blue-600",
          bg: "bg-blue-50",
          border: "border-blue-200",
        };
      case "medium":
        return {
          icon: AlertTriangle,
          headerLabel: "中等",
          color: "text-amber-600",
          bg: "bg-amber-50",
          border: "border-amber-200",
        };
      case "high":
        return {
          icon: AlertTriangle,
          headerLabel: "严重",
          color: "text-red-600",
          bg: "bg-red-50",
          border: "border-red-200",
        };
      default:
        return {
          icon: Info,
          headerLabel: "未知",
          color: "text-gray-600",
          bg: "bg-gray-50",
          border: "border-gray-200",
        };
    }
  };

  // pest 模式使用 severity 配置，其他模式使用固定配置
  const modeConfig = mode === "pest" ? getSeverityConfig(data.severity) : getModeConfig(mode);
  const IconComponent = modeConfig.icon;

  // 检查是否有详细检测数据（用于置信度展示）
  const enhancedData = data as EnhancedDetectionData;
  const hasDetailedData = enhancedData.detailed_detections && enhancedData.detailed_detections.length > 0;
  const detailedDetections = enhancedData.detailed_detections || [];
  const avgConfidence = enhancedData.avg_confidence || 0;

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      "overflow-hidden",
      modeConfig.bg,
      modeConfig.border
    )}>
      {/* 头部：标题 + 检测数量 */}
      <div className={cn(
        "flex items-center justify-between",
        "px-4 py-3 sm:px-5 sm:py-3.5",
        "border-b",
        modeConfig.border
      )}>
        <div className="flex items-center gap-2">
          <IconComponent className={cn("w-5 h-5", modeConfig.color)} />
          <h3 className="font-bold text-base text-stone-900">
            {toolName}
          </h3>
        </div>
        <div className={cn(
          "flex items-center gap-1.5 sm:gap-2",
          "px-2.5 py-1 rounded-full",
          "text-xs sm:text-sm font-medium",
          modeConfig.bg,
          modeConfig.color
        )}>
          <PieChart className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span>
            {mode === "count" ? `${data.totalCount}头` :
             mode === "identify" ? `${data.detections.length}种` :
             `${data.totalCount}个目标`}
          </span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-4 sm:p-5 space-y-4">
        {/* 主仪表盘 - 根据模式显示不同内容 */}
        <div className="bg-white/60 rounded-xl p-4 shadow-sm">
          {mode === "pest" && (
            <SeverityGauge severity={data.severity} totalCount={data.totalCount} />
          )}
          {mode === "count" && (
            <CountGauge totalCount={data.totalCount} avgConfidence={avgConfidence} />
          )}
          {mode === "identify" && (
            <IdentifyGauge detections={data.detections} />
          )}
        </div>

        {/* 检测结果分布图 */}
        {data.detections.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3">
              <DistributionChart detections={data.detections} mode={mode} />
            </div>
          </div>
        )}

        {/* 置信度展示（有详细数据时，仅 count 和 identify 模式） */}
        {hasDetailedData && mode !== "pest" && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3">🎯 置信度分析</div>
            {avgConfidence > 0 ? (
              <AverageConfidenceDisplay avgConfidence={avgConfidence} count={detailedDetections.length} />
            ) : (
              <ConfidenceDistributionChart detections={detailedDetections} />
            )}
          </div>
        )}

        {/* 处理建议 */}
        {data.suggestions && data.suggestions.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-stone-600 uppercase tracking-wide flex items-center gap-1.5">
              💡 处理建议
            </div>
            <div className="bg-white/60 rounded-lg p-3 space-y-2">
              {data.suggestions.map((suggestion, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-stone-700">
                  <span className={cn(
                    "mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0",
                    modeConfig.bg.replace("50", "500")
                  )} />
                  <span>{suggestion}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};