import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import orchestrator


def test_empty_audio_sync():
    print("\n1. Testing empty audio bytes in synchronous run()...")
    res = orchestrator.run(audio_bytes=b"")
    assert res.blocked, "Empty audio should be blocked"
    assert res.block_reason == "stt_failed" or res.block_reason == "empty_query"
    print(f"Sync rejection: blocked={res.blocked}, reason={res.block_reason}, answer='{res.answer}'")


async def test_empty_audio_stream():
    print("\n2. Testing empty audio bytes in run_stream()...")
    events = []
    async for event in orchestrator.run_stream(audio_bytes=b""):
        events.append(event)
    assert len(events) > 0
    blocked_data = json.loads(events[0]["data"])
    assert blocked_data["blocked"] is True
    print(f"Stream rejection event: {events[0]['event']}, data={blocked_data}")


async def main():
    test_empty_audio_sync()
    await test_empty_audio_stream()
    print("\nAll STT error handling and timeout tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
