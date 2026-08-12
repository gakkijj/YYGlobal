"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ExternalLink, RefreshCw, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, PackageMaterial } from "@/lib/api";

const statusLabels: Record<PackageMaterial["status"], string> = { ready: "符合要求", needs_edit: "需要修改", unverified: "已有但待核验", missing: "缺少", manual_review: "需人工确认" };

export function ApplicationPackages() {
  const client = useQueryClient();
  const packages = useQuery({ queryKey: ["application-packages"], queryFn: api.applicationPackages });
  const [notice, setNotice] = useState("");
  const [selectedProgram, setSelectedProgram] = useState<string | null>(null);
  useEffect(() => {
    setSelectedProgram(new URLSearchParams(window.location.search).get("program"));
  }, []);
  const update = useMutation({
    mutationFn: ({ packageId, row, status, asset }: { packageId: string; row: PackageMaterial; status: PackageMaterial["status"]; asset: string }) => {
      const [selected_asset_type = "", selected_asset_id = ""] = asset.split(":");
      return api.updatePackageMaterial(packageId, { material_key: row.material_key, status, selected_asset_type, selected_asset_id, note: "由用户在项目申请包中确认" });
    },
    onSuccess: () => { setNotice("已更新该项目的材料状态。其他项目不会自动继承此结论。"); client.invalidateQueries({ queryKey: ["application-packages"] }); },
    onError: (error) => setNotice(error instanceof Error ? error.message : "更新失败"),
  });
  const refresh = useMutation({ mutationFn: api.refreshApplicationPackage, onSuccess: () => client.invalidateQueries({ queryKey: ["application-packages"] }) });
  const items = [...(packages.data ?? [])].sort((a, b) => Number(b.program.id === selectedProgram) - Number(a.program.id === selectedProgram));
  return <section className="mt-6">
    {notice && <div className="mb-4 rounded-xl bg-mint/70 px-4 py-3 text-sm text-moss">{notice}</div>}
    <div className="mb-4"><p className="eyebrow">Per-program application packages</p><h2 className="mt-2 text-2xl font-black">项目申请包</h2><p className="mt-2 text-sm leading-6 text-ink/55">初始材料只是资产。每个项目必须根据自己的官网要求重新检查，并分别选择最终版本。</p></div>
    <div className="space-y-5">{items.map((pack) => <Card key={pack.id} className={pack.program.id === selectedProgram ? "border-moss ring-2 ring-mint" : ""}>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-lg font-black">{pack.program.university}｜{pack.program.name}</h3><a href={pack.program.official_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-moss">项目官网 <ExternalLink size={12} /></a></div><div className="flex items-center gap-2">{pack.ready ? <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-black text-emerald-700">申请包已就绪</span> : <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black text-amber-800">{pack.official_verified ? "材料准备中" : "官网要求待核验"}</span>}<Button size="sm" variant="secondary" onClick={() => refresh.mutate(pack.program.id)}><RefreshCw size={13} />重新检查资产</Button></div></div>
      {!pack.official_verified && <div className="mt-4 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800"><TriangleAlert className="mr-1 inline" size={14} />当前使用通用占位清单。请先在项目探索中核验该项目官网，核验后再重新检查。</div>}
      <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead><tr className="border-b border-black/10 text-xs text-ink/45"><th className="pb-2">官网材料要求</th><th className="pb-2">候选初始资产</th><th className="pb-2">适配结论</th><th className="pb-2">状态</th></tr></thead><tbody>{pack.checklist.map((row) => { const assetValue = row.selected_asset_id ? `${row.selected_asset_type}:${row.selected_asset_id}` : ""; return <tr key={row.material_key} className="border-b border-black/5 align-top"><td className="py-3 pr-3 font-bold">{row.name}<p className="mt-1 text-xs font-normal text-ink/40">{row.source_verified ? "官网清单已核验" : "通用占位，不能标记可提交"}</p></td><td className="py-3 pr-3"><select id={`${pack.id}-${row.material_key}`} className="field" defaultValue={assetValue}><option value="">未选择版本</option>{row.candidate_assets.map((asset) => <option key={`${asset.type}:${asset.id}`} value={`${asset.type}:${asset.id}`}>{asset.label}</option>)}</select>{!row.candidate_assets.length && <p className="mt-1 text-xs text-red-600">初始资产库中没有对应材料</p>}</td><td className="py-3 pr-3"><select id={`${pack.id}-${row.material_key}-status`} className="field" defaultValue={row.status}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></td><td className="py-3"><Button size="sm" variant="secondary" disabled={!pack.official_verified} onClick={() => { const asset = (document.getElementById(`${pack.id}-${row.material_key}`) as HTMLSelectElement).value; const status = (document.getElementById(`${pack.id}-${row.material_key}-status`) as HTMLSelectElement).value as PackageMaterial["status"]; update.mutate({ packageId: pack.id, row, status, asset }); }}>{row.status === "ready" ? <CheckCircle2 size={13} /> : null}保存判断</Button></td></tr>; })}</tbody></table></div>
      {pack.gaps.length > 0 && <div className="mt-4 rounded-xl bg-paper p-3 text-xs leading-6 text-ink/60"><strong>当前缺口：</strong>{pack.gaps.join("；")}</div>}
    </Card>)}{!items.length && <Card className="py-12 text-center"><p className="font-black">还没有项目申请包</p><p className="mt-2 text-sm text-ink/45">先在项目探索中选择项目并生成选校清单。</p></Card>}</div>
  </section>;
}
