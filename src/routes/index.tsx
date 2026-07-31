import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell,
} from "recharts";
import {
  Wallet, TrendingUp, PiggyBank, ShieldCheck, ArrowRight, Sparkles,
  AlertTriangle, Info, CheckCircle2,
} from "lucide-react";
import { StatCard } from "../components/stat-card";
import { getSummary, transactions, goals, inr, inrShort, alerts, CATEGORY_META } from "../lib/finance-data";
import { Progress } from "../components/ui/progress";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Dashboard — MoneyScope" }] }),
  component: Dashboard,
});

function Dashboard() {
  const s = getSummary();
  const recent = [...transactions].sort((a,b) => +new Date(b.date) - +new Date(a.date)).slice(0, 6);
  const utilization = Math.min((s.monthSpent / s.monthlyBudget) * 100, 100);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero */}
      <section className="glass-card rounded-3xl p-6 md:p-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-60 pointer-events-none"
             style={{ background: "radial-gradient(800px 300px at 90% 0%, color-mix(in oklab, var(--primary) 22%, transparent), transparent 60%)" }} />
        <div className="relative flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border border-border bg-card/60 text-muted-foreground">
              <Sparkles className="size-3 text-primary" /> AI insight ready
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-semibold tracking-tight">
              Good morning, <span className="text-gradient">Aarav</span>
            </h1>
            <p className="mt-1.5 text-muted-foreground text-sm md:text-base">
              You can safely spend <span className="text-foreground font-medium">{inr(s.safeToSpend)}</span> today and still hit your goals.
            </p>
          </div>
          <div className="flex items-center gap-6">
            <div>
              <div className="text-xs text-muted-foreground">Financial Health</div>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <div className="text-4xl font-semibold tracking-tight">{s.healthScore}</div>
                <div className="text-xs text-muted-foreground">/ 100</div>
              </div>
              <div className="mt-2 h-1.5 w-44 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full transition-all"
                     style={{ width: `${s.healthScore}%`, background: "var(--gradient-hero)" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Today spent"  value={inr(s.todaySpent)} delta="−12% vs avg" deltaTone="up"
          icon={<Wallet className="size-4" />} accent="color-mix(in oklab, var(--chart-1) 60%, transparent)" />
        <StatCard label="This month"   value={inrShort(s.monthSpent)} delta={`${Math.round(utilization)}% of budget`} deltaTone="neutral"
          icon={<PiggyBank className="size-4" />} accent="color-mix(in oklab, var(--chart-2) 60%, transparent)"
          sub={<span>· {inrShort(s.monthlyBudget)} cap</span>} />
        <StatCard label="Investments"  value={inrShort(s.invValue)} delta={`${s.invChangePct.toFixed(1)}%`} deltaTone={s.invChangePct >= 0 ? "up" : "down"}
          icon={<TrendingUp className="size-4" />} accent="color-mix(in oklab, var(--chart-4) 60%, transparent)" />
        <StatCard label="Safe to spend" value={inr(s.safeToSpend)} delta="daily" deltaTone="neutral"
          icon={<ShieldCheck className="size-4" />} accent="color-mix(in oklab, var(--chart-3) 60%, transparent)"
          sub={<span>· stay on track</span>} />
      </section>

      {/* Chart + Category */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-sm font-medium">Spending trend</div>
              <div className="text-xs text-muted-foreground">Last 14 days</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Total</div>
              <div className="text-sm font-medium">{inrShort(s.trend.reduce((a,b)=>a+b.spend,0))}</div>
            </div>
          </div>
          <div className="h-60">
            <ResponsiveContainer>
              <AreaChart data={s.trend} margin={{ top: 10, right: 10, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="spend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} axisLine={false} tickLine={false} interval={1} />
                <YAxis tickFormatter={(v) => inrShort(v)} tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} axisLine={false} tickLine={false} width={50} />
                <Tooltip
                  contentStyle={{ background: "var(--color-popover)", border: "1px solid var(--color-border)", borderRadius: 12, fontSize: 12 }}
                  labelStyle={{ color: "var(--color-muted-foreground)" }}
                  formatter={(v: number) => [inr(v), "Spent"]}
                />
                <Area type="monotone" dataKey="spend" stroke="var(--color-primary)" strokeWidth={2} fill="url(#spend)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium">Category breakdown</div>
            <div className="text-xs text-muted-foreground">This month</div>
          </div>
          <div className="h-44 -mt-2">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={s.categoryBreakdown} dataKey="value" innerRadius={48} outerRadius={70} paddingAngle={3} stroke="none">
                  {s.categoryBreakdown.map((c, i) => <Cell key={i} fill={c.color} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "var(--color-popover)", border: "1px solid var(--color-border)", borderRadius: 12, fontSize: 12 }}
                  formatter={(v: number, _n, p: any) => [inr(v), p.payload.name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-3 space-y-2">
            {s.categoryBreakdown.slice(0,4).map(c => (
              <li key={c.name} className="flex items-center gap-2 text-xs">
                <span className="size-2 rounded-full" style={{ background: c.color }} />
                <span className="flex-1 truncate">{CATEGORY_META[c.name as keyof typeof CATEGORY_META]?.emoji} {c.name}</span>
                <span className="text-muted-foreground">{inrShort(c.value)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Goals + Alerts */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-medium">Goals progress</div>
              <div className="text-xs text-muted-foreground">Track what you're saving toward</div>
            </div>
            <Link to="/goals" className="text-xs text-primary inline-flex items-center gap-1 hover:gap-1.5 transition-all">
              View all <ArrowRight className="size-3" />
            </Link>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {goals.slice(0,4).map(g => {
              const pct = Math.round((g.saved / g.target) * 100);
              return (
                <div key={g.id} className="rounded-xl border border-border/60 p-4 hover:bg-accent/30 transition">
                  <div className="flex items-center gap-2">
                    <div className="text-xl">{g.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{g.name}</div>
                      <div className="text-[11px] text-muted-foreground">by {g.deadline}</div>
                    </div>
                    <div className="text-xs font-medium">{pct}%</div>
                  </div>
                  <Progress value={pct} className="mt-3 h-1.5" />
                  <div className="mt-2 flex justify-between text-[11px] text-muted-foreground">
                    <span>{inrShort(g.saved)}</span><span>{inrShort(g.target)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="text-sm font-medium mb-3">Alerts</div>
          <div className="space-y-3">
            {alerts.map(a => {
              const Icon = a.type === "warning" ? AlertTriangle : a.type === "success" ? CheckCircle2 : Info;
              const tone = a.type === "warning" ? "text-warning" : a.type === "success" ? "text-success" : "text-primary";
              return (
                <div key={a.id} className="flex gap-3 rounded-xl border border-border/60 p-3">
                  <div className={`shrink-0 size-8 rounded-lg grid place-items-center bg-muted ${tone}`}>
                    <Icon className="size-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium leading-tight">{a.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{a.body}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Recent transactions */}
      <section className="glass-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-sm font-medium">Recent transactions</div>
            <div className="text-xs text-muted-foreground">Across all UPI apps</div>
          </div>
          <Link to="/transactions" className="text-xs text-primary inline-flex items-center gap-1 hover:gap-1.5 transition-all">
            View all <ArrowRight className="size-3" />
          </Link>
        </div>
        <ul className="divide-y divide-border/60">
          {recent.map(t => (
            <li key={t.id} className="flex items-center gap-3 py-3">
              <div className="size-9 rounded-xl grid place-items-center bg-muted text-base">
                {CATEGORY_META[t.category].emoji}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium truncate">{t.merchant}</div>
                <div className="text-[11px] text-muted-foreground">
                  {new Date(t.date).toLocaleString("en-IN", { day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit" })}
                  {" · "}{t.app}{" · "}{t.category}
                </div>
              </div>
              <div className={`text-sm font-medium tabular-nums ${t.amount < 0 ? "" : "text-success"}`}>
                {t.amount < 0 ? "−" : "+"}{inr(Math.abs(t.amount))}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
