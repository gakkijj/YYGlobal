"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, FilePenLine, Save, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { ProcessGuide } from "@/components/process-guide";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, MaterialDraft } from "@/lib/api";

export default function WritingPage() {
  const queryClient = useQueryClient();
  const [kind, setKind] = useState<"cv" | "ps">("cv");
  const [programId, setProgramId] = useState("");
  const [language, setLanguage] = useState<"English" | "Chinese">("English");
  const [prompt, setPrompt] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [notice, setNotice] = useState("");
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.profile });
  const packages = useQuery({ queryKey: ["application-packages"], queryFn: api.applicationPackages });
  const drafts = useQuery({ queryKey: ["material-drafts"], queryFn: api.materialDrafts });
  const selectedPrograms = packages.data?.map((item) => item.program) ?? [];
  const selected = useMemo(() => drafts.data?.find((item) => item.id === selectedId), [drafts.data, selectedId]);

  useEffect(() => { if (!selectedId && drafts.data?.length) setSelectedId(drafts.data[0].id); }, [drafts.data, selectedId]);
  useEffect(() => { if (selected) { setTitle(selected.title); setContent(selected.content); } }, [selected]);
  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("program") ?? "";
    if (requested) setProgramId(requested);
  }, []);

  const generate = useMutation({
    mutationFn: () => api.generateMaterialDraft({ kind, program_id: kind === "ps" ? programId : (programId || null), language, prompt }),
    onSuccess: (result) => {
      setNotice(`已生成并保存完整 ${result.kind.toUpperCase()} 草稿，请在右侧逐项复核。`);
      queryClient.setQueryData<MaterialDraft[]>(["material-drafts"], (items = []) => [result, ...items]);
      setSelectedId(result.id);
    },
    onError: (error) => setNotice(error instanceof Error ? error.message : "生成失败"),
  });
  const save = useMutation({
    mutationFn: (status: "draft" | "reviewed") => api.updateMaterialDraft(selectedId, { title, content, status }),
    onSuccess: (result) => {
      setNotice(result.status === "reviewed" ? `已创建 v${result.version_number} 并标记为已复核，旧版本已保留。` : `已创建 v${result.version_number}，旧版本已保留。`);
      queryClient.setQueryData<MaterialDraft[]>(["material-drafts"], (items = []) => [result, ...items]);
      setSelectedId(result.id);
    },
    onError: (error) => setNotice(error instanceof Error ? error.message : "保存失败"),
  });
  const ready = Boolean(profile.data?.confirmed && profile.data.experiences.some((item) => item.confirmed));

  return <div className="mx-auto max-w-7xl">
    <PageHeader eyebrow="Project-specific writing" title="项目 CV / PS 文书" description="先在选校清单中确定项目，再针对当前项目生成和管理 CV、PS。通用 CV 只作为基础版本，项目版本分别保存。" />
    <ProcessGuide current={4} completed={[0, 1, 2]} />
    {notice && <div className="mb-5 rounded-xl bg-mint/70 px-4 py-3 text-sm text-moss">{notice}</div>}
    {!ready && <Card className="mb-6 border-amber-200 bg-amber-50"><p className="font-black text-amber-900">生成前需要确认画像和至少一段经历</p><a href="/profile" className="mt-2 inline-block text-sm font-bold text-amber-800 underline">前往我的画像</a></Card>}
    {!packages.isLoading && !selectedPrograms.length && <Card className="mb-6 border-blue-200 bg-blue-50"><p className="font-black text-blue-950">请先完成项目选择</p><p className="mt-2 text-sm text-blue-900/70">只有加入选校清单并建立申请包的项目，才能生成项目定制 CV 和 PS。</p><a href="/shortlist" className="mt-2 inline-block text-sm font-bold text-blue-800 underline">前往选校清单</a></Card>}
    <div className="grid gap-6 xl:grid-cols-[370px_1fr]">
      <div className="space-y-5">
        <Card>
          <div className="grid grid-cols-2 gap-2 rounded-xl bg-paper p-1">{(["cv", "ps"] as const).map((value) => <button key={value} onClick={() => setKind(value)} className={`rounded-lg px-3 py-2 text-sm font-black ${kind === value ? "bg-ink text-white" : "text-ink/55"}`}>完整 {value.toUpperCase()}</button>)}</div>
          <label className="mt-5 block"><span className="label">当前已选项目 {kind === "ps" ? "（必选）" : "（选择项目即生成定制版）"}</span><select className="field w-full" value={programId} onChange={(event) => setProgramId(event.target.value)}><option value="">{kind === "ps" ? "请选择选校清单中的项目" : "不绑定项目：生成通用 CV"}</option>{selectedPrograms.map((program) => <option key={program.id} value={program.id}>{program.university}｜{program.name}</option>)}</select></label>
          <label className="mt-4 block"><span className="label">生成语言</span><select className="field w-full" value={language} onChange={(event) => setLanguage(event.target.value as "English" | "Chinese")}><option>English</option><option>Chinese</option></select></label>
          <label className="mt-4 block"><span className="label">{kind === "ps" ? "学校文书题目 / 字数要求" : "额外写作要求"}</span><textarea className="field min-h-28 w-full resize-y" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder={kind === "ps" ? "粘贴学校的 PS 题目、字数限制或希望重点回答的问题" : "例如：一页英文 CV，重点突出科研和项目经历"} /></label>
          <Button className="mt-5 w-full" disabled={!ready || (kind === "ps" && !programId) || generate.isPending} onClick={() => generate.mutate()}><Sparkles size={16} />{generate.isPending ? "正在生成完整文稿…" : `生成完整 ${kind.toUpperCase()}`}</Button>
          <p className="mt-3 text-xs leading-5 text-ink/45">项目版会绑定当前项目并独立保存，不覆盖通用版本或其他项目版本。提交学校前仍需本人逐项复核。</p>
        </Card>
        <Card><p className="eyebrow">Immutable history</p><h2 className="mt-2 text-lg font-black">文稿版本历史</h2><p className="mt-1 text-xs leading-5 text-ink/45">每次生成和保存都会创建新版本，不覆盖历史内容。</p><div className="mt-4 space-y-2">{drafts.data?.map((draft) => <button key={draft.id} onClick={() => setSelectedId(draft.id)} className={`w-full rounded-xl border p-3 text-left ${selectedId === draft.id ? "border-moss bg-mint/50" : "border-black/5"}`}><div className="flex items-center justify-between gap-2"><span className="text-sm font-black">{draft.kind.toUpperCase()} · v{draft.version_number} · {draft.title}</span>{draft.status === "reviewed" && <Check size={15} className="text-emerald-600" />}</div><p className="mt-1 text-xs text-ink/55">{draft.change_summary}</p><p className="mt-1 text-xs text-ink/40">{new Date(draft.created_at).toLocaleString("zh-CN")} · {draft.model_info.provider ?? "unknown"}</p></button>)}{!drafts.data?.length && <p className="text-sm text-ink/45">尚未生成文稿。</p>}</div></Card>
      </div>
      <Card className="min-h-[720px]">{selected ? <><div className="flex flex-wrap items-end gap-3"><label className="min-w-0 flex-1"><span className="label">文稿标题</span><input className="field w-full" value={title} onChange={(event) => setTitle(event.target.value)} /></label><a href={api.materialDraftExportUrl(selected.id, "docx")} download><Button variant="secondary"><Download size={15} />下载 DOCX</Button></a><a href={api.materialDraftExportUrl(selected.id, "pdf")} download><Button variant="secondary"><Download size={15} />下载 PDF</Button></a><Button variant="secondary" onClick={() => save.mutate("draft")} disabled={save.isPending}><Save size={15} />保存</Button><Button onClick={() => save.mutate("reviewed")} disabled={save.isPending}><Check size={15} />保存并标记已复核</Button></div><p className="mt-2 text-xs text-ink/40">下载的是当前选中的已保存版本；若刚修改正文，请先保存再下载。</p>{selected.warnings.length > 0 && <div className="mt-4 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">{selected.warnings.join("；")}</div>}<textarea aria-label="完整文稿编辑器" className="mt-5 min-h-[590px] w-full resize-y rounded-2xl border border-black/10 bg-white p-5 font-mono text-sm leading-7 outline-none focus:border-moss" value={content} onChange={(event) => setContent(event.target.value)} /></> : <div className="grid min-h-[650px] place-items-center text-center"><div><FilePenLine className="mx-auto text-ink/20" size={42} /><h2 className="mt-4 text-xl font-black">生成一份完整文稿</h2><p className="mt-2 text-sm text-ink/45">选择左侧 CV 或 PS，生成后可在这里继续编辑并保存。</p></div></div>}</Card>
    </div>
  </div>;
}
