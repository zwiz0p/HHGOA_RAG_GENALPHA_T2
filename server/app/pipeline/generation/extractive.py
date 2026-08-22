import re
from typing import List, Dict, Optional

HINDI_STOPWORDS = {
    "कब", "कहाँ", "कहा", "कैसे", "क्या", "क्यों", "किसने", "किसके", "किस", "कौन",
    "है", "हैं", "था", "थी", "थे", "हुई", "हुआ", "हुए", "होना", "होने",
    "की", "का", "के", "में", "पर", "से", "को", "ने", "और", "या", "एक", "यह", "वह", "द्वारा"
}

ENGLISH_STOPWORDS = {
    "who", "what", "where", "when", "how", "why", "which", "whose", "whom",
    "did", "does", "do", "the", "a", "an", "in", "on", "of", "to", "is", "was",
    "are", "were", "with", "for", "by", "at", "it", "this", "that", "from"
}


def extract_best_sentences(query: str, hits: List[Dict]) -> Optional[str]:
    """
    Sub-2ms Deterministic Extractive Generation:
    Extracts the highest-relevance proposition sentences from top-ranked passages.
    Supports English punctuation (. ! ?) and Indic Devanagari (। ! ?).
    """
    if not hits:
        return None

    top_hit = hits[0]
    passage_text = top_hit.get("text") or top_hit.get("parent_text", "")
    if not passage_text or not passage_text.strip():
        return None

    # Split into clean grammatical sentences
    raw_sentences = re.split(r"(?<=[.!?।])\s+", passage_text.strip())
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]

    if not sentences:
        return passage_text.strip()[:300]

    # Query tokens
    query_clean = re.sub(r"[^\w\s\u0900-\u097F]", " ", query.lower())
    is_hindi = bool(re.search(r"[\u0900-\u097F]", query_clean))
    all_stopwords = ENGLISH_STOPWORDS | HINDI_STOPWORDS

    query_tokens = [w for w in query_clean.split() if w not in all_stopwords and len(w) > 1]
    content_tokens = set(query_tokens)

    scored_sentences = []

    for idx, sent in enumerate(sentences):
        sent_clean = re.sub(r"[^\w\s\u0900-\u097F]", " ", sent.lower())
        sent_tokens = set(sent_clean.split())

        # 1. Token overlap score
        overlap = 0
        for q_tok in content_tokens:
            if q_tok in sent_tokens or q_tok in sent_clean:
                overlap += 1
            elif is_hindi and len(q_tok) >= 3 and any(t.startswith(q_tok[:3]) or q_tok[:3] in t for t in sent_tokens):
                overlap += 1
            elif not is_hindi and len(q_tok) >= 5 and any(t.startswith(q_tok[:5]) for t in sent_tokens if len(t) >= 5):
                overlap += 1

        score = overlap * 3.0

        # 2. Exact substring phrase bonus
        if len(query_clean.strip()) > 8 and query_clean.strip() in sent_clean:
            score += 6.0

        # 3. Consecutive bigram overlap bonus
        if len(query_tokens) >= 2:
            for i in range(len(query_tokens) - 1):
                bigram = f"{query_tokens[i]} {query_tokens[i+1]}"
                if bigram in sent_clean:
                    score += 2.5

        # 4. Position priority (first sentences usually contain the main proposition)
        score += max(0.0, 1.2 - (idx * 0.15))

        # 5. Length penalty for single-word or truncated fragments
        if len(sent.split()) < 3:
            score -= 3.0

        scored_sentences.append((score, idx, sent))

    # Sort by score descending to get top candidates
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    # Pick top 1-2 sentences and restore natural chronological reading order
    best_picks = sorted(scored_sentences[:2], key=lambda x: x[1])

    # Deduplicate sentences to prevent any repeated text
    unique_picks = []
    seen_texts = set()
    for s in best_picks:
        clean_text = s[2].strip()
        normalized_str = re.sub(r"\s+", " ", clean_text).lower()
        if clean_text and normalized_str not in seen_texts:
            seen_texts.add(normalized_str)
            unique_picks.append(clean_text)

    if not unique_picks:
        return passage_text.strip()[:300]

    return " ".join(unique_picks)
