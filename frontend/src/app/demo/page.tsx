"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ChevronUp, ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ToolCall {
  name: string;
  status: "运行中" | "已完成";
  resultImage?: string;
  summary?: string[];
}

interface Message {
  role: "user" | "assistant";
  content: string;
  image?: string;
  toolCalls?: ToolCall[];
}

const conversationData: Message[] = [
  // 第一轮：害虫检测
  {
    role: "user",
    content: "请帮我识别这张图片中的害虫",
    image: "/demo/pest-input.jpg",
  },
  {
    role: "assistant",
    content:
      "检测完成！图片中发现了1只甜菜夜蛾，检测置信度95%。\n\n**害虫分析：**\n甜菜夜蛾是常见的农业害虫，属于鳞翅目夜蛾科，主要危害蔬菜、棉花、玉米等作物。幼虫会啃食叶片造成缺刻或孔洞，严重时可将叶片吃光，对产量影响极大。\n\n**防治建议：**\n1. 物理防治：使用黄色粘虫板诱捕成虫，减少虫源\n2. 生物防治：释放赤眼蜂等天敌昆虫进行控制\n3. 化学防治：在幼虫2-3龄期使用氯虫苯甲酰胺等低毒农药\n4. 农业防治：及时清除田间杂草，深耕翻土消灭越冬蛹\n\n建议定期监测虫情，在害虫低龄期及时防治效果最佳，同时注意保护天敌，实现绿色防控。",
    toolCalls: [
      {
        name: "pest_detection_tool",
        status: "已完成",
        resultImage: "/demo/pest-output.jpg",
        summary: [
          "检测到害虫：甜菜夜蛾",
          "检测数量：1只",
        ]
      }
    ]
  },
  // 第二轮：大米检测
  {
    role: "user",
    content: "请帮我识别这张图片中的大米",
    image: "/demo/rice-input.jpg",
  },
  {
    role: "assistant",
    content:
      "检测完成！图片中包含5种大米品种，共计24粒大米样本：\n\n1. **糯米** - 5粒，圆润饱满，适合制作粽子、年糕等粘性食品\n2. **五常大米** - 5粒，产自黑龙江，口感软糯香甜，适合蒸饭\n3. **丝苗米** - 5粒，粒形细长，米质坚硬，适合炒饭\n4. **泰国香米** - 5粒，具有独特茉莉花香气，适合蒸饭或煮粥\n5. **珍珠大米** - 4粒，颗粒圆润如珍珠，适合煮粥\n\n**储存建议：**\n建议将不同品种的大米分开密封储存，避免串味影响口感。储存环境应保持干燥通风，温度控制在15℃以下，避免阳光直射。建议在3-6个月内食用完毕，以保证最佳风味和营养价值。定期检查是否有虫害或霉变现象。",
    toolCalls: [
      {
        name: "rice_detection_tool",
        status: "已完成",
        resultImage: "/demo/rice-output.jpg",
        summary: [
          "检测到大米品种：5种",
          "糯米：5粒",
          "五常大米：5粒",
          "丝苗米：5粒",
          "泰国香米：5粒",
          "珍珠大米：4粒"
        ]
      }
    ]
  },
  // 第三轮：牛只检测
  {
    role: "user",
    content: "请帮我识别这张图片中的牛",
    image: "/demo/cow-input.jpg",
  },
  {
    role: "assistant",
    content:
      "检测完成！图片中共识别到**8头牛**，检测置信度92%，所有牛只位置已精准标注。\n\n**养殖建议：**\n1. 牛群密度适中，确保每头牛有足够活动空间，避免拥挤造成应激\n2. 建立健康档案，每日观察牛只精神状态、采食量和反刍情况\n3. 定期清理粪污，保持圈舍干燥清洁，每周消毒1-2次预防疾病\n4. 提供充足清洁饮水和优质饲料，科学配比营养\n5. 严格按免疫程序接种疫苗，每季度驱虫一次\n\n建议建立养殖记录台账，定期邀请兽医健康检查，确保牛群稳定发展。",
    toolCalls: [
      {
        name: "cow_detection_tool",
        status: "已完成",
        resultImage: "/demo/cow-output.jpg",
        summary: [
          "检测数量：8头牛",
        ]
      }
    ]
  },
];

export default function DemoPage() {
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
                基于大模型的病虫害、水稻、牛只智能检测演示
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* 对话区域 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="space-y-6">
            {conversationData.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
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
          className={`px-4 py-2.5 rounded-2xl ${
            isUser
              ? "bg-green-600 text-white"
              : "bg-green-50 text-gray-800 border border-green-100"
          }`}
        >
          {isUser ? (
            <p className="text-xl leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="text-xl leading-relaxed prose prose-green max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1">
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

        {/* 用户上传的图片 */}
        {isUser && message.image && (
          <div className="mt-1">
            <Image
              src={message.image}
              alt="上传的图片"
              width={180}
              height={120}
              className="rounded-lg border border-gray-200 w-auto h-auto max-w-xs"
              unoptimized
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
}

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
              <Image
                src={toolCall.resultImage}
                alt="工具检测结果"
                width={180}
                height={120}
                className="rounded-lg border border-gray-200 w-auto h-auto max-w-xs"
                unoptimized
              />
            </div>
          )}
          
          {/* 检测结果摘要 */}
          {toolCall.summary && toolCall.summary.length > 0 && (
            <div>
              <div className="text-sm text-gray-500 mb-1.5">检测数据：</div>
              <div className="bg-gray-50 rounded p-2 space-y-1">
                {toolCall.summary.map((item, idx) => (
                  <div key={idx} className="text-sm text-gray-700 flex items-start">
                    <span className="text-green-600 mr-1.5">•</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
