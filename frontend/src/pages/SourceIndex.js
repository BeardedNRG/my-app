import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Search, Copy, ChevronRight, FileWarning } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { getSources, getSource } from "@/lib/api";
import { AuthorityTierBadge, ParseStatusBadge } from "@/components/Badges";

const TIERS = ["CONTROL_PACKET", "PRIMARY_ARCHITECTURE", "PROCESS_RULES", "CONCEPT_ONLY", "ARCHIVE_REFERENCE", "UNLISTED"];

export default function SourceIndex() {
  const [sources, setSources] = useState(null);
  const [search, setSearch] = useState("");
  const [tier, setTier] = useState("ALL");
  const [detail, setDetail] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const load = useCallback(async () => {
    const params = {};
    if (search) params.search = search;
    if (tier !== "ALL") params.tier = tier;
    const data = await getSources(params);
    setSources(data.sources);
  }, [search, tier]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  const openDetail = async (id) => {
    setDetailOpen(true);
    setLoadingDetail(true);
    try {
      const d = await getSource(id);
      setDetail(d);
    } catch (e) {
      toast.error("Failed to load source detail");
    } finally {
      setLoadingDetail(false);
    }
  };

  const copyHash = (hash) => {
    navigator.clipboard.writeText(hash);
    toast.success("Copied hash");
  };

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="font-heading text-2xl font-semibold tracking-tight">Source Index</h2>
          <p className="text-sm text-muted-foreground mt-1">Every source indexed, hashed, classified, and deep-read.</p>
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search filename or tag..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 w-[220px] h-9 text-sm"
              data-testid="source-index-search-input"
            />
          </div>
          <Select value={tier} onValueChange={setTier}>
            <SelectTrigger className="w-[180px] h-9 text-xs font-mono" data-testid="source-index-tier-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All tiers</SelectItem>
              {TIERS.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!sources ? (
        <div className="space-y-2">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
      ) : sources.length === 0 ? (
        <div className="rounded-md border border-border bg-card p-10 text-center">
          <FileWarning size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">
            {search || tier !== "ALL" ? "No sources match the current filter." : "No sources indexed yet. Run the Source Lock from the Overview page."}
          </p>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden">
          <Table data-testid="source-index-table">
            <TableHeader className="sticky top-0 bg-card z-10">
              <TableRow>
                <TableHead className="w-[38%]">File</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead className="text-center">Priority</TableHead>
                <TableHead className="hidden md:table-cell">Tags</TableHead>
                <TableHead className="hidden lg:table-cell">SHA256</TableHead>
                <TableHead className="hidden sm:table-cell text-right">Size</TableHead>
                <TableHead>Parse</TableHead>
                <TableHead className="w-8"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.map((s, i) => (
                <TableRow
                  key={s.source_id}
                  className={`cursor-pointer hover:bg-accent/10 transition-colors ${i % 2 === 1 ? "bg-muted/30" : ""}`}
                  onClick={() => openDetail(s.source_id)}
                  data-testid="source-row-open-detail"
                >
                  <TableCell className="font-mono text-xs max-w-[320px] truncate" title={s.filename}>{s.filename}</TableCell>
                  <TableCell><AuthorityTierBadge tier={s.authority_tier} /></TableCell>
                  <TableCell className="text-center font-mono text-xs">{s.priority_rank ?? "—"}</TableCell>
                  <TableCell className="hidden md:table-cell">
                    <div className="flex flex-wrap gap-1 max-w-[240px]">
                      {(s.tags || []).slice(0, 2).map((t) => (
                        <span key={t} className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">{t}</span>
                      ))}
                      {(s.tags || []).length > 2 && <span className="text-[10px] text-muted-foreground">+{s.tags.length - 2}</span>}
                    </div>
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <button
                      className="font-mono text-[11px] text-muted-foreground hover:text-foreground transition-colors"
                      onClick={(e) => { e.stopPropagation(); copyHash(s.sha256); }}
                      data-testid="source-copy-hash-button"
                      title="Copy full hash"
                    >
                      {s.sha256?.slice(0, 12)}… <Copy size={10} className="inline ml-0.5" />
                    </button>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-right font-mono text-[11px] text-muted-foreground">
                    {(s.size_bytes / 1024).toFixed(0)} KB
                  </TableCell>
                  <TableCell><ParseStatusBadge status={s.parse_status} /></TableCell>
                  <TableCell><ChevronRight size={14} className="text-muted-foreground" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent side="right" className="w-full sm:max-w-[620px] p-0" data-testid="source-detail-drawer">
          <ScrollArea className="h-full">
            <div className="p-6">
              {loadingDetail || !detail ? (
                <div className="space-y-3"><Skeleton className="h-6 w-3/4" /><Skeleton className="h-24" /><Skeleton className="h-40" /></div>
              ) : (
                <>
                  <SheetHeader className="mb-4">
                    <SheetTitle className="font-mono text-sm break-all text-left">{detail.filename}</SheetTitle>
                  </SheetHeader>
                  <div className="flex flex-wrap items-center gap-2 mb-4">
                    <AuthorityTierBadge tier={detail.authority_tier} full />
                    <ParseStatusBadge status={detail.parse_status} />
                    {detail.priority_rank && (
                      <span className="rounded-md border border-border px-2 py-0.5 text-[11px] font-mono text-muted-foreground">
                        PRIORITY {detail.priority_rank}{detail.feed_order ? ` · FEED ${detail.feed_order}` : ""}
                      </span>
                    )}
                  </div>
                  {!detail.listed && (
                    <div className="mb-4 rounded-md border border-[hsl(var(--warning))]/40 bg-[hsl(var(--warning))]/8 p-3">
                      <p className="text-xs text-[hsl(var(--warning))] font-medium">UNLISTED in operator handoff — requires operator classification.</p>
                      {detail.suggested_classification && (
                        <p className="text-[11px] text-muted-foreground mt-1">LLM-suggested tier: <span className="font-mono">{detail.suggested_classification}</span></p>
                      )}
                    </div>
                  )}
                  <div className="space-y-4 text-sm">
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="rounded-md border border-border bg-secondary/30 p-2.5">
                        <div className="text-muted-foreground text-[10px] font-mono mb-1">SHA256</div>
                        <button className="font-mono text-[10px] break-all text-left hover:text-[hsl(var(--tier-control))]" onClick={() => copyHash(detail.sha256)}>
                          {detail.sha256}
                        </button>
                      </div>
                      <div className="rounded-md border border-border bg-secondary/30 p-2.5">
                        <div className="text-muted-foreground text-[10px] font-mono mb-1">EXTRACTION</div>
                        <div className="font-mono text-[10px]">{detail.extraction_method} · {detail.text_chars?.toLocaleString()} chars · {(detail.size_bytes / 1024).toFixed(0)} KB</div>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xs font-mono text-muted-foreground mb-1.5">HANDOFF ROLE</h4>
                      <p className="text-xs text-muted-foreground leading-relaxed">{detail.handoff_role}</p>
                    </div>
                    {detail.summary && (
                      <div>
                        <h4 className="text-xs font-mono text-muted-foreground mb-1.5">DEEP-READ SUMMARY</h4>
                        <p className="text-xs leading-relaxed">{detail.summary}</p>
                      </div>
                    )}
                    {detail.key_claims?.length > 0 && (
                      <div>
                        <h4 className="text-xs font-mono text-muted-foreground mb-1.5">KEY CLAIMS</h4>
                        <ul className="space-y-1.5">
                          {detail.key_claims.map((c, i) => (
                            <li key={i} className="flex gap-2 text-xs leading-relaxed">
                              <span className="text-[hsl(var(--tier-control))] font-mono shrink-0">{String(i + 1).padStart(2, "0")}</span>
                              <span>{c}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {detail.build_relevance && (
                      <div>
                        <h4 className="text-xs font-mono text-muted-foreground mb-1.5">BUILD RELEVANCE</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">{detail.build_relevance}</p>
                      </div>
                    )}
                    <Collapsible>
                      <CollapsibleTrigger asChild>
                        <Button variant="secondary" size="sm" className="text-xs" data-testid="source-detail-show-text-button">
                          Show extracted text preview
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <pre className="mt-3 max-h-[400px] overflow-auto rounded-md border bg-secondary/40 p-3 text-[11px] leading-relaxed whitespace-pre-wrap">
                          {detail.text_preview || "(no text extracted)"}
                          {detail.text_truncated && "\n\n[... truncated preview ...]"}
                        </pre>
                      </CollapsibleContent>
                    </Collapsible>
                  </div>
                </>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </motion.div>
  );
}
