import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import { useRouter } from "vue-router";

import * as api from "../services/api";
import { useSessionStore } from "../stores/session";
import EndView from "./EndView.vue";

vi.mock("vue-router", () => {
  const push = vi.fn();
  const replace = vi.fn();
  return { useRouter: () => ({ push, replace }) };
});

vi.mock("../services/api", () => ({
  ApiError: class MockApiError extends Error {
    constructor(
      public code: string,
      message: string,
    ) {
      super(message);
    }
  },
  createSession: vi.fn(),
  reply: vi.fn(),
  endSession: vi.fn().mockResolvedValue({ ended: true }),
  sendSpeech: vi.fn(),
}));

vi.mock("../services/voice", () => ({
  startListening: vi.fn(),
  speak: vi.fn(),
}));

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
});

describe("EndView", () => {
  it("ending from the finish screen clears the server session", async () => {
    // Spec §8.3: 会话结束必须清理上下文 — the happy path (natural finish)
    // must end the server-side session too, not just wipe local state.
    const store = useSessionStore();
    store.sessionId = "sid-9";
    store.phase = "end";
    store.finished = true;
    const wrapper = mount(EndView);

    await wrapper.find(".primary-button").trigger("click");
    await flushPromises();

    expect(api.endSession).toHaveBeenCalledWith("sid-9");
    expect(useRouter().replace).toHaveBeenCalledWith("/");
    expect(store.sessionId).toBeNull();
  });
});
