/** Typed API client for the frozen Task-1 backend contract.
 *
 * External payloads are never trusted: every response is validated with zod
 * at this boundary before it reaches the rest of the app.
 */

import { z } from "zod";

import type {
  CreateSessionData,
  EndData,
  SpeechData,
  TurnData,
} from "../types/session";


const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ApiError";
  }
}

const errorEnvelopeSchema = z.object({
  success: z.literal(false),
  error: z.object({ code: z.string(), message: z.string() }),
});

const successEnvelopeSchema = z.object({
  success: z.literal(true),
  data: z.unknown(),
});

const turnDataSchema = z
  .object({
    assistant_text: z.string(),
    state: z.enum(["greeting", "listening", "praise"]),
    turn: z.number().int(),
    finished: z.boolean(),
  })
  .transform((raw) => ({
    assistantText: raw.assistant_text,
    state: raw.state,
    turn: raw.turn,
    finished: raw.finished,
  }));

const createSessionDataSchema = z
  .object({
    session_id: z.string().min(1),
    assistant_text: z.string(),
    state: z.enum(["greeting", "listening", "praise"]),
    turn: z.number().int(),
    finished: z.boolean(),
    max_turns: z.number().int(),
  })
  .transform((raw) => ({
    sessionId: raw.session_id,
    assistantText: raw.assistant_text,
    state: raw.state,
    turn: raw.turn,
    finished: raw.finished,
    maxTurns: raw.max_turns,
  }));

const endDataSchema = z
  .object({ ended: z.boolean() })
  .transform((raw) => ({ ended: raw.ended }));

// G3 (MVP closure): the child transcript is deliberately absent — the
// backend never echoes it back; the kiosk only needs the reply line.
const speechDataSchema = z
  .object({
    assistant_text: z.string(),
    state: z.enum(["greeting", "listening", "praise"]),
    turn: z.number().int(),
    finished: z.boolean(),
  })
  .transform((raw) => ({
    assistantText: raw.assistant_text,
    state: raw.state,
    turn: raw.turn,
    finished: raw.finished,
  }));

async function request<T>(
  path: string,
  schema: z.ZodType<T, z.ZodTypeDef, unknown>,
  options: { body?: unknown } = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers:
        options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" },
      body:
        options.body === undefined
          ? undefined
          : options.body instanceof FormData
            ? options.body
            : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(
      "network",
      "Network error. Please check the connection.",
    );
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(
      "bad_response",
      `Request failed with status ${response.status}.`,
    );
  }

  if (!response.ok) {
    const parsedError = errorEnvelopeSchema.safeParse(payload);
    if (parsedError.success) {
      throw new ApiError(
        parsedError.data.error.code,
        parsedError.data.error.message,
      );
    }
    throw new ApiError(
      "http_error",
      `Request failed with status ${response.status}.`,
    );
  }

  const envelope = successEnvelopeSchema.safeParse(payload);
  if (!envelope.success) {
    throw new ApiError(
      "bad_response",
      "Server response has an unexpected shape.",
    );
  }

  const parsed = schema.safeParse(envelope.data.data);
  if (!parsed.success) {
    throw new ApiError(
      "bad_response",
      "Server response has an unexpected shape.",
    );
  }
  return parsed.data;
}

export function createSession(
  ageGroup: string,
  topic: string,
): Promise<CreateSessionData> {
  return request("/api/sessions", createSessionDataSchema, {
    body: { age_group: ageGroup, topic },
  });
}

export function reply(sessionId: string, text: string): Promise<TurnData> {
  return request(
    `/api/sessions/${encodeURIComponent(sessionId)}/replies`,
    turnDataSchema,
    { body: { text } },
  );
}

export function endSession(sessionId: string): Promise<EndData> {
  return request(
    `/api/sessions/${encodeURIComponent(sessionId)}/end`,
    endDataSchema,
    { body: {} },
  );
}

export function sendSpeech(
  sessionId: string,
  audio: Blob,
  mimeType: string,
): Promise<SpeechData> {
  const form = new FormData();
  const extension = mimeType.includes("mp4") ? "m4a" : "webm";
  form.append("audio", audio, `speech.${extension}`);
  return request(
    `/api/sessions/${encodeURIComponent(sessionId)}/speech`,
    speechDataSchema,
    { body: form },
  );
}
