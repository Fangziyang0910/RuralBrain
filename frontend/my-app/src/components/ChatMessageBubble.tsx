// 客户端组件：聊天消息气泡，支持用户和助手消息展示，包含文本、图片及工具调用结果的渲染。
"use client";

import React, { useState } from "react";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronUp, ChevronDown, FileText, BookOpen } from "lucide-react";
import { cn } from "@/utils/cn";
import { LoadingDots } from "./ui/LoadingDots";

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
    <div className={`flex gap-4 mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
      {/* 头像 */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-600 to-green-700 flex items-center justify-center text-white text-lg">
          🌱
        </div>
      )}

      {/* 消息内容 */}
      <div className={`flex flex-col gap-2 max-w-3xl ${isUser ? "items-end" : "items-start"}`}>
        {/* 知识库引用展示 */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <KnowledgeSourceDisplay sources={message.sources} />
          </div>
        )}

        {/* 工具调用展示 */}
        {/* 条件渲染 */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="w-full">
            {message.toolCalls.map((toolCall, idx) => (
              <ToolCallDisplay key={idx} toolCall={toolCall} />
            ))}
          </div>
        )}

        {/* 文字消息 - 应用新的设计系统 */}
        <div
          className={cn(
            "message-bubble shadow-sm",
            isUser
              ? "message-user"
              : "message-ai hover:shadow-md"
          )}
        >
          {isUser ? (
            <p className="text-lg leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="text-base leading-relaxed">
              {!message.content && message.isStreaming ? (
                <LoadingDots size="md" color="#10b981" />
              ) : message.isStreaming ? (
                // 流式输出时显示纯文本，性能更好
                <div className="whitespace-pre-wrap">
                  {message.content}
                  <span className="inline-block w-0.5 h-4 ml-1 bg-primary-500 animate-pulse rounded-full" />
                </div>
              ) : (
                // 流式结束后渲染 Markdown
                <div className="prose prose-primary max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-headings:my-3">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="my-2 text-base">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold text-primary-800">{children}</strong>,
                      ul: ({ children }) => <ul className="list-none space-y-1 my-2 text-base">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 text-base">{children}</ol>,
                      li: ({ children }) => <li className="my-1">{children}</li>,
                      h1: ({ children }) => <h1 className="text-xl font-bold my-3 text-primary-900">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold my-2 text-primary-900">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-bold my-2 text-primary-900">{children}</h3>,
                      a: ({ children, href }) => (
                        <a
                          href={href}
                          className="text-primary-600 hover:text-primary-700 underline transition-colors"
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
                </div>
              )}
            </div>
          )}
        </div>

        {/* 用户上传的图片 */}
        {isUser && (message.images || message.image) && (
          <div className="mt-1">
            {message.images && message.images.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-w-md">
                {message.images.map((img, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={img}
                      alt={`上传的图片 ${index + 1}`}
                      className="rounded-lg border border-gray-200 w-full h-32 object-cover hover:scale-105 transition-transform"
                    />
                    <div className="absolute top-1 right-1 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
                      {index + 1}/{message.images?.length ?? 0}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <img
                src={message.image}
                alt="上传的图片"
                className="rounded-lg border border-gray-200 w-auto h-auto max-w-xs"
              />
            )}
          </div>
        )}
      </div>

      {/* 用户头像 */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-600 to-green-700 flex items-center justify-center text-white text-lg">
          👨‍🌾
        </div>
      )}
    </div>
  );
};

function ToolCallDisplay({ toolCall }: { toolCall: ToolCall }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toolNameMap: Record<string, string> = {
    pest_detection_tool: "🦗 病虫害识别工具",
    rice_detection_tool: "🌾 大米识别工具",
    cow_detection_tool: "🐄 牛只识别工具",
  };

  const displayName = toolNameMap[toolCall.name] || toolCall.name;

  return (
    <div className="bg-white border border-green-200 rounded-lg p-3 mb-2">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg font-medium text-gray-700">
            {displayName}
          </span>
          <span className="text-sm bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
            {toolCall.status}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-green-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-green-600" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-green-100 space-y-3">
          {/* 检测结果图片 */}
          {toolCall.resultImage && (
            <div>
              <div className="text-sm text-gray-500 mb-2">检测结果图片：</div>
              <img
                src={toolCall.resultImage}
                alt="工具检测结果"
                className="rounded-lg border border-gray-200 w-auto h-auto max-w-md"
              />
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
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">
            参考知识库 ({sources.length} 条来源)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-blue-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-blue-600" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-blue-100 space-y-3">
          {sources.map((source, idx) => (
            <div key={idx} className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="flex items-start gap-2 mb-2">
                <FileText className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-800">
                    {source.source}
                    {source.page !== undefined && (
                      <span className="text-gray-500 font-normal ml-1">
                        (第 {source.page} 页)
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-sm text-gray-600 pl-6 line-clamp-3">
                {source.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
