"""
FastAPI application for the Rulebook QA system.
POST /ask endpoint with corpus loaded at startup.
Serves the frontend as static files.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.models import QuestionRequest, QAResponse, PassageResult
from backend.ingest import load_corpus
from backend.retrieval import TFIDFRetriever
from backend.classify import classify
from backend.generate import generate_answer
from backend.config import CORPUS_DIR, TOP_K

# --- Application Setup ---
app = FastAPI(
    title="Rulebook QA System",
    description="A QA system that detects contradictions in university policy documents.",
    version="1.0.0"
)

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load corpus and build index at startup ---
print(f"[startup] Loading corpus from: {CORPUS_DIR}")
chunks = load_corpus(CORPUS_DIR)
retriever = TFIDFRetriever(chunks)
print(f"[startup] System ready. {len(chunks)} chunks indexed.")


@app.post("/ask", response_model=QAResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question to the rulebook QA system.
    Returns classification (answered/not_covered/conflict) with supporting passages.
    """
    question = request.question.strip()

    # Edge case: empty or gibberish — return not_covered
    if not question or len(question) < 2:
        return QAResponse(
            type="not_covered",
            answer=None,
            passages=[],
            conflict_note=None
        )

    # Step 1: Retrieve top-k chunks
    results = retriever.search(question, top_k=TOP_K)

    # Step 2: Classify
    classification = classify(results)

    # Step 3: Build response
    response_type = classification["type"]
    conflict_note = classification.get("conflict_note")

    # Build passage objects
    if response_type == "conflict":
        passages = [
            PassageResult(
                section_id=r.section_id,
                source_file=r.source_file,
                text=r.text,
                score=r.score
            )
            for r in classification["passages"]
        ]
    elif response_type == "not_covered":
        passages = []  # No passages for not_covered — nothing relevant to show
    else:  # answered
        passages = [
            PassageResult(
                section_id=r.section_id,
                source_file=r.source_file,
                text=r.text,
                score=r.score
            )
            for r in results[:5]  # Show top 5 passages
        ]

    # Generate answer (only for 'answered' type)
    answer = None
    if response_type == "answered":
        answer_passages = classification.get("answer_passages", results[:3])
        answer = generate_answer(question, answer_passages)

    return QAResponse(
        type=response_type,
        answer=answer,
        passages=passages,
        conflict_note=conflict_note
    )


# --- Serve Frontend ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Access the API at /ask"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "chunks_loaded": len(chunks),
        "corpus_dir": CORPUS_DIR
    }

# Serve style.css, app.js, about.html, etc. — must come after all routes above
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend-assets")