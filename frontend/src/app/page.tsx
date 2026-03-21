// 告知系统：这个文件要在浏览器端（客户端）运行
"use client";

import React, { useState, useCallback, useRef, useEffect, FormEvent } from "react";
import { ChatMessageBubble, type Message } from "@/components/ChatMessageBubble";
import { Button } from "@/components/ui/button";
import { ImagePreviewCard } from "@/components/ui/ImagePreviewCard";
import { FeatureDemoCard, type DemoConfig } from "@/components/FeatureDemoCard";
import { Upload, Send, Loader2, Mic } from "lucide-react";
import { useASR } from "@/hooks/useASR";

const API_BASE = "/api";

type WorkMode = "auto" | "fast" | "deep";

// 模型类型定义
interface Model {
  id: string;
  name: string;
  description: string;
  is_multimodal: boolean;
}

interface ModelsResponse {
  models: Model[];
  default_model: string;
}

// 演示功能配置
const demoConfigs: DemoConfig[] = [
  {
    title: "病虫害检测",
    icon: "🐛",
    description: "智能识别农作物病虫害，分析危害程度并提供科学防治方案",
    exampleQuery: "请帮我检测这张图片中的病虫害，并给出防治建议",
    demoImage: "/demo/pest-input.jpg",
  },
  {
    title: "大米品种识别",
    icon: "🍚",
    description: "识别大米品种，分析品质特征，提供烹饪建议和储存方法",
    exampleQuery: "请帮我识别这张图片中的大米品种",
    demoImage: "/demo/rice-input.jpg",
  },
  {
    title: "奶牛检测",
    icon: "🐄",
    description: "识别牛只品种和数量，提供养殖管理、疫病防控和繁殖建议",
    exampleQuery: "请帮我数一下这张图片中有多少头牛",
    demoImage: "/demo/cow-input.jpg",
  },
];

