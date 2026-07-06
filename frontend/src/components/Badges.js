const TIER_STYLES = {
  CONTROL_PACKET: "border-[hsl(var(--tier-control))]/30 bg-[hsl(var(--tier-control))]/12 text-[hsl(var(--tier-control))]",
  PRIMARY_ARCHITECTURE: "border-[hsl(var(--tier-primary))]/30 bg-[hsl(var(--tier-primary))]/12 text-[hsl(var(--tier-primary))]",
  PROCESS_RULES: "border-[hsl(var(--tier-process))]/30 bg-[hsl(var(--tier-process))]/12 text-[hsl(var(--tier-process))]",
  CONCEPT_ONLY: "border-[hsl(var(--tier-concept))]/30 bg-[hsl(var(--tier-concept))]/12 text-[hsl(var(--tier-concept))]",
  ARCHIVE_REFERENCE: "border-[hsl(var(--tier-archive))]/30 bg-[hsl(var(--tier-archive))]/12 text-[hsl(var(--tier-archive))]",
  UNLISTED: "border-[hsl(var(--tier-unlisted))]/30 bg-[hsl(var(--tier-unlisted))]/12 text-[hsl(var(--tier-unlisted))]",
};

const TIER_SHORT = {
  CONTROL_PACKET: "CONTROL",
  PRIMARY_ARCHITECTURE: "PRIMARY",
  PROCESS_RULES: "PROCESS",
  CONCEPT_ONLY: "CONCEPT",
  ARCHIVE_REFERENCE: "ARCHIVE",
  UNLISTED: "UNLISTED",
};

export const AuthorityTierBadge = ({ tier, full = false }) => {
  const cls = TIER_STYLES[tier] || TIER_STYLES.UNLISTED;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-mono font-medium whitespace-nowrap ${cls}`}
      data-testid="authority-tier-badge"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {full ? tier : TIER_SHORT[tier] || tier}
    </span>
  );
};

export const ParseStatusBadge = ({ status }) => {
  const map = {
    PARSED: "bg-[hsl(var(--success))]/12 text-[hsl(var(--success))] border-[hsl(var(--success))]/30",
    FAILED: "bg-[hsl(var(--danger))]/12 text-[hsl(var(--danger))] border-[hsl(var(--danger))]/30",
    SKIPPED: "bg-[hsl(var(--tier-archive))]/12 text-[hsl(var(--tier-archive))] border-[hsl(var(--tier-archive))]/30",
    PENDING: "bg-[hsl(var(--tier-archive))]/12 text-[hsl(var(--tier-archive))] border-[hsl(var(--tier-archive))]/30",
  };
  return (
    <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-mono ${map[status] || map.PENDING}`}>
      {status}
    </span>
  );
};

export const SeverityBadge = ({ severity }) => {
  const map = {
    HIGH: "bg-[hsl(var(--danger))]/12 text-[hsl(var(--danger))] border-[hsl(var(--danger))]/30",
    MEDIUM: "bg-[hsl(var(--warning))]/12 text-[hsl(var(--warning))] border-[hsl(var(--warning))]/30",
    LOW: "bg-[hsl(var(--info))]/12 text-[hsl(var(--info))] border-[hsl(var(--info))]/30",
  };
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-mono font-medium ${map[severity] || map.MEDIUM}`}>
      {severity}
    </span>
  );
};
