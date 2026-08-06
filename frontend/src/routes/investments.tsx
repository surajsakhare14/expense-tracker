import { createFileRoute } from "@tanstack/react-router";
import { ArrowDownRight, ArrowUpRight, Plus } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, LineChart, Line } from "recharts";
import { investments, inr, inrShort } from "../lib/finance-data";
import { Button } from "../components/ui/button";

export const Route = createFileRoute("/investments")({
  head: () => ({ meta: [{ title: "Investments — MoneyScope" }] }),
  component: Investments,
});

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)", "var(--primary)"];

// fake 12-month NAV trajectory for the portfolio
const portfolioSeries = Array.from({ length: 12 }, (_, i) => {
  const base = 280000;
  const drift = i * 4200;
  const noise = Math.sin(i * 0.9) * 6000;
  return { m: new Date(2025, i, 1).toLocaleString("en-IN", { month: "short" }), v: Math.round(base + drift + noise) };
});

function Investments() {
  const invested = investments.reduce((s,i) => s + i.invested, 0);
  const value = investments.reduce((s,i) => s + i.value, 0);
  const pl = value - invested;
  const plPct = (pl / invested) * 100;

  const byType = new Map<string, number>();
  investments.forEach(i => byType.set(i.type, (byType.get(i.type) ?? 0) + i.value));
  const allocation = Array.from(byType.entries()).map(([name, value]) => ({ name, value }));

  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Investments</h1>
          <p className="text-sm text-muted-foreground">Your portfolio at a glance.</p>
        </div>
        <Button className="rounded-xl gap-1.5"><Plus className="size-4" /> Add holding</Button>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-5 lg:col-span-2 relative overflow-hidden">
          <div className="absolute inset-0 opacity-50 pointer-events-none"
               style={{ background: "radial-gradient(700px 250px at 90% 0%, color-mix(in oklab, var(--chart-2) 22%, transparent), transparent 60%)" }} />
          <div className="relative flex flex-wrap items-end gap-8">
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Current value</div>
              <div className="text-4xl font-semibold tracking-tight mt-1">{inr(value)}</div>
              <div className={`mt-1 inline-flex items-center gap-1 text-sm ${pl >= 0 ? "text-success" : "text-destructive"}`}>
                {pl >= 0 ? <ArrowUpRight className="size-4" /> : <ArrowDownRight className="size-4" />}
                {pl >= 0 ? "+" : ""}{inr(pl)} ({plPct.toFixed(1)}%)
              </div>
            </div>
            <div className="text-sm text-muted-foreground">Invested <span className="text-foreground font-medium">{inr(invested)}</span></div>
          </div>
          <div className="h-44 mt-4 relative">
            <ResponsiveContainer>
              <LineChart data={portfolioSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <Tooltip
                  contentStyle={{ background: "var(--color-popover)", border: "1px solid var(--color-border)", borderRadius: 12, fontSize: 12 }}
                  formatter={(v: number) => [inr(v), "Value"]}
                />
                <Line type="monotone" dataKey="v" stroke="var(--color-primary)" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="text-sm font-medium">Allocation</div>
          <div className="text-xs text-muted-foreground">By asset type</div>
          <div className="h-44 mt-2">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={allocation} dataKey="value" innerRadius={48} outerRadius={70} paddingAngle={3} stroke="none">
                  {allocation.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "var(--color-popover)", border: "1px solid var(--color-border)", borderRadius: 12, fontSize: 12 }}
                  formatter={(v: number, _n, p: any) => [inr(v), p.payload.name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5">
            {allocation.map((a, i) => (
              <li key={a.name} className="flex items-center gap-2 text-xs">
                <span className="size-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="flex-1">{a.name}</span>
                <span className="text-muted-foreground">{inrShort(a.value)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="glass-card rounded-2xl p-5">
        <div className="text-sm font-medium mb-3">Holdings</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="py-2 pr-3 font-normal">Name</th>
                <th className="py-2 pr-3 font-normal">Type</th>
                <th className="py-2 pr-3 font-normal text-right">Invested</th>
                <th className="py-2 pr-3 font-normal text-right">Current</th>
                <th className="py-2 pr-3 font-normal text-right">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {investments.map(i => (
                <tr key={i.id} className="hover:bg-accent/30 transition">
                  <td className="py-3 pr-3 font-medium">{i.name}</td>
                  <td className="py-3 pr-3 text-muted-foreground">{i.type}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{inr(i.invested)}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{inr(i.value)}</td>
                  <td className={`py-3 pr-3 text-right tabular-nums font-medium ${i.change >= 0 ? "text-success" : "text-destructive"}`}>
                    {i.change >= 0 ? "+" : ""}{i.change.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