// export default 导出这个函数，让其他文件可以使用
export default function Home() {
  // 统一的消息历史和会话ID
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string>(() => `thread_${Date.now()}`);

  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const [enableKnowledgeBase, setEnableKnowledgeBase] = useState<boolean>(true);
  const [enableWebSearch, setEnableWebSearch] = useState<boolean>(false);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("deepseek");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    // messagesEndRef 指向聊天消息底部的指针
    // ?. 可选链操作符，如果元素存在才执行
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 智能滚动：检测用户是否正在查看历史消息
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(messages.length);
  const prevContentLengthRef = useRef(0);

  useEffect(() => {
    const hasStreamingMessage = messages.some(msg => msg.isStreaming);
    const currentContentLength = messages.reduce((total, msg) => total + msg.content.length, 0);

    // 计算当前是否接近底部（距离底部小于 150px）
    const isNearBottom = () => {
      const container = mainContainerRef.current;
      if (!container) return true;
      return container.scrollTop + container.clientHeight >= container.scrollHeight - 150;
    };

    if (hasStreamingMessage) {
      // 流式输出时，只有内容长度增加且接近底部时才滚动
      if (currentContentLength > prevContentLengthRef.current && isNearBottom()) {
        scrollToBottom();
        prevContentLengthRef.current = currentContentLength;
      }
    } else if (messages.length !== prevMessageCountRef.current) {
      // 新消息到达时，总是滚动到底部
      scrollToBottom();
      prevMessageCountRef.current = messages.length;
      prevContentLengthRef.current = currentContentLength;
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

  // 获取可用模型列表
  useEffect(() => {
    fetch(`${API_BASE}/models`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`请求失败: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setModels(data.models);
        setSelectedModelId(data.default_model);
      })
      .catch(err => {
        console.error("获取模型列表失败:", err);
        // 设置兜底默认模型
        setModels([{ id: "deepseek", name: "DeepSeek", description: "默认模型", is_multimodal: false }]);
        setSelectedModelId("deepseek");
      });
  }, []);

  // 语音识别 Hook
  const { isListening, isSupported, interimText, toggle } = useASR({
    onResult: (text) => {
      setInput(text);
      setVoiceStatus("");
    },
    onInterim: (text) => {
      setVoiceStatus(`识别中: ${text}`);
    },
    onError: (error) => {
      let errorMsg = `语音识别出错: ${error}`;
      if (error === 'network') {
        errorMsg = '网络错误：请检查网络连接或稍后重试';
      } else if (error === 'not-allowed') {
        errorMsg = '未授权：请允许麦克风权限';
      } else if (error === 'not-supported') {
        errorMsg = '不支持：请使用 Chrome 或 Edge 浏览器';
      }
      setVoiceStatus(errorMsg);
      setTimeout(() => setVoiceStatus(""), 5000);
    }
  });

  // 选择图片处理
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addImagesToState(files);
  };

  // 将图片添加到状态（提取为独立函数，供拖拽和粘贴使用）
  const addImagesToState = (files: File[]) => {
    // 限制最多10张图片
    const MAX_IMAGES = 10;
    const totalImages = selectedImages.length + files.length;

    if (totalImages > MAX_IMAGES) {
      alert(`最多只能上传 ${MAX_IMAGES} 张图片，当前已选 ${selectedImages.length} 张`);
      return;
    }

    // 过滤只保留图片文件
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      alert('请选择图片文件');
      return;
    }

    // 读取所有图片的预览
    const newPreviews: string[] = [];
    let loadedCount = 0;

    //使用 FileReader 读取图片数据
    imageFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        newPreviews.push(reader.result as string);
        loadedCount++;

        if (loadedCount === imageFiles.length) {
          setSelectedImages(prev => [...prev, ...imageFiles]);
          setImagePreviews(prev => [...prev, ...newPreviews]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  // 拖拽事件处理
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // 只在真正离开拖拽区域时才取消高亮
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    // 提取拖拽的文件
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      addImagesToState(files);
    }
  };

  // 粘贴事件处理
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = Array.from(e.clipboardData.items);
    const imageItems = items.filter(item =>
      item.type.startsWith('image/')
    );

    if (imageItems.length > 0) {
      e.preventDefault();
      const files = imageItems.map(item => item.getAsFile()).filter(Boolean) as File[];
      addImagesToState(files);
    }
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
            enable_knowledge_base: enableKnowledgeBase,
            enable_web_search: enableWebSearch,
            model_id: selectedModelId,
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
                  // 直接使用相对路径，Next.js rewrites 会自动代理到后端
                  // 这样在本地和远程服务器部署都能正常工作
                  const resultImageUrl = data.result_image || undefined;

                  const toolCall = {
                    name: data.tool_name,
                    status: data.status as "运行中" | "已完成",
                    resultImage: resultImageUrl,
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
                  console.log("工具调用:", data.tool_name, "结果图片:", resultImageUrl);
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
    [threadId, enableKnowledgeBase, enableWebSearch, selectedModelId]
  );

  // 处理演示卡片点击 - 从 URL 加载示例图片并发送
  const handleDemoClick = useCallback(
    async (query: string, imageUrl?: string) => {
      console.log("演示卡片点击:", query, imageUrl);

      if (imageUrl) {
        try {
          console.log("正在加载演示图片:", imageUrl);
          // 从 URL 获取图片
          const response = await fetch(imageUrl);

          if (!response.ok) {
            throw new Error(`图片加载失败: ${response.status}`);
          }

          const blob = await response.blob();
          console.log("图片加载成功, size:", blob.size, "type:", blob.type);

          // 获取文件扩展名
          const contentType = blob.type || "image/jpeg";
          let extension = "jpg";
          if (contentType.includes("png")) extension = "png";
          else if (contentType.includes("webp")) extension = "webp";

          // 创建 File 对象
          const filename = `demo_${Date.now()}.${extension}`;
          const file = new File([blob], filename, { type: contentType });
          console.log("File 对象创建成功:", filename);

          // 发送消息和图片
          await handleSendMessage(query, [file]);
        } catch (error) {
          console.error("加载演示图片失败:", error);
          // 如果图片加载失败，仍然发送文本消息（不带图片）
          await handleSendMessage(query);
        }
      } else {
        // 没有图片，直接发送文本消息
        await handleSendMessage(query);
      }
    },
    [handleSendMessage]
  );

  return (
    <div
      className="flex flex-col h-screen dynamic-texture page-load-animate"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* 拖拽遮罩层 - 全屏显示 */}
      {isDragging && (
        <div className="drag-overlay">
          <div className="drag-overlay-content">
            <Upload className="w-12 h-12 mb-3 text-paddy-600" />
            <p className="text-lg font-semibold text-stone-900">拖拽图片到任意位置</p>
            <p className="text-sm text-stone-500 mt-2">松开鼠标即可上传 · 支持 JPG、PNG、GIF、WebP</p>
          </div>
        </div>
      )}

      {/* 顶部标题栏 */}
      <header className="border-b border-stone-200 glass-enhanced">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-paddy-500 to-paddy-600 flex items-center justify-center text-white shadow-md">
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
      <main ref={mainContainerRef} className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* 条件渲染，显示欢迎信息或聊天消息 */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full pt-16">
              {/* 主图标区域 */}
              <div className="relative mb-6">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-paddy-400 to-paddy-500 flex items-center justify-center text-5xl shadow-lg">
                  🌾
                </div>
              </div>

              {/* 欢迎文字 */}
              <h2 className="text-2xl font-bold text-stone-900 mb-2">
                你好！我是 RuralBrain
              </h2>
              <p className="text-stone-600 mb-3">
                乡村智慧大脑，为你提供专业的智能服务
              </p>
              <p className="text-stone-500 text-sm mb-8">
                支持图像识别、规划咨询、科学方案等功能
              </p>

              {/* 功能演示卡片区域 */}
              <div className="w-full max-w-3xl mb-8">
                <p className="text-stone-600 text-sm font-medium mb-4 text-center">
                  ✨ 点击下方卡片快速体验功能
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {demoConfigs.map((config) => (
                    <FeatureDemoCard
                      key={config.title}
                      config={config}
                      onClick={(query, imageUrl) => handleDemoClick(query, imageUrl)}
                      disabled={loading}
                    />
                  ))}
                </div>
              </div>

              {/* 提示文字 */}
              <p className="text-stone-500 text-sm">
                💡 上传图片或直接提问，我会自动判断如何帮助你
              </p>
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
      <footer className="border-t border-stone-200 bg-white/95 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* 知识库开关 */}
            <button
              type="button"
              onClick={() => setEnableKnowledgeBase(!enableKnowledgeBase)}
              disabled={loading}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all border-2 shadow-sm hover:shadow-md ${
                enableKnowledgeBase
                  ? "bg-green-50 border-green-500 text-green-700"
                  : "bg-white border-stone-300 text-stone-600"
              }`}
            >
              知识库 {enableKnowledgeBase ? "✓" : ""}
            </button>

            {/* 联网搜索开关 */}
            <button
              type="button"
              onClick={() => setEnableWebSearch(!enableWebSearch)}
              disabled={loading}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all border-2 shadow-sm hover:shadow-md ${
                enableWebSearch
                  ? "bg-blue-50 border-blue-500 text-blue-700"
                  : "bg-white border-stone-300 text-stone-600"
              }`}
            >
              联网搜索 {enableWebSearch ? "✓" : ""}
            </button>

            {/* 模型选择器 */}
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              disabled={loading}
              className="px-4 py-2 rounded-full text-sm font-medium border-2 border-stone-200 bg-white text-stone-700 hover:border-stone-300 focus:outline-none focus:border-paddy-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>

            {/* 多模态提示 - 暂时隐藏，待实现真正的多模态消息封装后再启用 */}
            {/* 当前实现只是将图片路径拼接到文本中，并未让 LLM 真正接收图像数据 */}
            {/* {models.find(m => m.id === selectedModelId)?.is_multimodal && (
              <span className="text-xs text-green-600 font-medium">支持图片识别</span>
            )} */}

            {/* 图片预览 */}
            {imagePreviews.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {imagePreviews.map((preview, index) => (
                  <ImagePreviewCard
                    key={index}
                    src={preview}
                    alt={`预览 ${index + 1}`}
                    index={index}
                    total={imagePreviews.length}
                    onRemove={() => handleRemoveImage(index)}
                  />
                ))}
                {imagePreviews.length > 1 && (
                  <button
                    type="button"
                    onClick={handleRemoveAllImages}
                    className="px-5 py-2.5 bg-white text-stone-700 text-sm rounded-full hover:bg-red-50 hover:text-red-600 transition-all border-2 border-stone-200 hover:border-red-300 shadow-sm hover:shadow-md"
                  >
                    清除全部
                  </button>
                )}
              </div>
            )}

            {/* 输入框和按钮 */}
            <div className="input-container">
              {/* 上传按钮 */}
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
                className="flex-none"
              >
                <Upload className="w-5 h-5" />
              </Button>

              {/* 麦克风按钮 */}
              {isSupported ? (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={toggle}
                  disabled={loading}
                  className={`flex-none ${isListening ? 'voice-recording' : ''}`}
                  title={isListening ? '停止录音' : '点击开始语音输入'}
                >
                  <Mic className="w-5 h-5" />
                </Button>
              ) : null}

              {/* 文本输入框 */}
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                placeholder="输入消息... (Shift+Enter 换行，Ctrl+V 粘贴图片，拖拽图片到任意位置)"
                disabled={loading}
                className="input-enhanced flex-1 resize-none border-0 bg-transparent shadow-none focus:ring-0 focus:shadow-none"
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
              Enter 发送 · Shift+Enter 换行 · Ctrl+V 粘贴图片 · 拖拽图片到任意位置
              {isSupported && " · 点击麦克风语音输入"}
            </p>

            {/* 语音状态提示 */}
            {voiceStatus && (
              <div className="voice-status">
                {isListening && '🎙️ '}{voiceStatus}
              </div>
            )}
          </form>
        </div>
      </footer>
    </div>
  );
}
