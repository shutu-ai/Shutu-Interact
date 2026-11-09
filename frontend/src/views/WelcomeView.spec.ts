import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import WelcomeView from "./WelcomeView.vue";

vi.mock("vue-router", () => {
  const push = vi.fn();
  const replace = vi.fn();
  return { useRouter: () => ({ push, replace }) };
});

describe("WelcomeView", () => {
  it("shows the anonymous-interaction privacy notice (spec §7.1)", () => {
    setActivePinia(createPinia());
    const wrapper = mount(WelcomeView);

    expect(wrapper.text()).toContain("不收集任何个人信息");
    expect(wrapper.text()).toContain("no personal information is collected");
  });
});
