import { createFileRoute } from "@tanstack/react-router";
import {
  BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";
import { getSummary, transactions, inr, inrShort, APP_META, CATEGORY_META, type UpiApp } from "../lib/finance-data";

export const Route = createFileRoute("/analytics")({
  head: () => ({ meta: [{ title: "Analytics — MoneyScope" }] }),
  component: Analytics,
});

function Analytics() {
  const s = getSummary();

  // App split this month
  const now = new Date();
  const byApp = new Map<UpiApp, number>();
  transactions.filter(t => t.amount < 0 && new Date(t.date).getMonth() === now.getMonth())
    .forEach(t => byApp.set(t.app, (byApp.get(t.app) ?? 0) + -t.amount));
  const appData = Array.from(byApp.entries()).map(([name, value]) => ({ name, value }));

  const util = Math.min((s.monthSpent / s.monthlyBudget) * 100, 120);

  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <header>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">Deep dive into your money flow.</p>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-5 lg:col-span-2">
          <div className="text-sm font-medium">Daily spend</div>
          <div className="text-xs text-muted-foreground mb-2">Last 14 days</div>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={s.trend} margin={{ top: 10, right: 10, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={1} />
                    <stop offset="100%" stopColor="var(--color-chart-2)" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => inrShort(v)} tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} axisLine={false} tickLine={false} width={50} />
                <Tooltip
                  cursor={{ fill: "color-mix(in oklab, var(--primary) 12%, transparent)" }}
                  contentStyle={{ background: "var(--color-popover)", border: "1px solid var(--color-border)", borderRadius: 12, fontSize: 12 }}
                  formatter={(v: number) => [inr(v), "Spent"]}
                />
                <Bar dataKey="spend" fill="url(#bar)" radius={[8,8,2,2]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="text-sm font-medium">Budget utilization</div>
          <div className="text-xs text-muted-foreground mb-2">Monthly</div>
          <div className="h-56">
            <ResponsiveContainer>
              <RadialBarChart innerRadius="68%" outerRadius="100%" data={[{ name: "u", value: util, fill: "var(--color-primary)" }]} startAngle={220} endAngle={-40}>
                <PolarAngleAxis type="number" domain={[0,100]} tick={false} />
                <RadialBar background={{ fill: "var(--color-muted)" }} dataKey="value" cornerRadius={20} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <div className="-mt-32 text-center pointer-events-none">
            <div className="text-3xl font-semibold tracking-tight">{Math.round(util)}%</div>
            <div className="text-[11px] text-muted-foreground">{inrShort(s.monthSpent)} / {inrShort(s.monthlyBudget)}</div>
          </div>
          <div className="mt-28 text-center text-xs text-muted-foreground">
            {util > 90 ? "Tight — slow down." : util > 70 ? "On track, watch dining." : "Comfortably within budget."}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card rounded-2xl p-5">
          <div className="text-sm font-medium">By category</div>
          <div className="text-xs text-muted-foreground mb-3">This month</div>
          <ul className="space-y-3">
            {s.categoryBreakdown.map(c => {
              const pct = (c.value / s.monthSpent) * 100;
              return (
                <li key={c.name}>
                  <div className="flex items-center text-sm">
                    <span className="mr-2">{CATEGORY_META[c.name as keyof typeof CATEGORY_META]?.emoji}</span>
                    <span className="flex-1 truncate">{c.name}</span>
                    <span className="tabular-nums">{inr(c.value)}</span>
                    <span className="ml-2 w-10 text-right text-xs text-muted-foreground tabular-nums">{pct.toFixed(0)}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: c.color }} />
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="text-sm font-medium">By UPI app</div>
          <div className="text-xs text-muted-foreground mb-3">Where your money flows out</div>
          <div className="grid grid-cols-2 gap-3">
            {appData.sort((a,b) => b.value - a.value).map(a => {
              const pct = (a.value / s.monthSpent) * 100;
              return (
                <div key={a.name} className="rounded-xl border border-border/60 p-3">
                  <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full" style={{ background: APP_META[a.name].color }} />
                    <span className="text-sm font-medium">{a.name}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{pct.toFixed(0)}%</span>
                  </div>
                  <div className="mt-2 text-lg font-semibold tabular-nums">{inr(a.value)}</div>
                  <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: APP_META[a.name].color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
