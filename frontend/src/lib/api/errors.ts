/**
 * Turns whatever the API client returned as an error into a short sentence
 * a user can read. The backend sends errors as
 * { error: { code, message, request_id, details } }, but network failures
 * and unexpected responses do not follow that shape, so we fall back to a
 * generic message instead of showing raw JSON.
 */
export function readableError(error: unknown, fallback: string): string {
  if (typeof error === "object" && error !== null && "error" in error) {
    const inner = (error as { error?: { message?: unknown } }).error;
    if (inner && typeof inner.message === "string" && inner.message.length > 0) {
      return inner.message;
    }
  }
  return fallback;
}
