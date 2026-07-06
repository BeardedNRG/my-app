from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from classification import classify, PRIORITY_ORDER, FORBIDDEN_BUILD_AREAS, RESOLUTION_RULE  # noqa: E402
from extraction import enumerate_and_extract, WORKSPACE_ROOT, SOURCE_ROOT  # noqa: E402
from analysis import analyze_sources_batch, detect_contradictions  # noqa: E402
from artifacts import write_artifacts, ARTIFACT_NAMES  # noqa: E402

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="NRG Agent OS - Phase 0 Source Lock Console")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEXT_PREVIEW_LIMIT = 60000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def strip_mongo(doc):
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


class IngestRequest(BaseModel):
    force: bool = False


class AcceptRequest(BaseModel):
    operator: str
    note: Optional[str] = None


# ---------------- Ingestion pipeline ----------------

async def get_state():
    state = await db.state.find_one({"key": "phase0"})
    if not state:
        state = {"key": "phase0", "status": "UNLOCKED", "accepted_by": None,
                 "accepted_at": None, "note": None, "updated_at": now_iso()}
        await db.state.insert_one(dict(state))
    return strip_mongo(state)


async def run_ingestion(run_id: str, force: bool):
    async def set_run(**kwargs):
        kwargs["updated_at"] = now_iso()
        await db.runs.update_one({"run_id": run_id}, {"$set": kwargs})

    try:
        # ---- Stage 1: EXTRACTING ----
        await set_run(stage="EXTRACTING", message="Enumerating and extracting sources (read-only)...")
        entries = await asyncio.to_thread(lambda: list(enumerate_and_extract()))
        total = len(entries)
        await set_run(total_files=total, message=f"Extracted {total} files. Classifying...")

        for e in entries:
            c = classify(e["filename"])
            existing = await db.sources.find_one({"filename": e["filename"]})
            doc = {
                "source_id": existing["source_id"] if existing else str(uuid.uuid4()),
                "filename": e["filename"],
                "relative_path": e["relative_path"],
                "ext": e["ext"],
                "size_bytes": e["size_bytes"],
                "sha256": e["sha256"],
                "extracted_text": e["extracted_text"],
                "text_chars": e["text_chars"],
                "extraction_method": e["extraction_method"],
                "parse_status": e["parse_status"],
                "authority_tier": c["tier"],
                "priority_rank": c["priority_rank"],
                "feed_order": c.get("feed_order"),
                "tags": c["tags"],
                "handoff_role": c["role"],
                "listed": c["listed"],
                "updated_at": now_iso(),
            }
            # Preserve prior analysis if hash unchanged and not forced
            if existing and existing.get("sha256") == e["sha256"] and existing.get("summary") and not force:
                for k in ("summary", "key_claims", "document_role", "build_relevance", "suggested_classification"):
                    doc[k] = existing.get(k)
            await db.sources.update_one({"filename": e["filename"]}, {"$set": doc}, upsert=True)

        # ---- Stage 2: ANALYZING ----
        cursor = db.sources.find({})
        all_sources = [strip_mongo(d) async for d in cursor]
        pending = [s for s in all_sources if not s.get("summary") or force]
        await set_run(stage="ANALYZING", analyzed=0, to_analyze=len(pending),
                      message=f"Deep-read analysis: 0/{len(pending)} sources...")

        async def progress_cb(n):
            await set_run(analyzed=n, message=f"Deep-read analysis: {n}/{len(pending)} sources...")

        if pending:
            results = await analyze_sources_batch(pending, progress_cb)
            for filename, res in results.items():
                await db.sources.update_one({"filename": filename}, {"$set": {**res, "updated_at": now_iso()}})

        # ---- Stage 3: CONTRADICTIONS ----
        await set_run(stage="CONTRADICTIONS", message="Detecting contradictions across all key claims...")
        cursor = db.sources.find({})
        all_sources = [strip_mongo(d) async for d in cursor]
        contradictions = await detect_contradictions(all_sources)
        await db.contradictions.delete_many({})
        if contradictions:
            await db.contradictions.insert_many([dict(c, created_at=now_iso()) for c in contradictions])

        # ---- Stage 4: ARTIFACTS ----
        await set_run(stage="ARTIFACTS", contradictions_found=len(contradictions),
                      message="Generating Phase 0 artifacts in workspace root...")
        run_doc = strip_mongo(await db.runs.find_one({"run_id": run_id}))
        contents = await asyncio.to_thread(write_artifacts, all_sources, contradictions, run_doc or {})
        for name, content in contents.items():
            await db.artifacts.update_one(
                {"name": name},
                {"$set": {"name": name, "content": content, "path": str(WORKSPACE_ROOT / name),
                          "generated_at": now_iso()}},
                upsert=True,
            )

        # ---- Complete ----
        await set_run(stage="COMPLETE", finished_at=now_iso(),
                      message=f"Source lock complete. {total} sources indexed, "
                              f"{len(contradictions)} contradictions preserved, {len(contents)} artifacts generated.")
        await db.state.update_one({"key": "phase0"}, {"$set": {"status": "LOCKED", "updated_at": now_iso()}})
        logger.info(f"Ingestion run {run_id} complete.")
    except Exception as e:
        logger.exception(f"Ingestion run {run_id} failed")
        await set_run(stage="FAILED", message=f"Run failed: {e}", finished_at=now_iso())


