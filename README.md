# Corrective RAG (CRAG)

A fully local Corrective Retrieval-Augmented Generation system. It retrieves relevant document chunks, evaluates retrieval quality, rewrites the question and retries retrieval when the first results are weak, then generates a grounded answer with source references.

## 1. Project objective

Traditional RAG retrieves passages and sends them directly to an LLM. CRAG adds a correction loop:

1. Load and split course documents.
2. Create embeddings and store chunks in ChromaDB.
3. Retrieve the most relevant chunks for a question.
4. Grade the retrieved context as **relevant**, **partially relevant**, or **irrelevant**.
5. If context is weak, rewrite the question and retrieve again.
6. Select the strongest available context and generate an answer with citations.
7. If the documents do not contain enough evidence, say so instead of inventing an answer.

## 2. Main features

- Local LLM inference through Ollama (`qwen2.5:3b`).
- Local embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
- Persistent ChromaDB vector store.
- PDF, DOCX, and TXT ingestion.
- Retrieval relevance grading and query correction.
- One corrective retrieval attempt (configurable).
- Source filename and page information in responses.
- FastAPI backend and minimal React/Vite frontend.
- No paid API, subscription, or GPU required.

## 3. Technology stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Local LLM | Ollama – Qwen2.5 3B |
| Embeddings | Sentence Transformers – all-MiniLM-L6-v2 |
| Vector database | ChromaDB |
| API | FastAPI + Uvicorn |
| Document parsing | PyMuPDF, python-docx |
| Frontend | React + Vite |

The CRAG control flow is implemented explicitly in Python so the retrieval grader, query rewriting, and correction decision are easy to inspect. LangChain is not required to run this version.

## 4. Requirements

- Windows 10/11 (commands below use CMD)
- Python 3.10 or newer
- Node.js 20 or newer
- Ollama installed
- At least 8 GB RAM; 16 GB recommended
- Internet for the initial Python package and embedding-model downloads

No NVIDIA GPU is required. The first embedding-model download requires internet; after it is cached, embeddings can run locally.

## 5. Project structure

```text
Corrective-RAG/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── ingestion/
│   │   │   └── document_loader.py
│   │   ├── embeddings/
│   │   │   └── embedding_service.py
│   │   ├── vectorstore/
│   │   │   └── chroma_store.py
│   │   ├── retrieval/
│   │   │   ├── retriever.py
│   │   │   └── evaluator.py
│   │   ├── correction/
│   │   │   └── query_rewriter.py
│   │   └── generation/
│   │       └── answer_generator.py
│   ├── data/documents/       # Put course files here if desired
│   ├── chroma_db/            # Created automatically; do not upload
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/App.jsx
│   ├── src/main.jsx
│   ├── src/styles.css
│   ├── package.json
│   ├── index.html
│   └── vite.config.js
├── .gitignore
└── README.md
```

## 6. Installation and setup (Windows CMD)

### Step 1 – Verify Ollama and download the model

If you completed Project 2, Ollama and the model should already be installed. Verify:

```cmd
ollama --version
ollama list
```

Make sure `qwen2.5:3b` appears in the list. If it does not:

```cmd
ollama pull qwen2.5:3b
```

Keep Ollama running. Its local API is normally available at `http://localhost:11434`.

### Step 2 – Create and activate the backend environment

Open CMD inside the project folder:

```cmd
cd backend
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Use Python 3.10 or newer. The `py -3` command selects an available Python 3 installation; verify the selected version with `python --version` and make sure it is 3.10 or newer.

### Step 3 – Run the backend

From the `backend` directory, with `.venv` activated:

```cmd
uvicorn app.main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

### Step 4 – Install and run the frontend

Open a **second CMD window** in the project root:

```cmd
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually http://localhost:5173.

## 7. Add course documents

Use the website's upload control to upload PDF, DOCX, or TXT files. Alternatively, place supported files in `backend/data/documents/` and upload them through the API endpoint. The current starter indexes uploaded files through the API; simply copying a file into the folder does not automatically index it.

Supported formats: `.pdf`, `.docx`, `.txt`.

## 8. Test the API

1. Open http://127.0.0.1:8000/docs.
2. Run `POST /upload` and upload a course document.
3. Run `POST /ask` with a question that can be answered from that document.
4. Inspect `retrieval_status`, `corrected_query`, `attempts`, and `sources` in the response.

Example request:

```json
{
  "question": "What are the main topics covered in this document?"
}
```

Try a question that is not answered in the document as well. The system should clearly state when the available context is insufficient.

## 9. How the corrective workflow works

```text
Question
   ↓
Initial retrieval from ChromaDB
   ↓
LLM relevance grader
   ├── Relevant → Generate grounded answer
   └── Weak / partial → Rewrite query → Retrieve again → Grade again
                                               ↓
                                  Choose best available context
                                               ↓
                                  Generate answer + sources
```

The grader is an LLM-based heuristic, not a guaranteed fact checker. Always evaluate it with relevant, irrelevant, ambiguous, and out-of-scope questions.

## 10. Configuration

Edit `backend/.env`:

- `OLLAMA_BASE_URL`: local Ollama URL.
- `OLLAMA_MODEL`: model name; default `qwen2.5:3b`.
- `EMBEDDING_MODEL`: Sentence Transformers model.
- `TOP_K`: number of chunks retrieved per attempt.
- `CHUNK_SIZE` and `CHUNK_OVERLAP`: chunking configuration.
- `RELEVANCE_THRESHOLD`: minimum relevance score used by the grader.

## 11. Troubleshooting

- **Ollama connection error:** run `ollama list`; make sure the Ollama app/service is running.
- **Model not found:** run `ollama pull qwen2.5:3b`.
- **Port 8000 is busy:** run `uvicorn app.main:app --reload --port 8001` and update the frontend API URL if needed.
- **Port 5173 is busy:** Vite will usually offer another available port.
- **Slow first startup:** Sentence Transformers downloads and initializes its embedding model on first use.
- **No answer / no sources:** upload and index a document first; ask a question covered by its content.
- **Low-quality grading:** try a clearer question and inspect the grader output; LLM relevance grading can make mistakes.

## 12. GitHub upload

Create an empty repository on GitHub, for example `Corrective-RAG`. Do not initialize it with a README if you already have this local README.

From the project root:

```cmd
git init
git add .
git status
git commit -m "Add Corrective RAG project"
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/Corrective-RAG.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Check `git status` before committing. The `.gitignore` excludes virtual environments, `.env`, uploaded documents, and the local Chroma database. Do not upload private course material or model/cache files unless you have permission. If Git is not installed, install Git for Windows first.

## 13. Suggested evaluation checklist

- [ ] Relevant question: retrieves the expected source and answers correctly.
- [ ] Paraphrased question: still finds the right chunks.
- [ ] Weak initial retrieval: triggers query rewriting and another retrieval attempt.
- [ ] Out-of-scope question: avoids fabricating an answer.
- [ ] Multiple documents: cites the correct filenames/pages.
- [ ] Restart backend: previously indexed Chroma data remains available.

## 14. Limitations and future improvements

This is an educational starter implementation, not a production-grade knowledge platform. Useful next improvements include document deletion and re-indexing, per-course collections, hybrid search, cross-encoder reranking, stronger structured grading, streaming answers, automated evaluation datasets, and authentication.

## 15. License and responsible use

Use documents you own or are authorized to process. Review source passages before relying on generated answers. Add an appropriate open-source license before publishing if you intend others to reuse the code.
