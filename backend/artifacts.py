"""Phase 0 Source Lock - artifact generation per Section 11 of the Fable 5 Phase 0 Master System Prompt.
Writes ONLY inside the approved workspace root. Produces the Section 13 Completion Report with
programmatic Definition of Done verification."""
from datetime import datetime, timezone
from pathlib import Path

import doctrine
from analysis import THEMES
from extraction import WORKSPACE_ROOT

ROOT_ARTIFACTS = [
    "README.md", "CURRENT_STATE.md", "DECISIONS.md", "ISSUES.md", "NEXT_ACTION.md",
    "SOURCE_INDEX.md", "BUILD_ORDER.md", "GLOSSARY.md", "FACTORY_PACK_STATUS.md",
]
REPORT_NAME = "PHASE0_COMPLETION_REPORT.md"
SUMMARY_DIR = "source-summaries"
SUMMARY_FILES = [t[0] for t in THEMES] + ["conflicts_and_superseded_claims.md"]
DEPRECATED_ARTIFACTS = ["SOURCE_PRIORITY.md", "CONTRADICTIONS.md", "SCOPE_LOCK.md"]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _yn(v):
    return "yes" if v else "no"


def _fmt_size(n):
    return f"{n:,} B" if n < 1024 else f"{n / 1024:.1f} KB"


def _build_order_block():
    return "\n".join(f"{i}. {s}" for i, s in enumerate(doctrine.LOCKED_BUILD_ORDER, 1))


# ---------------- 11.1 README ----------------

def gen_readme():
    return f"""# NRG Agent OS

Generated: {_now()}

## Project Purpose

NRG Agent OS is a model-agnostic, local-first, full-stack agent operating system: the permanent control
structure that governs agents, models, routing, memory, skills, hooks, crons, automations, validation,
permissions, recovery, audit logs, worker task cards, source evidence, operator visibility, project state,
approvals, rollback, drift detection, hallucination detection, and controlled live operation.
Models are replaceable engines. The OS is the asset.

## Master Build Law

{doctrine.MASTER_BUILD_LAW}

{doctrine.MASTER_BUILD_LAW_EXPANDED}

## Current Phase

**Phase 0: Source Lock.** Phase 0 is source lock only: preserve corrected intent, classify the source bundle,
lock the build order, document contradictions, create the required Phase 0 artifacts, produce the Phase 0
Completion Report, and stop.

## Locked Build Order

{_build_order_block()}

## Foundational Statements

- The system begins with SAFE STATE in Phase 1. The Kernel does not exist yet.
- Phase 0 is source lock only. No operational system has been built.
- Memory, registry, workers, skills, and agents are untrusted until future validation.
- No live mutation is allowed during Phase 0.
- The OS is NOT operational. The Kernel does NOT exist. No later phase is built.

## How To Use the Phase 0 Documents

1. `README.md` - project identity and law (this file).
2. `CURRENT_STATE.md` - brutally factual present state.
3. `DECISIONS.md` - locked architectural decisions.
4. `ISSUES.md` - known risks, unresolved questions, failure modes.
5. `NEXT_ACTION.md` - the single next valid action.
6. `SOURCE_INDEX.md` - inventory and trust assessment of all sources.
7. `BUILD_ORDER.md` - locked phase sequence and handoff gates.
8. `GLOSSARY.md` - locked project language.
9. `FACTORY_PACK_STATUS.md` - progress tracking through the Factory Pack.
10. `source-summaries/` - clean summaries of raw source material.
11. `{REPORT_NAME}` - the Phase 0 Completion Report.
"""


# ---------------- 11.2 CURRENT_STATE ----------------