# ---------------- Routes ----------------

@api_router.get("/")
async def root():
    return {"service": "NRG Agent OS - Phase 0 Source Lock Console", "scope": "PHASE_0_ONLY"}


@api_router.get("/status")
async def get_status():
    state = await get_state()
    last_run = await db.runs.find_one({}, sort=[("started_at", -1)])
    total = await db.sources.count_documents({})
    tier_counts = {}
    async for doc in db.sources.aggregate([{"$group": {"_id": "$authority_tier", "n": {"$sum": 1}}}]):
        tier_counts[doc["_id"]] = doc["n"]
    contradictions_count = await db.contradictions.count_documents({})
    artifacts_count = await db.artifacts.count_documents({})
    parsed = await db.sources.count_documents({"parse_status": "PARSED"})
    return {
        "phase": "PHASE_0_SOURCE_LOCK",
        "state": state,
        "last_run": strip_mongo(last_run),
        "sources_total": total,
        "sources_parsed": parsed,
        "tier_counts": tier_counts,
        "contradictions_count": contradictions_count,
        "artifacts_count": artifacts_count,
        "forbidden_build_areas": FORBIDDEN_BUILD_AREAS,
        "workspace_root": str(WORKSPACE_ROOT),
        "source_root": str(SOURCE_ROOT),
    }


@api_router.post("/ingest")
async def start_ingest(req: IngestRequest):
    state = await get_state()
    if state["status"] == "ACCEPTED_WAIT":
        raise HTTPException(status_code=409, detail="Phase 0 has been accepted and frozen. System is in WAIT mode.")
    running = await db.runs.find_one({"stage": {"$nin": ["COMPLETE", "FAILED"]}})
    if running:
        raise HTTPException(status_code=409, detail="An ingestion run is already in progress.")
    run_id = str(uuid.uuid4())
    run = {
        "run_id": run_id, "stage": "QUEUED", "message": "Run queued.",
        "force": req.force, "started_at": now_iso(), "updated_at": now_iso(),
        "finished_at": None, "total_files": 0, "analyzed": 0, "to_analyze": 0,
        "contradictions_found": 0,
    }
    await db.runs.insert_one(dict(run))
    asyncio.create_task(run_ingestion(run_id, req.force))
    return {"run_id": run_id, "stage": "QUEUED"}


@api_router.get("/ingest/status")
async def ingest_status():
    last_run = await db.runs.find_one({}, sort=[("started_at", -1)])
    if not last_run:
        return {"stage": "NEVER_RUN", "message": "No ingestion run has been executed yet."}
    return strip_mongo(last_run)


