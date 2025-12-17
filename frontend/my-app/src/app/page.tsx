"use client";

import React, { useState, useCallback, useRef, useEffect, FormEvent } from "react";
import { ChatMessageBubble, type Message } from "@/components/ChatMessageBubble";
import { Button } from "@/components/ui/button";
import { Upload, Send, X, Loader2 } from "lucide-react";

const API_BASE = "/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [threadId] = useState(() => `thread_${Date.now()}`);
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 流式输出时持续滚动，非流式时只在消息数量变化时滚动
  const prevMessageCountRef = useRef(messages.length);
  
  useEffect(() => {
    const hasStreamingMessage = messages.some(msg => msg.isStreaming);
    
    if (hasStreamingMessage) {
      // 流式输出中，持续滚动
      scrollToBottom();
    } else if (messages.length !== prevMessageCountRef.current) {
      // 消息数量变化时滚动
      scrollToBottom();
      prevMessageCountRef.current = messages.length;
    }
  }, [messages]);

  // 自动调整文本框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && !selectedImage) || loading) return;

    handleSendMessage(input.trim() || "请帮我识别这张图片", selectedImage || undefined);
    setInput("");
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleSendMessage = useCallback(
    async (message: string, image?: File) => {
      let imagePath: string | undefined;
      let imagePreviewUrl: string | undefined;
      let assistantMessageId: string | null = null;

      // 添加用户消息
      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: message,
        image: image ? URL.createObjectURL(image) : undefined,
      };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        // 1. 如果有图片，先上传
        if (image) {
          const formData = new FormData();
          formData.append("file", image);

          const uploadResponse = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData,
          });

          if (!uploadResponse.ok) {
            throw new Error("图片上传失败");
          }

          const uploadData = await uploadResponse.json();
          imagePath = uploadData.file_path;
          imagePreviewUrl = userMessage.image;
        }

        // 2. 发送聊天请求（SSE流式）
        const chatResponse = await fetch(`${API_BASE}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            image_path: imagePath,
            thread_id: threadId,
          }),
        });

        if (!chatResponse.ok) {
          throw new Error("请求失败");
        }

        // 3. 处理SSE流
        const reader = chatResponse.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("无法读取响应");
        }

        // 创建助手消息
        assistantMessageId = `assistant_${Date.now()}`;

        setMessages((prev) => [
          ...prev,
          {
            id: assistantMessageId as string,
            role: "assistant",
            content: "",
            isStreaming: true,
          },
        ]);

        let buffer = "";
        let streamCompleted = false;
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          
          // 保留最后一行（可能不完整）
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.trim() === "") continue;
            
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;
                
                const data = JSON.parse(jsonStr);

                if (data.type === "start") {
                  console.log("流式输出开始, thread_id:", data.thread_id);
                } else if (data.type === "content") {
                  // 直接使用函数式更新，避免闭包问题
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: msg.content + data.content, isStreaming: true }
                        : msg
                    )
                  );
                } else if (data.type === "tool_call") {
                  // 处理工具调用事件
                  const toolCall = {
                    name: data.tool_name,
                    status: data.status as "运行中" | "已完成",
                    resultImage: data.result_image,
                  };
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? {
                            ...msg,
                            toolCalls: [...(msg.toolCalls || []), toolCall],
                          }
                        : msg
                    )
                  );
                  console.log("工具调用:", data.tool_name, "结果图片:", data.result_image);
                } else if (data.type === "end") {
                  streamCompleted = true;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, isStreaming: false }
                        : msg
                    )
                  );
                  console.log("流式输出完成, 总内容长度:", data.full_content?.length || 0);
                } else if (data.type === "error") {
                  throw new Error(data.error);
                }
              } catch (e) {
                console.error("解析SSE数据失败:", line, e);
              }
            }
          }
        }

        // 确保流结束时标记为非流式状态
        if (!streamCompleted) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
        }
      } catch (error) {
        console.error("发送消息失败:", error);
        
        // 移除未完成的流式消息
        if (assistantMessageId) {
          setMessages((prev) => 
            prev.filter(msg => msg.id !== assistantMessageId)
          );
        }
        
        // 显示错误信息
        const errorMessage = error instanceof Error ? error.message : "未知错误";
        const isNetworkError = errorMessage.includes("fetch") || errorMessage.includes("network");
        
        setMessages((prev) => [
          ...prev,
          {
            id: `error_${Date.now()}`,
            role: "assistant",
            content: `❌ 抱歉，发生了错误:\n\n${errorMessage}\n\n${
              isNetworkError ? "💡 提示：请检查网络连接或后端服务是否正常运行。" : ""
            }`,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [threadId]
  );

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-green-50/30 to-white">
      {/* 顶部标题栏 */}
      <header className="border-b border-green-100 bg-white/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌾</span>
            <div>
              <h1 className="text-xl font-semibold text-green-800">
                AI农业智能检测助手
              </h1>
              <p className="text-sm text-green-600 mt-0.5">
                基于大模型的病虫害、水稻、牛只智能检测
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* 对话区域 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-green-400 pt-20">
              <div className="text-6xl mb-4">🌾</div>
              <p className="text-lg mb-2 text-green-600">欢迎使用 AI农业智能检测助手</p>
              <p className="text-sm text-green-500">上传图片并提问，开始智能对话</p>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message) => (
                <ChatMessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* 输入区域 */}
      <footer className="border-t border-green-100 bg-white/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* 图片预览 */}
            {imagePreview && (
              <div className="relative inline-block">
                <img
                  src={imagePreview}
                  alt="预览"
                  className="h-20 w-20 object-cover rounded-lg border border-gray-200"
                />
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* 输入框和按钮 */}
            <div className="flex items-end gap-2">
              {/* 上传按钮 */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="flex-none border-green-300 text-green-700 hover:bg-green-50"
              >
                <Upload className="w-5 h-5" />
              </Button>

              {/* 文本输入框 */}
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息... (Shift+Enter 换行)"
                disabled={loading}
                className="flex-1 resize-none rounded-lg border border-green-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                rows={1}
              />

              {/* 发送按钮 */}
              <Button
                type="submit"
                disabled={(!input.trim() && !selectedImage) || loading}
                className="flex-none bg-green-600 hover:bg-green-700"
                size="icon"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            </div>

            {/* 提示文字 */}
            <p className="text-xs text-gray-400">
              Enter 发送，Shift+Enter 换行
            </p>
          </form>
        </div>
      </footer>
    </div>
  );
}
