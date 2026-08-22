from typing import List, Dict, AsyncGenerator
import json
import httpx

from app.core import config

SYSTEM_PROMPT = (
    "You are a factual AI assistant for the MSMARCO-XI dataset. "
    "Answer the user's question directly and concisely in 1-2 sentences in the same language as the query (English or Hindi) "
    "using the facts in the provided context passages. "
    "Do not say 'context lacks information' or 'संदर्भ में जानकारी नहीं है' — concisely state the relevant facts directly from the context."
)




GENERAL_KNOWLEDGE_SYSTEM_PROMPT = (
    "You are a knowledgeable, concise assistant. Answer the user's question accurately "
    "in 1-3 clear sentences using general world knowledge in the same language as the query (English or Hindi)."
)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_STREAM_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"


def build_prompt(query: str, chunks: List[Dict]) -> str:
    context_block = "\n\n".join(
        f"[Source {i+1}] {c['text']}" for i, c in enumerate(chunks)
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Answer in 1-2 concise sentences:"
    )


def generate(query: str, chunks: List[Dict]) -> str:
    prompt = build_prompt(query, chunks)
    url = GEMINI_URL.format(model=config.LLM_MODEL)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature": 0.1
        }
    }

    with httpx.Client(timeout=20) as client:
        resp = client.post(url, params={"key": config.LLM_API_KEY}, json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        candidates = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in candidates).strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {data}") from e


def generate_general(query: str) -> str:
    """Generates general world knowledge response when out of knowledge base scope."""
    url = GEMINI_URL.format(model=config.LLM_MODEL)
    prompt = f"{GENERAL_KNOWLEDGE_SYSTEM_PROMPT}\n\nQuestion: {query}\n\nAnswer:"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 250,
            "temperature": 0.2
        }
    }

    with httpx.Client(timeout=20) as client:
        resp = client.post(url, params={"key": config.LLM_API_KEY}, json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        candidates = data["candidates"][0]["content"]["parts"]
        body = "".join(p.get("text", "") for p in candidates).strip()
        return f"⚠️ *Note: Not found in indexed MSMARCO-XI dataset. Answering from General World Knowledge:*\n\n{body}"
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {data}") from e


async def stream_generate(query: str, chunks: List[Dict]) -> AsyncGenerator[str, None]:
    """Streams tokens directly from Gemini API using SSE."""
    prompt = build_prompt(query, chunks)
    url = GEMINI_STREAM_URL.format(model=config.LLM_MODEL)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", url, params={"key": config.LLM_API_KEY, "alt": "sse"}, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                    parts = chunk_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    for part in parts:
                        text = part.get("text", "")
                        if text:
                            yield text
                except Exception:
                    continue


async def stream_generate_general(query: str) -> AsyncGenerator[str, None]:
    """Streams general knowledge tokens with disclaimer prefix."""
    prefix = "⚠️ *Note: Not found in indexed MSMARCO-XI dataset. Answering from General World Knowledge:*\n\n"
    yield prefix

    url = GEMINI_STREAM_URL.format(model=config.LLM_MODEL)
    prompt = f"{GENERAL_KNOWLEDGE_SYSTEM_PROMPT}\n\nQuestion: {query}\n\nAnswer:"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 250,
            "temperature": 0.2
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", url, params={"key": config.LLM_API_KEY, "alt": "sse"}, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                    parts = chunk_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    for part in parts:
                        text = part.get("text", "")
                        if text:
                            yield text
                except Exception:
                    continue


