import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, createSession, endSession, reply, sendSpeech } from "./api";

const okEnvelope = (data: unknown) => ({
  ok: true,
  status: 200,
  json: async () => ({ success: true, data }),
});

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("createSession posts JSON and returns camelCase data", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okEnvelope({
        session_id: "abc123",
        assistant_text: "Hello! I'm Coco!",
        state: "greeting",
        turn: 0,
        finished: false,
        max_turns: 4,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const data = await createSession("7-9", "animals");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/sessions",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      age_group: "7-9",
      topic: "animals",
    });
    expect(data).toEqual({
      sessionId: "abc123",
      assistantText: "Hello! I'm Coco!",
      state: "greeting",
      turn: 0,
      finished: false,
      maxTurns: 4,
    });
  });

  it("throws ApiError with code and message on error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({
          success: false,
          error: { code: "session_not_found", message: "Session not found." },
        }),
      }),
    );

    const error = await reply("gone", "hi").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("session_not_found");
    expect((error as ApiError).message).toBe("Session not found.");
  });

  it("throws ApiError code 'network' when fetch rejects", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    const error = await createSession("4-6", "colors").catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("network");
  });

  it("reply posts text and returns turn data; end posts end", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okEnvelope({
        assistant_text: "Great job! What is your favorite animal?",
        state: "listening",
        turn: 1,
        finished: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const turn = await reply("abc123", "I like dogs");
    expect(turn).toEqual({
      assistantText: "Great job! What is your favorite animal?",
      state: "listening",
      turn: 1,
      finished: false,
    });
    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/api/sessions/abc123/replies",
    );

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(okEnvelope({ ended: true })),
    );
    await expect(endSession("abc123")).resolves.toEqual({ ended: true });
  });

  it("sendSpeech uploads FormData and returns only the turn data (G3: no transcript echo)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okEnvelope({
        assistant_text: "Great job! Do you have a pet?",
        state: "listening",
        turn: 1,
        finished: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const blob = new Blob(["fake-audio"], { type: "audio/webm" });
    const data = await sendSpeech("abc123", blob, "audio/webm");

    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/api/sessions/abc123/speech",
    );
    const init = fetchMock.mock.calls[0][1];
    expect(init.body).toBeInstanceOf(FormData);
    const form = init.body as FormData;
    const uploaded = form.get("audio");
    expect(uploaded).toBeInstanceOf(Blob);
    expect(init.headers).not.toHaveProperty("Content-Type");
    expect(data).toEqual({
      assistantText: "Great job! Do you have a pet?",
      state: "listening",
      turn: 1,
      finished: false,
    });
  });
});
