import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import type { CharacterState } from "../services/character";
import CocoCharacter from "./CocoCharacter.vue";

describe("CocoCharacter", () => {
  it("renders the asset mapped from the given state", () => {
    const wrapper = mount(CocoCharacter, { props: { state: "greeting" } });

    expect(wrapper.find("img").attributes("src")).toContain(
      "coco_mascot_greeting.png",
    );
  });

  it("falls back to the idle asset for an unknown state", () => {
    // Cast simulates invalid runtime input arriving at the view boundary;
    // the component must fall back to the idle asset instead of crashing.
    const bogus = "dancing" as CharacterState;
    const wrapper = mount(CocoCharacter, { props: { state: bogus } });

    expect(wrapper.find("img").attributes("src")).toContain(
      "coco_mascot_idle.png",
    );
  });
});