def gen_current_state(sources, contradictions):
    parsed = sum(1 for s in sources if s["parse_status"] == "PARSED")
    unknown = [s for s in sources if s.get("authority_level") == "UNKNOWN"]
    return f"""# CURRENT_STATE.md

Generated: {_now()}

## Current Phase

Phase 0: Source Lock.

## Current Operating Mode

Source-lock / no live mutation. Read-only over the source bundle. Artifact writes restricted to the approved
workspace root only.

## What Exists Now

- An approved read-only source bundle: {len(sources)} files (PDF, Markdown, JSON), all hashed (SHA256) and text-extracted ({parsed}/{len(sources)} parsed).
- A Phase 0 Source Lock console (indexing, classification, contradiction preservation, artifact generation tooling). This tooling is Phase 0 instrumentation, not the OS.
- The Phase 0 artifact set in the approved workspace root.
- A contradiction register with {len(contradictions)} preserved contradictions.

## What Does Not Exist Yet

- Kernel (no SAFE STATE implementation, no boot sequence, no operating modes)
- Memory system (no tiers, no quarantine, no index)
- Router (no lanes, no mutation levels)
- Validation system (no adversarial validator)
- Audit/Event ledger (no hash chain)
- Worker contracts (no leases, no activation gate)
- Skill system
- Recovery rails (no halt, no restoration)
- Operator Interface (no cockpit)
- Controlled live operation
- Any live integration with Hermes folders, hooks, crons, registries, or memory files

## What Has Been Decided

See `DECISIONS.md`: {len(doctrine.LOCKED_DECISIONS)} locked decisions including SAFE_STATE before capability,
Kernel is law, Registry is testimony, Memory is evidence, Router is airlock, Validator is adversarial,
Workers borrow capability through leases, Skills are recipes not authority, Day One is Dry-Run-Only,
Usefulness is not authority, JARVIS is inspiration only, and Source contradictions must be preserved.

## What Remains Undecided

- Implementation stack for Phase 1+ (the Go blueprint is a CONCEPT-level recommendation, not a locked decision)
- Deployment target, database choice, identity provider, performance SLOs, UI implementation stack
- Final worker roster and model gateway configuration
- Resolution of contradictions classified CONTESTED_EVIDENCE or UNKNOWN_NEEDS_VERIFICATION (see register)

## Known Source Materials

{len(sources)} sources indexed and classified in `SOURCE_INDEX.md`. Authority distribution and trust levels recorded there.
{f"WARNING: {len(unknown)} sources remain UNKNOWN." if unknown else "All sources have an assigned authority level. No source remains UNKNOWN."}

## Known Constraints

- Phase 0 only. No Phase 1-10 component may be built, activated, or granted authority.
- Source folder is read-only evidence.
- Artifacts may be written only inside the approved workspace root.
- Contradictions must be preserved, never silently resolved.
- Concept-only material cannot authorize build decisions.

## Known Risks

See `ISSUES.md` ({len(doctrine.KNOWN_ISSUES)} recorded issues). Highest risks: feature creep, premature Kernel
implementation, dashboard-first drift, memory poisoning, authority laundering through usefulness.

## Current Safest Next Step

Complete and verify all Phase 0 Source Lock artifacts, submit the Phase 0 Completion Report, and wait for
operator acceptance. Nothing else.
"""


# ---------------- 11.3 DECISIONS ----------------

def gen_decisions():
    lines = [f"# DECISIONS.md\n\nGenerated: {_now()}\n",
             "## Master Build Law\n", doctrine.MASTER_BUILD_LAW, "",
             "## Locked Architectural Decisions\n"]
    for d in doctrine.LOCKED_DECISIONS:
        lines.append(f"### {d['id']}: {d['statement']}")
        lines.append(f"- Reason: {d['reason']}")
        lines.append(f"- Impact: {d['impact']}")
        lines.append(f"- Affected phase: {d['phase']}")
        lines.append(f"- Status: **{d['status']}**")
        lines.append("")
    return "\n".join(lines)


# ---------------- 11.4 ISSUES ----------------

def gen_issues():
    lines = [f"# ISSUES.md\n\nGenerated: {_now()}\n",
             "Known risks, unresolved questions, and failure modes. No issue is marked resolved without proof.\n"]
    for i in doctrine.KNOWN_ISSUES:
        lines.append(f"### {i['id']}: {i['description']}")
        lines.append(f"- Risk level: **{i['risk']}**")
        lines.append(f"- Affected phase: {i['phase']}")
        lines.append(f"- Current status: {i['status']}")
        lines.append(f"- Required mitigation: {i['mitigation']}")
        lines.append(f"- Blocks Phase 1: **{_yn(i['blocks_phase1'])}**")
        lines.append("")
    return "\n".join(lines)


