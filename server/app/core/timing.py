"""
Lightweight context-manager based stage timer. The orchestrator uses this
to build the `timings` dict that goes into every response and every
benchmark row — this IS the mechanism that makes the P50/P70/P100 report
possible, so keep it dependency-free and cheap (no logging I/O inside the
timed block itself).
"""

import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self):
        self.timings = {}

    @contextmanager
    def track(self, stage_name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.timings[stage_name] = round(elapsed_ms, 2)

    @property
    def total_ms(self) -> float:
        return round(sum(self.timings.values()), 2)
