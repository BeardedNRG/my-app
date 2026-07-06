import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import { Download, FileText, FileWarning } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getArtifacts, getArtifact } from "@/lib/api";

const NAMES = ["SOURCE_INDEX.md", "SOURCE_PRIORITY.md", "CONTRADICTIONS.md", "SCOPE_LOCK.md", "PHASE0_COMPLETION_REPORT.md"];
const SHORT = { "SOURCE_INDEX.md": "Index", "SOURCE_PRIORITY.md": "Priority", "CONTRADICTIONS.md": "Contradictions", "SCOPE_LOCK.md": "Scope Lock", "PHASE0_COMPLETION_REPORT.md": "Report" };

export default function Artifacts() {
  const [available, setAvailable] = useState(null);
  const [active, setActive] = useState(NAMES[0]);
  const [artifact, setArtifact] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getArtifacts().then((d) => setAvailable(d.artifacts.map((a) => a.name))).catch(() => setAvailable([]));
  }, []);

  const loadArtifact = useCallback(async (name) => {
    setLoading(true);
    setArtifact(null);
    try {
      const d = await getArtifact(name);
      setArtifact(d);
    } catch {
      setArtifact(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (available?.includes(active)) loadArtifact(active);
  }, [active, available, loadArtifact]);

  const download = () => {
    if (!artifact) return;
    const blob = new Blob([artifact.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = artifact.name;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${artifact.name}`);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="font-heading text-2xl font-semibold tracking-tight">Phase 0 Artifacts</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Written only inside the approved workspace root: <span className="font-mono text-xs">NRG_Agent_OS_Phase0_SourceLock/</span>
          </p>
        </div>
        <Button variant="secondary" onClick={download} disabled={!artifact} data-testid="artifact-download-button">
          <Download size={14} /> Download
        </Button>
      </div>

      <Tabs value={active} onValueChange={setActive}>
        <TabsList className="flex-wrap h-auto">
          {NAMES.map((n) => (
            <TabsTrigger key={n} value={n} className="text-xs font-mono" data-testid={`artifact-tab-${n}`}>
              <FileText size={12} className="mr-1.5" />{SHORT[n]}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {available === null || loading ? (
        <Skeleton className="h-[400px]" />
      ) : !available.includes(active) || !artifact ? (
        <div className="rounded-md border border-border bg-card p-10 text-center">
          <FileWarning size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">Artifact not generated yet. Run the Source Lock from the Overview page.</p>
        </div>
      ) : (
        <div className="rounded-md border border-border bg-card p-6" data-testid="artifact-viewer">
          <div className="mb-4 flex items-center justify-between border-b border-border pb-3">
            <span className="font-mono text-xs text-muted-foreground">{artifact.path}</span>
            <span className="font-mono text-[10px] text-muted-foreground">generated {new Date(artifact.generated_at).toLocaleString()}</span>
          </div>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown>
          </div>
        </div>
      )}
    </motion.div>
  );
}
