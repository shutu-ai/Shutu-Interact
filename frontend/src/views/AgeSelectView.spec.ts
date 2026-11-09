import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import { useRouter } from "vue-router";

import AgeSelectView from "./AgeSelectView.vue";

vi.mock("vue-router", () => {
  const push = vi.fn();
  const replace = vi.fn();
  return { useRouter: () => ({ push, replace }) };
});

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
});

describe("AgeSelectView", () => {
  it("renders one big button per age group", () => {
    const wrapper = mount(AgeSelectView);

    expect(wrapper.findAll(".primary-button")).toHaveLength(3);
  });

  it("has a back button returning to the welcome page", async () => {
    const wrapper = mount(AgeSelectView);

    await wrapper.find(".back-button").trigger("click");

    expect(useRouter().push).toHaveBeenCalledWith("/");
  });
});