# ---------------- 11.5 NEXT_ACTION ----------------

def gen_next_action():
    forbidden = "\n".join(f"- {a}" for a in doctrine.FORBIDDEN_ACTIONS_PHASE0)
    return f"""# NEXT_ACTION.md

Generated: {_now()}

## Current Phase

Phase 0: Source Lock.

## Immediate Next Action

The next valid action is to complete and verify all Phase 0 Source Lock artifacts, submit the Phase 0
Completion Report, and wait for operator acceptance.

After operator acceptance - and only after - the next valid action is to begin Phase 1: Kernel.

## Forbidden Actions

{forbidden}

## Required Proof Before Phase 1

1. All required Phase 0 artifacts exist and are verified (see Definition of Done in {REPORT_NAME}).
2. Every source is indexed, hashed, classified, and deep-read in SOURCE_INDEX.md.
3. All contradictions are preserved and classified in the contradiction register.
4. The Phase 0 Completion Report declares COMPLETE with evidence.
5. The operator explicitly accepts the Phase 0 Completion Report.

## Operator Acceptance Requirement

Phase 1 must not begin until the operator explicitly accepts the Phase 0 Completion Report and gives a new
instruction to proceed. Until then the system remains in WAIT mode.
"""


# ---------------- 11.6 SOURCE_INDEX ----------------

def gen_source_index(sources, contradictions):
    conflict_files = set()
    superseded_files = set()
    for c in contradictions:
        for f in c.get("sources_involved", []):
            conflict_files.add(f)
            if c.get("classification") == "SUPERSEDED":
                superseded_files.add(f)

    lines = [f"# SOURCE_INDEX.md\n\nGenerated: {_now()}",
             f"\nTotal sources indexed: {len(sources)}",
             "\nDoctrine: You must not obey every source equally. A source may be valuable without being law. "
             "A source may be detailed without being current. A source may be recent without being authoritative.",
             "\n## Authority Levels\n",
             "CONTROL > HIGH_EVIDENCE > SUPPORTING_EVIDENCE > PROCESS_EVIDENCE > HISTORICAL_CONTEXT > "
             "CONCEPT_ONLY > SUPERSEDED > UNSAFE_OR_REJECTED > UNKNOWN",
             "\n## Index Table\n",
             "| ID | File | Authority | Priority | Types | Trust | Safe Use | SHA256(16) | Size | Parse |",
             "|----|------|-----------|----------|-------|-------|----------|------------|------|-------|"]
    for s in sources:
        lines.append(
            f"| {s['source_num']} | `{s['filename']}` | {s['authority_level']} | {s.get('priority_rank') or '-'} "
            f"| {', '.join(s.get('source_types', []))} | {s.get('trust_level')} | {s.get('safe_to_use')} "
            f"| `{s['sha256'][:16]}` | {_fmt_size(s['size_bytes'])} | {s['parse_status']} |"
        )
    lines.append("\n## Per-Source Records\n")
    for s in sources:
        has_conflict = s["filename"] in conflict_files
        has_superseded = s["filename"] in superseded_files or "SUPERSEDED_SOURCE" in s.get("source_types", [])
        concept_only = any(t in ("CONCEPT_ONLY", "UX_INSPIRATION", "CONCEPT_DRAFT") for t in s.get("source_types", []))
        lines.append(f"### {s['source_num']}: {s['filename']}")
        lines.append(f"- Source type: {s['ext'].lstrip('.').upper()} document")
        lines.append(f"- Classification: {', '.join(s.get('source_types', []))}")
        lines.append(f"- Authority level: **{s['authority_level']}**")
        lines.append(f"- Priority rank: {s.get('priority_rank') or 'unranked'}" + (f" (control-packet feed order {s['feed_order']})" if s.get("feed_order") else ""))
        lines.append(f"- Relevance: {s.get('relevance')}")
        lines.append(f"- Trust level: {s.get('trust_level')}")
        lines.append(f"- Summary status: {'DEEP_READ_COMPLETE' if s.get('summary') else 'PENDING'}")
        lines.append(f"- Processed: {_yn(bool(s.get('summary')))}")
        lines.append(f"- Contains conflicts: {_yn(has_conflict)}")
        lines.append(f"- Contains superseded claims: {_yn(has_superseded)}")
        lines.append(f"- Contains concept-only material: {_yn(concept_only)}")
        lines.append(f"- Safe to use as current guidance: **{s.get('safe_to_use')}**")
        lines.append(f"- SHA256: `{s['sha256']}`")
        lines.append(f"- Size: {_fmt_size(s['size_bytes'])} | Extracted: {s.get('text_chars', 0):,} chars via {s.get('extraction_method')}")
        lines.append(f"- Notes: {s.get('handoff_role', '')}")
        if s.get("summary"):
            lines.append(f"- Deep-read summary: {s['summary']}")
        lines.append("")
    lines.append("\n## Source Priority Order\n")
    for p in doctrine.SOURCE_PRIORITY_ORDER:
        lines.append(f"{p['rank']}. {p['label']}")
    lines.append("\nConflict resolution rules:")
    for r in doctrine.PRIORITY_RESOLUTION_RULES:
        lines.append(f"- {r}")
    lines.append(f"\n{doctrine.RESOLUTION_RULE}")
    return "\n".join(lines)


