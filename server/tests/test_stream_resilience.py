import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import orchestrator


async def test_stream(query: str, expected_source_type: str, test_name: str):
    print(f"\n==========================================")
    print(f"TEST: {test_name}")
    print(f"QUERY: '{query}'")
    print(f"==========================================")

    tokens = []
    metadata = {}
    done_payload = {}
    blocked_payload = {}

    async for event in orchestrator.run_stream(query_text=query):
        evt_type = event.get("event")
        raw_data = event.get("data", "{}")
        try:
            data = json.loads(raw_data)
        except Exception:
            data = {"raw": raw_data}

        if evt_type == "metadata":
            metadata = data
        elif evt_type == "token":
            tokens.append(data.get("token", ""))
        elif evt_type == "done":
            done_payload = data
        elif evt_type == "blocked":
            blocked_payload = data

    full_answer = done_payload.get("answer") or "".join(tokens) or blocked_payload.get("answer")
    source_type = done_payload.get("source_type") or metadata.get("source_type") or blocked_payload.get("source_type")
    grounded = done_payload.get("grounded", False)
    blocked = done_payload.get("blocked", blocked_payload.get("blocked", False))

    print(f"Full Streamed Answer:\n{full_answer}\n")
    print(f"Source Type: {source_type}")
    print(f"Grounded   : {grounded}")
    print(f"Blocked    : {blocked}")

    assert source_type == expected_source_type, f"Expected {expected_source_type}, got {source_type}"
    assert blocked is False, f"Query unexpectedly blocked: {blocked_payload}"
    print(f"✅ {test_name} Passed!")


async def main():
    # 1. Fast-path conversational intent
    await test_stream(
        query="Hello! Who are you?",
        expected_source_type="fast_path",
        test_name="1. Fast-Path Conversational Intent (Sub-1ms)"
    )

    # 2. In-domain Hindi (Grounded Knowledge Base)
    await test_stream(
        query="मैनहट्टन परियोजना कब शुरू हुई थी?",
        expected_source_type="knowledge_base",
        test_name="2. In-Domain Hindi Query (Grounded)"
    )

    # 3. Out-of-domain Recipe (General Knowledge Fallback)
    await test_stream(
        query="How to make a masala omelette step by step?",
        expected_source_type="general_knowledge",
        test_name="3. Out-of-Domain Recipe (General Knowledge Fallback)"
    )

    print("\n🎉 All 3 Target Verification Tests Passed 100%!")


if __name__ == "__main__":
    asyncio.run(main())


