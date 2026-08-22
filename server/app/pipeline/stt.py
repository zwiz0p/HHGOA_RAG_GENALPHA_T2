"""
Speech-to-text via Sarvam AI. Takes raw audio bytes (from the upload),
returns transcript text. Wrapped with retries and explicit timeouts.
"""

import httpx
from typing import Optional
import logging

from app.core import config

MAX_RETRIES = 1
TIMEOUT_SECONDS = 8.0

logger = logging.getLogger(__name__)


class STTError(Exception):
    pass


def transcribe(audio_bytes: bytes, filename: str = "audio.webm", language_code: Optional[str] = None) -> str:
    if not config.SARVAM_API_KEY:
        raise STTError("SARVAM_API_KEY not configured")

    if not audio_bytes or len(audio_bytes) < 800:
        raise STTError("Audio recording is too short or empty. Please speak clearly into the microphone.")

    headers = {"api-subscription-key": config.SARVAM_API_KEY}
    files = {"file": (filename, audio_bytes, "audio/webm")}
    data = {
        "model": "saarika:v2.5",
        "language_code": language_code or "unknown",  # Auto-detects English, Hindi, and code-mixed speech
    }

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                resp = client.post(config.SARVAM_STT_URL, headers=headers, files=files, data=data)
                if resp.status_code != 200:
                    raise STTError(f"Sarvam STT failed ({resp.status_code}): {resp.text}")
                
                payload = resp.json()
                transcript = payload.get("transcript", "").strip()
                if not transcript:
                    raise STTError("No speech detected in audio. Please try again.")
                return transcript
        except (httpx.HTTPError, STTError) as e:
            last_error = e
            logger.warning(f"STT attempt {attempt + 1} failed: {e}")
            continue

    raise STTError(f"STT failed: {last_error}")

