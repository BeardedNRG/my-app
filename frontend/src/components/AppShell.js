import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Shield, Lock, FileText, AlertTriangle, ListOrdered, FileCheck2,
  LayoutDashboard, Menu, Hourglass,
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { getStatus } from "@/lib/api";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, testid: "sidebar-nav-overview" },
  { to: "/sources", label: "Source Index", icon: FileText, testid: "sidebar-nav-source-index" },
  { to: "/contradictions", label: "Contradictions", icon: AlertTriangle, testid: "sidebar-nav-contradictions" },
  { to: "/priority", label: "Priority Order", icon: ListOrdered, testid: "sidebar-nav-priority" },
  { to: "/artifacts", label: "Artifacts", icon: FileCheck2, testid: "sidebar-nav-artifacts" },
  { to: "/report", label: "Completion Report", icon: Shield, testid: "sidebar-nav-report" },
];

const STATE_LABEL = {
  UNLOCKED: { text: "UNLOCKED", cls: "text-[hsl(var(--warning))] border-[hsl(var(--warning))]/40 bg-[hsl(var(--warning))]/10" },
  LOCKED: { text: "SOURCE LOCKED", cls: "text-[hsl(var(--success))] border-[hsl(var(--success))]/40 bg-[hsl(var(--success))]/10" },
  ACCEPTED_WAIT: { text: "WAIT MODE", cls: "text-[hsl(var(--info))] border-[hsl(var(--info))]/40 bg-[hsl(var(--info))]/10" },
};

function SidebarContent() {
  return (
    <div className="flex h-full flex-col">
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-[hsl(var(--tier-control))]/40 bg-[hsl(var(--tier-control))]/10">
            <Lock className="h-4.5 w-4.5 text-[hsl(var(--tier-control))]" size={18} />
          </div>
          <div>
            <div className="font-heading text-sm font-semibold leading-tight">NRG Agent OS</div>
            <div className="text-[11px] text-muted-foreground font-mono">PHASE 0 · SOURCE LOCK</div>
          </div>
        </div>
      </div>
      <Separator />
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV.map(({ to, label, icon: Icon, testid }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            data-testid={testid}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                isActive
                  ? "bg-secondary text-foreground font-medium"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 pb-5">
        <div className="rounded-md border border-border bg-secondary/40 p-3">
          <div className="text-[11px] font-mono text-muted-foreground leading-relaxed">
            Workspace root:<br />
            <span className="text-foreground/80 break-all">NRG_Agent_OS_Phase0_SourceLock</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export const AppShell = ({ children }) => {
  const [status, setStatus] = useState(null);
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    const load = () => getStatus().then((d) => mounted && setStatus(d)).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => { mounted = false; clearInterval(t); };
  }, [location.pathname]);

  const stateKey = status?.state?.status || "UNLOCKED";
  const badge = STATE_LABEL[stateKey] || STATE_LABEL.UNLOCKED;

  return (
    <div className="ops-shell min-h-screen bg-background">
      <div className="flex">
        <aside className="hidden lg:block w-[260px] shrink-0 border-r border-border bg-card/60 min-h-screen sticky top-0 h-screen">
          <SidebarContent />
        </aside>
        <div className="flex-1 min-w-0">
          <header
            className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur"
            data-testid="source-lock-status-header"
          >
            <div className="flex items-center justify-between px-4 sm:px-6 py-3">
              <div className="flex items-center gap-3">
                <Sheet>
                  <SheetTrigger asChild>
                    <Button variant="ghost" size="icon" className="lg:hidden" data-testid="mobile-menu-button" aria-label="Open menu">
                      <Menu size={18} />
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="left" className="w-[260px] p-0">
                    <SidebarContent />
                  </SheetContent>
                </Sheet>
                <h1 className="font-heading text-sm sm:text-base font-semibold tracking-tight">
                  Phase 0 Source Lock Console
                </h1>
              </div>
              <div className="flex items-center gap-2.5">
                {stateKey === "ACCEPTED_WAIT" && (
                  <span className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground" data-testid="wait-mode-indicator">
                    <Hourglass size={12} /> AWAITING COMMAND
                  </span>
                )}
                <span
                  className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[11px] font-mono font-medium ${badge.cls}`}
                  data-testid="lock-state-badge"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                  {badge.text}
                </span>
              </div>
            </div>
            <div
              className="flex items-start sm:items-center gap-2.5 border-t border-[hsl(var(--danger))]/30 bg-[hsl(0_62%_14%)] px-4 sm:px-6 py-2"
              data-testid="scope-lock-banner"
            >
              <AlertTriangle size={14} className="mt-0.5 sm:mt-0 shrink-0 text-[hsl(var(--danger))]" />
              <p className="text-[11px] sm:text-xs leading-snug text-foreground/90">
                <span className="font-semibold font-mono">SCOPE LOCK: PHASE 0 ONLY.</span>{" "}
                Forbidden build areas: Kernel · Memory · Router · Validation · Audit · Workers · Skills · Recovery · UI · Controlled Live Operation.
              </p>
            </div>
          </header>
          <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-[1400px]">{children}</main>
        </div>
      </div>
    </div>
  );
};
