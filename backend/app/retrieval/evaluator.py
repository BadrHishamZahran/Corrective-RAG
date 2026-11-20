import json
import re
from app.config import RELEVANCE_THRESHOLD, OLLAMA_BASE_URL, OLLAMA_MODEL
import requests

def _ollama(prompt: str) -> str:
    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}}, timeout=180)
    response.raise_for_status()
    return response.json().get("response", "")

def evaluate_retrieval(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {"status": "irrelevant", "score": 0.0, "reason": "No documents were retrieved."}
    context = "\n\n".join(f"[Passage {i+1}] {c['text'][:1200]}" for i, c in enumerate(chunks[:5]))
    prompt = f"""You are a strict retrieval relevance evaluator. Assess whether the passages contain information useful for answering the question. Return ONLY JSON with keys score (number 0 to 1), status (relevant, partial, or irrelevant), reason (short string). Do not answer the question.
Question: {question}
Passages:
{context}
JSON:"""
    try:
        raw = _ollama(prompt)
        match = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(match.group(0)) if match else {}
        score = float(data.get("score", 0))
        status = str(data.get("status", "partial")).lower()
        if status not in {"relevant", "partial", "irrelevant"}:
            status = "partial"
        return {"status": status, "score": max(0.0, min(1.0, score)), "reason": str(data.get("reason", "LLM relevance assessment"))}
    except Exception as exc:
        # Similarity-based fallback keeps the pipeline usable if the grader call fails.
        best = max((c["similarity"] for c in chunks), default=0.0)
        status = "relevant" if best >= RELEVANCE_THRESHOLD else "partial"
        return {"status": status, "score": best, "reason": f"Fallback to vector similarity because grader failed: {exc}"}
