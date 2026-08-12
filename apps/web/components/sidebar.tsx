"use client";

import { BriefcaseBusiness, FileText, GraduationCap, LayoutDashboard, ListChecks, PenLine, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const groups = [
  { label: "申请准备", links: [{ href: "/profile", label: "1. 画像与初始材料", icon: UserRound }] },
  { label: "项目选择", links: [{ href: "/programs", label: "2. 项目推荐", icon: GraduationCap }, { href: "/shortlist", label: "3. 选校与申请包", icon: ListChecks }] },
  { label: "材料准备", links: [{ href: "/materials", label: "4. 材料与项目检查", icon: FileText }, { href: "/writing", label: "5. CV / PS 文书", icon: PenLine }] },
  { label: "申请执行", links: [{ href: "/applications", label: "6. 申请看板", icon: BriefcaseBusiness }] },
];

const mobileLinks = [
  { href: "/", label: "首页", icon: LayoutDashboard },
  { href: "/profile", label: "准备", icon: UserRound },
  { href: "/programs", label: "项目", icon: GraduationCap },
  { href: "/materials", label: "材料", icon: FileText },
  { href: "/applications", label: "申请", icon: BriefcaseBusiness },
];

export function Sidebar() {
  const pathname = usePathname();
  const navLink = (href: string, label: string, Icon: typeof LayoutDashboard) => <Link key={href} href={href} className={cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition", pathname === href ? "bg-ink text-white" : "text-ink/60 hover:bg-mint/70 hover:text-ink")}><Icon size={17} />{label}</Link>;
  return <>
    <aside className="hidden border-r border-black/5 bg-white/75 px-5 py-7 backdrop-blur lg:fixed lg:inset-y-0 lg:left-0 lg:block lg:w-64">
      <Link href="/" className="mb-8 flex items-center gap-3"><span className="grid size-10 place-items-center rounded-2xl bg-ink text-lg font-black text-white">Y</span><span><strong className="block text-lg tracking-tight">YYGlobal</strong><small className="text-xs text-ink/50">你的申请控制台</small></span></Link>
      <nav className="space-y-5">{navLink("/", "今日工作台", LayoutDashboard)}{groups.map((group) => <section key={group.label}><p className="mb-1 px-3 text-[10px] font-black uppercase tracking-[0.16em] text-ink/35">{group.label}</p><div className="space-y-1">{group.links.map((item) => navLink(item.href, item.label, item.icon))}</div></section>)}</nav>
      <div className="absolute bottom-6 left-5 right-5 rounded-2xl bg-mint/70 p-4 text-xs leading-5 text-ink/65"><strong className="block text-ink">流程优先</strong>完成当前阶段后，再进入下一步。</div>
    </aside>
    <nav className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-5 border-t border-black/10 bg-white/95 px-1 py-1.5 backdrop-blur lg:hidden">{mobileLinks.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={cn("flex flex-col items-center gap-1 rounded-lg py-1.5 text-[10px] font-bold", pathname === href ? "bg-mint text-moss" : "text-ink/45")}><Icon size={17} />{label}</Link>)}</nav>
  </>;
}
