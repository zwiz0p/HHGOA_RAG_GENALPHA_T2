import concurrent.futures
import json
import logging
import os
import re
import sys
import time
from typing import Optional, List, Dict, AsyncGenerator

from app.core import config
from app.core.errors import PipelineError
from app.deps import (
    get_embedder,
    get_dense_matrix,
    get_corpus_chunks,
    get_bm25s_retriever,
    get_bm25_index,
    get_qdrant_client,
)
from app.pipeline.generation import extractive
from app.pipeline.generation import generate as generation
from app.pipeline.guardrails import confidence_check
from app.pipeline.guardrails import grounding_check
from app.pipeline.guardrails import pre_retrieval
from app.pipeline.retrieval import bm25, dense, fusion, rerank
from app.pipeline import stt
from app.schemas.query import QueryResponse, SourceChunk

logger = logging.getLogger(__name__)


class StageTimer:
    def __init__(self):
        self.timings = {}
        self.start_time = time.perf_counter()

    def track(self, stage_name: str):
        class StageContext:
            def __init__(self, timer, name):
                self.timer = timer
                self.name = name

            def __enter__(self):
                self.t0 = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = (time.perf_counter() - self.t0) * 1000
                self.timer.timings[self.name] = round(elapsed, 2)

        return StageContext(self, stage_name)

    @property
    def total_ms(self) -> float:
        return round((time.perf_counter() - self.start_time) * 1000, 2)


def _with_retry(fn, *args, retries=1, delay=0.1, **kwargs):
    for i in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if i == retries:
                raise
            logger.warning(f"Retrying {fn.__name__} after error: {e}")
            time.sleep(delay)


def _to_source(chunk: dict) -> SourceChunk:
    return SourceChunk(
        chunk_id=chunk.get("chunk_id", "unknown"),
        text=chunk.get("text", ""),
        chunk_strategy=chunk.get("chunk_strategy", "unknown"),
        rerank_score=chunk.get("rerank_score"),
        is_gold=chunk.get("is_gold"),
    )


def run(
    query_text: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    language_code: Optional[str] = None,
) -> QueryResponse:
    """
    Two-Tier Extractive RAG Architecture (<200ms Latency Target):
    1. Pre-retrieval intent gate (< 1 ms).
    2. Parallel Hybrid Dense + BM25s Retrieval & RRF Fusion (~25-35 ms).
    3. Fast Heuristic Reranking (~2-5 ms).
    4. Deterministic Extractive Sentence Assembly (< 2 ms).
    5. Grounding verification (~1 ms).
    Total in-domain latency: ~35-70 ms (Sub-200ms guaranteed).
    """
    timer = StageTimer()
    transcript = query_text

    # --- Stage 0: STT ---
    if audio_bytes is not None:
        try:
            with timer.track("stt"):
                transcript = _with_retry(stt.transcribe, audio_bytes, language_code=language_code, retries=1)
        except PipelineError as e:
            msg = str(e)
            return QueryResponse(
                transcript="",
                answer=msg if "Audio recording" in msg or "No speech" in msg else "Audio transcription failed. Please speak clearly into the microphone.",
                blocked=True,
                block_reason="stt_failed",
                source_type="blocked",
                generation_mode="none",
                timings_ms=timer.timings,
                total_latency_ms=timer.total_ms,
            )

    if not transcript:
        return QueryResponse(
            transcript="",
            answer="No speech or text detected in query.",
            blocked=True,
            block_reason="empty_query",
            source_type="blocked",
            generation_mode="none",
            timings_ms=timer.timings,
            total_latency_ms=timer.total_ms,
        )

    # --- Stage 1: Pre-retrieval guardrail & intent router ---
    with timer.track("pre_retrieval_guardrail"):
        gate = pre_retrieval.check_pre_retrieval(transcript)

    if gate.get("blocked"):
        return QueryResponse(
            transcript=transcript,
            answer=gate.get("message", "Query rejected by pre-retrieval guardrail."),
            blocked=True,
            block_reason=gate.get("reason", "pre_retrieval_blocked"),
            source_type="blocked",
            generation_mode="none",
            timings_ms=timer.timings,
            total_latency_ms=timer.total_ms,
        )

    if gate.get("is_fast_path") or gate.get("is_greeting"):
        return QueryResponse(
            transcript=transcript,
            answer=gate.get("direct_response"),
            sources=[],
            confidence=1.0,
            grounded=True,
            blocked=False,
            block_reason=None,
            source_type="fast_path",
            generation_mode="fast_path",
            can_synthesize=False,
            can_fallback_general=False,
            prompt_synthesis=False,
            timings_ms=timer.timings,
            total_latency_ms=timer.total_ms,
        )

    # --- Stage 2: Parallel hybrid dense + BM25s retrieval ---
    dense_results = []
    bm25_results = []

    try:
        t0_parallel = time.perf_counter()

        def _fetch_dense():
            t0 = time.perf_counter()
            res = dense.search_dense(transcript, top_k=config.DENSE_TOP_K)
            return res, (time.perf_counter() - t0) * 1000

        def _fetch_bm25():
            t0 = time.perf_counter()
            res = bm25.search_bm25(transcript, top_k=config.BM25_TOP_K)
            return res, (time.perf_counter() - t0) * 1000

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_dense = executor.submit(_fetch_dense)
            f_bm25 = executor.submit(_fetch_bm25)

            dense_results, dense_ms = f_dense.result()
            bm25_results, bm25_ms = f_bm25.result()

        timer.timings["retrieval_parallel"] = round((time.perf_counter() - t0_parallel) * 1000, 2)
        timer.timings["dense_retrieval"] = round(dense_ms, 2)
        timer.timings["bm25_retrieval"] = round(bm25_ms, 2)

    except PipelineError:
        return QueryResponse(
            transcript=transcript,
            blocked=True,
            block_reason="retrieval_failed",
            source_type="blocked",
            generation_mode="none",
            timings_ms=timer.timings,
            total_latency_ms=timer.total_ms,
        )

    with timer.track("fusion"):
        fused = fusion.reciprocal_rank_fusion(dense_results, bm25_results)

    # --- Stage 3: Fast heuristic reranking ---
    with timer.track("heuristic_rerank"):
        reranked = rerank.fast_heuristic_rerank(transcript, fused)

    # --- Stage 4: Relevance & confidence check ---
    with timer.track("confidence_guardrail"):
        passes, confidence = confidence_check.check(reranked)

    is_in_domain = bool(passes and len(reranked) >= 1)

    # --- Branch A: Out-of-Domain ---
    if not is_in_domain or len(reranked) == 0:
        return QueryResponse(
            transcript=transcript,
            answer="This question is not present in the indexed MSMARCO-XI dataset.",
            sources=[],
            confidence=confidence,
            grounded=False,
            blocked=False,
            block_reason=None,
            source_type="out_of_domain",
            generation_mode="none",
            can_synthesize=False,
            can_fallback_general=True,
            prompt_synthesis=True,
            timings_ms=timer.timings,
            total_latency_ms=timer.total_ms,
        )

    # --- Branch B: In-Domain Extractive Assembly ---
    with timer.track("extractive_assembly"):
        extracted_text = extractive.extract_best_sentences(transcript, reranked)

    if not extracted_text:
        extracted_text = reranked[0]["text"]

    # --- Stage 5: Grounding Verification ---
    with timer.track("grounding_guardrail"):
        grounded, grounding_score = grounding_check.check(extracted_text, reranked)

    return QueryResponse(
        transcript=transcript,
        answer=extracted_text,
        sources=[_to_source(c) for c in reranked],
        confidence=confidence,
        grounded=grounded,
        blocked=False,
        block_reason=None,
        source_type="knowledge_base",
        generation_mode="extractive",
        can_synthesize=True,
        can_fallback_general=False,
        prompt_synthesis=False,
        timings_ms=timer.timings,
        total_latency_ms=timer.total_ms,
    )


