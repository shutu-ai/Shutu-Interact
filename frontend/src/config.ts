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
