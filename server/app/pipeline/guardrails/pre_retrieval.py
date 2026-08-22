import os
import re
from typing import Tuple, Dict, Any, Optional

import numpy as np

from app.core import config
from app.deps import get_embedder, get_qdrant_client

INTENT_ROUTING_CONFIG = [
    {
        "intent": "greeting",
        "patterns": [
            r"^(hi|hello|hey|greetings|namaste|namaskar|नमस्ते|नमस्कार|हैलो|हेलो|हे)(\s.*)?$",
            r"^(good\s(morning|afternoon|evening|day))(\s.*)?$",
            r"^(सुप्रभात|शुभ\sसंध्या)$",
            r"^(hello\s+mera\s+naam\s+.*|mera\s+naam\s+.*)$",
        ],
        "response": "Hello! I am your voice-enabled assistant for MSMARCO-XI. What would you like to search today?"
    },
    {
        "intent": "gratitude",
        "patterns": [
            r"^(thanks|thank\syou|thx|many\sthanks|धन्यवाद|शुक्रिया|shukriya|bahut\sdhanyawad)(\s.*)?$",
            r"^(i\sappreciate\sit|that\shelps|great\shelp)$"
        ],
        "response": "You are welcome! Let me know if you have more questions."
    },
    {
        "intent": "farewell",
        "patterns": [
            r"^(bye|goodbye|see\syou|take\scare|अलविदा|फिर\sमिलेंगे)(\s.*)?$"
        ],
        "response": "Goodbye! Feel free to ask more questions whenever you return."
    },
    {
        "intent": "identity_capability",
        "patterns": [
            r"^(who\sare\syou|what\scan\syou\sdo|what\sis\sthis|help|आप\sकौन\sहैं|तुम\sक्या\sकर\sसकते\sहो)(\?)?$",
            r"^(how\sdoes\sthis\swork|what\sdataset\sdo\syou\suse)(\?)?$"
        ],
        "response": "I am a Voice RAG system built on the multilingual MSMARCO-XI dataset. You can ask me factual and historical questions in English and Hindi."
    },
    {
        "intent": "acknowledgment",
        "patterns": [
            r"^(ok|okay|got\sit|understood|sure|fine|cool|alright|हाँ|ठीक\sहै|अच्छा)$"
        ],
        "response": "Understood. Ask a factual question whenever you are ready."
    },
    {
        "intent": "creative_rejection",
        "patterns": [
            r"^(write\sa\s(poem|story|song|code|script)|tell\sme\sa\sjoke|कविता\sलिखो|चुटकला\sसुनाओ)(\s.*)?$"
        ],
        "response": "I am configured exclusively for factual dataset retrieval and QA. I cannot generate creative stories, jokes, or code."
    }
]

NOISE_PATTERNS = [
    r"^(um+|uh+|ah+|er+|hmm+|mhm+|shh+|huh+)$",
    r"^[.?,!~`@#$%^&*()_+=/\\|><:;\"' -]+$",
    r"^(\.|\.\.|\.\.\.)$",
]

UNSAFE_PATTERNS = [
    r"\b(bomb|weapon|hack|exploit|malware|poison|suicide|terrorist|kill)\b",
]


def is_noise(cleaned_query: str) -> bool:
    if not cleaned_query:
        return True
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, cleaned_query, re.IGNORECASE):
            return True
    return False


def contains_unsafe_content(cleaned_query: str) -> bool:
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, cleaned_query, re.IGNORECASE):
            return True
    return False


def _dataset_centroid() -> Optional[np.ndarray]:
    """
    Cached centroid of a sample of indexed vectors, used as a cheap
    "is this query even in-domain" proxy. Computed lazily on first call,
    cached in-process for the life of the server.
    """
    if not hasattr(_dataset_centroid, "_cache"):
        client = get_qdrant_client()
        sample = client.scroll(
            collection_name=config.QDRANT_COLLECTION,
            limit=500,
            with_vectors=True,
        )[0]
        vectors = np.array([p.vector for p in sample if p.vector is not None])
        _dataset_centroid._cache = vectors.mean(axis=0) if len(vectors) else None
    return _dataset_centroid._cache


