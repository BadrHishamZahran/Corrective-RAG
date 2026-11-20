from sentence_transformers import SentenceTransformer
from functools import lru_cache
from app.config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(EMBEDDING_MODEL, device="cpu")

def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()
