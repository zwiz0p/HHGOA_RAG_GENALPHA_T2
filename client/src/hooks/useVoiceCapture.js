import { useState, useRef, useCallback, useEffect } from "react";

export function useVoiceCapture({ onSilenceTimeout } = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);

  const startTimeRef = useRef(0);
  const lastSoundTimeRef = useRef(0);
  const silenceTimeoutTriggeredRef = useRef(false);

  const cleanupAudioAnalyser = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      startTimeRef.current = performance.now();
      lastSoundTimeRef.current = performance.now();
      silenceTimeoutTriggeredRef.current = false;

      // Setup Web Audio Analyser for reactive volume animation & VAD silence detection
      try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
          const audioCtx = new AudioContextClass();
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 64;
          analyser.smoothingTimeConstant = 0.5;

          const source = audioCtx.createMediaStreamSource(stream);
          source.connect(analyser);

          audioContextRef.current = audioCtx;
          analyserRef.current = analyser;

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const updateLevel = () => {
            if (!analyserRef.current) return;
            analyserRef.current.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            const normalized = Math.min(Math.max((avg - 10) / 70, 0), 1);
            setAudioLevel(normalized);

            const now = performance.now();
            if (normalized > 0.12) {
              lastSoundTimeRef.current = now;
            }

            // VAD Silence Detection: 1.3s of silence after at least 1.0s of speech recording
            if (
              onSilenceTimeout &&
              !silenceTimeoutTriggeredRef.current &&
              now - startTimeRef.current > 1200 &&
              now - lastSoundTimeRef.current > 1300
            ) {
              silenceTimeoutTriggeredRef.current = true;
              onSilenceTimeout();
            }

            animFrameRef.current = requestAnimationFrame(updateLevel);
          };
          updateLevel();
        }
      } catch (audioErr) {
        console.warn("Web Audio API analyser not supported:", audioErr);
      }

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      cleanupAudioAnalyser();
      console.error("Failed to access microphone:", err);
      throw err;
    }
  }, [cleanupAudioAnalyser, onSilenceTimeout]);

  const stopRecording = useCallback(() => {
    cleanupAudioAnalyser();
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setIsRecording(false);
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
        }
        setIsRecording(false);
        if (audioBlob.size < 800) {
          console.warn("Audio recording is too short or empty:", audioBlob.size);
          resolve(null);
        } else {
          resolve(audioBlob);
        }
      };

      recorder.stop();
    });
  }, [cleanupAudioAnalyser]);

  useEffect(() => {
    return () => {
      cleanupAudioAnalyser();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [cleanupAudioAnalyser]);

  return { isRecording, audioLevel, startRecording, stopRecording };
}
