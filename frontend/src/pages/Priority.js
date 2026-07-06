import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ListOrdered } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { getPriority } from "@/lib/api";
import { AuthorityTierBadge } from "@/components/Badges";

export default function Priority() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getPriority().then(setData).catch(() => {});
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-5">
      <div>
        <h2 className="font-heading text-2xl font-semibold tracking-tight">Source Priority Order</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Rank 1 is highest authority. If any source conflicts with the Master Build Law or the Phase 0-only restriction, the Master Build Law wins.
        </p>
      </div>

      {!data ? (
        <div className="space-y-3">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : (
        <div className="space-y-2.5" data-testid="priority-order-list">
          {data.priority_order.map((p) => (
            <div key={p.rank} className="rounded-md border border-border bg-card p-4">
              <div className="flex items-start gap-3.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[hsl(var(--tier-control))]/30 bg-[hsl(var(--tier-control))]/10 font-mono text-sm font-semibold text-[hsl(var(--tier-control))]">
                  {p.rank}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium leading-snug">{p.label}</p>
                  {p.members.length > 0 && (
                    <div className="mt-2.5 space-y-1.5">
                      {p.members.map((m) => (
                        <div key={m.filename} className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[11px] text-muted-foreground break-all">{m.filename}</span>
                          <AuthorityTierBadge tier={m.authority_tier} />
                          {m.feed_order && (
                            <span className="text-[10px] font-mono text-muted-foreground">feed {m.feed_order}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {data.unranked.length > 0 && (
            <div className="rounded-md border border-border bg-card p-4">
              <div className="flex items-start gap-3.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-secondary font-mono text-xs text-muted-foreground">
                  <ListOrdered size={14} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">Unranked (archive / do-not-feed-first / unlisted)</p>
                  <div className="mt-2.5 space-y-1.5">
                    {data.unranked.map((m) => (
                      <div key={m.filename} className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[11px] text-muted-foreground break-all">{m.filename}</span>
                        <AuthorityTierBadge tier={m.authority_tier} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
