/** Character state mapping (plan §7):
 *  idle → 默认等待, greeting → 欢迎/说话, listening → 等待语音输入, thumbsup → 结束鼓励.
 */

import type { TurnState } from "../types/session";

export type CharacterState = "idle" | "greeting" | "listening" | "thumbsup";

const ASSETS: Readonly<Record<CharacterState, string>> = {
  idle: "/assets/coco_mascot_idle.png",
  greeting: "/assets/coco_mascot_greeting.png",
  listening: "/assets/coco_mascot_listening.png",
  thumbsup: "/assets/coco_mascot_thumbsup.png",
};

export function assetFor(state: CharacterState): string {
  return ASSETS[state] ?? ASSETS.idle;
}

export function characterStateFor(
  turnState: TurnState | null,
): CharacterState {
  switch (turnState) {
    case "greeting":
      return "greeting";
    case "listening":
      return "listening";
    case "praise":
      return "thumbsup";
    default:
      return "idle";
  }
}
