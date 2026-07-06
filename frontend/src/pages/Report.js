import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import { ShieldCheck, Hourglass, FileWarning } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { getReport, operatorAccept } from "@/lib/api";

export default function Report() {
  const [data, setData] = useState(null);
  const [operator, setOperator] = useState("");
  const [note, setNote] = useState("");
  const [accepting, setAccepting] = useState(false);

  const load = () => getReport().then(setData).catch(() => {});
  useEffect(() => { load(); }, []);

  const accepted = data?.state?.status === "ACCEPTED_WAIT";
  const locked = data?.state?.status === "LOCKED";

  const handleAccept = async () => {
    setAccepting(true);
    try {
      const res = await operatorAccept(operator || "Operator", note || null);
      toast.success(res.message);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Acceptance failed");
    } finally {
      setAccepting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-5">
      <div>
        <h2 className="font-heading text-2xl font-semibold tracking-tight">Phase 0 Completion Report</h2>
        <p className="text-sm text-muted-foreground mt-1">Review the report, then accept to freeze Phase 0 and enter WAIT mode.</p>
      </div>

      {accepted && (
        <div className="rounded-md border border-[hsl(var(--info))]/40 bg-[hsl(var(--info))]/8 p-4 flex gap-3" data-testid="wait-mode-panel">
          <Hourglass size={18} className="shrink-0 text-[hsl(var(--info))] mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-[hsl(var(--info))]">PHASE 0 ACCEPTED — SYSTEM IN WAIT MODE</p>
            <p className="text-xs text-muted-foreground mt-1">
              Accepted by <span className="font-mono">{data.state.accepted_by}</span> at{" "}
              <span className="font-mono">{new Date(data.state.accepted_at).toLocaleString()}</span>.
              {data.state.note && <> Note: {data.state.note}</>}
            </p>
            <p className="text-xs text-muted-foreground mt-1">No further phases are authorized until explicitly commanded.</p>
          </div>
        </div>
      )}

      {!data ? (
        <Skeleton className="h-[400px]" />
      ) : !data.report ? (
        <div className="rounded-md border border-border bg-card p-10 text-center">
          <FileWarning size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">Completion report not generated yet. Run the Source Lock from the Overview page.</p>
        </div>
      ) : (
        <>
          <div className="rounded-md border border-border bg-card p-6" data-testid="completion-report-viewer">
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.report.content}</ReactMarkdown>
            </div>
          </div>

          {!accepted && (
            <div className="rounded-md border border-border bg-card p-5 space-y-4" data-testid="operator-accept-panel">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-[hsl(var(--success))]" />
                <h3 className="text-sm font-heading font-semibold">Operator Acceptance</h3>
              </div>
              <p className="text-xs text-muted-foreground">
                Accepting freezes Phase 0 outputs. Further ingestion runs are blocked and the system enters WAIT mode.
              </p>
              <div className="grid sm:grid-cols-2 gap-3">
                <Input
                  placeholder="Operator name"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                  data-testid="operator-name-input"
                  className="h-9 text-sm"
                />
                <Textarea
                  placeholder="Acceptance note (optional)"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  data-testid="operator-note-input"
                  className="min-h-[36px] text-sm"
                  rows={1}
                />
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button disabled={!locked || accepting} data-testid="operator-accept-button" className="active:scale-[0.98]">
                    <ShieldCheck size={15} /> Accept Phase 0 &amp; Enter WAIT Mode
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent data-testid="operator-accept-confirm-dialog">
                  <AlertDialogHeader>
                    <AlertDialogTitle>Freeze Phase 0?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This records operator acceptance, freezes the Phase 0 Source Lock outputs, and puts the system
                      into WAIT mode. No further phases are authorized until explicitly commanded. Ingestion re-runs will be blocked.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel data-testid="operator-accept-cancel">Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleAccept} data-testid="operator-accept-confirm">
                      Accept &amp; Freeze
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
              {!locked && (
                <p className="text-[11px] text-[hsl(var(--warning))] font-mono">
                  Acceptance unavailable: source lock has not completed yet.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
