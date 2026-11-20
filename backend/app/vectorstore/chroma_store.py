import chromadb
from app.config import CHROMA_PATH, COLLECTION_NAME
from app.embeddings.embedding_service import embed_texts

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

def add_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    texts = [item["text"] for item in chunks]
    embeddings = embed_texts(texts)
    ids = [item["id"] for item in chunks]
    metadatas = [item["metadata"] for item in chunks]
    collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return len(chunks)

def search(query: str, top_k: int) -> list[dict]:
    if collection.count() == 0:
        return []
    result = collection.query(query_embeddings=embed_texts([query]), n_results=min(top_k, collection.count()), include=["documents", "metadatas", "distances"])
    items = []
    for doc, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        items.append({"text": doc, "metadata": meta, "distance": float(distance), "similarity": max(0.0, 1.0 - float(distance))})
    return items
