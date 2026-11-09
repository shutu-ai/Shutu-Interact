/** Flow store: welcome → age → topic → session → end.
 *
 * Context (age/topic/sessionId/dialogue) is wiped on reset so nothing
 * outlives the session (spec §8.3).
 */

import { defineStore } from "pinia";

import * as api from "../services/api";
import { characterStateFor, type CharacterState } from "../services/character";
import type { AgeGroup, Topic } from "../types/session";

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
  error: null,
};

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
        this.sessionId = data.sessionId;
        this.assistantText = data.assistantText;
        this.characterState = characterStateFor(data.state);
        this.turn = data.turn;
        this.maxTurns = data.maxTurns;
        this.finished = false;
        this.phase = "session";
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
        this.assistantText = data.assistantText;
        this.characterState = characterStateFor(data.state);
        this.turn = data.turn;
        this.finished = data.finished;
        if (data.finished) {
          this.phase = "end";
        }
      } catch (err: unknown) {
        this.error = errorMessage(err);
      } finally {
        this.busy = false;
      }
    },

    async endSession(): Promise<void> {
      let endError: string | null = null;
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
      Object.assign(this, { ...initialState });
    },
  },
});
