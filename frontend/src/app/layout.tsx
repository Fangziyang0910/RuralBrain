import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RuralBrain - 乡村智慧大脑",
  description: "智能图像识别对话系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
