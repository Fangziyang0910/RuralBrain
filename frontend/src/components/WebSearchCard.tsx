"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink, Sparkles, Newspaper, FileText } from "lucide-react";
import { cn } from "@/utils/cn";
import { WebSearchData } from "@/types/tool";

interface WebSearchCardProps {
  data: WebSearchData;
}

export const WebSearchCard: React.FC<WebSearchCardProps> = ({ data }) => {
  const [expanded, setExpanded] = useState(false);
  const [showAllResults, setShowAllResults] = useState(false);

  const { ai_summary, results, stats } = data;
  const displayResults = showAllResults ? results : results.slice(0, 3);
  const hasMoreResults = results.length > 3;

  return (
    <div className={cn(
      "rounded-xl border-2 transition-all duration-200",
      "p-3 sm:p-4",
      "bg-gradient-to-br from-purple-50 to-white",
      "border-purple-300",
      "hover:shadow-md"
    )}>
      {/* Header */}
      <div
        className={cn(
          "flex items-center justify-between cursor-pointer group",
          "gap-2 sm:gap-3"
        )}
        onClick={() => setExpanded(!expanded)}
      >
        <div className={cn(
          "flex items-center gap-2 sm:gap-3",
          "flex-1 min-w-0"
        )}>
          {/* Icon */}
          <span className="text-xl sm:text-2xl flex-shrink-0" role="img" aria-label="联网搜索">
            🌐
          </span>
          {/* Title */}
          <span className={cn(
            "font-semibold truncate",
            "text-sm sm:text-base",
            "text-purple-700"
          )}>
            联网搜索
          </span>
          {/* Status */}
          <div className={cn(
            "flex items-center gap-1 sm:gap-1.5",
            "flex-shrink-0"
          )}>
            <span className={cn(
              "rounded-full font-medium",
              "text-[10px] sm:text-xs",
              "px-1.5 sm:px-2 py-0.5",
              "bg-green-100 text-green-700"
            )}>
              ✓ 已完成
            </span>
            <span className={cn(
              "text-[10px] sm:text-xs",
              "text-purple-500"
            )}>
              找到 {stats.total} 条结果
            </span>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className={cn(
            "transition-colors opacity-60 group-hover:opacity-100",
            "text-purple-700",
            "w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0"
          )} />
        ) : (
          <ChevronDown className={cn(
            "transition-colors opacity-60 group-hover:opacity-100",
            "text-purple-700",
            "w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0"
          )} />
        )}
      </div>

      {/* AI Summary */}
      {ai_summary && (
        <div className={cn(
          "mt-3 sm:mt-4",
          "bg-white rounded-lg p-2.5 sm:p-3",
          "border border-purple-200"
        )}>
          <div className={cn(
            "flex items-center gap-1.5 sm:gap-2 mb-1.5 sm:mb-2"
          )}>
            <Sparkles className={cn(
              "text-purple-500",
              "w-3.5 h-3.5 sm:w-4 sm:h-4"
            )} />
            <span className={cn(
              "font-semibold text-purple-700",
              "text-xs sm:text-sm"
            )}>
              AI 摘要
            </span>
          </div>
          <p className={cn(
            "text-stone-700 leading-relaxed",
            "text-xs sm:text-sm"
          )}>
            {ai_summary}
          </p>
        </div>
      )}

      {/* Stats Tags */}
      <div className={cn(
        "mt-2.5 sm:mt-3",
        "flex gap-2 sm:gap-3"
      )}>
        {stats.news > 0 && (
          <span className={cn(
            "rounded-full font-medium",
            "text-[10px] sm:text-xs",
            "px-2 sm:px-2.5 py-1 sm:py-1.5",
            "bg-yellow-100 text-yellow-700",
            "flex items-center gap-1"
          )}>
            <Newspaper className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
            新闻 {stats.news}
          </span>
        )}
        {stats.web > 0 && (
          <span className={cn(
            "rounded-full font-medium",
            "text-[10px] sm:text-xs",
            "px-2 sm:px-2.5 py-1 sm:py-1.5",
            "bg-blue-100 text-blue-700",
            "flex items-center gap-1"
          )}>
            <FileText className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
            网页 {stats.web}
          </span>
        )}
      </div>

      {/* Expand Button (when collapsed) */}
      {!expanded && (
        <div
          className={cn(
            "mt-3 sm:mt-4",
            "text-center",
            "text-purple-600",
            "text-xs sm:text-sm",
            "cursor-pointer hover:text-purple-800 transition-colors"
          )}
          onClick={() => setExpanded(true)}
        >
          ▼ 点击展开查看详细结果
        </div>
      )}

      {/* Results List (when expanded) */}
      {expanded && (
        <div className={cn(
          "border-t border-purple-200",
          "mt-3 sm:mt-4 pt-3 sm:pt-4",
          "space-y-2 sm:space-y-3",
          "animate-fade-in"
        )}>
          {displayResults.map((result, idx) => (
            <div
              key={idx}
              className={cn(
                "bg-white rounded-lg p-2.5 sm:p-3",
                "border border-purple-100",
                "hover:border-purple-300 transition-colors"
              )}
            >
              <div className={cn(
                "flex items-start gap-2 sm:gap-3"
              )}>
                {/* Type Badge */}
                <span className={cn(
                  "rounded font-medium",
                  "text-[10px] sm:text-xs",
                  "px-1.5 sm:px-2 py-0.5",
                  "flex-shrink-0",
                  result.type === "news"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-blue-100 text-blue-700"
                )}>
                  {result.type === "news" ? "新闻" : "网页"}
                </span>
                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Title with Link */}
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      "text-purple-700 hover:text-purple-900",
                      "font-semibold",
                      "text-xs sm:text-sm",
                      "flex items-center gap-1",
                      "transition-colors"
                    )}
                  >
                    <span className="truncate">{result.title}</span>
                    <ExternalLink className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0 opacity-60" />
                  </a>
                  {/* Snippet */}
                  <p className={cn(
                    "mt-1 sm:mt-1.5",
                    "text-stone-600 leading-relaxed",
                    "text-xs sm:text-sm"
                  )}>
                    {result.snippet}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {/* View All Button */}
          {hasMoreResults && !showAllResults && (
            <div
              className={cn(
                "text-center",
                "text-purple-600",
                "text-xs sm:text-sm",
                "cursor-pointer hover:text-purple-800 transition-colors",
                "mt-2 sm:mt-3"
              )}
              onClick={() => setShowAllResults(true)}
            >
              查看全部 {results.length} 条结果
            </div>
          )}
        </div>
      )}
    </div>
  );
};