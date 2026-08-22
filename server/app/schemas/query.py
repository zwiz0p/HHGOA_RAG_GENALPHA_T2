from typing import List, Optional, Dict
from pydantic import BaseModel


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    chunk_strategy: str
    rerank_score: Optional[float] = None
    is_gold: Optional[bool] = None


class QueryResponse(BaseModel):
    transcript: Optional[str] = None
    answer: Optional[str] = None
    sources: List[SourceChunk] = []
    confidence: Optional[float] = None
    grounded: Optional[bool] = None
    blocked: bool = False
    block_reason: Optional[str] = None
    source_type: Optional[str] = "knowledge_base"  # "knowledge_base", "out_of_domain", "general_knowledge", "fast_path", "blocked"
    generation_mode: Optional[str] = "extractive"  # "extractive", "conversational_synthesis", "general_knowledge", "none", "fast_path"
    can_synthesize: bool = False
    can_fallback_general: bool = False
    prompt_synthesis: bool = False
    timings_ms: Dict[str, float] = {}
    total_latency_ms: float = 0.0
