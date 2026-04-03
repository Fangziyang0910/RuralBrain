// 客户端组件：聊天消息气泡，支持用户和助手消息展示，包含文本、图片及工具调用结果的渲染。
"use client";

import React, { useState } from "react";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronUp, ChevronDown, FileText, BookOpen } from "lucide-react";
import { cn } from "@/utils/cn";
import { LoadingDots } from "./ui/LoadingDots";
import { MessageImageGallery } from "./ui/MessageImageGallery";
import { ToolResultImage } from "./ui/ToolResultImage";

interface ToolCall {
  name: string;
  status: "运行中" | "已完成";
  resultImage?: string;
  summary?: string[];
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
      {/* 头像 */}
      {!isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-2xl bg-gradient-to-br from-paddy-500 to-paddy-600 flex items-center justify-center text-white shadow-md">
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
        {/* 条件渲染 */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="w-full space-y-2">
            {message.toolCalls.map((toolCall, idx) => (
              <div key={idx} className="animate-slide-up" style={{ animationDelay: `${idx * 0.1}s` }}>
                <ToolCallDisplay toolCall={toolCall} />
              </div>
            ))}
          </div>
        )}

        {/* 文字消息 - 应用新的设计系统 */}
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
                <LoadingDots size="md" color="#22c55e" />
              ) : (
                <div className="prose prose-stone max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-headings:my-3">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="my-2 text-base text-stone-700">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold text-stone-900">{children}</strong>,
                      ul: ({ children }) => <ul className="list-none space-y-1.5 my-2 text-base">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1.5 my-2 text-base">{children}</ol>,
                      li: ({ children }) => <li className="my-1 text-stone-700">{children}</li>,
                      h1: ({ children }) => <h1 className="text-xl font-bold my-3 text-stone-900">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold my-2.5 text-stone-900">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-bold my-2 text-stone-900">{children}</h3>,
                      a: ({ children, href }) => (
                        <a
                          href={href}
                          className="text-paddy-600 hover:text-paddy-700 underline underline-offset-2 transition-colors"
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
                    <span className="inline-block w-0.5 h-4 ml-1 bg-paddy-500 animate-pulse rounded-full align-middle" />
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 用户上传的图片 */}
        {isUser && (message.images || message.image) && (
          <div className="mt-1.5">
            {message.images && message.images.length > 0 ? (
              <MessageImageGallery images={message.images} alt={message.content} />
            ) : (
              <div className="relative group inline-block">
                <div className="absolute -inset-1 bg-gradient-to-br from-gold-400/30 via-paddy-500/20 to-gold-600/30 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 blur-xl" />
                <img
                  src={message.image}
                  alt="上传的图片"
                  className="relative w-auto h-auto max-w-xs rounded-3xl shadow-2xl shadow-gold-500/20 group-hover:shadow-paddy-500/30 transition-all duration-500 group-hover:scale-[1.02]"
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* 用户头像 */}
      {isUser && (
        <div className="flex-shrink-0 w-9 h-9 rounded-2xl bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center text-white shadow-md">
          <span className="text-base">👨‍🌾</span>
        </div>
      )}
    </div>
  );
};

function ToolCallDisplay({ toolCall }: { toolCall: ToolCall }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toolNameMap: Record<string, string> = {
    // 检测类工具
    pest_detection_tool: "🦗 病虫害识别",
    rice_detection_tool: "🌾 大米品种识别",
    cow_detection_tool: "🐄 牛只目标检测",
    plant_disease_detection_tool: "🍃 植物病害识别",

    // 商业咨询类工具
    pricing_tool: "💰 定价分析",
    marketing_tool: "📈 营销策略",

    // 巡检类工具
    farm_inspection_tool: "🔍 农场巡检",
    scene_classifier_tool: "📷 场景分类",
    disease_prediction_tool: "🏥 疾病预测",

    // RAG 知识库工具
    document_list_tool: "📋 文档列表",
    document_overview_tool: "📖 文档概览",
    knowledge_search_tool: "🔎 知识检索",
    key_points_search_tool: "📌 要点搜索",

    // 网络搜索工具
    web_search_tool: "🌐 网络搜索",
  };

  const displayName = toolNameMap[toolCall.name] || toolCall.name;

  return (
    <div className="tool-card-enhanced">
      <div
        className="flex items-center justify-between cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold text-stone-800">
            {displayName}
          </span>
          <span className={cn(
            "text-xs px-2.5 py-1 rounded-full font-semibold",
            toolCall.status === "已完成"
              ? "bg-paddy-100 text-paddy-700"
              : "bg-gold-100 text-gold-700"
          )}>
            {toolCall.status}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-stone-400 group-hover:text-stone-600 transition-colors" />
        ) : (
          <ChevronDown className="w-5 h-5 text-stone-400 group-hover:text-stone-600 transition-colors" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-stone-100 space-y-3 animate-fade-in">
          {/* 检测结果图片 */}
          {toolCall.resultImage && (
            <ToolResultImage
              src={toolCall.resultImage}
              alt="工具检测结果"
              toolName={displayName}
            />
          )}

          {/* 工具调用摘要 */}
          {toolCall.summary && toolCall.summary.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-stone-600 mb-2 uppercase tracking-wide">
                执行摘要
              </div>
              <ul className="space-y-1.5">
                {toolCall.summary.map((item, idx) => (
                  <li key={idx} className="text-sm text-stone-700 flex items-start gap-2">
                    <span className="text-paddy-500 mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function KnowledgeSourceDisplay({ sources }: { sources: KnowledgeSource[] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="knowledge-card-enhanced">
      <div
        className="flex items-center justify-between cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-sky-600" />
          <span className="text-sm font-semibold text-sky-900">
            参考知识库
          </span>
          <span className="bg-sky-200 text-sky-800 text-xs px-2 py-0.5 rounded-full font-semibold">
            {sources.length}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-sky-600 group-hover:text-sky-800 transition-colors" />
        ) : (
          <ChevronDown className="w-4 h-4 text-sky-600 group-hover:text-sky-800 transition-colors" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-sky-100 space-y-3 animate-fade-in">
          {sources.map((source, idx) => (
            <div key={idx} className="knowledge-item-enhanced">
              <div className="flex items-start gap-3 mb-2">
                <FileText className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-stone-900 mb-1">
                    {source.source}
                    {source.page !== undefined && (
                      <span className="text-stone-500 font-normal ml-2 text-xs">
                        第 {source.page} 页
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-sm text-stone-600 leading-relaxed line-clamp-3">
                {source.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
