"use client";

import React, { useState } from "react";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "@/utils/cn";

interface ToolCall {
  name: string;
  status: "运行中" | "已完成";
  resultImage?: string;
  summary?: string[];
}

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  image?: string;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
};

interface ChatMessageBubbleProps {
  message: Message;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
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
        {/* 工具调用展示 */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="w-full">
            {message.toolCalls.map((toolCall, idx) => (
              <ToolCallDisplay key={idx} toolCall={toolCall} />
            ))}
          </div>
        )}

        {/* 文字消息 */}
        <div
          className={cn(
            "px-4 py-2.5 rounded-2xl",
            isUser
              ? "bg-green-600 text-white"
              : "bg-green-50 text-gray-800 border border-green-100"
          )}
        >
          {isUser ? (
            <p className="text-xl leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="text-xl leading-relaxed">
              {!message.content && message.isStreaming ? (
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                  <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                  <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                </div>
              ) : message.isStreaming ? (
                // 流式输出时显示纯文本，性能更好
                <div className="whitespace-pre-wrap">
                  {message.content}
                  <span className="inline-block w-1 h-4 ml-1 bg-green-400 animate-pulse" />
                </div>
              ) : (
                // 流式结束后渲染 Markdown
                <div className="prose prose-green max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="my-2 text-xl">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold text-green-800">{children}</strong>,
                      ul: ({ children }) => <ul className="list-none space-y-1 my-2 text-xl">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2 text-xl">{children}</ol>,
                      li: ({ children }) => <li className="my-1">{children}</li>,
                      h1: ({ children }) => <h1 className="text-2xl font-bold my-2">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-xl font-bold my-2">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-lg font-bold my-2">{children}</h3>,
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
        {isUser && message.image && (
          <div className="mt-1">
            <img
              src={message.image}
              alt="上传的图片"
              className="rounded-lg border border-gray-200 w-auto h-auto max-w-xs"
            />
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
