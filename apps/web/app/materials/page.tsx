"use client";

import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, FileUp, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { ProcessGuide } from "@/components/process-guide";
import { ApplicationPackages } from "@/components/application-packages";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, MaterialArtifact, MaterialPlan } from "@/lib/api";

type SelectedExperience = { experience_id: string; title: string; kind: string; reason: string };

function experienceList(plan: Record<string, unknown>): SelectedExperience[] {
  return Array.isArray(plan.selected_experiences) ? (plan.selected_experiences as SelectedExperience[]) : [];
}

function textList(plan: Record<string, unknown>, key: string): string[] {
  const value = plan[key];
  return Array.isArray(value) ? value.map(String) : [];
}

export default function MaterialsPage() {
  const queryClient = useQueryClient();
  const [programId, setProgramId] = useState("");
  const [artifactKind, setArtifactKind] = useState<"cv" | "ps">("cv");
  const [artifactScope, setArtifactScope] = useState<"general" | "program">("general");
  const [versionName, setVersionName] = useState("通用版本 v1");
  const [notice, setNotice] = useState("");
  const [programs, plans, artifacts] = useQueries({ queries: [
    { queryKey: ["programs"], queryFn: () => api.programs() },
    { queryKey: ["material-plans"], queryFn: api.materialPlans },
    { queryKey: ["material-artifacts"], queryFn: api.materialArtifacts },
  ] });
  const create = useMutation({ mutationFn: api.createMaterialPlan, onSuccess: () => { setNotice("已分别生成 CV 与 PS 方案，所有素材来自已确认经历库。 "); queryClient.invalidateQueries({ queryKey: ["material-plans"] }); }, onError: (error) => setNotice(error instanceof Error ? error.message : "生成失败") });
  const register = useMutation({
    mutationFn: async (file: File) => {
      const document = await api.uploadDocument(file, artifactKind);
      return api.createMaterialArtifact({
        document_id: document.id,
        program_id: artifactScope === "program" ? programId : null,
        kind: artifactKind,
        scope: artifactScope,
        version_name: versionName,
        status: "draft",
      });
    },
    onSuccess: () => { setNotice("文件已上传并登记为材料版本；确认后可标记为可提交。"); queryClient.invalidateQueries({ queryKey: ["material-artifacts"] }); },
    onError: (error) => setNotice(error instanceof Error ? error.message : "版本登记失败"),
  });
  const updateArtifact = useMutation({
    mutationFn: ({ id, values }: { id: string; values: Partial<MaterialArtifact> }) => api.updateMaterialArtifact(id, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["material-artifacts"] }),
    onError: (error) => setNotice(error instanceof Error ? error.message : "版本更新失败"),
  });
  const preflight = useMutation({
    mutationFn: ({ artifactId, targetProgramId }: { artifactId: string; targetProgramId: string }) => api.materialPreflight(artifactId, targetProgramId),
    onSuccess: (result) => setNotice(`${result.ready_to_upload ? "提交前检查通过" : "提交前检查未通过"}：${result.checks.map((item) => `${item.name}${item.passed ? "✓" : "✗"}`).join("；")}${result.warnings.length ? `。${result.warnings.join("；")}` : ""}`),
    onError: (error) => setNotice(error instanceof Error ? error.message : "检查失败"),
  });
  const programMap = new Map(programs.data?.map((item) => [item.id, item]) ?? []);
  function onArtifactFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) register.mutate(file);
    event.target.value = "";
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Grounded application materials" title="材料中心" description="CV（个人简历）和 PS（个人陈述）是两类独立材料。系统共享真实经历库，但分别执行不同的选择、规划和验证规则。" />
      <ProcessGuide current={4} completed={[0, 1, 2]} />
      <Card className="mb-6 border-blue-100 bg-blue-50"><p className="font-black text-blue-950">先盘点，再按项目检查</p><p className="mt-2 text-sm leading-6 text-blue-900/70">上半部分上传和登记的是初始材料资产，不代表任何项目已经完成。选校后，请在下方逐个打开项目申请包，对照官网清单检查可复用、需修改和缺失项。</p></Card>
      {notice && <div className="mb-5 rounded-xl bg-mint/70 px-4 py-3 text-sm text-moss">{notice}</div>}
      <Card className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end"><label className="flex-1"><span className="label">选择目标项目</span><select className="field" value={programId} onChange={(event) => setProgramId(event.target.value)}><option value="">请选择项目</option>{programs.data?.map((program) => <option key={program.id} value={program.id}>{program.university}｜{program.name}</option>)}</select></label><Button onClick={() => create.mutate(programId)} disabled={!programId || create.isPending}><Sparkles size={16} />生成 CV / PS 方案</Button></Card>
      <Card className="mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div className="mr-auto"><p className="eyebrow">Version registry</p><h2 className="mt-2 text-xl font-black">CV / PS 文件版本</h2><p className="mt-1 text-sm text-ink/50">登记通用、学校定制和已提交版本；上传前检查项目、语言、解析状态与确认状态。</p></div>
          <label><span className="label">材料</span><select className="field min-w-24" value={artifactKind} onChange={(event) => setArtifactKind(event.target.value as "cv" | "ps")}><option value="cv">CV</option><option value="ps">PS</option></select></label>
          <label><span className="label">版本范围</span><select className="field min-w-32" value={artifactScope} onChange={(event) => setArtifactScope(event.target.value as "general" | "program")}><option value="general">通用版本</option><option value="program">学校定制</option></select></label>
          <label><span className="label">版本名称</span><input className="field min-w-40" value={versionName} onChange={(event) => setVersionName(event.target.value)} /></label>
          <label className={`inline-flex h-10 cursor-pointer items-center gap-2 rounded-xl bg-ink px-4 text-sm font-bold text-white ${(artifactScope === "program" && !programId) || !versionName ? "pointer-events-none opacity-45" : ""}`}><FileUp size={16} />上传并登记<input className="hidden" type="file" accept=".pdf,.docx,.txt,.md" onChange={onArtifactFile} /></label>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {artifacts.data?.map((artifact) => {
            const targetId = artifact.program_id ?? programId;
            return <div key={artifact.id} className="rounded-2xl border border-black/5 bg-paper/60 p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-black">{artifact.kind.toUpperCase()} · {artifact.version_name}</p><p className="mt-1 text-xs text-ink/45">{artifact.filename} · {artifact.scope === "general" ? "通用" : programMap.get(artifact.program_id ?? "")?.university ?? "学校定制"}</p></div><span className="rounded-full bg-white px-2 py-1 text-xs font-bold">{artifact.status === "draft" ? "草稿" : artifact.status === "ready" ? "可提交" : "已提交"}</span></div><div className="mt-4 flex flex-wrap gap-2">{artifact.status === "draft" && <Button size="sm" variant="secondary" onClick={() => updateArtifact.mutate({ id: artifact.id, values: { status: "ready" } })}>确认可提交</Button>}<Button size="sm" variant="secondary" disabled={!targetId} onClick={() => targetId && preflight.mutate({ artifactId: artifact.id, targetProgramId: targetId })}><ShieldCheck size={14} />提交前检查</Button>{artifact.status === "ready" && <Button size="sm" variant="ghost" onClick={() => updateArtifact.mutate({ id: artifact.id, values: { status: "submitted" } })}>标记已提交</Button>}</div></div>;
          })}
          {!artifacts.data?.length && <p className="text-sm text-ink/45">还没有登记文件版本。学校定制版本需要先在上方选择目标项目。</p>}
        </div>
      </Card>
      {!plans.isLoading && !plans.data?.length && <Card className="py-16 text-center"><FileText className="mx-auto text-ink/25" size={36} /><h2 className="mt-4 text-xl font-black">还没有材料方案</h2><p className="mt-2 text-sm text-ink/50">选择一个项目后，系统会读取项目要求和经历库，分别生成 CV 与 PS 规划。</p></Card>}
      <div className="space-y-6">{plans.data?.map((plan: MaterialPlan) => {
        const program = programMap.get(plan.program_id);
        return <section key={plan.id}>
          <div className="mb-3"><p className="eyebrow">{program?.university ?? "目标项目"}</p><h2 className="mt-1 text-xl font-black">{program?.name ?? plan.program_id}</h2></div>
          <div className="grid gap-5 xl:grid-cols-[0.75fr_1fr_1fr]">
            <Card><p className="eyebrow">Checklist</p><h3 className="mt-2 text-lg font-black">项目材料清单</h3><div className="mt-4 space-y-3">{plan.checklist.map((item) => <div key={item.name} className="flex items-center justify-between gap-3 rounded-xl bg-paper/70 px-3 py-2.5"><span className="text-sm font-semibold">{item.name}</span><span title={item.source_verified ? "官网字段已自动核验" : "官网字段待核验"}>{item.source_verified ? <CheckCircle2 className="text-emerald-600" size={17} /> : <TriangleAlert className="text-amber-600" size={17} />}</span></div>)}</div>{plan.gaps.length > 0 && <div className="mt-5 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">{plan.gaps.join("；")}</div>}</Card>
            <Card className="border-blue-100"><div className="flex items-center justify-between"><div><p className="eyebrow">CV Skill</p><h3 className="mt-2 text-lg font-black">个人简历规划</h3></div><span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-700">Grounded</span></div><p className="label mt-5">表达重点</p><p className="text-sm leading-6 text-ink/70">{String(plan.cv_plan.focus ?? "待生成")}</p><p className="label mt-5">选择的经历</p><div className="space-y-3">{experienceList(plan.cv_plan).map((item, index) => <div key={item.experience_id} className="rounded-xl border border-black/5 p-3"><div className="flex gap-2"><span className="font-black text-blue-600">{index + 1}</span><p className="text-sm font-bold">{item.title}</p></div><p className="mt-1 text-xs leading-5 text-ink/50">{item.reason}</p></div>)}{!experienceList(plan.cv_plan).length && <p className="text-sm text-ink/45">没有已确认经历，系统不会生成虚构内容。</p>}</div></Card>
            <Card className="border-violet-100"><div className="flex items-center justify-between"><div><p className="eyebrow">PS Skill</p><h3 className="mt-2 text-lg font-black">个人陈述规划</h3></div><span className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-bold text-violet-700">Grounded</span></div><p className="label mt-5">题目状态</p><p className="text-sm leading-6 text-ink/70">{String(plan.ps_plan.prompt ?? "待解析学校题目")}</p><p className="label mt-5">文章提纲</p><ol className="space-y-2">{textList(plan.ps_plan, "outline").map((item, index) => <li key={item} className="flex gap-3 rounded-xl bg-paper/70 px-3 py-2.5 text-sm"><span className="font-black text-violet-600">0{index + 1}</span>{item}</li>)}</ol><p className="label mt-5">学校定制</p><p className="text-sm leading-6 text-ink/70">{String(plan.ps_plan.customization ?? "待生成")}</p></Card>
          </div>
        </section>;
      })}</div>
      <ApplicationPackages />
    </div>
  );
}
