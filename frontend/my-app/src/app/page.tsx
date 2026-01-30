// 告知系统：这个文件要在浏览器端（客户端）运行
"use client";

import React, { useState, useCallback, useRef, useEffect, FormEvent } from "react";
import { ChatMessageBubble, type Message } from "@/components/ChatMessageBubble";
import { Button } from "@/components/ui/button";
import { Upload, Send, X, Loader2 } from "lucide-react";

const API_BASE = "/api";

type WorkMode = "auto" | "fast" | "deep";

// export default 导出这个函数，让其他文件可以使用
export default function Home() {
  // 统一的消息历史和会话ID
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string>(() => `thread_${Date.now()}`);

  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    // messagesEndRef 指向聊天消息底部的指针
    // ?. 可选链操作符，如果元素存在才执行
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
  }, [messages]); // 依赖项：当 messages 变化时执行

  // 自动调整文本输入框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  // 选择图片处理
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    // 用户选择图片
    const files = Array.from(e.target.files || []);

    // 限制最多10张图片
    const MAX_IMAGES = 10;
    const totalImages = selectedImages.length + files.length;

    if (totalImages > MAX_IMAGES) {
      alert(`最多只能上传 ${MAX_IMAGES} 张图片，当前已选 ${selectedImages.length} 张`);
      return;
    }

    // 读取所有图片的预览
    const newPreviews: string[] = [];
    let loadedCount = 0;

    //使用 FileReader 读取图片数据
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        newPreviews.push(reader.result as string);
        loadedCount++;

        if (loadedCount === files.length) {
          setSelectedImages(prev => [...prev, ...files]);
          setImagePreviews(prev => [...prev, ...newPreviews]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  // 删除图片处理
  const handleRemoveImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
    if (fileInputRef.current && selectedImages.length === 1) {
      fileInputRef.current.value = "";
    }
  };
  // 删除全部图片处理
  const handleRemoveAllImages = () => {
    setSelectedImages([]);
    setImagePreviews([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // 处理提交消息（点击发送按钮时执行）
  // FormEvent: TypeScript 表单事件类型
  const handleSubmit = (e: FormEvent) => {
    // 阻止表单默认提交行为
    e.preventDefault();
    // 如果没有输入内容且没有选择图片，或者正在加载中，则不处理
    if ((!input.trim() && selectedImages.length === 0) || loading) return;

    const messageText = input.trim() ||
      (selectedImages.length === 1 ? "请帮我识别这张图片" : `请帮我识别这 ${selectedImages.length} 张图片`);

    // 调用发送消息函数
    handleSendMessage(messageText, selectedImages.length > 0 ? selectedImages : undefined);
    //清空输入框和已选图片
    setInput("");
    handleRemoveAllImages();
  };

  // 处理键盘按键（回车发送，Shift+回车换行）
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  // 发送消息函数，支持图片上传和SSE流式响应
  const handleSendMessage = useCallback(
    async (message: string, images?: File[]) => {
      let imagePaths: string[] | undefined;
      let imagePreviewUrls: string[] | undefined;
      let assistantMessageId: string | null = null;

      // 添加用户消息
      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: message,
        images: images ? images.map(img => URL.createObjectURL(img)) : undefined,
      };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        // 1. 如果有图片，先批量上传
        if (images && images.length > 0) {
          const formData = new FormData();
          images.forEach(image => {
            formData.append("files", image);
          });

          const uploadResponse = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData,
          });

          if (!uploadResponse.ok) {
            throw new Error("图片上传失败");
          }

          const uploadData = await uploadResponse.json();
          imagePaths = uploadData.file_paths;
          imagePreviewUrls = userMessage.images;
        }

        // 2. 发送聊天请求（SSE流式）- 由 Orchestrator Agent 智能路由
        const chatResponse = await fetch(`${API_BASE}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            image_paths: imagePaths,
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
                } else if (data.type === "tool") {
                  // Planning Service 的工具调用事件
                  console.log("工具调用:", data.tool_name, data.status);
                } else if (data.type === "tool_call") {
                  // 图像检测的工具调用事件（兼容旧版本）
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
                } else if (data.type === "sources") {
                  // 处理知识库来源事件
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? {
                            ...msg,
                            sources: data.sources,
                          }
                        : msg
                    )
                  );
                  console.log("收到知识库来源:", data.sources?.length || 0, "条");
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
          setMessages((prev) => prev.filter(msg => msg.id !== assistantMessageId));
        }

        // 显示错误信息
        const errorMessage = error instanceof Error ? error.message : "未知错误";
        const isNetworkError = errorMessage.includes("fetch") || errorMessage.includes("network");

        setMessages((prev) => [
          ...prev,
          {
            id: `error_${Date.now()}`,
            role: "assistant",
            content: `抱歉，发生了错误:\n\n${errorMessage}\n\n${
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
    <div className="flex flex-col h-screen bg-paddy-texture">
      {/* 顶部标题栏 */}
      <header className="border-b border-stone-200 glass">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-paddy-500 to-paddy-600 flex items-center justify-center text-white shadow-md shadow-paddy-500/30">
              <span className="text-xl">🌾</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-stone-900">
                RuralBrain 乡村智慧大脑
              </h1>
              <p className="text-sm text-stone-600 mt-0.5">
                统一智能助手 · 图像检测与规划咨询
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* 对话区域 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* 条件渲染，显示欢迎信息或聊天消息 */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full pt-16 animate-fade-in">
              {/* 主图标区域 */}
              <div className="relative mb-8">
                <div className="w-28 h-28 rounded-3xl bg-gradient-to-br from-paddy-400 via-paddy-500 to-paddy-600 flex items-center justify-center text-6xl shadow-xl shadow-paddy-500/30 animate-scale-in">
                  🌾
                </div>
                {/* 装饰元素 */}
                <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-gold-400/80 flex items-center justify-center text-sm animate-bounce-slow">
                  ✨
                </div>
                <div className="absolute -bottom-1 -left-1 w-6 h-6 rounded-full bg-sky-400/60 flex items-center justify-center text-xs animate-pulse-slow">
                  💡
                </div>
              </div>

              {/* 欢迎文字 */}
              <h2 className="text-2xl font-bold text-stone-900 mb-2 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                你好！我是 RuralBrain
              </h2>
              <p className="text-stone-600 mb-8 animate-slide-up" style={{ animationDelay: '0.2s' }}>
                乡村智慧大脑，为你提供专业的智能服务
              </p>

              {/* 功能卡片网格 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl mb-8">
                {/* 卡片 1 */}
                <div className="group card p-5 hover-lift cursor-pointer animate-slide-up" style={{ animationDelay: '0.3s' }}>
                  <div className="text-4xl mb-3">🖼️</div>
                  <h3 className="font-semibold text-stone-900 mb-1">图像识别</h3>
                  <p className="text-sm text-stone-600">
                    病虫害、农作物、牛只智能检测
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-paddy-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>上传图片开始</span>
                    <span>→</span>
                  </div>
                </div>

                {/* 卡片 2 */}
                <div className="group card p-5 hover-lift cursor-pointer animate-slide-up" style={{ animationDelay: '0.4s' }}>
                  <div className="text-4xl mb-3">🏘️</div>
                  <h3 className="font-semibold text-stone-900 mb-1">规划咨询</h3>
                  <p className="text-sm text-stone-600">
                    旅游、产业、政策发展建议
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-paddy-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>提问开始</span>
                    <span>→</span>
                  </div>
                </div>

                {/* 卡片 3 */}
                <div className="group card p-5 hover-lift cursor-pointer animate-slide-up" style={{ animationDelay: '0.5s' }}>
                  <div className="text-4xl mb-3">📊</div>
                  <h3 className="font-semibold text-stone-900 mb-1">科学方案</h3>
                  <p className="text-sm text-stone-600">
                    防治方案和定价分析
                  </p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-paddy-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>深入了解</span>
                    <span>→</span>
                  </div>
                </div>
              </div>

              {/* 提示文字 */}
              <div className="animate-slide-up" style={{ animationDelay: '0.6s' }}>
                <p className="text-stone-500 text-sm">
                  💡 上传图片或直接提问，我会自动判断如何帮助你
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 数组映射，把每条信息都渲染成一个消息气泡组件 */}
              {messages.map((message) => (
                <ChatMessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* 输入区域 */}
      <footer className="border-t border-stone-200 glass">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* 图片预览 */}
            {imagePreviews.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {imagePreviews.map((preview, index) => (
                  <div key={index} className="image-preview-card">
                    <img
                      src={preview}
                      alt={`预览 ${index + 1}`}
                      className="h-24 w-24 object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(index)}
                      className="absolute -top-2 -right-2 bg-stone-800 text-white rounded-full p-1.5 hover:bg-stone-700 transition-colors shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-stone-600"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                {imagePreviews.length > 1 && (
                  <button
                    type="button"
                    onClick={handleRemoveAllImages}
                    className="px-4 py-2 bg-stone-100 text-stone-700 text-sm rounded-xl hover:bg-stone-200 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-stone-500"
                  >
                    清除全部
                  </button>
                )}
              </div>
            )}

            {/* 输入框和按钮 */}
            <div className="flex items-end gap-3">
              {/* 上传按钮 - 始终可用 */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageSelect}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="btn btn-secondary flex-none"
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
                className="input flex-1 resize-none"
                rows={1}
              />

              {/* 发送按钮 */}
              <Button
                type="submit"
                disabled={(!input.trim() && selectedImages.length === 0) || loading}
                className="btn btn-primary flex-none"
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
            <p className="text-xs text-stone-500 text-center">
              Enter 发送 · Shift+Enter 换行 · 支持上传图片进行检测
            </p>
          </form>
        </div>
      </footer>
    </div>
  );
}
