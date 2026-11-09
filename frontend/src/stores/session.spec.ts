import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import * as api from "../services/api";
import { useSessionStore } from "./session";

vi.mock("../services/api", () => ({
  createSession: vi.fn(),
  reply: vi.fn(),
  endSession: vi.fn(),
}));

const mocked = vi.mocked(api);

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
});
