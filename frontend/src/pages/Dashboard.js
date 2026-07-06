import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Play, RefreshCw, FileText, AlertTriangle, FileCheck2, Layers, Loader2, CheckCircle2, XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { getStatus, startIngest, getIngestStatus, getContradictions } from "@/lib/api";
import { AuthorityTierBadge, SeverityBadge } from "@/components/Badges";
import { Link } from "react-router-dom";

const STAGES = ["EXTRACTING", "ANALYZING", "CONTRADICTIONS", "ARTIFACTS", "COMPLETE"];
const STAGE_LABEL = {
  QUEUED: "Queued", EXTRACTING: "Extracting sources", ANALYZING: "Deep-read analysis",
  CONTRADICTIONS: "Contradiction pass", ARTIFACTS: "Generating artifacts",
  COMPLETE: "Complete", FAILED: "Failed", NEVER_RUN: "Never run",
};

export default function Dashboard() {
  const [status, setStatus] = useState(null);
  const [run, setRun] = useState(null);
  const [contradictions, setContradictions] = useState([]);
  const [starting, setStarting] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [s, r, c] = await Promise.all([getStatus(), getIngestStatus(), getContradictions()]);
      setStatus(s); setRun(r); setContradictions(c.contradictions.slice(0, 4));
    } catch (e) { /* silent */ }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  const running = run && !["COMPLETE", "FAILED", "NEVER_RUN"].includes(run.stage);
  const accepted = status?.state?.status === "ACCEPTED_WAIT";

  const handleIngest = async (force = false) => {
    setStarting(true);
    try {
      await startIngest(force);
      toast.success("Ingestion run started");
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to start run");
    } finally {
      setStarting(false);
    }
  };

  const analysisProgress = run?.to_analyze ? Math.round((run.analyzed / run.to_analyze) * 100) : 0;
  const stageIndex = STAGES.indexOf(run?.stage);

  const tierCounts = status?.tier_counts || {};

  if (!status) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-6">
      {/* Header row */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-semibold tracking-tight">Source Lock Overview</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {status.sources_total > 0
              ? `${status.sources_total} sources indexed · ${status.sources_parsed} parsed · ${status.contradictions_count} contradictions preserved · ${status.artifacts_count}/5 artifacts`
              : "No sources indexed yet. Run ingestion to perform the Phase 0 Source Lock."}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => handleIngest(false)}
            disabled={running || starting || accepted}
            data-testid="ingestion-run-trigger-button"
            className="active:scale-[0.98]"
          >
            {running ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
            {running ? "Run in progress" : status.sources_total > 0 ? "Re-run Source Lock" : "Run Source Lock"}
          </Button>
          {status.sources_total > 0 && !accepted && (
            <Button variant="secondary" onClick={() => handleIngest(true)} disabled={running || starting}
              data-testid="ingestion-force-button" title="Force full re-analysis of all sources">
              <RefreshCw size={14} /> Force
            </Button>
          )}
        </div>
      </div>

      {/* Pipeline panel */}
      <Card data-testid="ingestion-progress">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-heading flex items-center gap-2">
            <Layers size={15} className="text-[hsl(var(--tier-control))]" />
            Ingestion Pipeline
            {run?.stage === "COMPLETE" && <CheckCircle2 size={15} className="text-[hsl(var(--success))]" />}
            {run?.stage === "FAILED" && <XCircle size={15} className="text-[hsl(var(--danger))]" />}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            {STAGES.map((s, i) => {
              const active = run?.stage === s;
              const done = stageIndex > i || run?.stage === "COMPLETE";
              return (
                <div key={s} className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-mono ${
                    active ? "border-[hsl(var(--tier-control))]/50 bg-[hsl(var(--tier-control))]/10 text-[hsl(var(--tier-control))]"
                    : done ? "border-[hsl(var(--success))]/40 bg-[hsl(var(--success))]/8 text-[hsl(var(--success))]"
                    : "border-border text-muted-foreground"
                  }`}>
                    {active && <Loader2 size={10} className="animate-spin" />}
                    {done && !active && <CheckCircle2 size={10} />}
                    {STAGE_LABEL[s]}
                  </span>
                  {i < STAGES.length - 1 && <span className="text-border">→</span>}
                </div>
              );
            })}
          </div>
          {run?.stage === "ANALYZING" && run.to_analyze > 0 && (
            <div className="space-y-1.5">
              <Progress value={analysisProgress} className="h-1.5" />
              <p className="text-[11px] font-mono text-muted-foreground">{run.analyzed}/{run.to_analyze} sources analyzed</p>
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-2 font-mono" data-testid="ingestion-status-message">
            {run?.message || "No run executed yet."}
          </p>
        </CardContent>
      </Card>

      {/* Tier counts */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3" data-testid="tier-count-cards">
        {["CONTROL_PACKET", "PRIMARY_ARCHITECTURE", "PROCESS_RULES", "CONCEPT_ONLY", "ARCHIVE_REFERENCE", "UNLISTED"].map((tier) => (
          <Card key={tier} className="bg-card/70">
            <CardContent className="pt-4 pb-3 px-4">
              <div className="text-2xl font-heading font-semibold">{tierCounts[tier] || 0}</div>
              <div className="mt-1.5"><AuthorityTierBadge tier={tier} /></div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Two-column: contradictions + quick links */}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-heading flex items-center gap-2">
              <AlertTriangle size={15} className="text-[hsl(var(--warning))]" /> Recent Contradictions
            </CardTitle>
            <Link to="/contradictions" className="text-xs text-[hsl(var(--tier-control))] hover:underline" data-testid="dashboard-view-all-contradictions">
              View all ({status.contradictions_count})
            </Link>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {contradictions.length === 0 && (
              <p className="text-xs text-muted-foreground">No contradictions recorded yet. Run the source lock.</p>
            )}
            {contradictions.map((c) => (
              <div key={c.id} className="rounded-md border border-border bg-secondary/30 p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium truncate">{c.title}</span>
                  <SeverityBadge severity={c.severity} />
                </div>
                <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">{c.resolution}</p>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-heading flex items-center gap-2">
              <FileCheck2 size={15} className="text-[hsl(var(--success))]" /> Phase 0 Deliverables
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {["SOURCE_INDEX.md", "SOURCE_PRIORITY.md", "CONTRADICTIONS.md", "SCOPE_LOCK.md", "PHASE0_COMPLETION_REPORT.md"].map((n) => (
              <Link key={n} to={n === "PHASE0_COMPLETION_REPORT.md" ? "/report" : "/artifacts"}
                className="flex items-center justify-between rounded-md border border-border bg-secondary/30 px-3 py-2 hover:bg-secondary/60 transition-colors"
                data-testid={`deliverable-link-${n}`}>
                <span className="text-xs font-mono flex items-center gap-2"><FileText size={13} /> {n}</span>
                <span className={`text-[10px] font-mono ${status.artifacts_count >= 5 ? "text-[hsl(var(--success))]" : "text-muted-foreground"}`}>
                  {status.artifacts_count >= 5 ? "GENERATED" : "PENDING"}
                </span>
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}
