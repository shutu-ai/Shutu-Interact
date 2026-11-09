import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import FullscreenToggle from "./FullscreenToggle.vue";

function stubFullscreen(element: Element | null): void {
  Object.defineProperty(document, "fullscreenElement", {
    value: element,
    configurable: true,
  });
  document.documentElement.requestFullscreen = vi
    .fn()
    .mockResolvedValue(undefined);
  document.exitFullscreen = vi.fn().mockResolvedValue(undefined);
}

afterEach(() => {
  stubFullscreen(null);
  vi.restoreAllMocks();
});

describe("FullscreenToggle", () => {
  it("shows the enter-fullscreen label when not fullscreen", () => {
    stubFullscreen(null);
    const wrapper = mount(FullscreenToggle);

    expect(wrapper.text()).toContain("全屏 Fullscreen");
    expect(wrapper.text()).not.toContain("Exit Fullscreen");
  });

  it("requests fullscreen on the document root when clicked", async () => {
    stubFullscreen(null);
    const wrapper = mount(FullscreenToggle);

    await wrapper.find("button").trigger("click");

    expect(document.documentElement.requestFullscreen).toHaveBeenCalledOnce();
  });

  it("exits fullscreen when already fullscreen", async () => {
    stubFullscreen(document.documentElement);
    const wrapper = mount(FullscreenToggle);
    // onMounted sync() updates a ref; the DOM settles a microtask later.
    await flushPromises();
    expect(wrapper.text()).toContain("Exit Fullscreen");

    await wrapper.find("button").trigger("click");

    expect(document.exitFullscreen).toHaveBeenCalledOnce();
  });

  it("follows fullscreenchange events in its label", async () => {
    stubFullscreen(null);
    const wrapper = mount(FullscreenToggle);

    stubFullscreen(document.documentElement);
    document.dispatchEvent(new Event("fullscreenchange"));
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Exit Fullscreen");
  });

  it("removes the fullscreenchange listener on unmount", () => {
    const spy = vi.spyOn(document, "removeEventListener");
    const wrapper = mount(FullscreenToggle);

    wrapper.unmount();

    expect(spy).toHaveBeenCalledWith(
      "fullscreenchange",
      expect.any(Function),
    );
  });
});