def is_off_topic(query: str) -> Tuple[bool, float]:
    centroid = _dataset_centroid()
    if centroid is None:
        return False, 1.0  # fail open if index isn't populated yet (dev mode)

    embedder = get_embedder()
    query_vec = embedder.encode(query)

    denom = np.linalg.norm(query_vec) * np.linalg.norm(centroid)
    similarity = float(np.dot(query_vec, centroid) / denom) if denom else 0.0

    return similarity < config.OFF_TOPIC_SIM_THRESHOLD, similarity


def check_pre_retrieval(query: str) -> Dict[str, Any]:
    if not query or not query.strip():
        return {
            "is_fast_path": False,
            "is_greeting": False,
            "intent": None,
            "blocked": True,
            "reason": "empty_query",
            "message": "Query cannot be empty. Please ask a complete question.",
        }

    cleaned = re.sub(r"[?!.,;।]+", "", query.strip().lower())
    
    # 1. Reject very short inputs
    if len(cleaned) < 2:
        return {
            "is_fast_path": False,
            "is_greeting": False,
            "intent": None,
            "blocked": True,
            "reason": "query_too_short",
            "message": "Query is too short. Please ask a complete question.",
        }

    # 2. Reject audio noise and filler tokens
    if is_noise(cleaned):
        return {
            "is_fast_path": False,
            "is_greeting": False,
            "intent": "noise",
            "blocked": True,
            "reason": "audio_noise_or_filler",
            "message": "Audio not recognized as a clear question. Please try again.",
        }

    # 3. Identity & Capability (Match first to catch 'Hello! Who are you?')
    if re.search(r"\b(who are you|what can you do|what is this|help|aap kaun ho|आप कौन हैं|tum kaun ho|who made you|about you)\b", cleaned):
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "identity",
            "blocked": False,
            "direct_response": "I am a Voice RAG system built on the multilingual MSMARCO-XI dataset. You can ask me factual and historical questions in English and Hindi."
        }

    # 4. Greetings (only when concise conversational openers)
    if re.search(r"\b(hi|hello|hey|namaste|namaskar|नमस्ते|नमस्कार|हैलो|हेलो|good morning|good evening|good afternoon|good day|सुप्रभात|शुभ संध्या)\b", cleaned) and len(cleaned.split()) <= 4:
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "greeting",
            "blocked": False,
            "direct_response": "Hello! I am your voice-enabled assistant for MSMARCO-XI. What would you like to search today?"
        }

    # 5. Gratitude
    if re.search(r"\b(thanks|thank you|thx|many thanks|धन्यवाद|शुक्रिया|shukriya|bahut dhanyawad)\b", cleaned):
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "gratitude",
            "blocked": False,
            "direct_response": "You are welcome! Let me know if you have more questions."
        }

    # 6. Farewell
    if re.search(r"\b(bye|goodbye|see you|take care|अलविदा|फिर मिलेंगे)\b", cleaned):
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "farewell",
            "blocked": False,
            "direct_response": "Goodbye! Feel free to ask more questions whenever you return."
        }

    # 7. Acknowledgment
    if re.search(r"^(ok|okay|got it|understood|sure|fine|cool|alright|हाँ|ठीक है|अच्छा)$", cleaned):
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "acknowledgment",
            "blocked": False,
            "direct_response": "Understood. Ask a factual question whenever you are ready."
        }

    # 8. Creative Rejection
    if re.search(r"\b(write a (poem|story|song|code|script)|tell me a joke|कविता लिखो|चुटकला सुनाओ)\b", cleaned):
        return {
            "is_fast_path": True,
            "is_greeting": True,
            "intent": "creative_rejection",
            "blocked": False,
            "direct_response": "I am configured exclusively for factual dataset retrieval and QA. I cannot generate creative stories, jokes, or code."
        }

    # 9. Unsafe content check
    if contains_unsafe_content(cleaned):
        return {
            "is_fast_path": False,
            "is_greeting": False,
            "intent": None,
            "blocked": True,
            "reason": "unsafe_content",
            "message": "Query contains restricted keywords.",
        }

    # 10. Valid factual query -> Proceed to Hybrid Search
    return {
        "is_fast_path": False,
        "is_greeting": False,
        "intent": None,
        "blocked": False,
        "reason": None,
        "message": None,
    }


def check(query: str) -> Dict[str, Any]:
    return check_pre_retrieval(query)