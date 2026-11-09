/** Flow store: welcome → age → topic → session → end.
 *
 * Context (age/topic/sessionId/dialogue) is wiped on reset so nothing
 * outlives the session (spec §8.3).
 */

import { defineStore } from "pinia";

import * as api from "../services/api";
import { characterStateFor, type CharacterState } from "../services/character";
import { speak, startListening, type RecordingHandle } from "../services/voice";
import type { AgeGroup, Topic, TurnData } from "../types/session";

export type Phase = "welcome" | "age" | "topic" | "session" | "end";

interface SessionFlowState {
  phase: Phase;
  ageGroup: AgeGroup | null;
  topic: Topic | null;
  sessionId: string | null;
  assistantText: string;
  characterState: CharacterState;
  turn: number;
  finished: boolean;
  maxTurns: number;
  busy: boolean;
  recording: boolean;
  error: string | null;
}

const initialState: SessionFlowState = {
  phase: "welcome",
  ageGroup: null,
  topic: null,
  sessionId: null,
  assistantText: "",
  characterState: "idle",
  turn: 0,
  finished: false,
  maxTurns: 4,
  busy: false,
  recording: false,
  error: null,
};

// Non-serializable browser handles stay outside the reactive state.
let activeRecording: RecordingHandle | null = null;

const ASR_RETRY_HINT =
  "没听清,请再试一次 Didn't catch that — please try again.";
const MIC_UNAVAILABLE =
  "无法访问麦克风 Microphone unavailable. Please check permission.";

function errorMessage(err: unknown): string {
  if (err instanceof api.ApiError) {
    return err.message;
  }
  return "Something went wrong. Please try again.";
}

export const useSessionStore = defineStore("session", {
  state: (): SessionFlowState => ({ ...initialState }),
  actions: {
    chooseAge(group: AgeGroup): void {
      this.ageGroup = group;
      this.phase = "topic";
    },

    async chooseTopic(topic: Topic): Promise<void> {
      if (!this.ageGroup) {
        this.error = "Please choose an age group first.";
        return;
      }
      this.topic = topic;
      this.busy = true;
      this.error = null;
      try {
        const data = await api.createSession(this.ageGroup, topic);
        this.applyTurnData(data);
        this.sessionId = data.sessionId;
        this.maxTurns = data.maxTurns;
        this.phase = "session";
        speak(data.assistantText);
      } catch (err: unknown) {
        this.error = errorMessage(err);
      } finally {
        this.busy = false;
      }
    },

    async sendChildText(text: string): Promise<void> {
      if (!this.sessionId || this.busy) {
        return;
      }
      const trimmed = text.trim();
      if (!trimmed) {
        return;
      }
      this.busy = true;
      this.error = null;
      try {
        const data = await api.reply(this.sessionId, trimmed);
        this.applyTurnData(data);
        speak(data.assistantText);
      } catch (err: unknown) {
        this.error = errorMessage(err);
      } finally {
        this.busy = false;
      }
    },

    async beginVoice(): Promise<void> {
      if (!this.sessionId || this.busy || this.recording) {
        return;
      }
      this.error = null;
      try {
        activeRecording = await startListening();
        this.recording = true;
      } catch {
        activeRecording = null;
        this.recording = false;
        this.error = MIC_UNAVAILABLE;
      }
    },

    async finishVoice(): Promise<void> {
      if (!activeRecording || !this.sessionId || this.busy) {
        return;
      }
      const handle = activeRecording;
      activeRecording = null;
      this.recording = false;
      this.busy = true;
      this.error = null;
      try {
        const { blob, mimeType } = await handle.stop();
        try {
          const data = await api.sendSpeech(this.sessionId, blob, mimeType);
          this.applyTurnData(data);
          speak(data.assistantText);
        } catch (err: unknown) {
          if (err instanceof api.ApiError && err.code === "asr_failed") {
            // ASR 失败最多重试 1 次 (plan §4.1) — same recording, one resend.
            try {
              const data = await api.sendSpeech(this.sessionId, blob, mimeType);
              this.applyTurnData(data);
              speak(data.assistantText);
            } catch (retryErr: unknown) {
              this.error =
                retryErr instanceof api.ApiError &&
                retryErr.code === "asr_failed"
                  ? ASR_RETRY_HINT
                  : errorMessage(retryErr);
            }
          } else {
            this.error = errorMessage(err);
          }
        }
      } finally {
        this.busy = false;
      }
    },

    async endSession(): Promise<void> {
      let endError: string | null = null;
      if (activeRecording) {
        activeRecording.cancel();
        activeRecording = null;
        this.recording = false;
      }
      if (this.sessionId) {
        try {
          await api.endSession(this.sessionId);
        } catch {
          // Exiting must always work: reset locally even if the server call
          // fails, but surface the failure instead of swallowing it.
          endError = "Could not reach the server while ending the session.";
        }
      }
      this.reset();
      if (endError) {
        this.error = endError;
      }
    },

    reset(): void {
      if (activeRecording) {
        activeRecording.cancel();
        activeRecording = null;
      }
      Object.assign(this, { ...initialState });
    },

    applyTurnData(data: TurnData): void {
      this.assistantText = data.assistantText;
      this.characterState = characterStateFor(data.state);
      this.turn = data.turn;
      this.finished = data.finished;
      if (data.finished) {
        this.phase = "end";
      }
    },
  },
});