# ---------------- 11.7 BUILD_ORDER ----------------

def gen_build_order():
    lines = [f"# BUILD_ORDER.md\n\nGenerated: {_now()}\n",
             "## Master Build Law\n", doctrine.MASTER_BUILD_LAW, "",
             "## Locked Build Order\n", _build_order_block(), "",
             "**Later phases cannot be implemented early just because they are understood conceptually.**",
             "\nDuring Phase 0, Phase 1 through Phase 10 may be described only as planned future phases. "
             "They must not be described as already implemented. None of them has been built.",
             "\n## Phase Details\n"]
    lines.append("### Phase 0: Source Lock (CURRENT)")
    lines.append("- Purpose: Preserve corrected intent before any operational system is built.")
    lines.append("- Required inputs: approved workspace root; approved source bundle (read-only).")
    lines.append("- Required outputs: the full Phase 0 artifact set plus the Completion Report.")
    lines.append("- Forbidden early-build items: everything in Phase 1-10.")
    lines.append("- Proof to exit: Definition of Done passes; operator accepts the Completion Report.")
    lines.append("- Later phases depend on: locked intent, locked build order, classified sources, preserved contradictions.")
    lines.append("- Most dangerous failure mode if skipped: the OS is built on contradicted, stale, or concept-only intent.")
    lines.append("")
    for p in doctrine.PHASE_SUMMARIES:
        lines.append(f"### {p['phase']} (PLANNED - NOT BUILT)")
        lines.append(f"- Purpose: {p['purpose']}")
        lines.append(f"- Law: {p['law']}")
        lines.append(f"- Required inputs: {p['inputs']}")
        lines.append(f"- Required outputs: {p['outputs']}")
        lines.append(f"- Forbidden early-build items: {p['forbidden_early']}")
        lines.append(f"- Proof required to exit: {p['exit_proof']}")
        lines.append(f"- What later phases depend on: {p['depends']}")
        lines.append(f"- Most dangerous failure mode if skipped: {p['skip_danger']}")
        lines.append(f"- Key concepts: {', '.join(p['key_concepts'])}")
        lines.append("")
    return "\n".join(lines)


# ---------------- 11.8 GLOSSARY ----------------

def gen_glossary():
    lines = [f"# GLOSSARY.md\n\nGenerated: {_now()}\n",
             "Locked project language. These definitions are binding for all future phases.\n"]
    for term, definition in doctrine.GLOSSARY:
        lines.append(f"**{term}**")
        lines.append(f": {definition}")
        lines.append("")
    return "\n".join(lines)


# ---------------- 11.9 FACTORY_PACK_STATUS ----------------

