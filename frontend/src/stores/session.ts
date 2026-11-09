/** Flow store: welcome → age → topic → session → end.
 *
 * G2 (MVP closure) guarantees:
 * - explicit voiceState machine: idle → listening → processing → speaking
 *   (→ idle) with "error" as a parked state — strict half-duplex, the mic
 *   only opens while idle and never while Coco speaks;
 * - an epoch counter guards every async turn: a response resolving after
 *   exit/reset can never touch the fresh state;
 * - a natural finish auto-ends the server session (no click needed);
 * - total session cap (~180s) and idle timeout gently auto-end the session;
 * - ASR failure never resends the original recording — the child records
 *   NEW audio, at most one re-record per turn;
 * - context is wiped on reset so nothing outlives the session (spec §8.3).
 */

import { defineStore } from "pinia";

import * as api from "../services/api";
import { IDLE_TIMEOUT_MS, SESSION_MAX_MS } from "../config";
import { characterStateFor, type CharacterState } from "../services/character";
import {
  speak,
  startListening,
  stopSpeaking,
  type RecordingHandle,
} from "../services/voice";
import type { AgeGroup, Topic, TurnData } from "../types/session";

export type Phase = "welcome" | "age" | "topic" | "session" | "end";
export type VoiceState =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "error";
export type EndReason = "finished" | "timeout" | "idle" | "exit" | null;

interface SessionFlowState {
  phase: Phase;
  voiceState: VoiceState;
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
  endReason: EndReason;
  asrReRecordsLeft: number;
  error: string | null;
}

const initialState: SessionFlowState = {
  phase: "welcome",
  voiceState: "idle",
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
  endReason: null,
  asrReRecordsLeft: 1,
  error: null,
};

// Non-serializable handles and the flow epoch stay outside reactive state.
let activeRecording: RecordingHandle | null = null;
let flowEpoch = 0;
let totalTimer: ReturnType<typeof setTimeout> | null = null;
let idleTimer: ReturnType<typeof setTimeout> | null = null;

const ASR_RE_RECORD_BUDGET = 1;
const ASR_RETRY_HINT =
  "没听清,请再试一次 Didn't catch that — please try again.";
const ASR_EXHAUSTED_HINT =
  "我们换成打字好吗?在文字框输入,或点退出重来。Let's type instead — use the text box, or exit and start over.";