@api_router.get("/sources")
async def list_sources(search: Optional[str] = None, tier: Optional[str] = None,
                       parse_status: Optional[str] = None):
    query = {}
    if tier:
        query["authority_tier"] = tier
    if parse_status:
        query["parse_status"] = parse_status
    if search:
        query["$or"] = [
            {"filename": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]
    cursor = db.sources.find(query, {"extracted_text": 0})
    docs = [strip_mongo(d) async for d in cursor]
    tier_order = {"CONTROL_PACKET": 0, "PRIMARY_ARCHITECTURE": 1, "PROCESS_RULES": 2,
                  "CONCEPT_ONLY": 3, "ARCHIVE_REFERENCE": 4, "UNLISTED": 5}
    docs.sort(key=lambda s: (tier_order.get(s.get("authority_tier"), 9),
                             s.get("priority_rank") or 99,
                             s.get("feed_order") or 99, s.get("filename", "")))
    return {"sources": docs, "total": len(docs)}


@api_router.get("/sources/{source_id}")
async def get_source(source_id: str):
    doc = await db.sources.find_one({"source_id": source_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Source not found")
    doc = strip_mongo(doc)
    text = doc.pop("extracted_text", "") or ""
    doc["text_preview"] = text[:TEXT_PREVIEW_LIMIT]
    doc["text_truncated"] = len(text) > TEXT_PREVIEW_LIMIT
    return doc


@api_router.get("/contradictions")
async def list_contradictions():
    cursor = db.contradictions.find({})
    docs = [strip_mongo(d) async for d in cursor]
    sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    docs.sort(key=lambda c: sev_order.get(c.get("severity", "MEDIUM"), 1))
    return {"contradictions": docs, "total": len(docs), "resolution_rule": RESOLUTION_RULE}


@api_router.get("/priority")
async def get_priority():
    cursor = db.sources.find({}, {"extracted_text": 0, "summary": 0, "key_claims": 0})
    docs = [strip_mongo(d) async for d in cursor]
    ranks = []
    for p in PRIORITY_ORDER:
        members = [d for d in docs if d.get("priority_rank") == p["rank"]]
        members.sort(key=lambda x: x.get("feed_order") or 99)
        ranks.append({**p, "members": members})
    unranked = [d for d in docs if not d.get("priority_rank")]
    return {"priority_order": ranks, "unranked": unranked, "resolution_rule": RESOLUTION_RULE}


@api_router.get("/artifacts")
async def list_artifacts():
    cursor = db.artifacts.find({}, {"content": 0})
    docs = [strip_mongo(d) async for d in cursor]
    order = {n: i for i, n in enumerate(ARTIFACT_NAMES)}
    docs.sort(key=lambda a: order.get(a.get("name"), 9))
    return {"artifacts": docs, "expected": ARTIFACT_NAMES}


@api_router.get("/artifacts/{name}")
async def get_artifact(name: str):
    doc = await db.artifacts.find_one({"name": name})
    if not doc:
        raise HTTPException(status_code=404, detail="Artifact not found. Run ingestion first.")
    return strip_mongo(doc)


@api_router.get("/report")
async def get_report():
    doc = await db.artifacts.find_one({"name": "PHASE0_COMPLETION_REPORT.md"})
    state = await get_state()
    return {"report": strip_mongo(doc), "state": state}


@api_router.post("/operator/accept")
async def operator_accept(req: AcceptRequest):
    state = await get_state()
    if state["status"] == "ACCEPTED_WAIT":
        raise HTTPException(status_code=409, detail="Phase 0 already accepted. System is in WAIT mode.")
    if state["status"] != "LOCKED":
        raise HTTPException(status_code=400, detail="Cannot accept: source lock has not completed. Run ingestion first.")
    update = {
        "status": "ACCEPTED_WAIT",
        "accepted_by": req.operator,
        "accepted_at": now_iso(),
        "note": req.note,
        "updated_at": now_iso(),
    }
    await db.state.update_one({"key": "phase0"}, {"$set": update})
    return {"status": "ACCEPTED_WAIT",
            "message": "Phase 0 accepted and frozen. System is now in WAIT mode. No further phases are authorized until explicitly commanded."}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def cleanup_stale_runs():
    """Mark runs orphaned by a server restart as FAILED so new runs can start."""
    result = await db.runs.update_many(
        {"stage": {"$nin": ["COMPLETE", "FAILED"]}},
        {"$set": {"stage": "FAILED", "message": "Run interrupted by server restart. Start a new run.",
                  "finished_at": now_iso(), "updated_at": now_iso()}},
    )
    if result.modified_count:
        logger.warning(f"Marked {result.modified_count} stale ingestion run(s) as FAILED.")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
