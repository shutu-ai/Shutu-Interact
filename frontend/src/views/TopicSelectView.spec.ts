import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import { useRouter } from "vue-router";

import { useSessionStore } from "../stores/session";
import TopicSelectView from "./TopicSelectView.vue";

vi.mock("vue-router", () => {
  const push = vi.fn();
  const replace = vi.fn();
  return { useRouter: () => ({ push, replace }) };
});

beforeEach(() => {
  setActivePinia(createPinia());
  vi.clearAllMocks();
});

describe("TopicSelectView", () => {
  it("renders one big button per topic", () => {
    const wrapper = mount(TopicSelectView);

    expect(wrapper.findAll(".primary-button")).toHaveLength(5);
  });

  it("has a back button returning to the age page", async () => {
    const wrapper = mount(TopicSelectView);

    await wrapper.find(".back-button").trigger("click");

    expect(useRouter().push).toHaveBeenCalledWith("/age");
  });

  it("marks the error line as an alert", () => {
    useSessionStore().error = "无法连接服务器";

    const wrapper = mount(TopicSelectView);

    expect(wrapper.find(".error").attributes("role")).toBe("alert");
  });
});
