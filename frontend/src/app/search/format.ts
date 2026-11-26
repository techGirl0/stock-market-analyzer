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
