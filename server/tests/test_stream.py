import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import orchestrator


async def main():
    print("Testing streaming pipeline for query: 'What causes acid rain?'")
    async for item in orchestrator.run_stream(query_text="What causes acid rain?"):
        ev = item["event"]
        data = json.loads(item["data"])
        if ev == "token":
            print(data["token"], end="", flush=True)
        elif ev == "metadata":
            print(f"\n[Metadata] Confidence: {data['confidence']:.2f}, Sources: {len(data['sources'])}, Timings: {data['timings_ms']}")
            print("[Answer streaming]: ", end="", flush=True)
        elif ev == "done":
            print(f"\n[Done] Grounded: {data['grounded']}, Total Latency: {data['total_latency_ms']}ms")
        elif ev == "blocked":
            print(f"\n[Blocked] Reason: {data.get('block_reason')}")


if __name__ == "__main__":
    asyncio.run(main())
