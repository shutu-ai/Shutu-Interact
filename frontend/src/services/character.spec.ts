import { describe, expect, it } from "vitest";

import { assetFor, characterStateFor } from "./character";

describe("character mapping", () => {
  it("maps character states to Coco asset paths", () => {
    expect(assetFor("greeting")).toContain("coco_mascot_greeting.png");
    expect(assetFor("listening")).toContain("coco_mascot_listening.png");
    expect(assetFor("thumbsup")).toContain("coco_mascot_thumbsup.png");
    expect(assetFor("idle")).toContain("coco_mascot_idle.png");
  });

  it("maps turn states to character states with an idle fallback", () => {
    expect(characterStateFor("greeting")).toBe("greeting");
    expect(characterStateFor("listening")).toBe("listening");
    expect(characterStateFor("praise")).toBe("thumbsup");
    expect(characterStateFor(null)).toBe("idle");
  });
});