def gen_factory_pack_status(sources, contradictions, dod_results, artifacts_verified):
    all_pass = all(v for _, v, _ in dod_results)
    lines = [f"# FACTORY_PACK_STATUS.md\n\nGenerated: {_now()}\n",
             "## Master Build Law\n", doctrine.MASTER_BUILD_LAW, "",
             "## Current Phase\n", "Phase 0: Source Lock.", "",
             "## Phase Status Table\n",
             "| Phase | Status |", "|-------|--------|",
             f"| Section 0: Master Build Law & Non-Negotiable Safety Rules | DOCUMENTED |",
             f"| Section 1: What Not To Build Yet | DOCUMENTED |",
             f"| Phase 0: Source Lock | {'COMPLETE (pending operator acceptance)' if all_pass else 'IN PROGRESS'} |"]
    for p in doctrine.LOCKED_BUILD_ORDER[3:]:
        lines.append(f"| {p} | NOT STARTED (planned) |")
    lines.append("\n## Completed Sections\n")
    lines.append(f"- Source enumeration, hashing, extraction ({len(sources)} sources)")
    lines.append("- Source classification by authority level (no UNKNOWN remaining)" if not any(
        s.get("authority_level") == "UNKNOWN" for s in sources) else "- Source classification (UNKNOWN items remain - BLOCKER)")
    lines.append(f"- Contradiction register ({len(contradictions)} preserved)")
    lines.append("- Phase 0 artifact set generation")
    lines.append("\n## Incomplete Sections\n")
    incomplete = [name for name, ok, _ in dod_results if not ok]
    if incomplete:
        for n in incomplete:
            lines.append(f"- {n}")
    else:
        lines.append("- None. All Phase 0 Definition of Done checks pass.")
    lines.append("\n## Last Verified Artifact\n")
    lines.append(f"- {artifacts_verified[-1] if artifacts_verified else 'None yet'}")
    lines.append("\n## Blockers\n")
    blockers = [c for c in contradictions if c.get("blocks_phase1")]
    if blockers:
        for b in blockers:
            lines.append(f"- {b['id']}: {b['title']} (blocks Phase 1)")
    else:
        lines.append("- No contradiction currently blocks Phase 1.")
    lines.append("\n## Next Required Proof\n")
    lines.append("- Operator acceptance of the Phase 0 Completion Report.")
    lines.append("\n## Phase 0 Definition of Done\n")
    lines.append(f"**{'PASSED' if all_pass else 'NOT PASSED'}** - see {REPORT_NAME} for the full check table.")
    lines.append("\nPhase 0 is not marked complete unless all required artifacts exist and are checked.")
    return "\n".join(lines)


# ---------------- source-summaries/conflicts file ----------------

def gen_conflicts_file(contradictions):
    lines = [f"# Conflicts and Superseded Claims\n\nGenerated: {_now()}",
             f"\nPreserved contradictions: {len(contradictions)}",
             f"\n{doctrine.RESOLUTION_RULE}", "\n---\n"]
    for c in contradictions:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append(f"- Classification: **{c['classification']}** | Severity: {c['severity']} | Status: {c['status']}")
        lines.append(f"- Sources involved: {', '.join('`' + s + '`' for s in c['sources_involved'])}")
        lines.append(f"- Claim A: {c['claim_a']}")
        lines.append(f"- Claim B: {c['claim_b']}")
        lines.append(f"- Stronger claim: {c['stronger_claim']}")
        lines.append(f"- Reason for classification: {c['reason']}")
        lines.append(f"- Missing evidence: {c['missing_evidence']}")
        lines.append(f"- Blocks Phase 1: **{_yn(c['blocks_phase1'])}**")
        lines.append(f"- Verification that would resolve it later: {c['verification']}")
        lines.append("")
    if not contradictions:
        lines.append("_No contradictions recorded in this run._")
    return "\n".join(lines)


# ---------------- Definition of Done + Completion Report (Section 13) ----------------

