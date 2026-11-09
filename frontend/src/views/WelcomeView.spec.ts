import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import WelcomeView from "./WelcomeView.vue";

vi.mock("vue-router", () => {
  const push = vi.fn();
  const replace = vi.fn();
  return { useRouter: () => ({ push, replace }) };
});

beforeEach(() => {
  setActivePinia(createPinia());
});

describe("WelcomeView", () => {
  it("states honestly that speech is uploaded and deleted after the interaction", () => {
    const wrapper = mount(WelcomeView);

    const note = wrapper.text();
    expect(note).toContain("语音会上传"); // audio IS uploaded — no absolutes
    expect(note).toContain("家长或监护人"); // adult presence requested
    expect(note).not.toContain("不收集任何个人信息"); // G3: drop the over-claim
    expect(note).not.toContain("no personal information is collected");
  });

  it("requires the guardian confirmation before Start is enabled", async () => {
    const wrapper = mount(WelcomeView);

    const start = wrapper.find(".primary-button");
    expect(start.attributes("disabled")).toBeDefined(); // locked at first

    const consent = wrapper.find(".consent-button");
    expect(consent.exists()).toBe(true);
    await consent.trigger("click");

    expect(wrapper.find(".primary-button").attributes("disabled")).toBeUndefined();
    expect(wrapper.find(".primary-button").text()).toContain("Start");
  });
});
