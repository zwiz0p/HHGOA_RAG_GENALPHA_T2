import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import query
from app.deps import (
    get_embedder,
    get_reranker,
    get_dense_matrix,
    get_corpus_chunks,
    get_bm25s_retriever,
    get_bm25_index,
    get_qdrant_client,
)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Loading RAG models and indexes...")

    get_embedder()
    get_reranker()
    get_dense_matrix()
    get_corpus_chunks()
    get_bm25s_retriever()
    get_bm25_index()
    get_qdrant_client()

    logging.info("RAG models and indexes loaded.")

    yield


app = FastAPI(
    title="HH Goa Voice RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(query.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}