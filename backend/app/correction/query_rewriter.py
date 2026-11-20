from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
import requests

def rewrite_query(question: str, reason: str) -> str:
    prompt = f"""Rewrite the user's question into one concise search query that is more likely to retrieve useful passages from course documents. Preserve the original intent. Return only the rewritten query, with no explanation.
Original question: {question}
Why retrieval was weak: {reason}
Rewritten search query:"""
    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}, timeout=180)
    response.raise_for_status()
    rewritten = response.json().get("response", "").strip().strip('"')
    return rewritten or question
