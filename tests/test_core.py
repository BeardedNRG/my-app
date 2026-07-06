"""
Phase 1 POC: NRG Agent OS Phase 0 Source Lock - Core Workflow Test
1. Enumerate all files in /app/sources (read-only source folder)
2. Extract text from every PDF (pdfplumber, pypdf fallback) and MD file
3. Compute sha256 + size inventory
4. One LLM structured-JSON analysis call (summary + key claims) to prove deep-read works
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

SOURCE_ROOT = Path("/app/sources/New folder (2)")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def extract_pdf(path: Path) -> tuple[str, str]:
    """Returns (text, method). Tries pdfplumber, falls back to pypdf."""
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                parts.append(t)
        text = "\n".join(parts)
        if text.strip():
            return text, "pdfplumber"
    except Exception as e:
        print(f"  pdfplumber failed on {path.name}: {e}")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        return text, "pypdf"
    except Exception as e:
        return "", f"FAILED: {e}"


def run_extraction():
    results = []
    failures = []
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        entry = {
            "file": path.name,
            "ext": ext,
            "bytes": path.stat().st_size,
            "sha256": sha256_of(path)[:16],
        }
        if ext == ".md":
            text = extract_md(path)
            entry["text_chars"] = len(text)
            entry["method"] = "utf8"
        elif ext == ".pdf":
            text, method = extract_pdf(path)
            entry["text_chars"] = len(text)
            entry["method"] = method
            if method.startswith("FAILED") or len(text.strip()) < 50:
                failures.append(entry)
        elif ext == ".json":
            text = extract_md(path)
            entry["text_chars"] = len(text)
            entry["method"] = "utf8-json"
        else:
            entry["text_chars"] = 0
            entry["method"] = f"skipped ({ext})"
        results.append(entry)
    return results, failures


async def run_llm_test():
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    # Deep-read the master intake pack (control packet #1)
    target = SOURCE_ROOT / "NRG-Agent-OS - Fable-5 Master Intake Pack - Copy 01.md"
    text = extract_md(target)[:20000]

    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id="poc-source-analysis",
        system_message=(
            "You are a forensic source analyst performing a Phase 0 Source Lock. "
            "You output ONLY valid JSON, no markdown fences, no prose."
        ),
    ).with_model("openai", "gpt-5.4-mini")

    prompt = (
        "Analyze this source document and return JSON with exactly these keys:\n"
        '{"summary": "<3-4 sentence summary>", "key_claims": ["<claim1>", "<claim2>", "<claim3>"], '
        '"document_role": "<what this document does in the project>"}\n\n'
        f"DOCUMENT: {target.name}\n---\n{text}"
    )
    resp = await chat.send_message(UserMessage(text=prompt))
    raw = resp.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    data = json.loads(raw)
    assert "summary" in data and "key_claims" in data, "Missing keys in LLM output"
    return data


def main():
    print("=" * 60)
    print("STEP 1-3: File enumeration + extraction + hashing")
    print("=" * 60)
    results, failures = run_extraction()
    total = len(results)
    pdfs = [r for r in results if r["ext"] == ".pdf"]
    mds = [r for r in results if r["ext"] == ".md"]
    print(f"Total files: {total} | PDFs: {len(pdfs)} | MDs: {len(mds)}")
    for r in results:
        print(f"  {r['file'][:60]:60s} {r['method']:12s} {r['text_chars']:>8d} chars  sha:{r['sha256']}")
    if failures:
        print(f"\nEXTRACTION FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f['file']}: {f['method']} ({f['text_chars']} chars)")
    else:
        print("\nAll PDFs extracted successfully.")

    print("\n" + "=" * 60)
    print("STEP 4: LLM structured deep-read test (Master Intake Pack)")
    print("=" * 60)
    data = asyncio.run(run_llm_test())
    print(json.dumps(data, indent=2)[:2000])

    ok = total >= 37 and not failures
    print("\n" + "=" * 60)
    print(f"POC RESULT: {'SUCCESS' if ok else 'PARTIAL - see failures above'}")
    print("=" * 60)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
