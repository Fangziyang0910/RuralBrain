// 客户端组件：聊天消息气泡，支持用户和助手消息展示，包含文本、图片及工具调用结果的渲染。
"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronUp, ChevronDown, FileText, BookOpen, CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "@/utils/cn";
import { LoadingDots } from "./ui/LoadingDots";
import { MessageImageGallery } from "./ui/MessageImageGallery";
import { ToolResultImage } from "./ui/ToolResultImage";
import { getToolConfig, getToolColorClass } from "@/config/tool-icons";
import { WebSearchData, DetectionData, DiseasePredictionData, InspectionData, EnhancedDetectionData } from "@/types/tool";
import { WebSearchCard } from "./WebSearchCard";
import { DetectionCard } from "./tool-cards/DetectionCard";
import { DiseasePredictionCard } from "./tool-cards/DiseasePredictionCard";
import { InspectionCard } from "./tool-cards/InspectionCard";

export interface ToolCall {
  name: string;
  status: "运行中" | "已完成";
  resultImage?: string;
  summary?: string[];
  resultData?: WebSearchData | DetectionData | DiseasePredictionData | InspectionData | EnhancedDetectionData;
}

interface KnowledgeSource {
  source: string;
  page?: number;
  content: string;
}

// export 表示该类型可在其他文件中导入使用
export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  image?: string;  // 兼容旧版本：单图片
  images?: string[];  // 新版本：多图片
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  sources?: KnowledgeSource[];  // 知识库引用
};

