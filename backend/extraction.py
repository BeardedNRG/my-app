"""Phase 0 Source Lock - deterministic file extraction (read-only over sources)."""
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SOURCE_ROOT = Path("/app/sources/New folder (2)")
WORKSPACE_ROOT = Path("/app/NRG_Agent_OS_Phase0_SourceLock")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def extract_pdf(path: Path) -> tuple[str, str]:
    """Returns (text, method). pdfplumber primary, pypdf fallback."""
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        text = "\n".join(parts)
        if text.strip():
            return text, "pdfplumber"
    except Exception as e:
        logger.warning(f"pdfplumber failed on {path.name}: {e}")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        return text, "pypdf"
    except Exception as e:
        return "", f"FAILED: {e}"


def enumerate_and_extract():
    """Walk the read-only source root, extract everything. Yields dicts."""
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Source root not found: {SOURCE_ROOT}")
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        entry = {
            "filename": path.name,
            "relative_path": str(path.relative_to(SOURCE_ROOT)),
            "ext": ext,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_of(path),
        }
        if ext in (".md", ".txt", ".json"):
            try:
                text = extract_text_file(path)
                entry["extracted_text"] = text
                entry["extraction_method"] = "utf8"
                entry["parse_status"] = "PARSED"
            except Exception as e:
                entry["extracted_text"] = ""
                entry["extraction_method"] = f"FAILED: {e}"
                entry["parse_status"] = "FAILED"
        elif ext == ".pdf":
            text, method = extract_pdf(path)
            entry["extracted_text"] = text
            entry["extraction_method"] = method
            entry["parse_status"] = "FAILED" if (method.startswith("FAILED") or len(text.strip()) < 50) else "PARSED"
        else:
            entry["extracted_text"] = ""
            entry["extraction_method"] = f"unsupported ({ext})"
            entry["parse_status"] = "SKIPPED"
        entry["text_chars"] = len(entry["extracted_text"])
        yield entry
