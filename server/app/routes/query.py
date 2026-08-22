from fastapi import APIRouter, UploadFile, File, Form, Body
from sse_starlette.sse import EventSourceResponse
from typing import Optional, Dict, Any

from app.pipeline import orchestrator
from app.pipeline.retrieval import chunk_comparison
from app.schemas.query import QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_text(
    text: str = Form(...),
    strategy: Optional[str] = Form("sentence_aware"),
):
    """Instant sub-70ms extractive text retrieval from MSMARCO dataset."""
    return orchestrator.run(query_text=text)


@router.post("/query/voice", response_model=QueryResponse)
async def query_voice(
    audio: UploadFile = File(...),
    language_code: Optional[str] = Form(None),
    strategy: Optional[str] = Form("sentence_aware"),
):
    """Voice-in path returning instant extractive answer in < 200ms."""
    audio_bytes = await audio.read()
    return orchestrator.run(audio_bytes=audio_bytes, language_code=language_code)


@router.post("/query/stream")
async def query_text_stream(
    text: str = Form(...),
    strategy: Optional[str] = Form("sentence_aware"),
):
    """Instant sub-70ms streaming text query via Server-Sent Events (SSE)."""
    return EventSourceResponse(orchestrator.run_stream(query_text=text))


@router.post("/query/voice/stream")
async def query_voice_stream(
    audio: UploadFile = File(...),
    language_code: Optional[str] = Form(None),
    strategy: Optional[str] = Form("sentence_aware"),
):
    """Streaming voice query path."""
    audio_bytes = await audio.read()
    return EventSourceResponse(orchestrator.run_stream(audio_bytes=audio_bytes, language_code=language_code))


@router.post("/query/synthesize")
@router.post("/synthesize/stream")
async def synthesize_stream(
    query: str = Form(...),
    mode: Optional[str] = Form("conversational_synthesis"),
    context: Optional[str] = Form(None),
):
    """
    On-Demand Conversational or General Knowledge Synthesis via Gemini 2.5 Flash.
    Accepts mode='conversational_synthesis' or mode='general_knowledge'.
    """
    return EventSourceResponse(orchestrator.stream_synthesize(
        query_text=query,
        mode=mode or "conversational_synthesis",
        context=context,
    ))


@router.post("/compare-chunking")
@router.post("/chunking/compare")
@router.get("/compare-chunking")
@router.get("/chunking/compare")
async def compare_chunking(
    query: Optional[str] = Form(None),
    body: Optional[Dict[str, Any]] = Body(None),
):
    """
    Live Multi-Strategy Chunking Comparison:
    Evaluates sentence_aware, fixed_overlap, semantic, and metadata_aware chunkers
    on the incoming query and returns side-by-side latency, boundary preservation, and scores.
    """
    q = query or (body.get("query") if body else None) or "Who directed the Los Alamos Laboratory during the Manhattan Project?"
    return chunk_comparison.compare_chunking_strategies(q)

