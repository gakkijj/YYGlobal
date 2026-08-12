"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ExternalLink, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { ProcessGuide } from "@/components/process-guide";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ProgramsPage() {
  const client = useQueryClient();
  const [input, setInput] = useState("");
  const [queryText, setQueryText] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [notice, setNotice] = useState("");
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.profile });
  const programs = useQuery({ queryKey: ["programs", queryText], queryFn: () => api.programs(queryText, !queryText) });
  const create = useMutation({
    mutationFn: () => api.createShortlist(selected),
    onSuccess: () => { setNotice("选校清单已生成，可以前往“选校清单”查看分层、理由和风险。 "); setSelected([]); client.invalidateQueries({ queryKey: ["shortlists"] }); },
    onError: (error) => setNotice(error instanceof Error ? error.message : "创建失败"),
  });
  const verify = useMutation({
    mutationFn: api.verifyProgram,
    onSuccess: () => { setNotice("官网已重新读取；自动抽取字段仍需查看证据后确认。 "); client.invalidateQueries({ queryKey: ["programs"] }); },
    onError: (error) => setNotice(error instanceof Error ? error.message : "官网核验失败"),
  });
  const verifyMatched = useMutation({
    mutationFn: () => api.verifyMatchedPrograms(5),
    onSuccess: (result) => { setNotice(`已按画像核验前 ${result.attempted_count} 个匹配项目：${result.verified_count} 个达到完整核验，${result.needs_review_count} 个已抽取部分证据待复核，${result.failed_count} 个读取失败。`); client.invalidateQueries({ queryKey: ["programs"] }); },
    onError: (error) => setNotice(error instanceof Error ? error.message : "批量官网核验失败"),
  });
  const profileReady = Boolean(profile.data?.confirmed && profile.data.target_fields.length && profile.data.target_countries.length);
  const toggle = (id: string) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Official-source research" title="项目探索" description="先完成并确认画像，再根据目标国家、目标专业和入学季生成目录；官网只按需核验画像匹配的项目。主动搜索仍可跨专业浏览。" actions={<div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => verifyMatched.mutate()} disabled={!profileReady || verifyMatched.isPending}><ShieldCheck size={15} />核验前 5 个匹配项目</Button><Button onClick={() => create.mutate()} disabled={!selected.length || create.isPending}>生成选校清单（{selected.length}）</Button></div>} />
      <ProcessGuide current={2} completed={[0, 1]} />
      {notice && <div className="mb-5 rounded-xl bg-mint/70 px-4 py-3 text-sm text-moss">{notice}</div>}
      <Card className="mb-6">
        <form onSubmit={(event) => { event.preventDefault(); setQueryText(input); }} className="flex gap-2">
          <div className="relative flex-1"><Search className="absolute left-3 top-3 text-ink/35" size={17} /><input className="field pl-10" value={input} onChange={(event) => setInput(event.target.value)} placeholder="搜索学校、项目或专业方向" /></div>
          <Button type="submit">搜索</Button>
        </form>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink/45"><span>{queryText ? "正在跨目录搜索" : `按画像推荐：${profile.data?.target_fields.join("、") || "请先填写目标方向"}`}</span><span>·</span><span>{programs.data?.length ?? 0} 个匹配项目</span><span>·</span><span>支持逐字段官网证据核验</span></div>
      </Card>
      {!queryText && !profileReady && <Card className="mb-6 border-amber-200 bg-amber-50 text-center"><h2 className="text-lg font-black text-amber-900">请先完成申请画像</h2><p className="mt-2 text-sm text-amber-800">至少确认目标国家和目标专业方向后，系统才会生成匹配目录并允许批量抓取官网。</p><a className="mt-4 inline-flex text-sm font-black text-amber-900 underline" href="/profile">前往填写画像</a></Card>}
      {programs.isLoading && <p className="py-20 text-center text-ink/45">正在载入项目目录…</p>}
      <div className="grid gap-4 xl:grid-cols-2">
        {programs.data?.map((program) => {
          const active = selected.includes(program.id);
          const requirement = program.requirement;
          return (
            <Card key={program.id} className={cn("transition", active && "border-moss/40 ring-2 ring-moss/10")}>
              <div className="flex items-start gap-4">
                <button onClick={() => toggle(program.id)} className={cn("mt-1 grid size-6 shrink-0 place-items-center rounded-lg border transition", active ? "border-moss bg-moss text-white" : "border-black/15 bg-white")} aria-label={active ? "取消选择" : "选择项目"}>{active && <Check size={14} />}</button>
                <div className="min-w-0 flex-1">
                  <p className="eyebrow">{program.country} · {program.city}</p>
                  <h2 className="mt-2 text-lg font-black leading-6">{program.university}</h2>
                  <p className="mt-1 text-sm text-ink/60">{program.name}</p>
                  <span className="mt-2 inline-flex rounded-full bg-sky-50 px-2.5 py-1 text-[11px] font-bold text-sky-700">{program.field} · {program.degree}</span>
                </div>
                <span className={cn("rounded-full px-2.5 py-1 text-xs font-bold", requirement?.verified ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-800")}>{requirement?.verified ? "已自动核验" : "待重新核验"}</span>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {[
                  ["学费", program.tuition ? `${program.currency} ${program.tuition.toLocaleString()}` : "待确认"],
                  ["截止", requirement?.deadline ?? "待确认"],
                  ["GPA", requirement?.min_gpa ? `≥ ${requirement.min_gpa}` : "待确认"],
                  ["语言", requirement?.language.TOEFL ? `TOEFL ${requirement.language.TOEFL}` : "待确认"],
                ].map(([label, value]) => <div key={label} className="rounded-xl bg-paper/80 p-3"><p className="text-[11px] font-bold uppercase tracking-wider text-ink/40">{label}</p><p className="mt-1 text-sm font-bold">{value}</p></div>)}
              </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {requirement?.materials.slice(0, 5).map((item) => <span key={item} className="rounded-full bg-mint/60 px-2.5 py-1 text-xs text-moss">{item}</span>)}
                </div>
                {requirement && requirement.deadlines.length > 1 && <details className="mt-3 rounded-xl bg-amber-50 p-3"><summary className="cursor-pointer text-xs font-black text-amber-900">查看全部 {requirement.deadlines.length} 个截止日期</summary><ul className="mt-2 space-y-1 text-xs text-ink/60">{requirement.deadlines.map((item, index) => <li key={`${item.date}-${index}`}>{item.round || "申请截止"}：{item.date}</li>)}</ul></details>}
              {program.evidence.length > 0 && <details className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/60 p-3"><summary className="cursor-pointer text-xs font-black text-emerald-800">查看 {program.evidence.length} 条官网原文证据</summary><div className="mt-3 space-y-2">{program.evidence.slice(0, 8).map((item) => <blockquote key={item.id} className="border-l-2 border-emerald-300 pl-3 text-xs leading-5 text-ink/60"><span className="font-black text-emerald-800">{item.field}</span>：{item.quote}</blockquote>)}</div></details>}
              <div className="mt-5 flex items-center justify-between border-t border-black/5 pt-4">
                <a href={program.official_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-bold text-moss hover:underline">查看官方页面 <ExternalLink size={13} /></a>
                <Button variant="ghost" size="sm" onClick={() => verify.mutate(program.id)} disabled={verify.isPending}><RefreshCw size={13} />重新核验</Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
