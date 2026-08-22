# Guardrails

Two checkpoints, chosen so the pipeline fails cheap and early rather than
expensively and late.

## 1. Pre-retrieval (`app/pipeline/guardrails/pre_retrieval.py`)

Runs before any embedding or search work.

- **Unsafe content**: deny-list keyword match. Placeholder-grade — flagged
  in code comments to swap for a real moderation endpoint before any
  production use beyond the hackathon.
- **Off-topic**: query embedding compared against a cached centroid of
  ~500 sampled indexed-chunk embeddings. If cosine similarity to the
  dataset's topic centroid is below threshold, we reject before spending
  retrieval+generation latency on something the corpus can't answer.

Example: "What's the weather in Goa?" against a MS MARCO-derived index →
rejected as off-topic, never reaches the LLM.

## 2. Post-retrieval confidence (`confidence_check.py`)

After rerank, before generation. If the top reranked candidate's
(sigmoid-normalized) score is below threshold, we skip generation entirely
and return "I don't have enough information" — this is also a latency
optimization, since it's the single most expensive stage we can skip.

## 3. Post-generation grounding (`grounding_check.py`)

After the LLM answers. Checks the answer against the retrieved context
using lexical token overlap as the primary signal, falling back to
embedding similarity for ambiguous mid-range overlap scores. Deliberately
**not** another LLM call — that would double generation latency for
marginal verification gain. If the answer isn't grounded, we return a
"couldn't generate a grounded answer" response instead of shipping a
plausible-sounding hallucination.

## What "doesn't answer" looks like end to end

| Guardrail | Trigger | Response |
|---|---|---|
| Pre-retrieval | off-topic / unsafe / empty | Blocked before retrieval, `block_reason` set |
| Confidence | weak retrieval match | "not enough information," sources shown for transparency |
| Grounding | answer diverges from context | "couldn't generate a grounded answer" |

All three paths return the same structured `QueryResponse` shape (see
`app/schemas/query.py`) with `blocked: true` and a `block_reason` — the
frontend renders these distinctly from successful answers rather than
treating them as errors.
