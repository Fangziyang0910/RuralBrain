"use client";

import React from "react";
import { Bug, CheckCircle2, AlertTriangle, Info, PieChart } from "lucide-react";
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

interface DetectionCardProps {
  data: DetectionCardData | EnhancedDetectionData;
  toolName: string;
}

/**
 * 严重程度仪表盘组件
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
 * 检测分布条形图组件
 */
function DistributionChart({ detections }: { detections: Detection[] }) {
  const maxCount = Math.max(...detections.map(d => d.count), 1);
  const colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#22c55e"];

  return (
    <div className="space-y-2.5">
      {detections.map((detection, idx) => {
        const percentage = (detection.count / maxCount) * 100;
        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-stone-700 w-20 truncate">{detection.name}</span>
              <span className="font-bold text-stone-900">{detection.count}</span>
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
  const getSeverityConfig = (severity: DetectionCardData["severity"]) => {
    switch (severity) {
      case "none":
        return {
          icon: CheckCircle2,
          label: "未检测到",
          color: "text-green-600",
          bg: "bg-green-50",
          border: "border-green-200",
        };
      case "low":
        return {
          icon: Info,
          label: "轻微",
          color: "text-blue-600",
          bg: "bg-blue-50",
          border: "border-blue-200",
        };
      case "medium":
        return {
          icon: AlertTriangle,
          label: "中等",
          color: "text-amber-600",
          bg: "bg-amber-50",
          border: "border-amber-200",
        };
      case "high":
        return {
          icon: AlertTriangle,
          label: "严重",
          color: "text-red-600",
          bg: "bg-red-50",
          border: "border-red-200",
        };
      default:
        return {
          icon: Info,
          label: "未知",
          color: "text-gray-600",
          bg: "bg-gray-50",
          border: "border-gray-200",
        };
    }
  };

  const severityConfig = getSeverityConfig(data.severity);

  // 检查是否有详细检测数据（用于置信度展示）
  const enhancedData = data as EnhancedDetectionData;
  const hasDetailedData = enhancedData.detailed_detections && enhancedData.detailed_detections.length > 0;
  const detailedDetections = enhancedData.detailed_detections || [];
  const avgConfidence = enhancedData.avg_confidence || 0;

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      "overflow-hidden",
      severityConfig.bg,
      severityConfig.border
    )}>
      {/* 头部：标题 + 检测数量 */}
      <div className={cn(
        "flex items-center justify-between",
        "px-4 py-3 sm:px-5 sm:py-3.5",
        "border-b",
        severityConfig.border
      )}>
        <div className="flex items-center gap-2">
          <Bug className={cn("w-5 h-5", severityConfig.color)} />
          <h3 className="font-bold text-base text-stone-900">
            {toolName}
          </h3>
        </div>
        <div className={cn(
          "flex items-center gap-1.5 sm:gap-2",
          "px-2.5 py-1 rounded-full",
          "text-xs sm:text-sm font-medium",
          severityConfig.bg,
          severityConfig.color
        )}>
          <PieChart className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span>{data.totalCount}个目标</span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-4 sm:p-5 space-y-4">
        {/* 严重程度仪表盘 */}
        <div className="bg-white/60 rounded-xl p-4 shadow-sm">
          <SeverityGauge severity={data.severity} totalCount={data.totalCount} />
        </div>

        {/* 检测结果分布图 */}
        {data.detections.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3">📊 检测分布</div>
            <DistributionChart detections={data.detections} />
          </div>
        )}

        {/* 置信度展示（有详细数据时） */}
        {hasDetailedData && (
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
                    severityConfig.bg.replace("bg-", "bg-").replace("50", "500")
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
