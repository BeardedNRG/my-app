"""Phase 0 Source Lock - LLM deep-read analysis, contradiction detection (Section 6 schema),
and thematic source summaries (Section 11.10)."""
import asyncio
import json
import logging
import os
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

ANALYSIS_MODEL = ("openai", "gpt-5.4-mini")
CONTRADICTION_MODEL = ("openai", "gpt-5.4")
SUMMARY_MODEL = ("openai", "gpt-5.4-mini")
DOC_TRUNCATE = 14000
CONCURRENCY = 4

SYSTEM_MSG = (
    "You are Fable 5 acting as forensic source-lock auditor performing Phase 0 Source Lock for NRG Agent OS. "
    "Doctrine: Control files tell you what to do. Primary sources tell you what the project is. "
    "Reference sources explain how the thinking evolved. Concept-only files inspire later design but cannot "
    "authorize build decisions. You must not smooth over contradictions. You must not invent missing facts. "
    "If something is unknown, mark it UNKNOWN_NEEDS_VERIFICATION. Prefer exactness over elegance, evidence over confidence."
)

CONTRADICTION_CLASSES = [
    "LOCKED_DECISION", "CURRENT_BEST_TRUTH", "CONTESTED_EVIDENCE", "HISTORICAL_CONTEXT",
    "SUPERSEDED", "UNSAFE_OR_REJECTED", "UNKNOWN_NEEDS_VERIFICATION",
]


def _parse_json(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    brace = raw.find("{")
    bracket = raw.find("[")
    candidates = [i for i in (brace, bracket) if i != -1]
    if candidates:
        start = min(candidates)
        if start > 0:
            raw = raw[start:]
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(raw)
    return obj


def _chat(model, session_prefix):
    return LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=f"{session_prefix}-{uuid.uuid4().hex[:10]}",
        system_message=SYSTEM_MSG,
    ).with_model(*model)


async def analyze_source(filename: str, authority: str, role: str, text: str) -> dict:
    chat = _chat(ANALYSIS_MODEL, "src")
    truncated = text[:DOC_TRUNCATE]
    note = "" if len(text) <= DOC_TRUNCATE else f" (truncated from {len(text)} chars)"
    prompt = (
        "Deep-read this source document and return JSON with exactly these keys (output ONLY JSON):\n"
        '{"summary": "<3-4 sentence forensic summary>", '
        '"key_claims": ["<4-6 concrete claims/assertions this document makes about the project, architecture, process, or intent>"], '
        '"document_role": "<one sentence: what this document does in the project>", '
        '"build_relevance": "<one sentence: how this affects Phase 0 or later build phases>", '
        '"suggested_classification": "<if the assigned authority level seems wrong, suggest one of: CONTROL, HIGH_EVIDENCE, SUPPORTING_EVIDENCE, PROCESS_EVIDENCE, HISTORICAL_CONTEXT, CONCEPT_ONLY, SUPERSEDED, UNSAFE_OR_REJECTED; else repeat the assigned level>"}\n\n'
        f"FILENAME: {filename}\nASSIGNED_AUTHORITY_LEVEL: {authority}\nHANDOFF_ROLE: {role}\n"
        f"DOCUMENT_TEXT{note}:\n---\n{truncated}"
    )
    resp = await chat.send_message(UserMessage(text=prompt))
    data = _parse_json(resp)
    return {
        "summary": str(data.get("summary", "")),
        "key_claims": [str(c) for c in data.get("key_claims", [])][:8],
        "document_role": str(data.get("document_role", "")),
        "build_relevance": str(data.get("build_relevance", "")),
        "suggested_classification": str(data.get("suggested_classification", authority)),
    }


async def analyze_sources_batch(sources: list[dict], progress_cb=None) -> dict:
    sem = asyncio.Semaphore(CONCURRENCY)
    results = {}
    done = {"n": 0}

    async def worker(src):
        async with sem:
            try:
                res = await analyze_source(src["filename"], src.get("authority_level", ""),
                                           src.get("handoff_role", ""), src.get("extracted_text", ""))
            except Exception as e:
                logger.error(f"Analysis failed for {src['filename']}: {e}")
                try:
                    await asyncio.sleep(2)
                    res = await analyze_source(src["filename"], src.get("authority_level", ""),
                                               src.get("handoff_role", ""), src.get("extracted_text", ""))
                except Exception as e2:
                    res = {"summary": f"ANALYSIS_FAILED: {e2}", "key_claims": [], "document_role": "",
                           "build_relevance": "", "suggested_classification": src.get("authority_level", "")}
            results[src["filename"]] = res
            done["n"] += 1
            if progress_cb:
                await progress_cb(done["n"])

    await asyncio.gather(*[worker(s) for s in sources])
    return results