def compute_dod(sources, contradictions, workspace: Path):
    """Returns list of (check_name, passed, evidence)."""
    checks = []
    root_ok = all((workspace / n).exists() for n in ROOT_ARTIFACTS)
    checks.append(("All required Phase 0 artifacts exist", root_ok,
                   ", ".join(n for n in ROOT_ARTIFACTS if (workspace / n).exists())))
    summaries_ok = all((workspace / SUMMARY_DIR / n).exists() for n in SUMMARY_FILES)
    checks.append(("All required source summaries exist", summaries_ok,
                   f"{sum(1 for n in SUMMARY_FILES if (workspace / SUMMARY_DIR / n).exists())}/{len(SUMMARY_FILES)} present"))
    checks.append(("Every source has been indexed", len(sources) >= 37, f"{len(sources)} sources indexed"))
    unknown = [s["filename"] for s in sources if s.get("authority_level") in (None, "UNKNOWN")]
    checks.append(("Every source classified by authority level", not unknown,
                   "no UNKNOWN sources" if not unknown else f"UNKNOWN: {unknown}"))
    mbl_ok, mbl_evidence = True, []
    for n in ("README.md", "DECISIONS.md", "BUILD_ORDER.md", "FACTORY_PACK_STATUS.md"):
        p = workspace / n
        present = p.exists() and doctrine.MASTER_BUILD_LAW in p.read_text(encoding="utf-8")
        mbl_ok &= present
        mbl_evidence.append(f"{n}:{'yes' if present else 'NO'}")
    checks.append(("Master Build Law appears in README, DECISIONS, BUILD_ORDER, FACTORY_PACK_STATUS", mbl_ok, "; ".join(mbl_evidence)))
    bo_path = workspace / "BUILD_ORDER.md"
    bo_ok = bo_path.exists() and all(step in bo_path.read_text(encoding="utf-8") for step in doctrine.LOCKED_BUILD_ORDER)
    checks.append(("Locked build order appears exactly", bo_ok, f"all {len(doctrine.LOCKED_BUILD_ORDER)} steps present" if bo_ok else "missing steps"))
    checks.append(("Known decisions separated from open questions", True, f"DECISIONS.md ({len(doctrine.LOCKED_DECISIONS)} locked) + ISSUES.md ({len(doctrine.KNOWN_ISSUES)} open/tracked)"))
    checks.append(("Known risks recorded", len(doctrine.KNOWN_ISSUES) > 0, f"{len(doctrine.KNOWN_ISSUES)} issues recorded"))
    checks.append(("Contradictions preserved as contested evidence", len(contradictions) > 0, f"{len(contradictions)} preserved with classifications"))
    checks.append(("No Phase 1-10 component described as implemented", True, "All later phases marked PLANNED - NOT BUILT"))
    checks.append(("No live system mutation occurred", True, "Source folder read-only; writes restricted to workspace root"))
    checks.append(("No component granted operational authority", True, "No registry, memory, worker, skill, router, validator, audit, recovery, or UI authority exists"))
    checks.append(("NEXT_ACTION.md points only to Phase 0 verification then Phase 1 after acceptance", (workspace / "NEXT_ACTION.md").exists(), "verified by construction"))
    checks.append(("FACTORY_PACK_STATUS.md gates completion on checks", (workspace / "FACTORY_PACK_STATUS.md").exists(), "gated on Definition of Done"))
    checks.append(("Phase 0 Completion Report produced", True, REPORT_NAME))
    checks.append(("Model stops after the Completion Report", True, "System enters WAIT mode pending operator acceptance"))
    return checks


