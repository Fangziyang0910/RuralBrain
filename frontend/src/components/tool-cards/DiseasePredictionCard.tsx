"use client";

import React from "react";
import { Activity, AlertTriangle, Syringe, Stethoscope, TrendingUp } from "lucide-react";
import { cn } from "@/utils/cn";

/**
 * 单个疾病预测结果
 */
export interface DiseasePrediction {
  name: string;
  probability: number;
  reason: string;
}

/**
 * 疾病预测工具结构化数据
 */
export interface DiseasePredictionCardData {
  diseases: DiseasePrediction[];
  urgency: "high" | "medium" | "low";
  symptoms: string[];
  suggestions: {
    isolation?: string;
    treatment?: string;
    prevention?: string;
  };
  reminder?: string;
}

interface DiseasePredictionCardProps {
  data: DiseasePredictionCardData;
  toolName?: string;
}

/**
 * 疾病判断依据组件（支持展开/收起）
 */
function DiseaseReasonDisplay({ reason }: { reason: string }) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // 提取关键信息：移除冗余词汇，保留核心内容
  const formatReason = (text: string) => {
    return text
      .replace(/症状与.{1,10}?高度吻合：?/, "") // 移除"症状与XXX高度吻合"
      .replace(/检测模型.{3,30}?列为.{3,15}?(?:主要|次要)可能。?/, "") // 移除检测模型说明
      .replace(/知识库中.{3,30}?但.{3,15}?是.{3,30}?。?/, "") // 移除知识库说明
      .replace(/当前描述.{3,30}?，?故.{3,15}?较低。?$/, "") // 移除"当前描述...故较低"
      .replace(/不能完全排除.{3,30}?，?但.{3,15}?更指向。?$/, "") // 移除"不能完全排除"
      .trim();
  };

  const formattedReason = formatReason(reason);
  const shouldTruncate = formattedReason.length > 60;
  const displayReason = shouldTruncate && !isExpanded
    ? formattedReason.substring(0, 60) + "..."
    : formattedReason;

  return (
    <div className="text-xs text-stone-600 mt-1.5">
      <div className="bg-stone-50 rounded-lg p-2">
        <div className="flex items-start gap-1">
          <span className="flex-shrink-0 mt-0.5">🔍</span>
          <span className="flex-1 leading-relaxed">
            <span>{displayReason}</span>
            {shouldTruncate && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="ml-2 text-blue-600 hover:text-blue-700 font-medium underline decoration-blue-600 underline-offset-2 whitespace-nowrap"
              >
                {isExpanded ? "收起" : "展开"}
              </button>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * 处理建议项组件（支持展开/收起）
 */
interface SuggestionItemProps {
  icon: string;
  title: string;
  content: string;
}

function SuggestionItem({ icon, title, content }: SuggestionItemProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // 拆分内容为多个要点
  const parseContent = (text: string) => {
    // 按编号或句号拆分
    const items = text.split(/(?=\d+[\.\、)]|(?<=。))/).filter(s => s.trim());
    return items;
  };

  const items = parseContent(content);
  const shouldTruncate = !isExpanded && items.length > 2;
  const displayItems = shouldTruncate ? items.slice(0, 2) : items;

  return (
    <div className="flex items-start gap-2 text-sm text-stone-700 bg-white/50 p-2.5 rounded-lg">
      <span className="mt-0.5">{icon}</span>
      <div className="flex-1">
        <div className="font-semibold text-stone-900 text-xs mb-1">{title}</div>
        <div className="text-xs text-stone-600 space-y-1">
          {displayItems.map((item, idx) => (
            <div key={idx} className="flex items-start gap-1">
              <span className="flex-shrink-0 text-stone-400">•</span>
              <span className="leading-relaxed">{item.trim()}</span>
            </div>
          ))}
        </div>
        {items.length > 2 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium underline"
          >
            {isExpanded ? "收起" : `查看全部 ${items.length} 项`}
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 紧急程度仪表盘组件
 */
function UrgencyGauge({ urgency }: { urgency: DiseasePredictionCardData["urgency"] }) {
  const getUrgencyConfig = (u: DiseasePredictionCardData["urgency"]) => {
    switch (u) {
      case "high": return { color: "#ef4444", label: "紧急", percent: 90 };
      case "medium": return { color: "#f59e0b", label: "中等", percent: 60 };
      case "low": return { color: "#3b82f6", label: "一般", percent: 30 };
      default: return { color: "#9ca3af", label: "未知", percent: 0 };
    }
  };

  const { color, label, percent } = getUrgencyConfig(urgency);

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-24 h-24">
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
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold" style={{ color }}>{label}</span>
          <span className="text-xs text-stone-500">{percent}%</span>
        </div>
      </div>
      <div className="flex-1 text-xs text-stone-500 space-y-1">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          <span>高风险</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-500" />
          <span>中风险</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span>低风险</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 疾病概率条形图组件
 */
function DiseaseProbabilityChart({ diseases }: { diseases: DiseasePrediction[] }) {
  const colors = ["#ef4444", "#f59e0b", "#eab308", "#84cc16", "#06b6d4"];

  return (
    <div className="space-y-3">
      {diseases.map((disease, idx) => (
        <div key={idx} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-stone-800 flex-1">{disease.name}</span>
            <span className="font-bold text-stone-900">{disease.probability}%</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out relative"
              style={{
                width: `${disease.probability}%`,
                backgroundColor: colors[idx % colors.length],
              }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>
          {disease.reason && <DiseaseReasonDisplay reason={disease.reason} />}
        </div>
      ))}
    </div>
  );
}

/**
 * 前三名疾病柱状图组件
 */
function TopDiseasesBarChart({ diseases }: { diseases: DiseasePrediction[] }) {
  // 取前三名疾病
  const topDiseases = diseases
    .sort((a, b) => b.probability - a.probability)
    .slice(0, 3);

  if (topDiseases.length === 0) return null;

  const maxProbability = Math.max(...topDiseases.map(d => d.probability), 100);
  const colors = ["#ef4444", "#f59e0b", "#eab308"]; // 红、橙、黄

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-center gap-6 h-36 px-4">
        {topDiseases.map((disease, idx) => {
          const heightPercent = (disease.probability / maxProbability) * 100;
          const barHeight = Math.max(heightPercent * 0.8, 15); // 0.8是缩放因子，确保柱子不会太高，最小15px

          return (
            <div key={idx} className="flex flex-col items-center gap-2 flex-1 max-w-[90px]">
              {/* 概率数值 */}
              <span className="text-sm font-bold text-stone-900">{disease.probability}%</span>

              {/* 柱状图容器 */}
              <div className="relative w-16 bg-stone-100 rounded-t-lg overflow-hidden" style={{ height: '100px' }}>
                {/* 柱子 */}
                <div
                  className="absolute bottom-0 left-0 right-0 rounded-t-lg transition-all duration-700 ease-out relative overflow-hidden"
                  style={{
                    height: `${barHeight}px`,
                    backgroundColor: colors[idx],
                  }}
                >
                  {/* 渐变效果 */}
                  <div
                    className="absolute inset-0 opacity-20"
                    style={{
                      background: `linear-gradient(to top, ${colors[idx]}, transparent)`,
                    }}
                  />
                  {/* 光泽效果 */}
                  <div className="absolute top-0 left-0 right-0 h-1 bg-white/30" />
                  {/* 概率标签（柱子内部） */}
                  <div className="absolute top-2 left-0 right-0 text-center">
                    <span className="text-xs font-bold text-white/90 drop-shadow">{disease.probability}%</span>
                  </div>
                </div>
              </div>

              {/* 底部标签 */}
              <div className="text-center w-16">
                <div className="text-xs font-semibold text-stone-800 line-clamp-2 leading-tight">
                  {disease.name}
                </div>
                <div className="text-[10px] text-stone-500 mt-0.5">#{idx + 1}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * 疾病预测专用卡片组件
 */
export const DiseasePredictionCard: React.FC<DiseasePredictionCardProps> = ({
  data,
}) => {
  const getUrgencyConfig = (urgency: DiseasePredictionCardData["urgency"]) => {
    switch (urgency) {
      case "high":
        return {
          icon: AlertTriangle,
          label: "紧急",
          labelEn: "HIGH",
          color: "text-red-600",
          bg: "bg-red-50",
          border: "border-red-200",
          iconBg: "bg-red-100",
        };
      case "medium":
        return {
          icon: AlertTriangle,
          label: "中等",
          labelEn: "MEDIUM",
          color: "text-amber-600",
          bg: "bg-amber-50",
          border: "border-amber-200",
          iconBg: "bg-amber-100",
        };
      case "low":
        return {
          icon: Activity,
          label: "一般",
          labelEn: "LOW",
          color: "text-blue-600",
          bg: "bg-blue-50",
          border: "border-blue-200",
          iconBg: "bg-blue-100",
        };
      default:
        return {
          icon: Activity,
          label: "未知",
          labelEn: "UNKNOWN",
          color: "text-gray-600",
          bg: "bg-gray-50",
          border: "border-gray-200",
          iconBg: "bg-gray-100",
        };
    }
  };

  const urgencyConfig = getUrgencyConfig(data.urgency);

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      "overflow-hidden",
      urgencyConfig.bg,
      urgencyConfig.border
    )}>
      {/* 头部：标题 + 紧急程度 */}
      <div className={cn(
        "flex items-center justify-between",
        "px-4 py-3 sm:px-5 sm:py-3.5",
        "border-b",
        urgencyConfig.border
      )}>
        <div className="flex items-center gap-2">
          <Stethoscope className={cn("w-5 h-5", urgencyConfig.color)} />
          <h3 className="font-bold text-base text-stone-900">
            疾病预测分析
          </h3>
        </div>
        <div className={cn(
          "flex items-center gap-1.5 sm:gap-2",
          "px-2.5 py-1 rounded-full",
          "text-xs sm:text-sm font-medium",
          urgencyConfig.iconBg,
          urgencyConfig.color
        )}>
          <TrendingUp className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span>{urgencyConfig.labelEn}</span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-4 sm:p-5 space-y-4">
        {/* 紧急程度仪表盘 */}
        <div className="bg-white/60 rounded-xl p-4 shadow-sm">
          <UrgencyGauge urgency={data.urgency} />
        </div>

        {/* 前三名疾病柱状图 */}
        {data.diseases.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3">📊 前三名疾病预测</div>
            <TopDiseasesBarChart diseases={data.diseases} />
          </div>
        )}

        {/* 疾病概率图表 */}
        {data.diseases.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3">📋 详细概率分析</div>
            <DiseaseProbabilityChart diseases={data.diseases} />
          </div>
        )}

        {/* 关键症状标签云 */}
        {data.symptoms.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-stone-600 uppercase tracking-wide flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              关键症状
            </div>
            <div className="flex flex-wrap gap-2">
              {data.symptoms.map((symptom, idx) => (
                <span
                  key={idx}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-xs font-medium shadow-sm",
                    "bg-white border",
                    urgencyConfig.border,
                    urgencyConfig.color,
                    "hover:scale-105 transition-transform"
                  )}
                >
                  {symptom}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 处理建议 */}
        {(data.suggestions.isolation || data.suggestions.treatment || data.suggestions.prevention) && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-stone-600 uppercase tracking-wide flex items-center gap-1.5">
              <Syringe className="w-3.5 h-3.5" />
              处理建议
            </div>
            <div className="space-y-2">
              {data.suggestions.isolation && (
                <SuggestionItem
                  icon="🏠"
                  title="隔离观察"
                  content={data.suggestions.isolation}
                />
              )}
              {data.suggestions.treatment && (
                <SuggestionItem
                  icon="💊"
                  title="对症治疗"
                  content={data.suggestions.treatment}
                />
              )}
              {data.suggestions.prevention && (
                <SuggestionItem
                  icon="🛡️"
                  title="预防措施"
                  content={data.suggestions.prevention}
                />
              )}
            </div>
          </div>
        )}

        {/* 重要提醒 */}
        {data.reminder && (
          <div className={cn(
            "mt-4 p-3 rounded-lg",
            "bg-amber-50 border border-amber-200",
            "text-xs text-amber-800"
          )}>
            <div className="flex items-start gap-2">
              <span className="text-base">⚠️</span>
              <div>
                <div className="font-semibold mb-1">重要提醒</div>
                <div>{data.reminder}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
