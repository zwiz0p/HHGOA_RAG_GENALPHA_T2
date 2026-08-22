# Latency Report
Benchmarked over 20 queries (11 completed, 9 blocked by guardrails).
## End-to-end
| Percentile | Latency (ms) |
|---|---|
| P50 | 2363.84 |
| P70 | 2518.79 |
| P100 | 2663.83 |

## Per-stage breakdown
| Stage | P50 | P70 | P100 |
|---|---|---|---|
| bm25_retrieval | 1.78 | 2.19 | 4.45 |
| confidence_guardrail | 0.01 | 0.01 | 0.02 |
| dense_retrieval | 287.32 | 298.65 | 334.05 |
| fusion | 0.05 | 0.05 | 0.08 |
| generation | 1387.87 | 1635.77 | 1957.25 |
| grounding_guardrail | 0.15 | 0.23 | 59.67 |
| pre_retrieval_guardrail | 0.02 | 0.02 | 0.03 |
| rerank | 149.64 | 184.92 | 218.92 |
| retrieval_parallel | 288.06 | 299.42 | 334.84 |
