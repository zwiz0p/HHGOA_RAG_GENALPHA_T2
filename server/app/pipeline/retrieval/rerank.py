import re
from typing import List, Dict

from app.core import config
from app.deps import get_reranker

MAX_RERANK_CANDIDATES = 4

GENERIC_WORDS = {
    "how", "what", "who", "where", "when", "why", "which", "whose", "whom",
    "did", "does", "do", "make", "making", "use", "using", "used", "step", "steps",
    "types", "type", "find", "get", "give", "tell", "way", "ways",
    "work", "works", "program", "form", "mean", "means", "know", "different",
    "best", "good", "easy", "simple", "fast", "quick", "called", "name", "named",
    "the", "a", "an", "in", "on", "of", "to", "is", "was", "are", "were", "with",
    "for", "by", "at", "it", "this", "that", "from", "about", "into", "over", "after", "before", "and", "or", "but", "so", "if",
    "का", "की", "के", "में", "पर", "से", "को", "ने", "और", "या", "एक", "यह", "वह",
    "है", "हैं", "था", "थी", "थे", "हुई", "हुआ", "हुए", "होना", "होने",
    "कैसे", "क्या", "क्यों", "कहाँ", "कब", "किस", "किसने", "किसके", "कौन"
}

CORE_MODIFIERS = {
    "immediate", "impact", "effects", "effect", "success", "history", "reason",
    "reasons", "cause", "causes", "process", "procedure", "meaning", "definition",
    "define", "result", "results", "consequence", "cast", "wear", "class", "role",
    "प्रभाव", "कारण", "सफलता", "परिणाम", "अर्थ", "परिभाषा", "कास्ट"
}


def fast_heuristic_rerank(query: str, candidates: List[Dict], top_k: int = config.RERANK_TOP_K) -> List[Dict]:
    """
    Sub-5ms Calibrated Multilingual Heuristic Reranker with Subject-Entity Grounding:
    Enforces strict domain-subject entity preservation to eliminate distractor hallucinations.
    """
    if not candidates:
        return []

    eval_candidates = candidates[:8]
    query_clean = re.sub(r"[^\w\s\u0900-\u097F]", " ", query.lower())
    is_hindi_query = bool(re.search(r"[\u0900-\u097F]", query_clean))

    all_words = [w for w in query_clean.split() if len(w) > 1 and w not in GENERIC_WORDS]
    subject_entities = [w for w in all_words if w not in CORE_MODIFIERS]
    if not subject_entities:
        subject_entities = all_words

    num_subjects = max(len(subject_entities), 1)
    num_all = max(len(all_words), 1)

    for c in eval_candidates:
        text_raw = c.get("text", "")
        text_clean = re.sub(r"[^\w\s\u0900-\u097F]", " ", text_raw.lower())
        text_tokens = set(text_clean.split())
        c_lang = c.get("language", "")
        dense_score = float(c.get("dense_score", 0.0))

        # 1. Subject entity matching
        matched_subjects = set()
        for ent in subject_entities:
            if ent in text_tokens or ent in text_clean:
                matched_subjects.add(ent)
            elif is_hindi_query and len(ent) >= 3:
                if any(t.startswith(ent[:3]) or ent[:3] in t for t in text_tokens):
                    matched_subjects.add(ent)
            elif not is_hindi_query and len(ent) >= 5:
                # English inflection/stem matching (e.g. directed -> director, produce -> produced)
                stem = ent[:5]
                if any(t.startswith(stem) for t in text_tokens if len(t) >= 5):
                    matched_subjects.add(ent)

        subject_ratio = len(matched_subjects) / num_subjects

        # 2. All content words matching
        matched_all = set()
        for w in all_words:
            if w in text_tokens or w in text_clean:
                matched_all.add(w)
            elif is_hindi_query and len(w) >= 3:
                if any(t.startswith(w[:3]) or w[:3] in t for t in text_tokens):
                    matched_all.add(w)
            elif not is_hindi_query and len(w) >= 5:
                stem = w[:5]
                if any(t.startswith(stem) for t in text_tokens if len(t) >= 5):
                    matched_all.add(w)

        all_ratio = len(matched_all) / num_all

        # Exact substring phrase match
        exact_bonus = 0.40 if (len(query_clean.strip()) > 8 and query_clean.strip() in text_clean) else 0.0

        # Bigram matches
        bigram_count = 0
        if len(all_words) >= 2:
            for i in range(len(all_words) - 1):
                if f"{all_words[i]} {all_words[i+1]}" in text_clean:
                    bigram_count += 1
        bigram_bonus = min(bigram_count * 0.20, 0.40)

        # Normalized signals
        norm_dense = min(max((dense_score - 0.35) / 0.40, 0.0), 1.0)
        raw_fusion = c.get("fusion_score", 0.0)
        norm_fusion = min(raw_fusion / 0.030, 1.0)
        lang_bonus = 0.10 if (is_hindi_query and "hin" in c_lang) or (not is_hindi_query and "eng" in c_lang) else 0.0

        # Strict Subject Grounding Check:
        # If the key subject entity (e.g. 'omelette' or 'mars') is completely absent, reject distractor
        if len(subject_entities) <= 3 and subject_ratio < 0.95 and exact_bonus == 0.0:
            h_score = 0.05 * norm_fusion
        elif len(subject_entities) > 3 and subject_ratio < 0.60 and exact_bonus == 0.0:
            h_score = 0.05 * norm_fusion
        elif exact_bonus > 0.0:
            h_score = 0.85 + (0.15 * norm_fusion)
        elif subject_ratio >= 0.80:
            h_score = (0.45 * all_ratio) + (0.25 * norm_dense) + (0.20 * norm_fusion) + bigram_bonus + lang_bonus
        else:
            h_score = (0.35 * all_ratio) + (0.20 * norm_dense) + (0.20 * norm_fusion) + bigram_bonus + lang_bonus

        c["rerank_score"] = round(min(h_score, 1.0), 4)

    ranked = sorted(eval_candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]


def rerank(query: str, candidates: List[Dict], top_k: int = config.RERANK_TOP_K) -> List[Dict]:
    """
    Neural Cross-Encoder Reranker (Used for deep synthesis & multi-strategy benchmarks).
    """
    if not candidates:
        return []

    eval_candidates = candidates[:MAX_RERANK_CANDIDATES]
    reranker = get_reranker()
    pairs = [(query, c["text"]) for c in eval_candidates]

    scores = reranker.predict(
        pairs,
        batch_size=MAX_RERANK_CANDIDATES,
        show_progress_bar=False,
    )

    for c, s in zip(eval_candidates, scores):
        c["rerank_score"] = float(s)

    ranked = sorted(eval_candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]
