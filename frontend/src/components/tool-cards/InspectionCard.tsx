"use client";

import React from "react";
import { ClipboardCheck, Camera, Scan, Wrench, FileText, CheckCircle2 } from "lucide-react";
import { cn } from "@/utils/cn";
import { InspectionData } from "@/types/tool";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface InspectionCardProps {
  data: InspectionData;
  toolName?: string;
}

/**
 * 场景置信度指示器组件
 */
function SceneConfidenceIndicator({ scene_name, confidence }: { scene_name: string; confidence: number }) {
  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) {
      return { color: "#22c55e", label: "高", bg: "bg-green-50", border: "border-green-200", text: "text-green-600" };
    }
    if (conf >= 0.5) {
      return { color: "#f59e0b", label: "中", bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-600" };
    }
    return { color: "#ef4444", label: "低", bg: "bg-red-50", border: "border-red-200", text: "text-red-600" };
  };

  const conf = getConfidenceColor(confidence);

  return (
    <div className={cn(
      "flex items-center gap-2 px-3 py-2 rounded-lg",
      conf.bg,
      conf.border
    )}>
      <div className="flex items-center gap-2 flex-1">
        <span className="font-medium text-stone-800">{scene_name}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="text-xs text-stone-500">置信度</div>
        <span className="text-sm font-bold" style={{ color: conf.color }}>
          {(confidence * 100).toFixed(0)}%
        </span>
        <span className={cn(
          "text-xs px-1.5 py-0.5 rounded font-medium",
          conf.bg,
          conf.text
        )}>
          {conf.label}
        </span>
      </div>
    </div>
  );
}

/**
 * 巡检报告专用卡片组件
 */
export const InspectionCard: React.FC<InspectionCardProps> = ({
  data,
}) => {
  const isSmartInspection = data.inspection_type.includes("智能");
  const multimodalReport = data.multimodal_analysis?.report;
  const hasMultimodalReport = !!multimodalReport;

  // 获取巡检类型颜色配置
  const getInspectionTypeConfig = () => {
    if (isSmartInspection) {
      return {
        icon: Camera,
        label: "智能巡检",
        color: "text-indigo-600",
        bg: "bg-indigo-50",
        border: "border-indigo-200",
        iconBg: "bg-indigo-100",
      };
    }
    return {
      icon: ClipboardCheck,
      label: "传感器巡检",
      color: "text-teal-600",
      bg: "bg-teal-50",
      border: "border-teal-200",
      iconBg: "bg-teal-100",
    };
  };

  const typeConfig = getInspectionTypeConfig();

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      "overflow-hidden",
      typeConfig.bg,
      typeConfig.border
    )}>
      {/* 头部：标题 + 巡检类型 */}
      <div className={cn(
        "flex items-center justify-between",
        "px-4 py-3 sm:px-5 sm:py-3.5",
        "border-b",
        typeConfig.border
      )}>
        <div className="flex items-center gap-2">
          <typeConfig.icon className={cn("w-5 h-5", typeConfig.color)} />
          <h3 className="font-bold text-base text-stone-900">
            农场巡检报告
          </h3>
        </div>
        <div className={cn(
          "flex items-center gap-1.5 sm:gap-2",
          "px-2.5 py-1 rounded-full",
          "text-xs sm:text-sm font-medium",
          typeConfig.iconBg,
          typeConfig.color
        )}>
          <Scan className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span>{typeConfig.label}</span>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-4 sm:p-5 space-y-4">
        {/* 巡检基本信息 */}
        <div className="bg-white/60 rounded-xl p-4 shadow-sm">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-stone-500 mb-1">农场 ID</div>
              <div className="font-semibold text-stone-900">{data.farm_id}</div>
            </div>
            <div>
              <div className="text-xs text-stone-500 mb-1">巡检时间</div>
              <div className="font-semibold text-stone-900 text-xs">
                {data.inspection_time}
              </div>
            </div>
            {data.media_type_name && (
              <>
                <div>
                  <div className="text-xs text-stone-500 mb-1">拍摄方式</div>
                  <div className="font-semibold text-stone-900">{data.media_type_name}</div>
                </div>
                {data.image_count !== undefined && (
                  <div>
                    <div className="text-xs text-stone-500 mb-1">图片数量</div>
                    <div className="font-semibold text-stone-900">{data.image_count} 张</div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* 智能巡检：场景分类结果 */}
        {isSmartInspection && data.scene_classification && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3 flex items-center gap-1.5">
              <Scan className="w-3.5 h-3.5" />
              场景识别结果
            </div>
            <div className="space-y-2">
              <SceneConfidenceIndicator
                scene_name={data.scene_classification.primary_scene}
                confidence={
                  data.scene_classification.all_scenes[0]?.confidence || 0
                }
              />
              {data.scene_classification.all_scenes.length > 1 && (
                <div className="text-xs text-stone-500 mt-2">
                  共识别 {data.scene_classification.all_scenes.length} 个场景
                </div>
              )}
            </div>
          </div>
        )}

        {/* 智能巡检：推荐工具 */}
        {isSmartInspection && data.recommended_tools && data.recommended_tools.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3 flex items-center gap-1.5">
              <Wrench className="w-3.5 h-3.5" />
              建议调用的检测工具
            </div>
            <div className="space-y-2">
              {data.recommended_tools.map((tool, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <div className="mt-0.5 w-1.5 h-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-stone-900">{tool.tool}</div>
                    <div className="text-xs text-stone-600 mt-0.5">{tool.reason}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 多模态综合分析报告 */}
        {hasMultimodalReport && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" />
              AI 综合分析报告
            </div>
            <div className="max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p className="my-2 text-sm text-stone-700 leading-relaxed">{children}</p>,
                  strong: ({ children }) => <strong className="font-bold text-stone-900">{children}</strong>,
                  em: ({ children }) => <em className="italic text-stone-700">{children}</em>,
                  ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2 text-sm text-stone-800 pl-3">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 text-sm text-stone-800 pl-3">{children}</ol>,
                  li: ({ children }) => <li className="my-1 text-stone-700 leading-snug">{children}</li>,
                  h1: ({ children }) => <h1 className="text-base font-bold my-2 text-stone-900">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-sm font-bold my-2 text-stone-900">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold my-2 text-stone-900">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-xs font-bold my-1.5 text-stone-900">{children}</h4>,
                  hr: () => <hr className="my-3 border-t border-stone-300" />,
                  a: ({ children, href }) => (
                    <a
                      href={href}
                      className="text-earth-600 hover:text-earth-700 underline underline-offset-2 transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {multimodalReport}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* 建议行动（没有多模态报告时） */}
        {!hasMultimodalReport && data.suggested_actions && data.suggested_actions.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              建议后续行动
            </div>
            <div className="space-y-2">
              {data.suggested_actions.map((action, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-stone-700">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 传感器巡检：传感器数据概览 */}
        {!isSmartInspection && data.sensor_data && (
          <div className="bg-white/60 rounded-xl p-4 shadow-sm">
            <div className="text-xs font-semibold text-stone-600 mb-3 flex items-center gap-1.5">
              <ClipboardCheck className="w-3.5 h-3.5" />
              传感器数据概览
            </div>
            <div className="space-y-2 text-sm text-stone-700">
              {Object.keys(data.sensor_data).map((key) => {
                const sensorData = data.sensor_data!;
                const value = sensorData[key];
                return (
                  <div key={key} className="flex justify-between items-center py-1 border-b border-stone-100 last:border-0">
                    <span className="capitalize">{key}</span>
                    <span className="text-stone-500">
                      {Array.isArray(value)
                        ? `${value.length} 项`
                        : "查看详情"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
