/** Browser voice I/O: microphone capture + speech synthesis.
 *
 * TTS default is the browser's speechSynthesis (en-US, slowed for kids) —
 * no upload, works offline, natural for a kiosk.
 * REPLACEMENT POINT: to use a cloud voice, POST the assistant line to the
 * backend `/api/tts` endpoint (Task-3) and play the returned WAV instead.
 */

export interface RecordingHandle {
  stop(): Promise<{ blob: Blob; mimeType: string }>;
  cancel(): void;
}

function stopStream(stream: MediaStream): void {
  stream.getTracks().forEach((track) => track.stop());
}

export async function startListening(): Promise<RecordingHandle> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks: BlobPart[] = [];
  recorder.ondataavailable = (event: BlobEvent) => {
    if (event.data.size > 0) {
      chunks.push(event.data);
    }
  };
  recorder.start();

  return {
    stop: () =>
      new Promise((resolve) => {
        recorder.onstop = () => {
          const mimeType = recorder.mimeType || "audio/webm";
          stopStream(stream);
          resolve({ blob: new Blob(chunks, { type: mimeType }), mimeType });
        };
        recorder.stop();
      }),
    cancel: () => {
      stopStream(stream);
      if (recorder.state !== "inactive") {
        recorder.stop();
      }
    },
  };
}

export function speak(text: string, onEnded?: () => void): void {
  if (!("speechSynthesis" in window)) {
    // No synthesis available (tests, exotic browsers): nothing plays, so
    // the caller must not wait forever — report "finished" immediately.
    onEnded?.();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.9;
  const done = () => {
    utterance.onend = null;
    utterance.onerror = null;
    onEnded?.();
  };
  utterance.onend = done;
  utterance.onerror = done;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

/** Half-duplex teardown: cut any playing reply immediately (exit, safety
 * timeout, reset). Safe to call when nothing is playing. */
export function stopSpeaking(): void {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