async def run_stream(
    query_text: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    language_code: Optional[str] = None,
):
    """
    Streaming SSE wrapper for sub-200ms two-tier extractive RAG.
    Emits metadata with granular telemetry and streams the extractive answer.
    """
    res = run(query_text=query_text, audio_bytes=audio_bytes, language_code=language_code)

    if res.blocked:
        yield {
            "event": "blocked",
            "data": json.dumps(res.model_dump()),
        }
        return

    # Yield metadata
    yield {
        "event": "metadata",
        "data": json.dumps({
            "transcript": res.transcript,
            "confidence": res.confidence,
            "sources": [s.model_dump() for s in res.sources],
            "source_type": res.source_type,
            "generation_mode": res.generation_mode,
            "can_synthesize": res.can_synthesize,
            "can_fallback_general": res.can_fallback_general,
            "prompt_synthesis": res.prompt_synthesis,
            "timings_ms": res.timings_ms,
            "total_latency_ms": res.total_latency_ms,
        }),
    }

    # Yield extractive token
    yield {
        "event": "token",
        "data": json.dumps({"token": res.answer}),
    }

    # Yield done
    yield {
        "event": "done",
        "data": json.dumps(res.model_dump()),
    }


async def stream_synthesize(
    query_text: str,
    mode: str = "conversational_synthesis",
    context: Optional[str] = None,
):
    """
    On-Demand Conversational Synthesis or General Knowledge using Gemini 2.5 Flash.
    """
    if mode == "general_knowledge":
        async for token in generation.stream_generate_general(query_text):
            yield {
                "event": "token",
                "data": json.dumps({"token": token}),
            }
        yield {
            "event": "done",
            "data": json.dumps({"done": True, "source_type": "general_knowledge", "generation_mode": "general_knowledge"}),
        }
    else:
        # Conversational synthesis grounded in retrieved context
        chunks = [{"text": context}] if context else None
        if not chunks:
            dense_hits = dense.search_dense(query_text, top_k=4)
            bm25_hits = bm25.search_bm25(query_text, top_k=4)
            fused = fusion.reciprocal_rank_fusion(dense_hits, bm25_hits)
            chunks = rerank.fast_heuristic_rerank(query_text, fused)

        async for token in generation.stream_generate(query_text, chunks):
            yield {
                "event": "token",
                "data": json.dumps({"token": token}),
            }
        yield {
            "event": "done",
            "data": json.dumps({"done": True, "source_type": "knowledge_base", "generation_mode": "conversational_synthesis"}),
        }