async def detect_contradictions(sources: list[dict]) -> list[dict]:
    """Section 6 contradiction schema. Contradictions are preserved, never resolved silently."""
    chat = _chat(CONTRADICTION_MODEL, "contradictions")
    claims_block = []
    for s in sources:
        if not s.get("key_claims"):
            continue
        claims_block.append(
            f"SOURCE: {s['filename']} | AUTHORITY: {s.get('authority_level')} | PRIORITY: {s.get('priority_rank')}\n"
            + "\n".join(f"  - {c}" for c in s["key_claims"])
        )
    corpus = "\n\n".join(claims_block)
    prompt = (
        "Below are key claims extracted from every source in the NRG Agent OS bundle, with authority level and "
        "priority rank (lower rank = higher authority; CONTROL outranks all; CONCEPT_ONLY cannot authorize builds).\n\n"
        "Identify GENUINE contradictions: conflicts about project identity, architecture, scope, process, roles, "
        "naming, stack, or intent. Focus on: (a) early drafts vs final corrected intent, (b) JARVIS/cinematic/"
        "dashboard-first concepts vs the full-stack control-system doctrine, (c) intake/processing discipline "
        "violations, (d) stack or implementation prescriptions not confirmed by control documents, (e) anything "
        "conflicting with the Phase 0-only restriction or Master Build Law. Report the 8-14 most significant.\n\n"
        "Return a JSON array where each item has exactly these keys:\n"
        '{"title": "<short name>", '
        '"claim_a": "<what one side asserts, citing which source>", '
        '"claim_b": "<what the other side asserts, citing which source>", '
        '"sources_involved": ["<filename1>", "<filename2>"], '
        f'"classification": "<one of: {", ".join(CONTRADICTION_CLASSES)}>", '
        '"stronger_claim": "<which claim is stronger under the source priority order, or NONE>", '
        '"reason": "<one sentence: why this classification>", '
        '"missing_evidence": "<what evidence is missing, or NONE>", '
        '"blocks_phase1": <true|false>, '
        '"verification": "<what verification would resolve this later>", '
        '"severity": "<HIGH|MEDIUM|LOW>"}\n\n'
        f"CLAIMS CORPUS:\n{corpus[:90000]}"
    )
    resp = await chat.send_message(UserMessage(text=prompt))
    data = _parse_json(resp)
    items = data if isinstance(data, list) else data.get("contradictions", [])
    out = []
    for i, item in enumerate(items, 1):
        cls = str(item.get("classification", "CONTESTED_EVIDENCE")).upper()
        if cls not in CONTRADICTION_CLASSES:
            cls = "CONTESTED_EVIDENCE"
        out.append({
            "id": f"CON-{i:02d}",
            "uid": str(uuid.uuid4()),
            "title": str(item.get("title", "Untitled contradiction")),
            "claim_a": str(item.get("claim_a", "")),
            "claim_b": str(item.get("claim_b", "")),
            "sources_involved": [str(x) for x in item.get("sources_involved", [])],
            "classification": cls,
            "stronger_claim": str(item.get("stronger_claim", "NONE")),
            "reason": str(item.get("reason", "")),
            "missing_evidence": str(item.get("missing_evidence", "NONE")),
            "blocks_phase1": bool(item.get("blocks_phase1", False)),
            "verification": str(item.get("verification", "")),
            "severity": str(item.get("severity", "MEDIUM")).upper(),
            "status": "PRESERVED",
        })
    return out


# ---------------- Thematic source summaries (Section 11.10) ----------------