const SESSION_ENDED_HINT =
  "互动已结束,我们重新开始吧! The session ended — let's start again.";
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

  getters: {
    /** The mic may open only in the idle state of a live session. After
     * the ASR re-record budget is exhausted the state parks at "error",
     * which keeps this false until a turn succeeds. */
    canRecord(state): boolean {
      return (
        state.phase === "session" &&
        state.sessionId !== null &&
        state.voiceState === "idle" &&
        !state.busy
      );
    },
  },

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
      const epoch = flowEpoch;
      this.busy = true;
      this.voiceState = "processing";
      this.error = null;
      try {
        const data = await api.createSession(this.ageGroup, topic);
        if (epoch !== flowEpoch) {
          return;
        }
        this.applyTurnData(data);
        this.sessionId = data.sessionId;
        this.maxTurns = data.maxTurns;
        this.asrReRecordsLeft = ASR_RE_RECORD_BUDGET;
        this.phase = "session";
        this.armTotalTimer();
        this.announce(data.assistantText);
      } catch (err: unknown) {
        if (epoch !== flowEpoch) {
          return;
        }
        this.voiceState = "idle";
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
      const epoch = flowEpoch;
      this.clearIdleTimer();
      this.busy = true;
      this.voiceState = "processing";
      this.error = null;
      try {
        const data = await api.reply(this.sessionId, trimmed);
        if (epoch !== flowEpoch) {
          return;
        }
        this.applyTurnData(data);
        if (!data.finished) {
          this.announce(data.assistantText);
        }
      } catch (err: unknown) {
        if (epoch !== flowEpoch) {
          return;
        }
        this.handleTurnError(err);
      } finally {
        this.busy = false;
      }
    },

    async beginVoice(): Promise<void> {
      if (!this.sessionId || this.busy || this.voiceState !== "idle") {
        return; // half-duplex: never record while Coco speaks or thinks
      }
      this.clearIdleTimer();
      this.error = null;
      try {
        activeRecording = await startListening();
        this.recording = true;
        this.voiceState = "listening";
      } catch {
        activeRecording = null;
        this.recording = false;
        this.voiceState = "idle";
        this.error = MIC_UNAVAILABLE;
        this.armIdleTimer();
      }
    },

    async finishVoice(): Promise<void> {
      if (
        !activeRecording ||
        !this.sessionId ||
        this.busy ||
        this.voiceState !== "listening"
      ) {
        return;
      }
      const handle = activeRecording;
      activeRecording = null;
      this.recording = false;
      const epoch = flowEpoch;
      this.busy = true;
      this.voiceState = "processing";
      this.error = null;
      try {
        const { blob, mimeType } = await handle.stop();
        if (epoch !== flowEpoch) {
          return;
        }
        try {
          const data = await api.sendSpeech(this.sessionId, blob, mimeType);
          if (epoch !== flowEpoch) {
            return;
          }
          this.applyTurnData(data);
          if (!data.finished) {
            this.announce(data.assistantText);
          }
        } catch (err: unknown) {
          if (epoch !== flowEpoch) {
            return;
          }
          if (err instanceof api.ApiError && err.code === "asr_failed") {
            this.handleAsrFailure();
          } else {
            this.handleTurnError(err);
          }
        }
      } finally {
        this.busy = false;
      }
    },

    handleAsrFailure(): void {
      // Never resend the original recording (closure B-05): invite the
      // child to record NEW audio, at most one re-record per turn.
      if (this.asrReRecordsLeft > 0) {
        this.asrReRecordsLeft -= 1;
        this.voiceState = "idle";
        this.error = ASR_RETRY_HINT;
        this.armIdleTimer();
        return;
      }
      this.voiceState = "error";
      this.error = ASR_EXHAUSTED_HINT;
    },

    handleTurnError(err: unknown): void {
      if (err instanceof api.ApiError && err.code === "session_not_found") {
        this.reset();
        this.error = SESSION_ENDED_HINT;
        return;
      }
      this.voiceState = "idle";
      this.error = errorMessage(err);
      this.armIdleTimer();
    },

    /** Play the reply; the mic stays closed until synthesis ends. */
    announce(text: string): void {
      const epoch = flowEpoch;
      this.voiceState = "speaking";
      speak(text, () => {
        if (
          epoch !== flowEpoch ||
          this.phase !== "session" ||
          this.voiceState !== "speaking"
        ) {
          return;
        }
        this.voiceState = "idle";
        this.armIdleTimer();
      });
    },

    /** Voice I/O teardown — speech synthesis plus any open recorder. */
    stopVoiceIO(): void {
      stopSpeaking();
      if (activeRecording) {
        activeRecording.cancel();
        activeRecording = null;
      }
      this.recording = false;
    },

    async endSession(): Promise<void> {
      const sid = this.sessionId;
      this.reset();
      this.endReason = "exit";
      if (sid) {
        try {
          await api.endSession(sid);
        } catch (err: unknown) {
          if (
            err instanceof api.ApiError &&
            err.code === "session_not_found"
          ) {
            return; // already gone (e.g. auto-ended on finish): goal met
          }
          // Exiting must always work: reset locally even if the server
          // call fails, but surface the failure instead of swallowing it.
          this.error = "Could not reach the server while ending the session.";
        }
      }
    },

    async finishDueToTimeout(reason: "timeout" | "idle"): Promise<void> {
      if (this.phase !== "session") {
        return;
      }
      const sid = this.sessionId;
      this.reset();
      this.endReason = reason;
      this.phase = "end";
      if (sid) {
        try {
          await api.endSession(sid);
        } catch {
          // The server TTL will collect it; the child experience is fine.
        }
      }
    },

    armTotalTimer(): void {
      this.clearTotalTimer();
      totalTimer = setTimeout(() => {
        void this.finishDueToTimeout("timeout");
      }, SESSION_MAX_MS);
    },

    armIdleTimer(): void {
      this.clearIdleTimer();
      if (this.phase !== "session" || this.finished) {
        return;
      }
      idleTimer = setTimeout(() => {
        void this.finishDueToTimeout("idle");
      }, IDLE_TIMEOUT_MS);
    },

    clearIdleTimer(): void {
      if (idleTimer !== null) {
        clearTimeout(idleTimer);
        idleTimer = null;
      }
    },

    clearTotalTimer(): void {
      if (totalTimer !== null) {
        clearTimeout(totalTimer);
        totalTimer = null;
      }
    },

    reset(): void {
      flowEpoch += 1;
      this.clearTimers();
      this.stopVoiceIO();
      Object.assign(this, { ...initialState });
    },

    clearTimers(): void {
      this.clearIdleTimer();
      this.clearTotalTimer();
    },

    applyTurnData(data: TurnData): void {
      this.assistantText = data.assistantText;
      this.characterState = characterStateFor(data.state);
      this.turn = data.turn;
      this.finished = data.finished;
      this.asrReRecordsLeft = ASR_RE_RECORD_BUDGET;
      if (data.finished) {
        this.endReason = "finished";
        this.voiceState = "idle";
        this.phase = "end";
        this.clearTimers();
        this.stopVoiceIO();
        // Natural finish auto-ends the server session (closure G2): no
        // click needed. The backend also deletes on the finished turn, so
        // a 404 here is success — swallow it.
        if (this.sessionId) {
          void Promise.resolve(api.endSession(this.sessionId)).catch(() => {});
        }
      }
    },
  },
});
