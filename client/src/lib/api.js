const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function queryVoice(audioBlob, languageCode = null) {
  const form = new FormData();
  form.append("audio", audioBlob, "query.webm");
  if (languageCode) {
    form.append("language_code", languageCode);
  }

  const res = await fetch(`${API_BASE}/api/query/voice`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  return res.json();
}

export async function queryText(text) {
  const form = new FormData();
  form.append("text", text);

  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  return res.json();
}

export async function queryVoiceStream(
  audioBlob,
  languageCodeOrOnEvent = null,
  onEventOrSignal = () => {},
  maybeSignal = null
) {
  let languageCode = null;
  let onEvent = () => {};
  let signal = null;

  if (typeof languageCodeOrOnEvent === "function") {
    onEvent = languageCodeOrOnEvent;
    signal = onEventOrSignal;
  } else {
    languageCode = languageCodeOrOnEvent;
    onEvent = typeof onEventOrSignal === "function" ? onEventOrSignal : () => {};
    signal = maybeSignal;
  }

  const form = new FormData();
  form.append("audio", audioBlob, "query.webm");
  if (languageCode) {
    form.append("language_code", languageCode);
  }

  const response = await fetch(`${API_BASE}/api/query/voice/stream`, {
    method: "POST",
    body: form,
    signal,
  });

  if (!response.ok) {
    throw new Error(`Streaming query failed: ${response.status}`);
  }

  return readSSEStream(response, onEvent, signal);
}

export async function queryTextStream(
  text,
  strategyOrOnEvent = "sentence_aware",
  onEventOrSignal = () => {},
  maybeSignal = null
) {
  let strategy = "sentence_aware";
  let onEvent = () => {};
  let signal = null;

  if (typeof strategyOrOnEvent === "function") {
    onEvent = strategyOrOnEvent;
    signal = onEventOrSignal;
  } else {
    strategy = strategyOrOnEvent || "sentence_aware";
    onEvent = typeof onEventOrSignal === "function" ? onEventOrSignal : () => {};
    signal = maybeSignal;
  }

  const form = new FormData();
  form.append("text", text);
  if (strategy) {
    form.append("strategy", strategy);
  }

  const response = await fetch(`${API_BASE}/api/query/stream`, {
    method: "POST",
    body: form,
    signal,
  });

  if (!response.ok) {
    throw new Error(`Streaming query failed: ${response.status}`);
  }

  return readSSEStream(response, onEvent, signal);
}

export async function synthesizeQuery(
  { query, mode = "conversational_synthesis", context = null },
  onEvent = () => {},
  signal = null
) {
  const form = new FormData();
  form.append("query", query);
  form.append("mode", mode);
  if (context) form.append("context", context);

  const response = await fetch(`${API_BASE}/api/query/synthesize`, {
    method: "POST",
    body: form,
    signal,
  });

  if (!response.ok) {
    throw new Error(`Synthesis streaming failed: ${response.status}`);
  }

  return readSSEStream(response, onEvent, signal);
}

export async function compareChunking(query) {
  const form = new FormData();
  form.append("query", query);

  const res = await fetch(`${API_BASE}/api/compare-chunking`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    throw new Error(`Comparison failed: ${res.status}`);
  }

  return res.json();
}

async function readSSEStream(response, onEvent, signal = null) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      if (signal?.aborted) {
        reader.cancel().catch(() => {});
        break;
      }

      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split(/\r?\n\r?\n/);
      buffer = chunks.pop();

      for (const chunk of chunks) {
        if (!chunk.trim()) continue;
        const eventMatch = chunk.match(/event:\s*([^\r\n]+)/);
        const dataMatch = chunk.match(/data:\s*([^\r\n]+)/);

        const eventType = eventMatch ? eventMatch[1].trim() : "message";
        let data = null;
        if (dataMatch) {
          try {
            data = JSON.parse(dataMatch[1].trim());
          } catch {
            data = dataMatch[1].trim();
          }
        }

        onEvent({ event: eventType, data });
      }
    }
  } catch (err) {
    if (err.name === "AbortError" || signal?.aborted) {
      console.log("SSE Stream aborted by user");
      return;
    }
    throw err;
  }
}
