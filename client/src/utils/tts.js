let currentUtterance = null;

/**
 * Clean and speak text using the browser's Web Speech API.
 * Automatically chooses Hindi or English voices based on script detection.
 */
export function speakText(text, onStart, onEnd) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    console.warn("Speech synthesis not supported in this browser.");
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const clean = text
    .replace(/^⚠️\s*\*Note:[^*]+\*\s*\n*/i, "")
    .replace(/^⚠️\s*\*Not found[^*]+\*\s*\n*/i, "")
    .replace(/[\*\#\`\_]/g, "")
    .replace(/\$[^$]+\$/g, "")
    .trim();

  if (!clean) return;

  const isHindi = /[\u0900-\u097F]/.test(clean);
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  const voices = window.speechSynthesis.getVoices();
  if (isHindi) {
    const hiVoice = voices.find(
      (v) => v.lang.startsWith("hi") || v.name.toLowerCase().includes("hindi")
    );
    if (hiVoice) utterance.voice = hiVoice;
    utterance.lang = "hi-IN";
  } else {
    const enVoice = voices.find(
      (v) =>
        v.lang.startsWith("en-IN") ||
        v.lang.startsWith("en-US") ||
        v.name.toLowerCase().includes("natural") ||
        v.name.toLowerCase().includes("google")
    );
    if (enVoice) utterance.voice = enVoice;
    utterance.lang = "en-US";
  }

  if (onStart) utterance.onstart = onStart;
  utterance.onend = () => {
    currentUtterance = null;
    if (onEnd) onEnd();
  };
  utterance.onerror = () => {
    currentUtterance = null;
    if (onEnd) onEnd();
  };

  currentUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

export function stopSpeech() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  currentUtterance = null;
}

export function isSpeaking() {
  return typeof window !== "undefined" && "speechSynthesis" in window && window.speechSynthesis.speaking;
}
