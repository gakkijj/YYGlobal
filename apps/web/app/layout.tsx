import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "YYGlobal｜留学申请 Agent",
  description: "从学生画像、项目研究到 CV、PS 和申请时间线的智能工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>
          <Sidebar />
          <main className="min-h-screen px-4 pb-24 pt-6 sm:px-6 lg:ml-64 lg:px-10 lg:py-9">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
