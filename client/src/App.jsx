import React, { useState, useRef } from "react";
import { Layers, RotateCcw, Cpu } from "lucide-react";
import { Glass } from "@samasante/liquid-glass";
import SkyBackground from "./components/SkyBackground";
import ChatContainer from "./components/ChatContainer";
import BottomInputBar from "./components/BottomInputBar";
import StrategyCompareModal from "./components/StrategyCompareModal";
import PipelineArchitectureModal from "./components/PipelineArchitectureModal";
import { useVoiceCapture } from "./hooks/useVoiceCapture";
import {
  queryVoiceStream,
  queryTextStream,
  synthesizeQuery,
  compareChunking,
} from "./lib/api";
import { playTactileClick } from "./utils/sound";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [selectedStrategy, setSelectedStrategy] =
    useState("sentence_aware");

  const abortControllerRef = useRef(null);

  // Voice recording
  const { isRecording, audioLevel, startRecording, stopRecording } =
    useVoiceCapture({
      onSilenceTimeout: () => {
        if (isRecording) {
          handleToggleRecord();
        }
      },
    });

  // Chunking comparison modal
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Architecture modal
  const [isArchOpen, setIsArchOpen] = useState(false);

  // ============================================================
  // STOP ACTIVE STREAM
  // ============================================================

  function handleStop() {
    playTactileClick();

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setLoading(false);

    setMessages((prev) => {
      const next = [...prev];

      if (
        next.length > 0 &&
        next[next.length - 1].role === "assistant"
      ) {
        next[next.length - 1] = {
          ...next[next.length - 1],
          streaming: false,
          synthesizing: false,
        };
      }

      return next;
    });
  }

  // ============================================================
  // VOICE RECORDING
  // ============================================================

  async function handleToggleRecord() {
    playTactileClick();

    if (isRecording) {
      try {
        const audioBlob = await stopRecording();

        if (!audioBlob) return;

        await handleAudioStream(audioBlob);
      } catch (err) {
        console.error("Recording stop error:", err);
      }
    } else {
      try {
        await startRecording();
      } catch (err) {
        console.error("Microphone access error:", err);
      }
    }
  }

  // ============================================================
  // VOICE QUERY STREAM
  // ============================================================

  async function handleAudioStream(blob) {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);

    const assistantMsgIndex = messages.length + 1;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: "🎙️ Voice Query...",
      },
      {
        role: "assistant",
        text: "",
        streaming: true,
        data: null,
        isVoiceTriggered: true,
      },
    ]);

    try {
      await queryVoiceStream(
        blob,
        null,
        ({ event, data }) => {
          // -----------------------------
          // METADATA
          // -----------------------------
          if (event === "metadata") {
            setMessages((prev) => {
              const next = [...prev];

              if (
                next[assistantMsgIndex - 1] &&
                data?.transcript
              ) {
                next[assistantMsgIndex - 1].text =
                  data.transcript;
              }

              if (next[assistantMsgIndex]) {
                next[assistantMsgIndex].data = {
                  ...next[assistantMsgIndex].data,
                  ...data,
                };

                next[assistantMsgIndex].userQuery =
                  data?.transcript || "";
              }

              return next;
            });
          }

          // -----------------------------
          // TOKEN
          // -----------------------------
          else if (event === "token") {
            setMessages((prev) => {
              const next = [...prev];

              if (next[assistantMsgIndex]) {
                const incoming =
                  typeof data === "object" &&
                    data?.token !== undefined
                    ? data.token
                    : data;

                next[assistantMsgIndex].text =
                  (next[assistantMsgIndex].text || "") +
                  (incoming || "");
              }

              return next;
            });
          }

          // -----------------------------
          // DONE
          // IMPORTANT:
          // Replace streamed text with
          // authoritative final answer.
          // -----------------------------
          else if (event === "done") {
            setMessages((prev) => {
              const next = [...prev];

              if (next[assistantMsgIndex]) {
                next[assistantMsgIndex] = {
                  ...next[assistantMsgIndex],
                  streaming: false,

                  // IMPORTANT: do NOT append.
                  // Backend's done.answer is final.
                  text:
                    data?.answer ||
                    next[assistantMsgIndex].text ||
                    "",

                  data: {
                    ...next[assistantMsgIndex].data,
                    ...data,
                  },
                };
              }

              return next;
            });

            setLoading(false);
          }

          // -----------------------------
          // BLOCKED / ERROR
          // -----------------------------
          else if (
            event === "blocked" ||
            event === "error"
          ) {
            setMessages((prev) => {
              const next = [...prev];

              if (next[assistantMsgIndex]) {
                next[assistantMsgIndex] = {
                  ...next[assistantMsgIndex],
                  streaming: false,
                  text:
                    data?.answer ||
                    data?.message ||
                    "Query was not completed.",
                  data: data || null,
                };
              }

              return next;
            });

            setLoading(false);
          }
        },
        controller.signal
      );
    } catch (err) {
      if (err.name === "AbortError") {
        console.log("Audio query stream aborted by user.");
      } else {
        console.error("Audio stream error:", err);
      }

      setLoading(false);
    }
  }

  // ============================================================
  // TEXT QUERY STREAM
  // ============================================================

  async function executeSingleQueryStream(
    query,
    options = {}
  ) {
    return new Promise(async (resolve) => {
      const controller = new AbortController();

      abortControllerRef.current = controller;

      let msgIndex = 0;
      let finalData = null;
      let finalAnswer = "";

      // Create user + assistant messages
      setMessages((prev) => {
        msgIndex = prev.length + 1;

        return [
          ...prev,
          {
            role: "user",
            text: query,
          },
          {
            role: "assistant",
            text: "",
            streaming: true,
            data: null,
            isVoiceTriggered:
              !!options.isVoiceTriggered,
            userQuery: query,
          },
        ];
      });

      try {
        await queryTextStream(
          query,
          selectedStrategy,
          ({ event, data }) => {
            // -----------------------------
            // METADATA
            // -----------------------------
            if (event === "metadata") {
              setMessages((prev) => {
                const next = [...prev];

                if (next[msgIndex]) {
                  next[msgIndex].data = {
                    ...next[msgIndex].data,
                    ...data,
                  };

                  next[msgIndex].userQuery = query;
                }

                return next;
              });
            }

            // -----------------------------
            // TOKEN
            // -----------------------------
            else if (event === "token") {
              setMessages((prev) => {
                const next = [...prev];

                if (next[msgIndex]) {
                  const incoming =
                    typeof data === "object" &&
                      data?.token !== undefined
                      ? data.token
                      : data;

                  next[msgIndex].text =
                    (next[msgIndex].text || "") +
                    (incoming || "");
                }

                return next;
              });
            }

            // -----------------------------
            // DONE
            // IMPORTANT:
            // Replace streamed text with
            // final answer.
            // -----------------------------
            else if (event === "done") {
              finalData = data;
              finalAnswer = data?.answer || "";

              setMessages((prev) => {
                const next = [...prev];

                if (next[msgIndex]) {
                  next[msgIndex] = {
                    ...next[msgIndex],

                    streaming: false,

                    // IMPORTANT:
                    // Replace, don't append.
                    text: finalAnswer,

                    data: {
                      ...next[msgIndex].data,
                      ...data,
                    },
                  };
                }

                return next;
              });

              resolve({
                data: finalData,
                text: finalAnswer,
              });
            }

            // -----------------------------
            // BLOCKED / ERROR
            // -----------------------------
            else if (
              event === "blocked" ||
              event === "error"
            ) {
              const errorText =
                data?.answer ||
                data?.message ||
                "Query not found in dataset.";

              setMessages((prev) => {
                const next = [...prev];

                if (next[msgIndex]) {
                  next[msgIndex] = {
                    ...next[msgIndex],
                    streaming: false,
                    text: errorText,
                    data: data || null,
                  };
                }

                return next;
              });

              resolve({
                data,
                text: errorText,
              });
            }
          },
          controller.signal
        );
      } catch (err) {
        resolve({
          error: err,
        });
      }
    });
  }

  // ============================================================
  // TEXT SUBMIT
  // ============================================================

  async function handleTextSubmit(e) {
    if (e) e.preventDefault();

    const query = textInput.trim();

    if (!query || loading) return;

    setTextInput("");
    setLoading(true);

    await executeSingleQueryStream(query);

    setLoading(false);
  }

  // ============================================================
  // JUDGE BENCHMARK SUITE
  // ============================================================

  async function handleRunJudgeSuite() {
    if (loading) return;

    setLoading(true);

    const BENCHMARK_SUITE = [
      {
        id: "en_indomain",
        label: "English In-Domain",
        query: "Who directed the Manhattan Project?",
        expectedType: "in_domain",
      },
      {
        id: "hi_indomain",
        label: "Hindi In-Domain",
        query:
          "अम्लीय वर्षा के मुख्य कारण क्या हैं?",
        expectedType: "in_domain",
      },
      {
        id: "ood",
        label: "Out-of-Domain",
        query:
          "How to make a masala omelette step by step?",
        expectedType: "out_of_domain",
      },
    ];

    const suiteResults = [];
    const suiteStart = performance.now();

    for (
      let i = 0;
      i < BENCHMARK_SUITE.length;
      i++
    ) {
      const item = BENCHMARK_SUITE[i];

      const qStart = performance.now();

      const res = await executeSingleQueryStream(
        item.query
      );

      const qElapsed =
        performance.now() - qStart;

      suiteResults.push({
        label: item.label,
        query: item.query,
        latencyMs:
          Math.round(qElapsed * 100) / 100,
        serverLatencyMs:
          res.data?.total_latency_ms ||
          Math.round(qElapsed * 100) / 100,
        sourceType:
          res.data?.source_type ||
          "knowledge_base",
      });

      await new Promise((r) =>
        setTimeout(r, 600)
      );
    }

    const totalSuiteTime = Math.round(
      performance.now() - suiteStart
    );

    const latencies = suiteResults
      .map((r) => r.serverLatencyMs)
      .sort((a, b) => a - b);

    const p50 =
      latencies[Math.floor(latencies.length / 2)];

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text:
          `🏁 **Judge Benchmark Suite Completed** in **${totalSuiteTime}ms** (P50: **${p50}ms**)\n\n` +
          `1. **${suiteResults[0].label}**: \`${suiteResults[0].serverLatencyMs}ms\` (${suiteResults[0].sourceType})\n` +
          `2. **${suiteResults[1].label}**: \`${suiteResults[1].serverLatencyMs}ms\` (${suiteResults[1].sourceType})\n` +
          `3. **${suiteResults[2].label}**: \`${suiteResults[2].serverLatencyMs}ms\` (${suiteResults[2].sourceType})\n\n` +
          `*All 3 queries evaluated sequentially through real dual-engine hybrid retrieval without page reloads.*`,
        data: {
          source_type: "fast_path",
          total_latency_ms: p50,
          confidence: 0.99,
        },
      },
    ]);

    setLoading(false);
  }

  // ============================================================
  // SYNTHESIS
  // ============================================================

  async function handleSynthesize(
    messageIndex,
    query,
    context
  ) {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const t0 = performance.now();

    setMessages((prev) => {
      const next = [...prev];

      if (next[messageIndex]) {
        next[messageIndex] = {
          ...next[messageIndex],
          text: "",
          synthesizing: true,
          isSynthesized: true,
        };
      }

      return next;
    });

    try {
      await synthesizeQuery(
        {
          query,
          mode: "conversational_synthesis",
          context,
        },
        ({ event, data }) => {
          if (event === "token") {
            setMessages((prev) => {
              const next = [...prev];

              if (next[messageIndex]) {
                const incoming =
                  typeof data === "object" &&
                    data?.token !== undefined
                    ? data.token
                    : data;

                next[messageIndex].text =
                  (next[messageIndex].text || "") +
                  (incoming || "");
              }

              return next;
            });
          } else if (event === "done") {
            const elapsed =
              performance.now() - t0;

            setMessages((prev) => {
              const next = [...prev];

              if (next[messageIndex]) {
                next[messageIndex].synthesizing =
                  false;

                next[messageIndex].synthesisLatency =
                  elapsed;

                next[messageIndex].data = {
                  ...next[messageIndex].data,
                  generation_mode:
                    "conversational_synthesis",
                };
              }

              return next;
            });
          }
        },
        controller.signal
      );
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error(
          "Synthesis error:",
          err
        );
      }

      setMessages((prev) => {
        const next = [...prev];

        if (next[messageIndex]) {
          next[messageIndex].synthesizing =
            false;
        }

        return next;
      });
    }
  }

  // ============================================================
  // GENERAL KNOWLEDGE
  // ============================================================

  async function handleGenerateGeneral(
    messageIndex,
    query
  ) {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const t0 = performance.now();

    setMessages((prev) => {
      const next = [...prev];

      if (next[messageIndex]) {
        next[messageIndex] = {
          ...next[messageIndex],
          text: "",
          synthesizing: true,
        };
      }

      return next;
    });

    try {
      await synthesizeQuery(
        {
          query,
          mode: "general_knowledge",
        },
        ({ event, data }) => {
          if (event === "token") {
            setMessages((prev) => {
              const next = [...prev];

              if (next[messageIndex]) {
                const incoming =
                  typeof data === "object" &&
                    data?.token !== undefined
                    ? data.token
                    : data;

                next[messageIndex].text =
                  (next[messageIndex].text || "") +
                  (incoming || "");
              }

              return next;
            });
          } else if (event === "done") {
            const elapsed =
              performance.now() - t0;

            setMessages((prev) => {
              const next = [...prev];

              if (next[messageIndex]) {
                next[messageIndex].synthesizing =
                  false;

                next[messageIndex].synthesisLatency =
                  elapsed;

                next[messageIndex].data = {
                  ...next[messageIndex].data,
                  source_type:
                    "general_knowledge",
                  generation_mode:
                    "general_knowledge",
                  prompt_synthesis: false,
                };
              }

              return next;
            });
          }
        },
        controller.signal
      );
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error(
          "General knowledge error:",
          err
        );
      }

      setMessages((prev) => {
        const next = [...prev];

        if (next[messageIndex]) {
          next[messageIndex].synthesizing =
            false;
        }

        return next;
      });
    }
  }

  // ============================================================
  // PROMPT SELECT
  // ============================================================

  function handleSelectPrompt(q) {
    setTextInput(q);
  }

  // ============================================================
  // CHUNKING COMPARISON
  // ============================================================

  async function handleOpenCompare() {
    playTactileClick();

    setIsCompareOpen(true);
    setCompareLoading(true);

    const latestUserMsg = [...messages]
      .reverse()
      .find((m) => m.role === "user");

    const testQuery =
      latestUserMsg?.text ||
      "Who directed the Los Alamos Laboratory during the Manhattan Project?";

    try {
      const res =
        await compareChunking(testQuery);

      setCompareData(res);
    } catch (err) {
      console.error("Compare error:", err);
    } finally {
      setCompareLoading(false);
    }
  }

  // ============================================================
  // UI
  // ============================================================

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        position: "relative",
        color: "var(--ink)",
      }}
    >
      <SkyBackground />

      {/* HEADER */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          padding: "16px 28px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >
          {/* Architecture */}
          <Glass
            optics={{
              depth: 0.6,
              dispersion: 0.25,
              strength: 0.45,
              frost: 14,
              brightness: 0.1,
              specular: 1.2,
              sheen: 0.8,
              glow: 0.35,
              curvature: 0.35,
              bend: 0.2,
              bendWidth: 0.12,
            }}
            radius={999}
            style={{ borderRadius: "999px" }}
          >
            <button
              type="button"
              onClick={() => {
                playTactileClick();
                setIsArchOpen(true);
              }}
              title="Inspect complete AURA system specification & pipeline flow"
              className="liquid-glass-btn font-accent"
              style={{
                padding: "8px 18px",
                fontSize: "14px",
                fontWeight: 700,
                gap: "7px",
                color: "var(--ink)",
                borderRadius: "999px",
              }}
            >
              <Cpu
                size={15}
                color="var(--sun-dark)"
              />
              <span>🛠️ Architecture</span>
            </button>
          </Glass>

          {/* Chunking Matrix */}
          <Glass
            optics={{
              depth: 0.6,
              dispersion: 0.25,
              strength: 0.45,
              frost: 14,
              brightness: 0.1,
              specular: 1.2,
              sheen: 0.8,
              glow: 0.35,
              curvature: 0.35,
              bend: 0.2,
              bendWidth: 0.12,
            }}
            radius={999}
            style={{ borderRadius: "999px" }}
          >
            <button
              type="button"
              onClick={handleOpenCompare}
              title="Evaluate 4 chunking strategies side by side"
              className="liquid-glass-btn font-accent"
              style={{
                padding: "8px 18px",
                fontSize: "14px",
                fontWeight: 700,
                gap: "7px",
                color: "var(--ink)",
                borderRadius: "999px",
              }}
            >
              <Layers
                size={15}
                color="var(--mint)"
              />
              <span>Chunking Matrix</span>
            </button>
          </Glass>

          {/* Reset */}
          {messages.length > 0 && (
            <Glass
              optics={{
                depth: 0.6,
                dispersion: 0.25,
                strength: 0.45,
                frost: 14,
                brightness: 0.1,
                specular: 1.2,
                sheen: 0.8,
                glow: 0.35,
                curvature: 0.35,
                bend: 0.2,
                bendWidth: 0.12,
              }}
              radius={999}
              style={{ borderRadius: "999px" }}
            >
              <button
                type="button"
                onClick={() => {
                  playTactileClick();
                  setMessages([]);
                }}
                className="liquid-glass-btn font-accent"
                style={{
                  padding: "8px 16px",
                  fontSize: "14px",
                  fontWeight: 700,
                  color: "var(--terracotta)",
                  gap: "6px",
                  borderRadius: "999px",
                }}
              >
                <RotateCcw size={14} />
                <span>Reset</span>
              </button>
            </Glass>
          )}
        </div>

        {/* Logo */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            userSelect: "none",
          }}
        >
          <img
            src="/assets/aura-top.png"
            alt="AURA"
            style={{
              width: "clamp(120px, 14vw, 175px)",
              height: "auto",
              objectFit: "contain",
              filter:
                "drop-shadow(0 8px 20px rgba(0, 0, 0, 0.20))",
              cursor: "pointer",
            }}
            onClick={() => {
              playTactileClick();
              setMessages([]);
            }}
          />
        </div>
      </header>

      {/* MAIN CHAT */}
      <main
        style={{
          flex: 1,
          width: "100%",
          maxWidth: "760px",
          margin: "0 auto",
          padding: "0 16px",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          zIndex: 10,
        }}
      >
        <ChatContainer
          messages={messages}
          isRecording={isRecording}
          isLoading={loading}
          audioLevel={audioLevel}
          onSelectPrompt={handleSelectPrompt}
          onSynthesize={handleSynthesize}
          onGenerateGeneral={handleGenerateGeneral}
        />
      </main>

      {/* INPUT */}
      <BottomInputBar
        textInput={textInput}
        onChangeText={setTextInput}
        onSubmit={handleTextSubmit}
        onStop={handleStop}
        isRecording={isRecording}
        isLoading={loading}
        audioLevel={audioLevel}
        onToggleRecord={handleToggleRecord}
        selectedStrategy={selectedStrategy}
        onOpenCompare={handleOpenCompare}
        onSelectPrompt={handleSelectPrompt}
        onRunJudgeSuite={handleRunJudgeSuite}
      />

      {/* CHUNKING MODAL */}
      <StrategyCompareModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        data={compareData}
        loading={compareLoading}
        query={
          messages
            .filter((m) => m.role === "user")
            .slice(-1)[0]?.text
        }
      />

      {/* ARCHITECTURE MODAL */}
      <PipelineArchitectureModal
        isOpen={isArchOpen}
        onClose={() => setIsArchOpen(false)}
      />
    </div>
  );
}