from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
import requests

def generate_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I couldn't find supporting information in the uploaded documents, so I can't provide a reliable answer."
    context = "\n\n".join(f"[Source {i+1}: {c['metadata'].get('filename', 'document')}, page {c['metadata'].get('page') or 'N/A'}]\n{c['text']}" for i, c in enumerate(chunks))
    prompt = f"""You are a careful course assistant. Answer using ONLY the supplied context. If the context does not contain enough evidence, say that clearly. Do not invent facts. Respond in the same language as the question. Refer to sources using [Source 1], [Source 2], etc.
Question: {question}
Context:
{context}
Answer:"""
    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}, timeout=240)
    response.raise_for_status()
    return response.json().get("response", "").strip()
