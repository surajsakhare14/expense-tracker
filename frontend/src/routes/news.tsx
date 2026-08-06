import { createFileRoute } from "@tanstack/react-router";
import { Flame, Clock } from "lucide-react";
import { newsItems } from "../lib/finance-data";
import { Badge } from "../components/ui/badge";

export const Route = createFileRoute("/news")({
  head: () => ({ meta: [{ title: "Financial News — MoneyScope" }] }),
  component: News,
});

function News() {
  const hot = newsItems.filter(n => n.hot);
  const rest = newsItems.filter(n => !n.hot);

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Daily financial news</h1>
        <p className="text-sm text-muted-foreground">Curated headlines that affect your money.</p>
      </header>

      <section className="grid md:grid-cols-2 gap-4">
        {hot.map(n => (
          <article key={n.id} className="glass-card rounded-2xl p-5 relative overflow-hidden hover:translate-y-[-2px] transition">
            <div className="absolute inset-0 opacity-60 pointer-events-none"
                 style={{ background: "radial-gradient(500px 200px at 100% 0%, color-mix(in oklab, var(--primary) 22%, transparent), transparent 60%)" }} />
            <div className="relative">
              <div className="flex items-center gap-2 text-xs">
                <Badge className="rounded-full bg-warning/15 text-warning border-warning/30">
                  <Flame className="size-3 mr-1" /> Trending
                </Badge>
                <span className="text-muted-foreground">{n.source} · {n.time} ago</span>
              </div>
              <h2 className="mt-3 text-lg font-semibold leading-tight">{n.title}</h2>
              <div className="mt-3 text-xs text-muted-foreground">Tag · {n.tag}</div>
            </div>
          </article>
        ))}
      </section>

      <section className="glass-card rounded-2xl p-2">
        <ul className="divide-y divide-border/60">
          {rest.map(n => (
            <li key={n.id} className="flex items-start gap-4 p-4 hover:bg-accent/30 rounded-xl transition cursor-pointer">
              <div className="size-10 shrink-0 rounded-xl grid place-items-center bg-muted">
                <Clock className="size-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium leading-snug">{n.title}</h3>
                <div className="mt-1 text-xs text-muted-foreground flex items-center gap-2">
                  <span>{n.source}</span><span>·</span><span>{n.time} ago</span>
                  <Badge variant="secondary" className="rounded-full text-[10px] py-0 px-2 font-normal ml-1">{n.tag}</Badge>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