interface ChatMessageBubbleProps {
  message: Message;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  // 解构参数获取消息内容
  message,
}) => {
  const isUser = message.role === "user";

  // 调试：查看消息更新
  if (!isUser && message.isStreaming) {
    console.log("渲染流式消息，长度:", message.content.length, "内容预览:", message.content.slice(0, 50));
  }

  return (
    <div className={`flex gap-3 mb-8 animate-fade-in ${isUser ? "justify-end" : "justify-start"}`}>
      {/* 头像 - Organic Biophilic 设计 */}
      {!isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-organic-xl bg-gradient-to-br from-earth-500 to-earth-700 flex items-center justify-center text-white shadow-organic">
          <span className="text-base">🌱</span>
        </div>
      )}

      {/* 消息内容 */}
      <div className={`flex flex-col gap-2.5 ${isUser ? "items-end" : "items-start"}`}>
        {/* 知识库引用展示 */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full animate-slide-up">
            <KnowledgeSourceDisplay sources={message.sources} />
          </div>
        )}

        {/* 工具调用展示 */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="w-full space-y-2">
            {message.toolCalls.map((toolCall, idx) => (
              <div key={idx} className="animate-slide-up" style={{ animationDelay: `${idx * 0.1}s` }}>
                {/* 原始工具调用卡片 */}
                <ToolCallDisplay toolCall={toolCall} />

                {/* 结构化数据专用卡片 */}
                {toolCall.name === "disease_prediction_tool" && toolCall.resultData && (
                  <div className="mt-2 tool-call-animate-in" style={{ animationDelay: `${idx * 100 + 200}ms` }}>
                    <DiseasePredictionCard data={toolCall.resultData as DiseasePredictionData} />
                  </div>
                )}
                {(toolCall.name === "pest_detection_tool" ||
                  toolCall.name === "rice_detection_tool" ||
                  toolCall.name === "cow_detection_tool") && toolCall.resultData && (
                  <div className="mt-2 tool-call-animate-in" style={{ animationDelay: `${idx * 100 + 200}ms` }}>
                    <DetectionCard
                      data={toolCall.resultData as DetectionData}
                      toolName={getToolConfig(toolCall.name).label}
                    />
                  </div>
                )}
                {toolCall.name === "web_search_tool" && toolCall.resultData && (
                  <div className="mt-2 tool-call-animate-in" style={{ animationDelay: `${idx * 100 + 200}ms` }}>
                    <WebSearchCard data={toolCall.resultData as WebSearchData} />
                  </div>
                )}
                {toolCall.name === "farm_inspection_tool" && toolCall.resultData && (
                  <div className="mt-2 tool-call-animate-in" style={{ animationDelay: `${idx * 100 + 200}ms` }}>
                    <InspectionCard data={toolCall.resultData as InspectionData} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 文字消息 - Organic Biophilic 设计 */}
        <div
          className={cn(
            "message-bubble",
            isUser
              ? "message-user-enhanced"
              : "message-ai-enhanced"
          )}
        >
          {isUser ? (
            <p className="text-base leading-relaxed font-medium">
              {message.content}
            </p>
          ) : (
            <div className="text-base leading-relaxed">
              {!message.content && message.isStreaming ? (
                <LoadingDots size="md" color="#22C55E" />
              ) : (
                <div className="prose prose-stone max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-headings:my-3">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="my-2 text-base text-earth-800">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold text-earth-900">{children}</strong>,
                      ul: ({ children }) => <ul className="list-none space-y-1.5 my-2 text-base">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1.5 my-2 text-base">{children}</ol>,
                      li: ({ children }) => <li className="my-1 text-earth-700">{children}</li>,
                      h1: ({ children }) => <h1 className="text-xl font-bold my-3 text-earth-900">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold my-2.5 text-earth-900">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-bold my-2 text-earth-900">{children}</h3>,
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
                    {message.content}
                  </ReactMarkdown>
                  {message.isStreaming && (
                    <span className="inline-block w-0.5 h-4 ml-1 bg-earth-500 animate-pulse rounded-full align-middle" />
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 用户上传的图片 */}
        {isUser && (message.images || message.image) && (
          <div className="mt-1.5 max-w-[120px] xs:max-w-[140px] sm:max-w-[180px] md:max-w-[320px]">
            {message.images && message.images.length > 0 ? (
              <MessageImageGallery images={message.images} alt={message.content} />
            ) : (
              <div className="relative group inline-block max-w-[120px] xs:max-w-[140px] sm:max-w-[180px] md:max-w-[320px]">
                <div className="absolute -inset-1 bg-gradient-to-br from-harvest-400/30 via-earth-500/20 to-harvest-600/30 rounded-organic-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl" />
                <img
                  src={message.image}
                  alt="上传的图片"
                  className="relative w-full h-auto max-h-[120px] xs:max-h-[140px] sm:max-h-[180px] md:max-h-[280px] object-contain rounded-organic-2xl shadow-organic-lg group-hover:shadow-organic-md transition-all duration-500 group-hover:scale-[1.02]"
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* 用户头像 - 丰收金 */}
      {isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-organic-xl bg-gradient-to-br from-harvest-500 to-harvest-700 flex items-center justify-center text-white shadow-organic">
          <span className="text-base">👨‍🌾</span>
        </div>
      )}
    </div>
  );
};

function KnowledgeSourceDisplay({ sources }: { sources: KnowledgeSource[] }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedSource, setSelectedSource] = useState<number | null>(null);

  return (
    <div className={cn(
      "rounded-xl border bg-sky-50 transition-all duration-200 hover:shadow-sm",
      "border-sky-200 p-3 sm:p-3.5" // 响应式内边距
    )}>
      <div
        className={cn(
          "flex items-center justify-between cursor-pointer group",
          "gap-2 sm:gap-2.5" // 响应式间距
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={cn(
          "flex items-center gap-2 sm:gap-2.5", // 响应式间距
          "flex-1 min-w-0" // 允许内容换行
        )}>
          <div className={cn(
            "rounded-lg bg-sky-100 flex items-center justify-center",
            "w-7 h-7 sm:w-8 sm:h-8" // 响应式图标容器大小
          )}>
            <BookOpen className={cn(
              "text-sky-600",
              "w-4 h-4 sm:w-4.5 sm:h-4.5" // 响应式图标大小
            )} />
          </div>
          <span className={cn(
            "font-semibold text-sky-900",
            "text-xs sm:text-sm" // 响应式字体
          )}>
            知识库引用
          </span>
          <span className={cn(
            "rounded-full font-semibold",
            "bg-sky-200 text-sky-800",
            "text-[10px] sm:text-xs", // 响应式字体
            "px-1.5 sm:px-2 py-0.5" // 响应式内边距
          )}>
            {sources.length} 条来源
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className={cn(
            "text-sky-600 group-hover:text-sky-800 transition-colors",
            "w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" // 响应式图标大小
          )} />
        ) : (
          <ChevronDown className={cn(
            "text-sky-600 group-hover:text-sky-800 transition-colors",
            "w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" // 响应式图标大小
          )} />
        )}
      </div>

      {isExpanded && (
        <div className={cn(
          "border-t border-sky-200 space-y-2 sm:space-y-3 animate-fade-in",
          "mt-3 sm:mt-4 pt-3 sm:pt-4" // 响应式间距
        )}>
          {sources.map((source, idx) => (
            <div
              key={idx}
              className={cn(
                "rounded-lg border p-2.5 sm:p-3 transition-all cursor-pointer", // 响应式内边距
                selectedSource === idx
                  ? "border-sky-400 bg-sky-100"
                  : "border-sky-100 bg-white hover:border-sky-200"
              )}
              onClick={() => setSelectedSource(selectedSource === idx ? null : idx)}
            >
              <div className={cn(
                "flex items-start gap-2 sm:gap-3 mb-1.5 sm:mb-2" // 响应式间距
              )}>
                <FileText className={cn(
                  "text-sky-600 mt-0.5 flex-shrink-0",
                  "w-3.5 h-3.5 sm:w-4 sm:h-4" // 响应式图标大小
                )} />
                <div className="flex-1 min-w-0">
                  <div className={cn(
                    "font-semibold text-stone-900 mb-1",
                    "text-xs sm:text-sm" // 响应式字体
                  )}>
                    <span className="truncate block">{source.source}</span>
                    {source.page !== undefined && (
                      <span className={cn(
                        "text-sky-600 font-normal bg-sky-100 rounded",
                        "ml-0 sm:ml-2", // 移动端无左边距
                        "text-[10px] sm:text-xs", // 响应式字体
                        "px-1 sm:px-1.5 py-0.5", // 响应式内边距
                        "inline-block mt-1 sm:mt-0" // 移动端换行显示
                      )}>
                        第 {source.page} 页
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className={cn(
                "text-stone-600 leading-relaxed transition-all",
                "text-xs sm:text-sm", // 响应式字体
                selectedSource === idx ? "line-clamp-none" : "line-clamp-2"
              )}>
                {source.content}
              </div>
              {selectedSource === idx && (
                <div className={cn(
                  "text-sky-600 flex items-center gap-1",
                  "mt-1.5 sm:mt-2", // 响应式间距
                  "text-[10px] sm:text-xs" // 响应式字体
                )}>
                  <span>👆 点击收起</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}