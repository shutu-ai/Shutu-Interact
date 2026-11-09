import { afterEach, describe, expect, it, vi } from "vitest";

import { speak } from "./voice";

describe("speak (browser TTS)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("speaks English at a kid-friendly rate via speechSynthesis", () => {
    class FakeUtterance {
      text: string;
      lang = "";
      rate = 1;
      constructor(text: string) {
        this.text = text;
      }
    }
    const speakMock = vi.fn();
    const cancelMock = vi.fn();
    vi.stubGlobal("SpeechSynthesisUtterance", FakeUtterance);
    vi.stubGlobal("speechSynthesis", { speak: speakMock, cancel: cancelMock });

    speak("Hello! I'm Coco!");

    expect(speakMock).toHaveBeenCalledTimes(1);
    const utterance = speakMock.mock.calls[0][0];
    expect(utterance.text).toBe("Hello! I'm Coco!");
    expect(utterance.lang).toBe("en-US");
    expect(utterance.rate).toBe(0.9);
    expect(cancelMock).toHaveBeenCalled();
  });
});