THEMES = [
    ("00_master_intent_summary.md", "Master Intent",
     ["NRG-Agent-OS - Fable-5 Master Intake Pack - Copy 01.md", "NRG-Agent-OS - Phase 0 System State - Source Lock - Copy 01.md", "NRG-Agent-OS - Project Manifest.md", "End Of Source Conversation.pdf"]),
    ("01_source_processing_summary.md", "Source Processing Rules",
     ["NRG Agent OS Source Intake Prompt.pdf", "concept designs - NRG Agent OS Workflow.pdf", "concept designs - Review Request.pdf", "concept designs - Startup Prompt Creation.pdf", "concept designs - Startup Prompt Instructions.pdf"]),
    ("02_factory_pack_summary.md", "Factory Pack",
     ["NRG Agent OS Factory Pack.pdf", "Fable Pack Feedback.pdf"]),
    ("03_dashboard_assessment_summary.md", "Dashboard Information Pack Assessment",
     ["NRG Agent OS Dashboard Information Pack Assessment.pdf"]),
    ("04_kernel_and_boot_summary.md", "Kernel and Boot Sequence",
     ["Boot Sequence Design.pdf", "Architecting the NRG Agent OS - Google Gemini.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md"]),
    ("05_memory_summary.md", "Memory",
     ["concept designs - Memory Integration and Planning.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md", "concept designs - NRG Agent OS Overview.pdf"]),
    ("06_router_summary.md", "Router",
     ["concept designs - Agent OS Design Principles.pdf", "Architecting the NRG Agent OS - Google Gemini.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md"]),
    ("07_validation_summary.md", "Validation",
     ["Architecting the NRG Agent OS - Google Gemini.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md", "NRG-Agent-OS - Agent Rules - XML Behavioral Framework.md"]),
    ("08_audit_summary.md", "Audit / Event Log",
     ["Architecting the NRG Agent OS - Google Gemini.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md"]),
    ("09_worker_contracts_summary.md", "Worker Contracts",
     ["NRG-Agent-OS - Worker Task Card Template - Minimal Verification Gate.md", "NRG-Agent-OS - Agent Rules - XML Behavioral Framework.md", "Dashboard OS Agent Framework Setup - Google Gemini.pdf"]),
    ("10_skill_system_summary.md", "Skill System",
     ["NRG-Agent-OS - Skill - fable.forensic-methodology.md", "concept designs - Agent OS Design Principles.pdf"]),
    ("11_recovery_rails_summary.md", "Recovery Rails",
     ["Architecting the NRG Agent OS - Google Gemini.pdf", "NRG_Agent_OS_Complete_Build_Architecture_Archive.md", "Boot Sequence Design.pdf"]),
    ("12_operator_interface_summary.md", "Operator Interface",
     ["NRG Agent OS Dashboard Information Pack Assessment.pdf", "Dashboard OS Agent Framework Setup - Google Gemini.pdf", "JARVIS-Prompt-Pack.pdf"]),
    ("13_controlled_live_operation_summary.md", "Controlled Live Operation",
     ["NRG_Agent_OS_Complete_Build_Architecture_Archive.md", "NRG Agent OS Factory Pack.pdf"]),
    ("14_jarvis_inspiration_summary.md", "JARVIS Inspiration",
     ["JARVIS-Prompt-Pack.pdf", "concept designs jarvis style  - Final Fable Handoff.pdf", "concept designs - Memory Integration and Planning.pdf"]),
    ("15_fable_methodology_summary.md", "Fable Methodology",
     ["NRG-Agent-OS - Skill - fable.forensic-methodology.md", "Fable 5 Model Behavioural Biopsy - Google Gemini.pdf", "NRG-Agent-OS - Fable-5 Master Intake Pack - Copy 01.md"]),
    ("16_hermes_runtime_summary.md", "Hermes Runtime",
     ["concept designs - Combine Plan Optimization.pdf", "concept designs - Final Fable Handoff.pdf", "concept designs - NRG Agent OS Overview.pdf"]),
    ("17_concept_designs_summary.md", "Concept Designs (all)",
     ["concept designs - NRG Agent OS Overview.pdf", "concept designs - Agent OS Design Principles.pdf", "concept designs - Combine Plan Optimization.pdf", "concept designs - Final Fable Handoff.pdf", "concept designs - Memory Integration and Planning.pdf", "concept designs - NRG Agent OS Workflow.pdf"]),
]

REQUIRED_SUMMARY_SECTIONS = [
    "What the sources claim", "What is useful", "What is risky", "What conflicts with other sources",
    "What has been superseded", "What should be carried forward", "What must not be treated as authority",
]


async def generate_theme_summary(theme_title: str, sources: list[dict]) -> str:
    chat = _chat(SUMMARY_MODEL, "summary")
    per_source_budget = max(3000, 24000 // max(len(sources), 1))
    blocks = []
    for s in sources:
        text = (s.get("extracted_text") or "")[:per_source_budget]
        blocks.append(f"=== SOURCE: {s['filename']} (authority: {s.get('authority_level')}) ===\n{text}")
    sections = "\n".join(f"## {sec}" for sec in REQUIRED_SUMMARY_SECTIONS)
    prompt = (
        f"Write the Phase 0 source summary for the theme: {theme_title}.\n"
        "You are summarizing raw source material so that raw chaos does not become active instruction.\n"
        f"Use EXACTLY these markdown section headings, in this order:\n{sections}\n\n"
        "Rules: cite source filenames when attributing claims; be forensic and concise (bullet points preferred); "
        "do not invent facts; mark unknowns as UNKNOWN_NEEDS_VERIFICATION; concept-only material must be flagged "
        "as unable to authorize build decisions. Output markdown only, no preamble.\n\n"
        + "\n\n".join(blocks)
    )
    resp = await chat.send_message(UserMessage(text=prompt))
    return resp.strip()


async def generate_all_summaries(sources_by_name: dict, progress_cb=None) -> dict:
    """Returns {filename: markdown_content} for the 18 thematic summaries."""
    sem = asyncio.Semaphore(3)
    results = {}
    done = {"n": 0}

    async def worker(fname, title, source_names):
        async with sem:
            subset = [sources_by_name[n] for n in source_names if n in sources_by_name]
            try:
                body = await generate_theme_summary(title, subset)
            except Exception as e:
                logger.error(f"Summary failed for {fname}: {e}")
                try:
                    await asyncio.sleep(2)
                    body = await generate_theme_summary(title, subset)
                except Exception as e2:
                    body = f"## SUMMARY_GENERATION_FAILED\n\n{e2}"
            header = (f"# {title} - Source Summary\n\n"
                      f"Sources covered: {', '.join('`' + n + '`' for n in source_names)}\n\n---\n\n")
            results[fname] = header + body
            done["n"] += 1
            if progress_cb:
                await progress_cb(done["n"])

    await asyncio.gather(*[worker(f, t, s) for f, t, s in THEMES])
    return results
