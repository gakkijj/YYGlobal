"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bot, Braces, CheckCircle2, Wrench } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

const capabilityInfo: Record<string, { title: string; stage: string; summary: string; examples: string[]; href: string; action: string }> = {
  "applicant-profile": { title: "学生画像整理", stage: "申请准备", summary: "整理教育背景、成绩、经历、目标国家和专业，只使用用户确认的信息。", examples: ["发现画像缺失项", "整理确认后的申请目标"], href: "/profile", action: "完善画像" },
  "program-research": { title: "项目研究", stage: "项目选择", summary: "按画像检索项目，并区分项目目录信息、官网证据和待核验内容。", examples: ["查找目标专业项目", "核验项目官网信息"], href: "/programs", action: "探索项目" },
  "program-compare": { title: "项目对比", stage: "项目选择", summary: "从专业匹配、要求、费用、材料和风险等维度比较多个项目。", examples: ["比较两个项目", "解释差异和风险"], href: "/programs", action: "选择项目" },
  "shortlist-builder": { title: "选校清单", stage: "项目选择", summary: "把候选项目组织为冲刺、主申和相对稳健三档，不承诺录取概率。", examples: ["生成三档选校", "说明分档理由"], href: "/shortlist", action: "查看选校" },
  "cv-planner": { title: "CV 规划与生成", stage: "材料准备", summary: "从已确认经历中选择和组织内容，生成通用或项目定制 CV。", examples: ["规划经历顺序", "生成完整 CV"], href: "/writing", action: "处理 CV" },
  "ps-planner": { title: "项目专属 PS", stage: "材料准备", summary: "结合真实经历、具体项目和学校题目，规划或生成项目专属个人陈述。", examples: ["分析 PS 题目", "生成项目专属初稿"], href: "/writing", action: "处理 PS" },
  "application-timeline": { title: "申请时间线", stage: "申请执行", summary: "项目申请包就绪后，根据已核验截止日期生成任务和时间安排。", examples: ["倒排申请任务", "识别临近截止风险"], href: "/applications", action: "查看申请" },
};

export default function CapabilitiesPage() {
  const skills = useQuery({ queryKey: ["skills"], queryFn: api.skills });
  return <div className="mx-auto max-w-6xl">
    <PageHeader eyebrow="Professional Skills" title="7 个留学申请专业 Skills" description="针对画像、项目研究、项目对比、选校、CV、PS 和时间线提供专业化能力。" actions={<Link href="/"><Button variant="secondary">返回工作台</Button></Link>} />
    <Card className="mb-6 border-blue-100 bg-blue-50"><div className="flex gap-3"><Bot className="mt-0.5 shrink-0 text-blue-700" size={20} /><div><p className="font-black text-blue-950">覆盖留学申请的关键环节</p><p className="mt-1 text-sm leading-6 text-blue-900/70">每个专业 Skill 都有明确的使用场景、工具权限和结构化输出，帮助用户按申请流程完成对应任务。</p></div></div></Card>
    <div className="grid gap-5 md:grid-cols-2">{skills.data?.map((skill, index) => {
      const info = capabilityInfo[skill.name] ?? { title: skill.name, stage: "AI 能力", summary: skill.description, examples: [], href: "/", action: "开始使用" };
      return <Card key={skill.name} className="flex flex-col">
        <div className="flex items-start justify-between gap-3"><div><p className="eyebrow">{String(index + 1).padStart(2, "0")} · {info.stage}</p><h2 className="mt-2 text-xl font-black">{info.title}</h2></div><span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700"><CheckCircle2 size={13} />已启用</span></div>
        <p className="mt-4 flex-1 text-sm leading-6 text-ink/60">{info.summary}</p>
        <div className="mt-4 flex flex-wrap gap-2">{info.examples.map((example) => <span key={example} className="rounded-full bg-paper px-2.5 py-1 text-xs text-ink/55">{example}</span>)}</div>
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-black/5 pt-4"><div className="flex gap-3 text-xs text-ink/40"><span className="flex items-center gap-1"><Wrench size={13} />{skill.tools.length} 个工具</span><span className="flex items-center gap-1"><Braces size={13} />结构化输出</span></div><Link href={info.href} className="inline-flex items-center gap-1 text-sm font-black text-moss">{info.action}<ArrowRight size={14} /></Link></div>
      </Card>;
    })}</div>
    {skills.isLoading && <Card className="py-16 text-center text-sm text-ink/45">正在读取 AI 能力…</Card>}
  </div>;
}
