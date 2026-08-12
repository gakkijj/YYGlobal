import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-2xl border border-black/5 bg-white/80 p-5 shadow-soft backdrop-blur", className)} {...props} />;
}

