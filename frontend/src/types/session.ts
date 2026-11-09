/** Contract types mirroring the Task-1 backend API (camelCase internally). */

export type AgeGroup = "4-6" | "7-9" | "10-12";

export type Topic = "animals" | "colors" | "fruits" | "sports" | "hobbies";

export type TurnState = "greeting" | "listening" | "praise";

export interface TurnData {
  assistantText: string;
  state: TurnState;
  turn: number;
  finished: boolean;
}

export interface CreateSessionData extends TurnData {
  sessionId: string;
  maxTurns: number;
}

export interface EndData {
  ended: boolean;
}
