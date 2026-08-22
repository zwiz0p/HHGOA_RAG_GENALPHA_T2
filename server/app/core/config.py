import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Load environment variables from server/.env
load_dotenv(os.path.join(BASE_DIR, ".env"))

QDRANT_PATH = os.path.join(BASE_DIR, "data", "processed", "qdrant_local")
BM25_INDEX_PATH = os.path.join(BASE_DIR, "data", "processed", "bm25_index.pkl")
BM25S_INDEX_DIR = os.path.join(BASE_DIR, "data", "processed", "bm25s_index")
DENSE_VECTORS_PATH = os.path.join(BASE_DIR, "data", "processed", "dense_vectors.npy")
CHUNKS_PATH = os.path.join(BASE_DIR, "data", "processed", "chunks_sentence_aware.jsonl")
QDRANT_COLLECTION = "msmarco_xi_chunks"

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")  # Gemini API key from aistudio.google.com/apikey
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-3.5-flash-lite")  # fast low-latency model

# Retrieval tuning
DENSE_TOP_K = 20
BM25_TOP_K = 20
FUSION_TOP_K = 8
RERANK_TOP_K = 3

# Guardrail thresholds
MIN_RETRIEVAL_SCORE = float(os.environ.get("MIN_RETRIEVAL_SCORE", "0.35"))
MIN_GROUNDING_SCORE = float(os.environ.get("MIN_GROUNDING_SCORE", "0.4"))

# Off-topic classifier: simple keyword/embedding-similarity gate against
# known dataset topic centroid — see guardrails/pre_retrieval.py
OFF_TOPIC_SIM_THRESHOLD = float(os.environ.get("OFF_TOPIC_SIM_THRESHOLD", "0.25"))

UNSAFE_KEYWORDS = [
    # basic deny-list gate — placeholder, expand with a real moderation
    # endpoint before treating this as production-grade
    "bomb", "kill", "suicide", "weapon", "hack into",
]
