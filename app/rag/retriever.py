import json, os, glob, math
from pathlib import Path

INDEX_DIR = Path("data/index")

def ask_question(q: str):
    # Toy retriever: selects top chunks by shared tokens (no external deps)
    tokens = set([t.lower() for t in q.split() if t.strip()])
    scored = []
    for fp in glob.glob(str(INDEX_DIR / "*.json")):
        data = json.loads(open(fp, encoding="utf-8").read())
        for ch in data.get("chunks", []):
            ch_tokens = set(ch.lower().split())
            score = len(tokens & ch_tokens)
            if score > 0:
                scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    context = "

".join([c for _, c in scored[:3]]) if scored else ""
    # Simulate LLM: return context snippet
    answer = f"Top context:
{context[:800]}"
    citations = [{"source": os.path.basename(fp)} for fp in glob.glob(str(INDEX_DIR / '*.json'))][:3]
    return {"answer": answer, "citations": citations}
