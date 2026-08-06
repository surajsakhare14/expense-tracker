import { createFileRoute } from "@tanstack/react-router";
import { Bell, Shield, Smartphone, CreditCard, Moon, Globe, Download } from "lucide-react";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { useTheme } from "../components/theme-provider";
import { APP_META, type UpiApp } from "../lib/finance-data";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — MoneyScope" }] }),
  component: Settings,
});

const APPS: UpiApp[] = ["GPay", "PhonePe", "Paytm", "BHIM", "CRED", "Amazon Pay"];

function Row({ icon, title, desc, action }: { icon: React.ReactNode; title: string; desc: string; action: React.ReactNode }) {
  return (
    <div className="flex items-center gap-4 py-4">
      <div className="size-10 rounded-xl bg-muted grid place-items-center">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-muted-foreground">{desc}</div>
      </div>
      {action}
    </div>
  );
}

function Settings() {
  const { theme, toggle } = useTheme();

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <header>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Tune MoneyScope to your habits.</p>
      </header>

      <section className="glass-card rounded-2xl p-5 relative overflow-hidden">
        <div className="absolute inset-0 opacity-50 pointer-events-none"
             style={{ background: "radial-gradient(500px 200px at 90% 0%, color-mix(in oklab, var(--primary) 22%, transparent), transparent 60%)" }} />
        <div className="relative flex items-center gap-4">
          <div className="size-14 rounded-2xl grid place-items-center text-xl font-semibold text-primary-foreground"
               style={{ background: "var(--gradient-hero)" }}>AS</div>
          <div className="flex-1">
            <div className="font-medium">Aarav Sharma</div>
            <div className="text-xs text-muted-foreground">aarav@moneyscope.app · Pro plan</div>
          </div>
          <Button variant="outline" className="rounded-xl">Edit</Button>
        </div>
      </section>

      <section className="glass-card rounded-2xl px-5 divide-y divide-border/60">
        <Row icon={<Moon className="size-4" />} title="Appearance" desc={`Currently ${theme}`} action={<Switch checked={theme === "dark"} onCheckedChange={toggle} />} />
        <Row icon={<Bell className="size-4" />} title="Overspending alerts" desc="Get a nudge at 80% budget use" action={<Switch defaultChecked />} />
        <Row icon={<CreditCard className="size-4" />} title="Bill reminders" desc="3 days before due date" action={<Switch defaultChecked />} />
        <Row icon={<Shield className="size-4" />} title="App lock" desc="Require Face ID / PIN on open" action={<Switch />} />
        <Row icon={<Globe className="size-4" />} title="Currency" desc="Indian Rupee · ₹" action={<Button variant="outline" size="sm" className="rounded-lg">INR</Button>} />
      </section>

      <section className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Smartphone className="size-4 text-muted-foreground" />
          <div className="text-sm font-medium">Linked UPI apps</div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {APPS.map(a => (
            <button key={a} className="flex items-center gap-2 rounded-xl border border-border bg-card/40 px-3 py-2.5 text-sm hover:bg-accent/40 transition">
              <span className="size-2.5 rounded-full" style={{ background: APP_META[a].color }} />
              <span className="flex-1 text-left">{a}</span>
              <span className="text-[10px] text-success">Linked</span>
            </button>
          ))}
        </div>
      </section>

      <section className="glass-card rounded-2xl p-5">
        <div className="text-sm font-medium">Install as an app</div>
        <p className="text-xs text-muted-foreground mt-1">
          Add MoneyScope to your home screen for a native-app experience and instant access to your finances.
        </p>
        <Button className="rounded-xl mt-3 gap-1.5"><Download className="size-4" /> Install MoneyScope</Button>
      </section>

      <div className="text-center text-[11px] text-muted-foreground py-4">
        MoneyScope · v1.0 · Made with care
      </div>
    </div>
  );
}
