import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import { useRouter } from "vue-router";

import { useSessionStore } from "../stores/session";
import SessionView from "./SessionView.vue";

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

function mountView() {
  return mount(SessionView);
}

function seedSession(): ReturnType<typeof useSessionStore> {
  const store = useSessionStore();
  store.sessionId = "sid-1";
  store.phase = "session";
  store.assistantText = "Hello! I'm Coco!";
  store.turn = 2;
  store.maxTurns = 4;
  return store;
}

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
});

describe("SessionView", () => {
  it("shows the thinking hint while waiting for a reply", () => {
    seedSession().busy = true;

    const wrapper = mountView();

    expect(wrapper.text()).toContain("Coco is thinking");
    expect(wrapper.find(".mic-button").attributes("disabled")).toBeDefined();
  });

  it("shows the round progress", () => {
    seedSession();

    const wrapper = mountView();

    expect(wrapper.text()).toContain("2 / 4");
  });

  it("marks the error line as an alert", () => {
    seedSession().error = "没听清,请再试一次";

    const wrapper = mountView();

    expect(wrapper.find(".error").attributes("role")).toBe("alert");
  });

  it("exit returns to the welcome page", async () => {
    seedSession();
    const wrapper = mountView();

    await wrapper.find(".exit-button").trigger("click");
    await flushPromises();

    expect(useRouter().replace).toHaveBeenCalledWith("/");
  });

  it("does not navigate away while the session runs", () => {
    seedSession();

    mountView();

    expect(useRouter().replace).not.toHaveBeenCalled();
  });
});
