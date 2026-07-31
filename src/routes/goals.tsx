import { createFileRoute } from "@tanstack/react-router";
import { Plus, Trophy } from "lucide-react";
import { goals, inr, inrShort } from "../lib/finance-data";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";

export const Route = createFileRoute("/goals")({
  head: () => ({ meta: [{ title: "Goals — MoneyScope" }] }),
  component: Goals,
});

function Goals() {
  const total = goals.reduce((s,g) => s + g.target, 0);
  const saved = goals.reduce((s,g) => s + g.saved, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Savings & Goals</h1>
          <p className="text-sm text-muted-foreground">Plan it. Save it. Celebrate it.</p>
        </div>
        <Button className="rounded-xl gap-1.5"><Plus className="size-4" /> New goal</Button>
      </header>

      <section className="glass-card rounded-3xl p-6 relative overflow-hidden">
        <div className="absolute inset-0 opacity-50 pointer-events-none"
             style={{ background: "radial-gradient(700px 250px at 80% 0%, color-mix(in oklab, var(--chart-2) 25%, transparent), transparent 60%)" }} />
        <div className="relative grid md:grid-cols-3 gap-6 items-center">
          <div>
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Total saved</div>
            <div className="text-4xl font-semibold tracking-tight mt-1">{inr(saved)}</div>
            <div className="text-sm text-muted-foreground mt-1">of {inr(total)} across {goals.length} goals</div>
          </div>
          <div className="md:col-span-2">
            <Progress value={(saved/total)*100} className="h-3 rounded-full" />
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>{Math.round((saved/total)*100)}% complete</span>
              <span>{inr(total - saved)} to go</span>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map(g => {
          const pct = (g.saved / g.target) * 100;
          const left = g.target - g.saved;
          return (
            <article key={g.id} className="glass-card rounded-2xl p-5 hover:translate-y-[-2px] transition">
              <div className="flex items-start gap-3">
                <div className="size-12 rounded-2xl grid place-items-center text-2xl"
                     style={{ background: `color-mix(in oklab, ${g.color} 18%, transparent)` }}>
                  {g.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{g.name}</h3>
                    {pct >= 70 && <Trophy className="size-4 text-warning" />}
                  </div>
                  <div className="text-xs text-muted-foreground">Target by {g.deadline}</div>
                </div>
              </div>
              <div className="mt-4">
                <div className="flex items-baseline justify-between">
                  <div className="text-2xl font-semibold tabular-nums">{inrShort(g.saved)}</div>
                  <div className="text-sm text-muted-foreground">/ {inrShort(g.target)}</div>
                </div>
                <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full rounded-full transition-all"
                       style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${g.color}, color-mix(in oklab, ${g.color} 55%, white))` }} />
                </div>
                <div className="mt-3 flex justify-between text-xs">
                  <span className="text-muted-foreground">{pct.toFixed(0)}% reached</span>
                  <span>{inr(left)} left</span>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button variant="outline" size="sm" className="rounded-xl flex-1">Add funds</Button>
                <Button variant="ghost" size="sm" className="rounded-xl">Edit</Button>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