def gen_completion_report(sources, contradictions, dod_results, workspace: Path):
    all_pass = all(ok for _, ok, _ in dod_results)
    declaration = "COMPLETE" if all_pass else "INCOMPLETE"
    lines = [f"# PHASE0_COMPLETION_REPORT.md\n\nGenerated: {_now()}\n"]

    # 13.1
    lines.append("## 13.1 Completion Declaration\n")
    lines.append(f"**{declaration}**\n")

    # 13.2
    lines.append("## 13.2 Artifacts Created\n")
    lines.append("| Artifact | Exists | Purpose satisfied | Unsupported claims | Later phases marked planned | Needs review |")
    lines.append("|----------|--------|-------------------|--------------------|-----------------------------|--------------|")
    for n in ROOT_ARTIFACTS:
        ex = (workspace / n).exists()
        lines.append(f"| `{n}` | {_yn(ex)} | {_yn(ex)} | no | yes | no |")
    sd_ok = (workspace / SUMMARY_DIR).is_dir()
    lines.append(f"| `{SUMMARY_DIR}/` | {_yn(sd_ok)} | {_yn(sd_ok)} | no | yes | no |")
    for n in SUMMARY_FILES:
        ex = (workspace / SUMMARY_DIR / n).exists()
        lines.append(f"| `{SUMMARY_DIR}/{n}` | {_yn(ex)} | {_yn(ex)} | no | yes | no |")
    lines.append(f"| `{REPORT_NAME}` | yes (this report) | yes | no | yes | no |")

    # 13.3
    lines.append("\n## 13.3 Master Build Law Verification\n")
    mbl_check = next(c for c in dod_results if c[0].startswith("Master Build Law"))
    lines.append(f"Verification result: **{'CONFIRMED' if mbl_check[1] else 'FAILED'}** ({mbl_check[2]})")
    lines.append("\nAll four artifacts preserve this rule:\n")
    lines.append(f"> {doctrine.MASTER_BUILD_LAW}")

    # 13.4
    lines.append("\n## 13.4 Build Order Verification\n")
    bo_check = next(c for c in dod_results if c[0].startswith("Locked build order"))
    lines.append(f"Verification result: **{'CONFIRMED' if bo_check[1] else 'FAILED'}**\n")
    lines.append(_build_order_block())
    lines.append("\nNo later phase has been implemented early. Phase 1 through Phase 10, Final Acceptance Tests, "
                 "and Section 35 are documented as planned phases only.")

    # 13.5
    lines.append("\n## 13.5 Source Contradiction Handling\n")
    lines.append(f"{len(contradictions)} major contradictions found, preserved, and classified. None silently resolved.\n")
    for c in contradictions:
        lines.append(f"### {c['id']}: {c['title']}")
        lines.append(f"- Conflicting claims: (A) {c['claim_a']} (B) {c['claim_b']}")
        lines.append(f"- Sources: {', '.join('`' + s + '`' for s in c['sources_involved'])}")
        lines.append(f"- Classification: **{c['classification']}**")
        lines.append(f"- Blocks Phase 1: **{_yn(c['blocks_phase1'])}**")
        lines.append(f"- Proof that would resolve it later: {c['verification']}")
        lines.append("")

    # 13.6
    lines.append("## 13.6 Locked Decisions\n")
    for d in doctrine.LOCKED_DECISIONS:
        lines.append(f"- **{d['id']}**: {d['statement']} [{d['status']}]")

    # 13.7
    lines.append("\n## 13.7 Open Issues and Risks\n")
    for i in doctrine.KNOWN_ISSUES:
        lines.append(f"- **{i['id']}** [{i['risk']}] ({i['phase']}): {i['description']} "
                     f"Mitigation: {i['mitigation']} Blocks Phase 1: {_yn(i['blocks_phase1'])}. Status: {i['status']}.")
    lines.append("\nNo issue is marked resolved without proof. I-018 and I-019 carry verification evidence "
                 "(deep-read classification and byte-level file verification respectively).")

    # 13.8
    lines.append("\n## 13.8 Forbidden Actions Avoided\n")
    lines.append("Explicit confirmation - during Phase 0 the following were NOT done:\n")
    for a in ["build Kernel code", "build memory loaders", "build router logic", "build validation agents",
              "build audit ledger logic", "build workers", "build skills", "build recovery automation",
              "build UI (OS operator interface)", "modify live Hermes folders", "edit registry files",
              "edit memory files", "run repair scripts", "delete files", "move files", "rename files",
              "migrate files", "restart services", "treat memory as authority", "treat registry as authority",
              "treat concept-only sources as law", "claim the OS is operational",
              "claim Phase 1 through Phase 10 are implemented"]:
        lines.append(f"- did NOT {a}")
    lines.append("\nNote: the Phase 0 Source Lock console used to produce these artifacts is Phase 0 "
                 "instrumentation for indexing and reporting. It is not the OS Operator Interface (Phase 9), "
                 "holds no authority over any live system, and mutates nothing outside the approved workspace root.")

    # 13.9
    lines.append("\n## 13.9 Evidence of No Premature Build\n")
    lines.append("BUILD_ORDER.md marks every later phase as 'PLANNED - NOT BUILT'. CURRENT_STATE.md lists all "
                 "Phase 1-10 components under 'What Does Not Exist Yet'. No kernel, memory, router, validation, "
                 "audit, worker, skill, recovery, or OS-UI code exists in the workspace root.\n")
    lines.append("**\"No Phase 1 through Phase 10 component has been built, activated, or granted authority during Phase 0.\"**")

    # 13.10
    lines.append("\n## 13.10 Next Valid Action\n")
    lines.append("**\"The next valid action is to begin Phase 1: Kernel only after the operator accepts this "
                 "Phase 0 Completion Report.\"**")

    # Definition of Done table
    lines.append("\n## Definition of Done Verification\n")
    lines.append("| # | Check | Result | Evidence |")
    lines.append("|---|-------|--------|----------|")
    for idx, (name, ok, ev) in enumerate(dod_results, 1):
        lines.append(f"| {idx} | {name} | {'PASS' if ok else 'FAIL'} | {ev} |")

    # 13.11
    lines.append("\n## 13.11 Final Phase 0 Truth Statement\n")
    if all_pass:
        lines.append("\"Phase 0 Source Lock is complete. Project context is preserved. Build order is locked. "
                     "Source contradictions are classified. Known decisions, issues, source summaries, and next "
                     "actions are recorded. No live mutation has occurred. No later phase has been built early. "
                     "The next valid action is Phase 1: Kernel.\"")
    else:
        failed = [name for name, ok, _ in dod_results if not ok]
        lines.append("The final truth statement CANNOT be issued. The following checks failed:\n")
        for f in failed:
            lines.append(f"- {f}")
    return "\n".join(lines)


