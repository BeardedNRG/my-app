"""
Phase 0 Source Lock - Classification doctrine per the Fable 5 Phase 0 Master System Prompt.
Deterministic filename -> classification / authority level / trust level / priority mapping.

Doctrine: You must not obey every source equally. Classify, preserve, and constrain.
A source may be valuable without being law. A source may be detailed without being current.
A source may be recent without being authoritative.
"""

# Authority levels (Section 11.6)
AUTH_CONTROL = "CONTROL"
AUTH_HIGH = "HIGH_EVIDENCE"
AUTH_SUPPORTING = "SUPPORTING_EVIDENCE"
AUTH_PROCESS = "PROCESS_EVIDENCE"
AUTH_HISTORICAL = "HISTORICAL_CONTEXT"
AUTH_CONCEPT = "CONCEPT_ONLY"
AUTH_SUPERSEDED = "SUPERSEDED"
AUTH_UNSAFE = "UNSAFE_OR_REJECTED"
AUTH_UNKNOWN = "UNKNOWN"

AUTHORITY_LEVELS = [AUTH_CONTROL, AUTH_HIGH, AUTH_SUPPORTING, AUTH_PROCESS,
                    AUTH_HISTORICAL, AUTH_CONCEPT, AUTH_SUPERSEDED, AUTH_UNSAFE, AUTH_UNKNOWN]

SOURCE_TYPE_TAGS = [
    "CONTROL_DOCUMENT", "LOCKED_INTENT_SOURCE", "PRIMARY_ARCHITECTURE_SOURCE", "SOURCE_PROCESSING_RULES",
    "SOURCE_EVIDENCE", "PACKAGING_GUIDANCE", "BEHAVIOURAL_ANALYSIS", "STRATEGY_DRAFT", "CONCEPT_DRAFT",
    "HISTORICAL_CONTEXT", "CONCEPT_ONLY", "UX_INSPIRATION", "PROCESS_CORRECTION", "DUPLICATE_REFERENCE",
    "SUPERSEDED_SOURCE", "UNSAFE_OR_REJECTED_SOURCE", "UNKNOWN_NEEDS_REVIEW",
]

TRUST_BY_AUTHORITY = {
    AUTH_CONTROL: "TRUSTED",
    AUTH_HIGH: "TRUSTED",
    AUTH_SUPPORTING: "TRUSTED_LIMITED",
    AUTH_PROCESS: "TRUSTED_LIMITED",
    AUTH_HISTORICAL: "CONTEXT_ONLY",
    AUTH_CONCEPT: "INSPIRATION_ONLY",
    AUTH_SUPERSEDED: "CONTEXT_ONLY",
    AUTH_UNSAFE: "REJECTED",
    AUTH_UNKNOWN: "UNVERIFIED",
}

SAFE_USE_BY_AUTHORITY = {
    AUTH_CONTROL: "yes",
    AUTH_HIGH: "yes",
    AUTH_SUPPORTING: "limited",
    AUTH_PROCESS: "limited",
    AUTH_HISTORICAL: "limited",
    AUTH_CONCEPT: "limited",
    AUTH_SUPERSEDED: "no",
    AUTH_UNSAFE: "no",
    AUTH_UNKNOWN: "no",
}

