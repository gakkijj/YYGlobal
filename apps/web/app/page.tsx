"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import { ArrowRight, Bot, CheckCircle2, CircleDashed, Send, Sparkles } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, AgentEvent, streamAgent } from "@/lib/api";

type ChatLine = { role: "user" | "agent" | "progress"; text: string };

export default function DashboardPage() {
  const results = useQueries({
    queries: [
      { queryKey: ["profile"], queryFn: api.profile },
      { queryKey: ["programs"], queryFn: () => api.programs() },
      { queryKey: ["tasks"], queryFn: api.tasks },
      { queryKey: ["health"], queryFn: api.health },
    ],
  });
  const skills = useQuery({ queryKey: ["skills"], queryFn: api.skills });
  const [message, setMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [chat, setChat] = useState<ChatLine[]>([
    { role: "agent", text: "你好，我会把画像、项目研究、选校、CV、PS 和时间线串成一条申请流程。你想先从哪里开始？" },
  ]);
  const profile = results[0].data;
  const programs = results[1].data ?? [];
  const tasks = results[2].data ?? [];
  const health = results[3].data;
  const openTasks = tasks.filter((item) => item.status !== "done");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = message.trim();
    if (!value || running) return;
    setChat((current) => [...current, { role: "user", text: value }]);
    setMessage("");
    setRunning(true);
    try {
      await streamAgent(value, ({ event: name, data }: AgentEvent) => {
        if (name === "plan.created") {
          const plan = data.plan as { name: string }[];
          setChat((current) => [...current, { role: "progress", text: `计划：${plan.map((item) => item.name).join(" → ")}` }]);
        }
        if (name === "message.completed") {
          setChat((current) => [...current, { role: "agent", text: String(data.content) }]);
        }
        if (name === "guardrail.triggered") {
          setChat((current) => [...current, { role: "progress", text: "本次请求触发了安全边界。" }]);
        }
      });
    } catch (error) {
      setChat((current) => [...current, { role: "agent", text: error instanceof Error ? error.message : "Agent 请求失败" }]);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow="P0 Application OS"
        title={`早上好${profile?.full_name ? `，${profile.full_name}` : ""}`}
        description="今天只做最影响申请结果的事。Agent 会保留证据、解释决策，并把需要你确认的操作停在提交之前。"
        actions={
          <span className="rounded-full border border-black/5 bg-white/70 px-3 py-1.5 text-xs text-ink/60">
            {health?.llm_mode === "dashscope"
              ? "阿里云百炼模式"
              : health?.llm_mode === "openai"
                ? "OpenAI 模式"
                : "本地可运行模式"}
          </span>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { value: profile?.confirmed ? "画像已确认" : "画像待完善", label: profile?.confirmed ? "核心信息可用于选校" : "先补齐学校、GPA 与目标", icon: profile?.confirmed ? CheckCircle2 : CircleDashed, href: "/profile" },
          { value: `${programs.length} 个`, label: "画像匹配项目目录", icon: Sparkles, href: "/programs" },
          { value: `${openTasks.length} 项`, label: "未完成申请任务", icon: CircleDashed, href: "/applications" },
          { value: `${skills.data?.length ?? 0} 个`, label: "留学申请专业 Skills", icon: Bot, href: "/capabilities" },
        ].map(({ value, label, icon: Icon, href }) => (
          <Link key={label} href={href} className="group">
            <Card className="flex h-full items-start justify-between transition group-hover:-translate-y-0.5 group-hover:border-moss/30 group-hover:shadow-md">
              <div><p className="text-2xl font-black">{value}</p><p className="mt-1 text-sm text-ink/50">{label}</p><p className="mt-3 flex items-center gap-1 text-xs font-bold text-moss opacity-0 transition group-hover:opacity-100">查看详情 <ArrowRight size={12} /></p></div>
              <span className="rounded-xl bg-mint p-2 text-moss"><Icon size={18} /></span>
            </Card>
          </Link>
        ))}
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <Card className="flex min-h-[560px] flex-col p-0">
          <div className="flex items-center justify-between border-b border-black/5 px-5 py-4">
            <div><strong>AI 申请助手</strong><p className="text-xs text-ink/45">理解需求、制定步骤、调用工具并保留依据</p></div>
            <span className="flex items-center gap-1.5 text-xs font-semibold text-moss"><span className="size-2 rounded-full bg-emerald-500" />在线</span>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            {chat.map((line, index) => (
              <div key={`${line.role}-${index}`} className={line.role === "user" ? "ml-auto max-w-[82%] rounded-2xl rounded-br-sm bg-ink px-4 py-3 text-sm leading-6 text-white" : line.role === "progress" ? "mx-auto max-w-[92%] rounded-xl bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800" : "max-w-[88%] rounded-2xl rounded-bl-sm bg-mint/70 px-4 py-3 text-sm leading-6 text-ink"}>{line.text}</div>
            ))}
            {running && <div className="max-w-[60%] animate-pulse rounded-2xl bg-mint/70 px-4 py-3 text-sm text-ink/60">正在规划并执行…</div>}
          </div>
          <form onSubmit={submit} className="border-t border-black/5 p-4">
            <div className="flex gap-2 rounded-2xl border border-black/10 bg-white p-2 shadow-sm focus-within:border-moss/50">
              <input value={message} onChange={(event) => setMessage(event.target.value)} className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none" placeholder="例如：根据我的情况帮我规划 CV" />
              <Button type="submit" disabled={running || !message.trim()} aria-label="发送"><Send size={16} /></Button>
            </div>
          </form>
        </Card>

        <div className="space-y-6">
          <Card>
            <p className="eyebrow">Next best actions</p>
            <h2 className="mt-2 text-xl font-black">下一步建议</h2>
            <div className="mt-4 space-y-3">
              {[
                [profile?.confirmed ? "复查申请目标" : "完善并确认学生画像", "/profile"],
                ["筛选并核验目标项目", "/programs"],
                ["生成 CV 与 PS 独立方案", "/materials"],
              ].map(([label, href], index) => (
                <Link key={href} href={href} className="flex items-center gap-3 rounded-xl border border-black/5 bg-paper/70 p-3 text-sm font-semibold transition hover:border-moss/30 hover:bg-mint/40">
                  <span className="grid size-7 place-items-center rounded-full bg-white text-xs">{index + 1}</span><span className="flex-1">{label}</span><ArrowRight size={15} />
                </Link>
              ))}
            </div>
          </Card>
          <Card>
            <p className="eyebrow">Upcoming</p>
            <h2 className="mt-2 text-xl font-black">临近任务</h2>
            <div className="mt-4 space-y-4">
              {openTasks.slice(0, 5).map((task) => <div key={task.id} className="border-l-2 border-amber pl-3"><p className="text-sm font-semibold">{task.title}</p><p className="mt-1 text-xs text-ink/45">{task.due_date ?? "待设定日期"}</p></div>)}
              {!openTasks.length && <p className="text-sm text-ink/45">生成申请时间线后，任务会出现在这里。</p>}
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
