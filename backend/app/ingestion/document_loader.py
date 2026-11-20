from pathlib import Path
import pymupdf
from docx import Document
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def load_document(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    pages = []
    if suffix == ".pdf":
        with pymupdf.open(path) as pdf:
            for i, page in enumerate(pdf):
                text = page.get_text("text").strip()
                if text:
                    pages.append({"text": text, "page": i + 1})
    elif suffix == ".docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if text:
            pages.append({"text": text, "page": None})
    elif suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            pages.append({"text": text, "page": None})
    else:
        raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")
    return pages

def split_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + CHUNK_SIZE]).strip()
        if chunk:
            chunks.append(chunk)
        if start + CHUNK_SIZE >= len(words):
            break
    return chunks
