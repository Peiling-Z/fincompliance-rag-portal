import os, io, hashlib, tempfile, json
from pathlib import Path

DATA_DIR = Path("data/docs")
INDEX_DIR = Path("data/index")
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def _chunk_bytes(b: bytes, size: int = 1200) -> list[str]:
    # naive chunker on bytes->text
    text = b.decode(errors="ignore")
    return [text[i:i+size] for i in range(0, len(text), size)]

def ingest_pdf_to_store(filename: str, content: bytes):
    # For simplicity, treat as text; in real-world use PDF parser
    h = hashlib.sha1(content).hexdigest()[:12]
    raw_path = DATA_DIR / f"{h}_{filename}"
    raw_path.write_bytes(content)

    chunks = _chunk_bytes(content)
    # Persist simple JSON "index" for demo
    (INDEX_DIR / f"{h}.json").write_text(json.dumps({"chunks": chunks}, ensure_ascii=False))
    return {"doc_id": h, "chunks": len(chunks)}
