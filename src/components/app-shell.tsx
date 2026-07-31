import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard, Receipt, BarChart3, Target, TrendingUp, Newspaper, Settings,
  Sun, Moon, Search, Bell, Plus
} from "lucide-react";
import { useTheme } from "./theme-provider";
import { Button } from "./ui/button";
import type { ReactNode } from "react";

const NAV = [
  { to: "/",            label: "Dashboard",    icon: LayoutDashboard },
  { to: "/transactions",label: "Transactions", icon: Receipt },
  { to: "/analytics",   label: "Analytics",    icon: BarChart3 },
  { to: "/goals",       label: "Goals",        icon: Target },
  { to: "/investments", label: "Investments",  icon: TrendingUp },
  { to: "/news",        label: "News",         icon: Newspaper },
  { to: "/settings",    label: "Settings",     icon: Settings },
] as const;

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <div className="grid place-items-center size-9 rounded-xl text-primary-foreground"
           style={{ background: "var(--gradient-hero)", boxShadow: "var(--shadow-glow)" }}>
        <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 17l5-6 4 4 8-10" />
          <path d="M14 5h6v6" />
        </svg>
      </div>
      <div className="leading-tight">
        <div className="font-semibold tracking-tight">MoneyScope</div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Personal Finance</div>
      </div>
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { theme, toggle } = useTheme();
  const path = useRouterState({ select: s => s.location.pathname });

  return (
    <div className="min-h-screen flex">
      {/* Sidebar (desktop) */}
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-border/60 bg-card/30 backdrop-blur-xl px-4 py-6 sticky top-0 h-screen">
        <Logo />
        <nav className="mt-8 flex-1 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = to === "/" ? path === "/" : path.startsWith(to);
            return (
              <Link key={to} to={to}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition
                  ${active
                    ? "bg-primary/10 text-foreground font-medium shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--primary)_30%,transparent)]"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/40"}`}>
                <Icon className={`size-4 ${active ? "text-primary" : ""}`} />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="rounded-2xl p-4 border border-border/60 bg-gradient-to-br from-primary/10 to-transparent">
          <div className="text-xs text-muted-foreground">Pro tip</div>
          <div className="mt-1 text-sm leading-snug">Set a weekly cap on dining to save up to ₹4,200/month.</div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Topbar */}
        <header className="sticky top-0 z-30 backdrop-blur-xl bg-background/70 border-b border-border/60">
          <div className="flex items-center gap-3 px-4 md:px-8 h-16">
            <div className="md:hidden"><Logo /></div>
            <div className="hidden md:flex items-center gap-2 flex-1 max-w-md">
              <div className="flex items-center gap-2 w-full rounded-xl border border-border bg-card/60 px-3 py-2 text-sm text-muted-foreground">
                <Search className="size-4" />
                <span>Search transactions, merchants…</span>
                <kbd className="ml-auto text-[10px] border border-border rounded px-1.5 py-0.5">⌘K</kbd>
              </div>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Button size="icon" variant="ghost" onClick={toggle} aria-label="Toggle theme">
                {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
              </Button>
              <Button size="icon" variant="ghost" aria-label="Notifications" className="relative">
                <Bell className="size-4" />
                <span className="absolute top-2 right-2 size-1.5 rounded-full bg-primary" />
              </Button>
              <Button size="sm" className="gap-1.5 rounded-xl">
                <Plus className="size-4" /> Add
              </Button>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 md:px-8 py-6 pb-24 md:pb-10 animate-fade-in">{children}</main>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/85 backdrop-blur-xl">
          <div className="grid grid-cols-5 px-2 py-1.5">
            {[NAV[0], NAV[1], NAV[2], NAV[4], NAV[6]].map(({ to, label, icon: Icon }) => {
              const active = to === "/" ? path === "/" : path.startsWith(to);
              return (
                <Link key={to} to={to}
                  className={`flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[10px] ${active ? "text-primary" : "text-muted-foreground"}`}>
                  <Icon className="size-5" />
                  {label}
                </Link>
              );
            })}
          </div>
          <div className="pb-[env(safe-area-inset-bottom)]" />
        </nav>
      </div>
    </div>
  );
}
