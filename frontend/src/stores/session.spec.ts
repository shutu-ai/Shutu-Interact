import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import * as api from "../services/api";
import * as voice from "../services/voice";
import { useSessionStore } from "./session";

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
}));

const mocked = vi.mocked(api);
const mockedVoice = vi.mocked(voice);

function mockRecording(): void {
  mockedVoice.startListening.mockResolvedValue({
    stop: vi
      .fn()
      .mockResolvedValue({ blob: new Blob(["x"]), mimeType: "audio/webm" }),
    cancel: vi.fn(),
  });
}

const greetingData = {
  sessionId: "sid-1",
  assistantText: "Hello! I'm Coco! Do you like dogs?",
  state: "greeting" as const,
  turn: 0,
  finished: false,
  maxTurns: 4,
};

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
});

describe("session store", () => {
  it("chooseAge records the age group and moves to topic phase", async () => {
    const store = useSessionStore();

    store.chooseAge("4-6");

    expect(store.ageGroup).toBe("4-6");
    expect(store.phase).toBe("topic");
  });

  it("chooseTopic creates a session and stores the greeting", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();

    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    expect(mocked.createSession).toHaveBeenCalledWith("7-9", "animals");
    expect(store.sessionId).toBe("sid-1");
    expect(store.assistantText).toContain("Coco");
    expect(store.characterState).toBe("greeting");
    expect(store.phase).toBe("session");
    expect(store.error).toBeNull();
  });

  it("sendChildText updates the dialogue and flips to thumbsup when finished", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mocked.reply.mockResolvedValue({
      assistantText: "Great job! Do you have a pet?",
      state: "listening",
      turn: 1,
      finished: false,
    });
    await store.sendChildText("I like dogs");
    expect(store.turn).toBe(1);
    expect(store.characterState).toBe("listening");
    expect(store.phase).toBe("session");

    mocked.reply.mockResolvedValue({
      assistantText: "Amazing talking with you!",
      state: "praise",
      turn: 4,
      finished: true,
    });
    await store.sendChildText("bye");
    expect(store.finished).toBe(true);
    expect(store.characterState).toBe("thumbsup");
    expect(store.phase).toBe("end");
  });

  it("endSession calls the API and resets all context", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mocked.endSession.mockResolvedValue({ ended: true });
    await store.endSession();

    expect(mocked.endSession).toHaveBeenCalledWith("sid-1");
    expect(store.sessionId).toBeNull();
    expect(store.ageGroup).toBeNull();
    expect(store.topic).toBeNull();
    expect(store.assistantText).toBe("");
    expect(store.phase).toBe("welcome");
  });

  it("endSession still resets locally when the API call fails", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mocked.endSession.mockRejectedValue(new Error("network down"));
    await store.endSession();

    expect(store.sessionId).toBeNull();
    expect(store.phase).toBe("welcome");
    expect(store.error).not.toBeNull();
  });

  it("sendChildVoice records, uploads, applies the turn and speaks", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mockRecording();
    mocked.sendSpeech.mockResolvedValue({
      transcript: "I like dogs.",
      assistantText: "Great job! Do you have a pet?",
      state: "listening",
      turn: 1,
      finished: false,
    });

    await store.beginVoice();
    expect(store.recording).toBe(true);

    await store.finishVoice();

    expect(mocked.sendSpeech).toHaveBeenCalledWith(
      "sid-1",
      expect.any(Blob),
      "audio/webm",
    );
    expect(store.turn).toBe(1);
    expect(store.characterState).toBe("listening");
    expect(mockedVoice.speak).toHaveBeenCalledWith(
      "Great job! Do you have a pet?",
    );
    expect(store.recording).toBe(false);
    expect(store.busy).toBe(false);
  });

  it("retries ASR once with the same recording before failing", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mockRecording();
    const asrError = new api.ApiError(
      "asr_failed",
      "Speech recognition failed.",
    );
    mocked.sendSpeech
      .mockRejectedValueOnce(asrError)
      .mockRejectedValueOnce(asrError);

    await store.beginVoice();
    await store.finishVoice();

    expect(mocked.sendSpeech).toHaveBeenCalledTimes(2);
    expect(store.error).not.toBeNull();
    expect(store.busy).toBe(false);
  });

  it("recovers when the ASR retry succeeds", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mockRecording();
    const asrError = new api.ApiError(
      "asr_failed",
      "Speech recognition failed.",
    );
    mocked.sendSpeech
      .mockRejectedValueOnce(asrError)
      .mockResolvedValueOnce({
        transcript: "I like dogs.",
        assistantText: "Awesome! What animal do you think is funny?",
        state: "listening",
        turn: 1,
        finished: false,
      });

    await store.beginVoice();
    await store.finishVoice();

    expect(mocked.sendSpeech).toHaveBeenCalledTimes(2);
    expect(store.turn).toBe(1);
    expect(store.error).toBeNull();
    expect(mockedVoice.speak).toHaveBeenCalled();
  });

  it("reports a friendly error when the microphone is unavailable", async () => {
    mocked.createSession.mockResolvedValue(greetingData);
    const store = useSessionStore();
    store.chooseAge("7-9");
    await store.chooseTopic("animals");

    mockedVoice.startListening.mockRejectedValue(
      new Error("NotAllowedError"),
    );

    await store.beginVoice();

    expect(store.recording).toBe(false);
    expect(store.error).not.toBeNull();
  });
});
