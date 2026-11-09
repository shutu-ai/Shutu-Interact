/** G2 (MVP closure) lifecycle behaviors: strict half-duplex, stale-response
 * epoch guard, natural-finish auto-end, 404 recovery, session/idle caps,
 * and voice I/O teardown on exit.
 */

import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { flushPromises } from "@vue/test-utils";

import * as api from "../services/api";
import * as voice from "../services/voice";
import { IDLE_TIMEOUT_MS, SESSION_MAX_MS } from "../config";
import { useSessionStore } from "./session";
import type { TurnData } from "../types/session";

vi.mock("../services/api", () => ({
  ApiError: class MockApiError extends Error {
    constructor(
      public code: string,
      message: string,
    ) {
      super(message);
      this.name = "ApiError";
    }
  },
  createSession: vi.fn(),
  reply: vi.fn(),
  endSession: vi.fn(),
  sendSpeech: vi.fn(),
}));

vi.mock("../services/voice", () => ({
  startListening: vi.fn(),
  speak: vi.fn(),
  stopSpeaking: vi.fn(),
}));

const mocked = vi.mocked(api);
const mockedVoice = vi.mocked(voice);

const greetingData = {
  sessionId: "sid-1",
  assistantText: "Hello! I'm Coco! Do you like dogs?",
  state: "greeting" as const,
  turn: 0,
  finished: false,
  maxTurns: 4,
};

const listeningTurn = (turn: number): TurnData => ({
  assistantText: `Great job! Question ${turn}?`,
  state: "listening",
  turn,
  finished: false,
});

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
  mocked.endSession.mockResolvedValue({ ended: true });
  mockedVoice.startListening.mockImplementation(async () => ({
    stop: vi
      .fn()
      .mockResolvedValue({ blob: new Blob(["x"]), mimeType: "audio/webm" }),
    cancel: vi.fn(),
  }));
});

afterEach(() => {
  vi.useRealTimers();
});

type SessionStore = ReturnType<typeof useSessionStore>;

async function startSession(): Promise<SessionStore> {
  mocked.createSession.mockResolvedValue(greetingData);
  const store = useSessionStore();
  store.chooseAge("7-9");
  await store.chooseTopic("animals");
  return store;
}

/** The speech synthesis finished playing (invoke the store's callback). */
function cocoFinishedSpeaking(): void {
  const call = mockedVoice.speak.mock.calls.at(-1);
  expect(call, "speak should have been called").toBeDefined();
  const onEnded = call![1] as (() => void) | undefined;
  expect(onEnded, "speak should receive an onEnded callback").toBeDefined();
  onEnded!();
}

describe("half-duplex voice loop", () => {
  it("refuses to record while Coco is speaking", async () => {
    const store = await startSession();

    expect(store.voiceState).toBe("speaking");
    await store.beginVoice();

    expect(mockedVoice.startListening).not.toHaveBeenCalled();
    expect(store.voiceState).toBe("speaking");
    expect(store.recording).toBe(false);
  });

  it("returns to idle when the reply finishes playing, then allows recording", async () => {
    const store = await startSession();

    cocoFinishedSpeaking();

    expect(store.voiceState).toBe("idle");
    await store.beginVoice();
    expect(store.recording).toBe(true);
    expect(store.voiceState).toBe("listening");
  });

  it("goes through processing while a turn is in flight", async () => {
    const store = await startSession();
    cocoFinishedSpeaking();

    let resolveReply: (data: TurnData) => void = () => {};
    mocked.reply.mockReturnValueOnce(
      new Promise<TurnData>((resolve) => {
        resolveReply = resolve;
      }),
    );
    const pending = store.sendChildText("I like dogs");
    await flushPromises();
    expect(store.voiceState).toBe("processing");

    resolveReply(listeningTurn(1));
    await flushPromises();
    expect(store.voiceState).toBe("speaking");

    cocoFinishedSpeaking();
    expect(store.voiceState).toBe("idle");
    await pending;
  });

  it("exit stops speech synthesis and any recording", async () => {
    const store = await startSession();
    cocoFinishedSpeaking();
    await store.beginVoice();
    expect(store.recording).toBe(true);

    await store.endSession();

    expect(mockedVoice.stopSpeaking).toHaveBeenCalled();
    expect(store.recording).toBe(false);
  });
});

