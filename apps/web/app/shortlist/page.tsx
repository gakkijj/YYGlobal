"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FolderKanban, PenLine, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { ProcessGuide } from "@/components/process-guide";
import { Status } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

const tierLabels = { reach: "冲刺", target: "主申", safer: "相对稳健" };

export default function ShortlistPage() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["shortlists"], queryFn: api.shortlists });
  const packages = useQuery({ queryKey: ["application-packages"], queryFn: api.applicationPackages });
  const refresh = useMutation({ mutationFn: api.refreshApplicationPackage, onSuccess: () => client.invalidateQueries({ queryKey: ["application-packages"] }) });
  const shortlist = query.data?.[0];
  return <div className="mx-auto max-w-6xl">
    <PageHeader eyebrow="Decision support" title="选校清单" description="确定项目后，每个项目都建立独立申请包；项目之间的材料要求和就绪状态互不继承。" actions={<Link href="/programs"><Button variant="secondary">调整项目</Button></Link>} />
    <ProcessGuide current={2} completed={[0, 1]} />
    <Card className="mb-5 border-blue-100 bg-blue-50"><p className="font-black text-blue-950">这一步怎么做？</p><p className="mt-2 text-sm leading-6 text-blue-900/70">确认项目分档后，为每个项目打开申请包。先核验项目官网，再检查初始 CV、PS 和其他材料是可用、需修改还是缺失。</p></Card>
    {!query.isLoading && !shortlist && <Card className="py-16 text-center"><h2 className="text-xl font-black">还没有选校清单</h2><p className="mt-2 text-sm text-ink/50">先在项目探索中选择多个项目，再生成分层方案。</p><Link href="/programs"><Button className="mt-5">前往项目探索</Button></Link></Card>}
    {shortlist && <><Card className="mb-5 bg-ink text-white"><p className="text-xs font-bold uppercase tracking-[0.18em] text-white/50">Latest shortlist</p><h2 className="mt-2 text-2xl font-black">{shortlist.name}</h2><p className="mt-2 text-sm text-white/60">{shortlist.rationale}</p><div className="mt-5 flex gap-5 text-sm">{(["reach", "target", "safer"] as const).map((tier) => <span key={tier}><strong className="text-xl">{shortlist.items.filter((item) => item.tier === tier).length}</strong> <span className="text-white/50">{tierLabels[tier]}</span></span>)}</div></Card>
      <div className="space-y-4">{shortlist.items.map((item) => { const pack = packages.data?.find((value) => value.program.id === item.program.id); return <Card key={item.id} className="grid gap-4 md:grid-cols-[1fr_110px_1.1fr]">
        <div><div className="flex items-center gap-2"><Status value={item.tier}>{tierLabels[item.tier]}</Status><span className="text-xs font-bold text-ink/40">匹配分 {item.score.toFixed(0)}</span></div><h3 className="mt-3 text-lg font-black">{item.program.university}</h3><p className="mt-1 text-sm text-ink/55">{item.program.name}</p><a href={item.program.official_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-moss">官网 <ExternalLink size={12} /></a></div>
        <div className="grid place-items-center"><div className="grid size-20 place-items-center rounded-full border-[7px] border-mint text-xl font-black text-moss">{item.score.toFixed(0)}</div></div>
        <div><p className="label">项目申请包</p>{pack ? <><p className="text-sm font-bold">{pack.ready ? "材料已就绪" : pack.official_verified ? "材料准备中" : "等待官网深度核验"}</p><p className="mt-1 text-xs text-ink/45">{pack.checklist.filter((row) => row.status === "ready").length}/{pack.checklist.length} 项符合 · {pack.gaps.length} 个待处理</p><div className="mt-3 flex flex-wrap gap-2"><Link href={`/materials?program=${item.program.id}`}><Button size="sm"><FolderKanban size={14} />打开申请包</Button></Link><Link href={`/writing?program=${item.program.id}`}><Button size="sm" variant="secondary"><PenLine size={14} />生成项目 CV / PS</Button></Link></div></> : <Button size="sm" variant="secondary" disabled={refresh.isPending} onClick={() => refresh.mutate(item.program.id)}>建立申请包</Button>}<p className="label mt-4">风险与待确认</p>{item.risks.length ? <ul className="space-y-1.5">{item.risks.map((risk) => <li key={risk} className="flex gap-2 text-sm text-amber-800"><ShieldAlert className="mt-0.5 shrink-0" size={14} />{risk}</li>)}</ul> : <p className="text-sm text-ink/45">仍需人工复核官网。</p>}</div>
      </Card>; })}</div></>}
  </div>;
}
