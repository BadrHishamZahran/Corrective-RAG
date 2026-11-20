from app.config import TOP_K
from app.vectorstore.chroma_store import search

def retrieve(query: str) -> list[dict]:
    return search(query, TOP_K)
