"use client";

import React, { useRef, useEffect, useState, FormEvent } from "react";
import { ChatMessageBubble, type Message } from "./ChatMessageBubble";
import { Button } from "./ui/button";
import { ImagePreviewCard } from "./ui/ImagePreviewCard";
import { Upload, Send, Loader2 } from "lucide-react";
import LoadingIndicator from "./ui/LoadingIndicator";

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string, image?: File) => void;
  loading?: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  loading = false,
}) => {
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
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
      addImageToState(file);
    }
  };

  // 将图片添加到状态（提取为独立函数，供拖拽和粘贴使用）
  const addImageToState = (file: File) => {
    // 检查是否为图片文件
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }

    setSelectedImage(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
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

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // 只取第一个文件
      addImageToState(files[0]);
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
      const file = imageItems[0].getAsFile();
      if (file) {
        addImageToState(file);
      }
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

    onSendMessage(input.trim() || "请帮我识别这张图片", selectedImage || undefined);
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

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* 头部 */}
      <div className="flex-none border-b border-stone-200 bg-white/95 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-paddy-500 to-paddy-600 flex items-center justify-center text-white shadow-md">
            🌾
          </div>
          <div>
            <h1 className="text-xl font-bold text-stone-900">
              AI农业智能检测助手
            </h1>
            <p className="text-sm text-stone-600 mt-0.5">
              基于大模型的病虫害、水稻、牛只智能检测
            </p>
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-stone-600">
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-paddy-400 to-paddy-500 flex items-center justify-center text-4xl shadow-lg mb-4">
              🌾
            </div>
            <p className="text-lg mb-2 text-stone-900 font-semibold">欢迎使用 AI农业智能检测助手</p>
            <p className="text-sm text-stone-600">上传图片并提问，开始智能对话</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}
            {loading && (
              <div className="flex justify-start mb-6">
                <div className="bg-primary-50 rounded-xl px-4 py-3 border border-primary-100 shadow-sm">
                  <LoadingIndicator size="sm" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div className="flex-none border-t border-stone-200 bg-white/95 backdrop-blur-sm px-6 py-4">
        <form
          onSubmit={handleSubmit}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={`space-y-3 ${isDragging ? 'drag-active' : ''}`}
        >
          {/* 图片预览 */}
          {imagePreview && (
            <ImagePreviewCard
              src={imagePreview}
              alt="预览"
              onRemove={handleRemoveImage}
              showNumber={false}
            />
          )}

          {/* 输入框和按钮 */}
          <div className="input-container">
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
              className="flex-none"
            >
              <Upload className="w-5 h-5" />
            </Button>

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
              disabled={(!input.trim() && !selectedImage) || loading}
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
          <p className="text-xs text-muted-foreground">
            Enter 发送，Shift+Enter 换行
          </p>

          {/* 拖拽遮罩层 */}
          {isDragging && (
            <div className="drag-overlay">
              <div className="drag-overlay-content">
                <Upload className="w-12 h-12 mb-3 text-primary-600" />
                <p className="text-lg font-semibold">松开鼠标上传图片</p>
                <p className="text-sm text-muted-foreground mt-2">支持 JPG、PNG、GIF、WebP 等格式</p>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
