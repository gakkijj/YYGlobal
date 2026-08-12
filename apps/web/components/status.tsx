import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  reach: "bg-amber-100 text-amber-800",
  target: "bg-blue-100 text-blue-800",
  safer: "bg-emerald-100 text-emerald-800",
  todo: "bg-stone-100 text-stone-700",
  doing: "bg-blue-100 text-blue-700",
  done: "bg-emerald-100 text-emerald-700",
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
};

export function Status({ value, children }: { value: string; children?: React.ReactNode }) {
  return <span className={cn("rounded-full px-2.5 py-1 text-xs font-bold", styles[value] ?? "bg-stone-100 text-stone-700")}>{children ?? value}</span>;
}

