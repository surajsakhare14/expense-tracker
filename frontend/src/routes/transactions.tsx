import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search, Upload, Filter, Plus } from "lucide-react";
import { transactions, inr, CATEGORY_META, APP_META, type UpiApp } from "../lib/finance-data";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";

export const Route = createFileRoute("/transactions")({
  head: () => ({ meta: [{ title: "Transactions — MoneyScope" }] }),
  component: TransactionsPage,
});

const APPS: UpiApp[] = ["GPay", "PhonePe", "Paytm", "BHIM", "CRED", "Amazon Pay"];

function TransactionsPage() {
  const [q, setQ] = useState("");
  const [app, setApp] = useState<UpiApp | "All">("All");

  const filtered = useMemo(() => {
    return [...transactions]
      .sort((a,b) => +new Date(b.date) - +new Date(a.date))
      .filter(t => (app === "All" || t.app === app))
      .filter(t => !q || t.merchant.toLowerCase().includes(q.toLowerCase()) || t.category.toLowerCase().includes(q.toLowerCase()));
  }, [q, app]);

  // group by day
  const groups = useMemo(() => {
    const map = new Map<string, typeof transactions>();
    filtered.forEach(t => {
      const k = new Date(t.date).toLocaleDateString("en-IN", { weekday: "long", day: "2-digit", month: "long" });
      const arr = map.get(k) ?? [];
      arr.push(t);
      map.set(k, arr);
    });
    return Array.from(map.entries());
  }, [filtered]);

  const totalSpend = filtered.filter(t=>t.amount<0).reduce((s,t)=>s+ -t.amount, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Transactions</h1>
          <p className="text-sm text-muted-foreground">{filtered.length} entries · {inr(totalSpend)} spent</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="rounded-xl gap-1.5"><Upload className="size-4" /> Import CSV</Button>
          <Button className="rounded-xl gap-1.5"><Plus className="size-4" /> Add transaction</Button>
        </div>
      </header>

      <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input value={q} onChange={e => setQ(e.target.value)} placeholder="Search by merchant or category" className="pl-9 rounded-xl bg-background/40" />
        </div>
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          <Button
            onClick={() => setApp("All")}
            variant={app === "All" ? "default" : "outline"}
            size="sm"
            className="rounded-full"
          >
            <Filter className="size-3.5 mr-1" /> All apps
          </Button>
          {APPS.map(a => (
            <Button key={a}
              onClick={() => setApp(a)}
              variant={app === a ? "default" : "outline"}
              size="sm"
              className="rounded-full whitespace-nowrap">
              <span className="size-2 rounded-full mr-1.5" style={{ background: APP_META[a].color }} />
              {a}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-5">
        {groups.map(([day, items]) => {
          const total = items.filter(t => t.amount < 0).reduce((s,t)=>s+ -t.amount, 0);
          return (
            <section key={day} className="glass-card rounded-2xl p-4">
              <div className="flex items-center justify-between px-1 pb-2">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{day}</div>
                <div className="text-xs text-muted-foreground">{inr(total)}</div>
              </div>
              <ul className="divide-y divide-border/60">
                {items.map(t => (
                  <li key={t.id} className="flex items-center gap-3 py-3">
                    <div className="size-10 rounded-xl grid place-items-center bg-muted text-lg">{CATEGORY_META[t.category].emoji}</div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{t.merchant}</div>
                      <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 mt-0.5">
                        <span className="size-1.5 rounded-full" style={{ background: APP_META[t.app].color }} />
                        {t.app}
                        <span>·</span>
                        <Badge variant="secondary" className="rounded-full text-[10px] py-0 px-2 font-normal">{t.category}</Badge>
                        <span>·</span>
                        {new Date(t.date).toLocaleTimeString("en-IN",{ hour:"2-digit", minute:"2-digit" })}
                      </div>
                    </div>
                    <div className={`text-sm font-semibold tabular-nums ${t.amount > 0 ? "text-success" : ""}`}>
                      {t.amount < 0 ? "−" : "+"}{inr(Math.abs(t.amount))}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