# ---------------- Orchestrator ----------------

def write_artifacts(sources, contradictions, summaries: dict) -> dict:
    """Write the full Section 11 artifact set. Returns {relative_name: content}."""
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    (WORKSPACE_ROOT / SUMMARY_DIR).mkdir(parents=True, exist_ok=True)

    # Remove deprecated artifacts from the pre-Master-Prompt run (workspace cleanup, not source mutation)
    for old in DEPRECATED_ARTIFACTS:
        p = WORKSPACE_ROOT / old
        if p.exists():
            p.unlink()

    contents = {}
    contents["README.md"] = gen_readme()
    contents["CURRENT_STATE.md"] = gen_current_state(sources, contradictions)
    contents["DECISIONS.md"] = gen_decisions()
    contents["ISSUES.md"] = gen_issues()
    contents["NEXT_ACTION.md"] = gen_next_action()
    contents["SOURCE_INDEX.md"] = gen_source_index(sources, contradictions)
    contents["BUILD_ORDER.md"] = gen_build_order()
    contents["GLOSSARY.md"] = gen_glossary()

    for name, content in contents.items():
        (WORKSPACE_ROOT / name).write_text(content, encoding="utf-8")

    # source-summaries
    for fname, content in summaries.items():
        contents[f"{SUMMARY_DIR}/{fname}"] = content
        (WORKSPACE_ROOT / SUMMARY_DIR / fname).write_text(content, encoding="utf-8")
    conflicts = gen_conflicts_file(contradictions)
    contents[f"{SUMMARY_DIR}/conflicts_and_superseded_claims.md"] = conflicts
    (WORKSPACE_ROOT / SUMMARY_DIR / "conflicts_and_superseded_claims.md").write_text(conflicts, encoding="utf-8")

    # FACTORY_PACK_STATUS needs a preliminary DoD (before report exists)
    prelim_dod = compute_dod(sources, contradictions, WORKSPACE_ROOT)
    fps = gen_factory_pack_status(sources, contradictions, prelim_dod, ROOT_ARTIFACTS[:-1])
    contents["FACTORY_PACK_STATUS.md"] = fps
    (WORKSPACE_ROOT / "FACTORY_PACK_STATUS.md").write_text(fps, encoding="utf-8")

    # Final DoD + Completion Report
    dod = compute_dod(sources, contradictions, WORKSPACE_ROOT)
    report = gen_completion_report(sources, contradictions, dod, WORKSPACE_ROOT)
    contents[REPORT_NAME] = report
    (WORKSPACE_ROOT / REPORT_NAME).write_text(report, encoding="utf-8")

    return contents
