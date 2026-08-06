import type { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export function StatCard({
  label, value, delta, deltaTone = "neutral", icon, accent, sub,
}: {
  label: string;
  value: ReactNode;
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
  icon?: ReactNode;
  accent?: string;
  sub?: ReactNode;
}) {
  const toneClass =
    deltaTone === "up"   ? "text-success" :
    deltaTone === "down" ? "text-destructive" : "text-muted-foreground";

  return (
    <div className="glass-card rounded-2xl p-5 relative overflow-hidden group transition hover:translate-y-[-2px]">
      {accent && (
        <div className="absolute -top-12 -right-12 size-32 rounded-full opacity-30 blur-2xl"
             style={{ background: accent }} />
      )}
      <div className="flex items-start justify-between relative">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="mt-2 text-2xl md:text-3xl font-semibold tracking-tight relative">{value}</div>
      <div className="mt-1.5 flex items-center gap-1.5 text-xs relative">
        {delta && (
          <span className={`inline-flex items-center gap-0.5 ${toneClass}`}>
            {deltaTone === "up" ? <ArrowUpRight className="size-3" /> :
             deltaTone === "down" ? <ArrowDownRight className="size-3" /> : null}
            {delta}
          </span>
        )}
        {sub && <span className="text-muted-foreground">{sub}</span>}
      </div>
    </div>
  );
}
