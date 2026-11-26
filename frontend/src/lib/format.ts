/**
 * The backend sends prices and percentages as decimal strings (e.g. "189.84")
 * so they are not rounded on the way. We only format them for display here.
 */

export function formatPrice(price: string | null | undefined, currency?: string | null): string {
  if (price == null) return "—";
  const value = Number(price);
  if (!Number.isFinite(value)) return "—";
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(value);
  } catch {
    // Unknown currency code: show the number with the code next to it.
    return `${value.toFixed(2)} ${currency ?? ""}`.trim();
  }
}

export type Direction = "up" | "down" | "flat";

export function formatChange(
  changePercent: string | null | undefined,
): { text: string; direction: Direction } | null {
  if (changePercent == null) return null;
  const value = Number(changePercent);
  if (!Number.isFinite(value)) return null;
  const direction: Direction = value > 0 ? "up" : value < 0 ? "down" : "flat";
  const sign = value > 0 ? "+" : "";
  return { text: `${sign}${value.toFixed(1)}%`, direction };
}

/** Large numbers in short form: 2.9T, 54.1M. Used for market cap and volume. */
export function formatCompact(value: number | null | undefined, currency?: string | null): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const options: Intl.NumberFormatOptions = { notation: "compact", maximumFractionDigits: 1 };
  if (currency) {
    try {
      return new Intl.NumberFormat("en-US", { ...options, style: "currency", currency }).format(value);
    } catch {
      // fall through to a plain number
    }
  }
  return new Intl.NumberFormat("en-US", options).format(value);
}

/** "26 Nov 2026, 18:45" in the user's own time zone. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "unknown time";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "unknown time";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

/** How old the data is, e.g. "3 minutes old". */
export function formatAge(iso: string | null | undefined, now: Date = new Date()): string {
  if (!iso) return "age unknown";
  const ms = now.getTime() - new Date(iso).getTime();
  if (!Number.isFinite(ms)) return "age unknown";
  const minutes = Math.max(0, Math.round(ms / 60_000));
  if (minutes < 1) return "less than a minute old";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} old`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} hour${hours === 1 ? "" : "s"} old`;
  return `${Math.round(hours / 24)} days old`;
}
