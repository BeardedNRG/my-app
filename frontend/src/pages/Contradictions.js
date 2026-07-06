import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Scale } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { getContradictions } from "@/lib/api";
import { SeverityBadge } from "@/components/Badges";

export default function Contradictions() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getContradictions().then(setData).catch(() => {});
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-5">
      <div>
        <h2 className="font-heading text-2xl font-semibold tracking-tight">Contradictions Register</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Contradictions are preserved, never silently resolved or deleted.
        </p>
      </div>

      <div className="rounded-md border border-[hsl(var(--tier-control))]/30 bg-[hsl(var(--tier-control))]/8 p-3.5 flex gap-2.5" data-testid="resolution-rule-panel">
        <Scale size={15} className="shrink-0 mt-0.5 text-[hsl(var(--tier-control))]" />
        <p className="text-xs leading-relaxed text-foreground/90">
          <span className="font-semibold font-mono">RESOLUTION RULE:</span>{" "}
          {data?.resolution_rule || "If any source conflicts with the current Master Build Law or the Phase 0-only restriction, the current Master Build Law wins."}
        </p>
      </div>

      {!data ? (
        <div className="space-y-3">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-28" />)}</div>
      ) : data.contradictions.length === 0 ? (
        <div className="rounded-md border border-border bg-card p-10 text-center">
          <AlertTriangle size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">No contradictions recorded yet. Run the Source Lock from the Overview page.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.contradictions.map((c, idx) => (
            <div key={c.id} className="rounded-md border border-border bg-card p-4" data-testid="contradiction-card">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs text-muted-foreground">{String(idx + 1).padStart(2, "0")}</span>
                  <h3 className="text-sm font-semibold">{c.title}</h3>
                </div>
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={c.severity} />
                  <span className="rounded-md border border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/12 px-2 py-0.5 text-[10px] font-mono font-medium text-[hsl(var(--warning))]">
                    {c.status}
                  </span>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-3 mb-3">
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] font-mono text-muted-foreground mb-1">CLAIM A</div>
                  <p className="text-xs leading-relaxed">{c.claim_a}</p>
                </div>
                <div className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="text-[10px] font-mono text-muted-foreground mb-1">CLAIM B</div>
                  <p className="text-xs leading-relaxed">{c.claim_b}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {c.sources_involved.map((s) => (
                  <span key={s} className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">{s}</span>
                ))}
              </div>
              <p className="text-xs text-[hsl(var(--success))] leading-relaxed">
                <span className="font-mono text-[10px] text-muted-foreground mr-1">RESOLUTION:</span>{c.resolution}
              </p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
