/** Front-of-house timings (MVP closure G2). Build-time configurable via
 * VITE_* env vars; defaults match the backend's SESSION_MAX_SECONDS.
 */

function toMs(raw: string | undefined, fallbackMs: number): number {
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallbackMs;
}

/** Total interaction time before the session auto-ends (child safety). */
export const SESSION_MAX_MS = toMs(import.meta.env.VITE_SESSION_MAX_MS, 180_000);

/** How long Coco waits for the child before gently wrapping up. */
export const IDLE_TIMEOUT_MS = toMs(import.meta.env.VITE_SESSION_IDLE_MS, 60_000);

/** Max time the farewell may play after a natural finish before the flow
 * returns home anyway (closure G2: play until complete OR timeout). */
export const FAREWELL_TIMEOUT_MS = toMs(
  import.meta.env.VITE_FAREWELL_TIMEOUT_MS,
  15_000,
);
