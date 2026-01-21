"use client";

import React, { useRef, useEffect, useState, FormEvent } from "react";
import { ChatMessageBubble, type Message } from "./ChatMessageBubble";
import { Button } from "./ui/button";
import { Upload, Send, X, Loader2 } from "lucide-react";
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
    <div className="flex flex-col h-screen bg-gradient-to-b from-primary-50/30 to-white">
      {/* 头部 */}
      <div className="flex-none border-b border-primary-100 bg-white/80 backdrop-blur-sm px-6 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white shadow-sm">
            🌾
          </div>
          <div>
            <h1 className="text-xl font-semibold text-primary-900">
              AI农业智能检测助手
            </h1>
            <p className="text-sm text-primary-700 mt-0.5">
              基于大模型的病虫害、水稻、牛只智能检测
            </p>
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-primary-300">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center text-5xl mb-6 shadow-sm">
              🌾
            </div>
            <p className="text-lg mb-2 text-primary-700 font-medium">欢迎使用 AI农业智能检测助手</p>
            <p className="text-sm text-primary-600">上传图片并提问，开始智能对话</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}
            {loading && (
              <div className="flex justify-start mb-6">
                <div className="bg-primary-50 rounded-2xl px-4 py-3 border border-primary-100 shadow-sm">
                  <LoadingIndicator size="sm" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div className="flex-none border-t border-primary-100 bg-white/90 backdrop-blur-sm px-6 py-4 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* 图片预览 */}
          {imagePreview && (
            <div className="image-preview-card">
              <img
                src={imagePreview}
                alt="预览"
                className="h-20 w-20 object-cover rounded-lg"
              />
              <button
                type="button"
                onClick={handleRemoveImage}
                className="absolute -top-2 -right-2 bg-error text-white rounded-full p-1.5 hover:bg-error/90 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error"
              >
                <X className="w-3.5 h-3.5" />
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
        </form>
      </div>
    </div>
  );
};
