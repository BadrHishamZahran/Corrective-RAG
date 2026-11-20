from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import DATA_DIR, MAX_CORRECTION_ATTEMPTS
from app.ingestion.document_loader import load_document, split_text
from app.vectorstore.chroma_store import add_chunks, collection
from app.retrieval.retriever import retrieve
from app.retrieval.evaluator import evaluate_retrieval
from app.correction.query_rewriter import rewrite_query
from app.generation.answer_generator import generate_answer

app = FastAPI(title="Corrective RAG API", version="1.0.0", description="Local CRAG system with retrieval evaluation and corrective re-retrieval")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)

@app.get("/")
def root():
    return {"message": "Corrective RAG API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "indexed_chunks": collection.count()}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported.")
    safe_name = Path(file.filename).name
    destination = DATA_DIR / f"{uuid4().hex}_{safe_name}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    destination.write_bytes(content)
    try:
        pages = load_document(destination)
        chunks = []
        for page_data in pages:
            for index, chunk in enumerate(split_text(page_data["text"])):
                chunks.append({"id": f"{destination.stem}_{page_data['page']}_{index}_{uuid4().hex[:8]}", "text": chunk, "metadata": {"filename": safe_name, "page": page_data["page"] or 0}})
        count = add_chunks(chunks)
        if count == 0:
            raise ValueError("No readable text was found in this file.")
        return {"message": "Document indexed successfully", "filename": safe_name, "chunks_added": count}
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/ask")
def ask(request: AskRequest):
    if collection.count() == 0:
        raise HTTPException(status_code=400, detail="Upload at least one document before asking a question.")
    original = request.question.strip()
    current_query = original
    attempts = []
    best_chunks = []
    best_grade = {"status": "irrelevant", "score": 0.0, "reason": "No retrieval attempted"}
    for attempt in range(MAX_CORRECTION_ATTEMPTS + 1):
        chunks = retrieve(current_query)
        grade = evaluate_retrieval(original, chunks)
        attempts.append({"query": current_query, "retrieved": len(chunks), "evaluation": grade})
        if grade["score"] >= best_grade["score"]:
            best_chunks, best_grade = chunks, grade
        if grade["status"] == "relevant" and grade["score"] >= 0.65:
            break
        if attempt < MAX_CORRECTION_ATTEMPTS:
            current_query = rewrite_query(original, grade.get("reason", "Weak retrieval"))
    answer = generate_answer(original, best_chunks)
    sources = []
    seen = set()
    for chunk in best_chunks:
        meta = chunk["metadata"]
        key = (meta.get("filename"), meta.get("page"))
        if key not in seen:
            seen.add(key)
            sources.append({"filename": meta.get("filename"), "page": meta.get("page") or None, "similarity": round(chunk["similarity"], 3)})
    return {"question": original, "answer": answer, "retrieval_status": best_grade["status"], "retrieval_score": round(best_grade["score"], 3), "corrected_query": current_query if current_query != original else None, "attempts": attempts, "sources": sources}