# Exact filename -> classification map.
# priority_rank refers to the 15-level Source Priority Order in doctrine.SOURCE_PRIORITY_ORDER.
# feed_order = position in the operator's feed-first control packet (1-9), where applicable.
CLASSIFICATION_MAP = {
    # ---- Phase 0 Source Lock control files (rank 3) ----
    "NRG-Agent-OS - Fable-5 Master Intake Pack - Copy 01.md": {
        "types": ["CONTROL_DOCUMENT", "LOCKED_INTENT_SOURCE"], "authority": AUTH_CONTROL,
        "priority_rank": 3, "feed_order": 1, "relevance": "CRITICAL",
        "role": "Master intake pack: assigns Fable 5 as architect and quality gate; defines role split, safety constraints, build sequence. Current control prompt within the bundle.",
    },
    "NRG-Agent-OS - Phase 0 System State - Source Lock - Copy 01.md": {
        "types": ["CONTROL_DOCUMENT"], "authority": AUTH_CONTROL,
        "priority_rank": 3, "feed_order": 2, "relevance": "CRITICAL",
        "role": "Declares the current system state: Phase 0 Source Lock.",
    },
    "NRG-Agent-OS - Worker Task Card Template - Minimal Verification Gate.md": {
        "types": ["CONTROL_DOCUMENT"], "authority": AUTH_CONTROL,
        "priority_rank": 3, "feed_order": 9, "relevance": "HIGH",
        "role": "Worker boundary template with minimal verification gate. Defines the bounded task-card executor pattern. "
                "VERIFIED: 495 bytes of complete, valid template content (task card ID, target model, allowed scope, "
                "forbidden actions, verification requirement). The '0 KB' display was a console rounding defect, now fixed. "
                "NOT empty, NOT EMPTY_OR_INVALID. SHA256 prefix cd0f798da6c74cf9.",
    },
    # ---- Project Manifest (rank 4) ----
    "NRG-Agent-OS - Project Manifest.md": {
        "types": ["CONTROL_DOCUMENT"], "authority": AUTH_CONTROL,
        "priority_rank": 4, "feed_order": 3, "relevance": "CRITICAL",
        "role": "Project manifest: core objective, system paradigm (the OS is the asset), eight structural layers.",
    },
    # ---- Complete Build Architecture Archive (rank 5) ----
    "NRG_Agent_OS_Complete_Build_Architecture_Archive.md": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "LOCKED_INTENT_SOURCE"], "authority": AUTH_HIGH,
        "priority_rank": 5, "feed_order": 4, "relevance": "CRITICAL",
        "role": "Consolidated build architecture archive - the stronger active source for architecture detail.",
    },
    # ---- End Of Source Conversation (rank 6) ----
    "End Of Source Conversation.pdf": {
        "types": ["LOCKED_INTENT_SOURCE", "PROCESS_CORRECTION"], "authority": AUTH_HIGH,
        "priority_rank": 6, "feed_order": 6, "relevance": "CRITICAL",
        "role": "Final corrected intent. Marks the end of source intake. Later corrections supersede earlier drafts.",
    },
    # ---- Source Intake Prompt (rank 7) ----
    "NRG Agent OS Source Intake Prompt.pdf": {
        "types": ["SOURCE_PROCESSING_RULES"], "authority": AUTH_PROCESS,
        "priority_rank": 7, "feed_order": 5, "relevance": "HIGH",
        "role": "Source-reading rules: preserve latest corrected intent; do not treat early drafts as final; do not mix intake and processing.",
    },
    # ---- Dashboard Information Pack Assessment (rank 8) ----
    "NRG Agent OS Dashboard Information Pack Assessment.pdf": {
        "types": ["SOURCE_EVIDENCE", "BEHAVIOURAL_ANALYSIS"], "authority": AUTH_SUPPORTING,
        "priority_rank": 8, "feed_order": 7, "relevance": "HIGH",
        "role": "External assessment: the pack is architecturally strong but not yet an executable system baseline. Assessment is evidence, not law.",
    },
    # ---- Factory Pack (rank 9) ----
    "NRG Agent OS Factory Pack.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE"], "authority": AUTH_HIGH,
        "priority_rank": 9, "feed_order": 8, "relevance": "CRITICAL",
        "role": "Original factory pack: defines the OS as a full-stack control system rather than Hermes, Fable, Ornith, JARVIS, or a neon dashboard.",
    },
    # ---- Primary architecture drafts (rank 10) ----
    "Architecting the NRG Agent OS - Google Gemini.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "STRATEGY_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "Architecture dialogue: kernel, registry validation, memory, router, validation, audit, workers, skills, recovery, UI, Day One, final tests.",
    },
    "Boot Sequence Design.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "Boot sequence design reference for the future Kernel phase.",
    },
    "Fable 5 OS Design Blueprint - Google Gemini.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "STRATEGY_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "OS design blueprint dialogue.",
    },
    "NRG-Agent-OS - Fable-5 Master OS Architecture Intake.md": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "Master OS architecture intake document (earlier intake variant).",
    },
    "NRG-Agent-OS - Agent Rules - XML Behavioral Framework.md": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "XML behavioral rules framework for agents.",
    },
    "NRG-Agent-OS - Skill - fable.forensic-methodology.md": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "Forensic methodology skill definition (recipe pattern; carries no authority).",
    },
    "deep-research-report.md": {
        "types": ["SOURCE_EVIDENCE", "STRATEGY_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "Deep research report supporting architecture decisions.",
    },
    "DISTILL 7 FOLD!.md": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "STRATEGY_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "Seven-fold distillation of doctrine.",
    },
    "concept designs - NRG Agent OS Overview.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "CONCEPT_DRAFT"], "authority": AUTH_HIGH,
        "priority_rank": 10, "relevance": "CRITICAL",
        "role": "Repeats the core: full-stack OS, first-class memory, kernel/control layer, workers as bounded task-card executors, default readonly, dashboard after contracts exist.",
    },
    "concept designs - Agent OS Design Principles.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "CONCEPT_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "Model-agnostic OS, router, skills, full-stack layers, local/cloud strategy.",
    },
    "concept designs - Combine Plan Optimization.pdf": {
        "types": ["STRATEGY_DRAFT", "CONCEPT_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "Fable as architect, Hermes runtime, durable assets, model-agnostic goal.",
    },
    "concept designs - Final Fable Handoff.pdf": {
        "types": ["STRATEGY_DRAFT", "HISTORICAL_CONTEXT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "MEDIUM",
        "role": "Fable handoff draft: role split, source priority, corrected core intent. Earlier handoff attempt.",
    },
    "concept designs - Memory Integration and Planning.pdf": {
        "types": ["PRIMARY_ARCHITECTURE_SOURCE", "CONCEPT_DRAFT"], "authority": AUTH_SUPPORTING,
        "priority_rank": 10, "relevance": "HIGH",
        "role": "Persistent memory design; JARVIS explicitly inspiration-only; memory capture ideas.",
    },
    # ---- Process-correction files (rank 11) ----
    "concept designs - NRG Agent OS Workflow.pdf": {
        "types": ["PROCESS_CORRECTION", "SOURCE_PROCESSING_RULES"], "authority": AUTH_PROCESS,
        "priority_rank": 11, "relevance": "HIGH",
        "role": "Records the earlier failure: the model started producing the Factory Pack before all source material was supplied. Do not mix intake and processing. WAIT MODE / PROCESS NOW discipline.",
    },
    "concept designs - Review Request.pdf": {
        "types": ["PROCESS_CORRECTION", "HISTORICAL_CONTEXT"], "authority": AUTH_PROCESS,
        "priority_rank": 11, "relevance": "MEDIUM",
        "role": "Review request history - how sources should be read and reviewed.",
    },
    "concept designs - Startup Prompt Creation.pdf": {
        "types": ["PROCESS_CORRECTION", "HISTORICAL_CONTEXT"], "authority": AUTH_PROCESS,
        "priority_rank": 11, "relevance": "MEDIUM",
        "role": "Startup prompt creation history.",
    },
    "concept designs - Startup Prompt Instructions.pdf": {
        "types": ["PROCESS_CORRECTION", "HISTORICAL_CONTEXT"], "authority": AUTH_PROCESS,
        "priority_rank": 11, "relevance": "MEDIUM",
        "role": "Startup prompt instruction history.",
    },
    # ---- Concept design / scaffold files (rank 12) ----
    "Dashboard OS Agent Framework Setup - Google Gemini.pdf": {
        "types": ["CONCEPT_DRAFT", "HISTORICAL_CONTEXT"], "authority": AUTH_HISTORICAL,
        "priority_rank": 12, "relevance": "LOW",
        "role": "Historical agent-framework scaffold. Useful later for worker/agent registry ideas. Must not authorize Phase 6 agents or Phase 9 dashboard work early.",
    },
    # ---- Behavioural-biopsy files (rank 13) ----
    "Fable 5 Model Behavioural Biopsy - Google Gemini.pdf": {
        "types": ["BEHAVIOURAL_ANALYSIS"], "authority": AUTH_SUPPORTING,
        "priority_rank": 13, "relevance": "MEDIUM",
        "role": "Explains why Fable is best as architect/reviewer. Benchmark, pricing, personality, fallback-model, and behavioural claims are NOT Kernel law.",
    },
    "Fable Pack Feedback.pdf": {
        "types": ["PACKAGING_GUIDANCE"], "authority": AUTH_PROCESS,
        "priority_rank": 13, "relevance": "MEDIUM",
        "role": "Kernel/skill/task-card compression doctrine. Not live prompt law unless aligned with the Master Build Law.",
    },
    # ---- JARVIS / cinematic inspiration (rank 14) ----
    "JARVIS-Prompt-Pack.pdf": {
        "types": ["CONCEPT_ONLY", "UX_INSPIRATION"], "authority": AUTH_CONCEPT,
        "priority_rank": 14, "relevance": "LOW",
        "role": "Use for grounded answers, source proof, memory capture, voice, model hot-swap, action confirmation, cinematic language. Do not copy the memory galaxy. Do not turn NRG Agent OS into JARVIS.",
    },
    "concept designs jarvis style  - Final Fable Handoff.pdf": {
        "types": ["CONCEPT_ONLY", "UX_INSPIRATION", "DUPLICATE_REFERENCE"], "authority": AUTH_CONCEPT,
        "priority_rank": 14, "relevance": "LOW",
        "role": "JARVIS-styled handoff variant - inspiration only, duplicate of the Final Fable Handoff line. Not architecture law.",
    },
    # ---- Early drafts / operator reference / archive (rank 15) ----
    "user-adhd-communication-style.md": {
        "types": ["SOURCE_EVIDENCE"], "authority": AUTH_SUPPORTING,
        "priority_rank": 15, "relevance": "MEDIUM",
        "role": "Operator communication reference. Shapes communication style and report clarity only. Not OS architecture.",
    },
    "NRG_Agent_OS_Final_Archive_Report.md": {
        "types": ["HISTORICAL_CONTEXT", "DUPLICATE_REFERENCE"], "authority": AUTH_HISTORICAL,
        "priority_rank": 15, "relevance": "LOW",
        "role": "Archive report - storage container, not a working prompt. Do not feed first. The Complete Build Architecture Archive is the stronger active source.",
    },
    "NRG_Agent_OS_Source_Manifest.json": {
        "types": ["SOURCE_EVIDENCE", "DUPLICATE_REFERENCE"], "authority": AUTH_HISTORICAL,
        "priority_rank": 15, "relevance": "LOW",
        "role": "Machine manifest from a prior intake run. Used for SHA256 hash cross-verification only.",
    },
    # ---- Formerly UNLISTED - classified per operator instruction (deep-read verified) ----
    "Production-Ready Go Blueprint for NRG Agent OS.pdf": {
        "types": ["STRATEGY_DRAFT", "CONCEPT_DRAFT"], "authority": AUTH_CONCEPT,
        "priority_rank": 15, "relevance": "MEDIUM",
        "role": ("CLASSIFIED: CONCEPT. Derived research blueprint proposing an unconfirmed Go modular-monolith "
                 "implementation stack. The document itself admits the corpus lacks a repository baseline, locked "
                 "deployment target, database choice, identity provider, SLOs, and UI stack (unspecified assumptions). "
                 "Useful as a future stack recommendation only; cannot authorize build decisions or lock a stack."),
    },
    "deep-research-report #2.md": {
        "types": ["STRATEGY_DRAFT", "CONCEPT_DRAFT", "DUPLICATE_REFERENCE"], "authority": AUTH_CONCEPT,
        "priority_rank": 15, "relevance": "MEDIUM",
        "role": ("CLASSIFIED: CONCEPT + DUPLICATE_REFERENCE. Markdown source of 'Production-Ready Go Blueprint for "
                 "NRG Agent OS.pdf' (identical title and executive summary - duplicate lineage pair). Same constraint: "
                 "future stack recommendation only; cannot authorize build decisions."),
    },
    "Detailed System Architecture Blueprint.pdf": {
        "types": ["SOURCE_EVIDENCE", "CONCEPT_DRAFT"], "authority": AUTH_CONCEPT,
        "priority_rank": 15, "relevance": "LOW",
        "role": ("CLASSIFIED: CONCEPT. Generic monorepo architectural doctrine ('Architectural Blueprint and Tactical "
                 "Directives for Scalable Monorepo Systems'). Contains no NRG-specific corrected intent. Engineering "
                 "reference for future implementation phases only; cannot authorize build decisions."),
    },
}


def classify(filename: str) -> dict:
    """Return classification for a filename. Unlisted files are UNKNOWN_NEEDS_REVIEW."""
    if filename in CLASSIFICATION_MAP:
        c = dict(CLASSIFICATION_MAP[filename])
        c["listed"] = True
    else:
        c = {
            "types": ["UNKNOWN_NEEDS_REVIEW"],
            "authority": AUTH_UNKNOWN,
            "priority_rank": None,
            "relevance": "UNKNOWN",
            "role": ("Present in the bundle but NOT listed in the operator handoff. Indexed and preserved as "
                     "UNKNOWN_NEEDS_REVIEW; requires operator classification decision. Not safe to use as current guidance."),
            "listed": False,
        }
    c["trust_level"] = TRUST_BY_AUTHORITY[c["authority"]]
    c["safe_to_use"] = SAFE_USE_BY_AUTHORITY[c["authority"]]
    return c