describe("natural finish", () => {
  it("auto-ends the server session without waiting for a click", async () => {
    const store = await startSession();

    mocked.reply.mockResolvedValueOnce({
      assistantText: "Amazing talking with you!",
      state: "praise",
      turn: 4,
      finished: true,
    });
    await store.sendChildText("bye");

    expect(mocked.endSession).toHaveBeenCalledWith("sid-1");
    expect(store.phase).toBe("end");
    expect(store.finished).toBe(true);
    expect(store.endReason).toBe("finished");
  });
});

describe("stale responses", () => {
  it("a reply resolving after exit cannot touch the fresh state", async () => {
    const store = await startSession();
    cocoFinishedSpeaking();

    let resolveReply: (data: TurnData) => void = () => {};
    mocked.reply.mockReturnValueOnce(
      new Promise<TurnData>((resolve) => {
        resolveReply = resolve;
      }),
    );
    const pending = store.sendChildText("I like dogs");
    await flushPromises();

    await store.endSession();
    resolveReply(listeningTurn(1));
    await flushPromises();
    await pending;

    expect(store.sessionId).toBeNull();
    expect(store.assistantText).toBe("");
    expect(store.phase).toBe("welcome");
    expect(mockedVoice.speak).toHaveBeenCalledTimes(1); // greeting only
  });
});

describe("lost sessions", () => {
  it("session_not_found resets the flow with a friendly hint", async () => {
    const store = await startSession();
    cocoFinishedSpeaking();

    mocked.reply.mockRejectedValueOnce(
      new api.ApiError("session_not_found", "Session not found or already ended."),
    );
    await store.sendChildText("I like dogs");

    expect(store.phase).toBe("welcome");
    expect(store.sessionId).toBeNull();
    expect(store.error).toContain("重新开始");
  });
});

describe("session caps (fake timers)", () => {
  it("auto-ends when the total session cap is hit — even mid-speech", async () => {
    vi.useFakeTimers();
    const store = await startSession();
    // Greeting is still "speaking" (no onEnded), so no idle timer is armed.

    vi.advanceTimersByTime(SESSION_MAX_MS);
    await flushPromises();

    expect(store.phase).toBe("end");
    expect(store.endReason).toBe("timeout");
    expect(mocked.endSession).toHaveBeenCalledWith("sid-1");
    expect(mockedVoice.stopSpeaking).toHaveBeenCalled();
  });

  it("auto-ends after idle silence at the mic", async () => {
    vi.useFakeTimers();
    const store = await startSession();
    cocoFinishedSpeaking(); // idle timer armed

    vi.advanceTimersByTime(IDLE_TIMEOUT_MS);
    await flushPromises();

    expect(store.phase).toBe("end");
    expect(store.endReason).toBe("idle");
    expect(mocked.endSession).toHaveBeenCalledWith("sid-1");
  });

  it("child activity pushes the idle timeout back", async () => {
    vi.useFakeTimers();
    const store = await startSession();
    cocoFinishedSpeaking();

    vi.advanceTimersByTime(IDLE_TIMEOUT_MS - 1_000);
    mocked.reply.mockResolvedValueOnce(listeningTurn(1));
    await store.sendChildText("I like dogs");
    expect(store.phase).toBe("session");
    cocoFinishedSpeaking(); // new idle window armed

    vi.advanceTimersByTime(IDLE_TIMEOUT_MS - 1_000);
    expect(store.phase).toBe("session");
  });
});

describe("ASR re-record budget", () => {
  it("after a second ASR failure the mic pauses until a turn succeeds", async () => {
    const store = await startSession();
    cocoFinishedSpeaking();
    const asrError = new api.ApiError(
      "asr_failed",
      "Speech recognition failed.",
    );
    mocked.sendSpeech.mockRejectedValue(asrError);

    await store.beginVoice();
    await store.finishVoice(); // failure #1 → re-record invited
    expect(store.canRecord).toBe(true);

    await store.beginVoice();
    await store.finishVoice(); // failure #2 → budget exhausted

    expect(store.canRecord).toBe(false);
    expect(store.voiceState).toBe("error");
    expect(store.error).not.toBeNull();

    mocked.reply.mockResolvedValueOnce(listeningTurn(1));
    await store.sendChildText("text fallback"); // a turn succeeds
    cocoFinishedSpeaking();

    expect(store.canRecord).toBe(true); // budget restored for the new turn
  });
});
