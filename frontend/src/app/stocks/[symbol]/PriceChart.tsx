"use client";

import { useEffect, useRef, useState } from "react";
import type { IChartApi, UTCTimestamp } from "lightweight-charts";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/generated/schema";
import { readableError } from "@/lib/api/errors";
import { formatPrice } from "@/lib/format";
import { LoadingState } from "@/components/feedback/LoadingState";
import { MessageBox } from "@/components/feedback/MessageBox";
import styles from "./dashboard.module.css";

type Candle = components["schemas"]["Candle"];
type HistoryResponse = components["schemas"]["HistoryResponse"];

/** Range buttons above the chart. Short ranges use hourly candles, longer ones daily. */
const RANGES = [
  { key: "1W", label: "1 week", days: 7, interval: "1h" },
  { key: "1M", label: "1 month", days: 30, interval: "1d" },
  { key: "3M", label: "3 months", days: 91, interval: "1d" },
  { key: "6M", label: "6 months", days: 182, interval: "1d" },
  { key: "1Y", label: "1 year", days: 365, interval: "1d" },
] as const;

type RangeKey = (typeof RANGES)[number]["key"];

type HistoryState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "done"; history: HistoryResponse; candles: Candle[] };

interface PriceChartProps {
  symbol: string;
  currency: string | null | undefined;
}

export function PriceChart({ symbol, currency }: PriceChartProps) {
  const [rangeKey, setRangeKey] = useState<RangeKey>("3M");
  const [state, setState] = useState<HistoryState>({ status: "loading" });
  const [retryCount, setRetryCount] = useState(0);
  const range = RANGES.find((r) => r.key === rangeKey)!;

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });

    const end = new Date();
    const start = new Date(end.getTime() - range.days * 24 * 60 * 60 * 1000);

    apiClient
      .GET("/api/v1/instruments/{symbol}/history", {
        params: {
          path: { symbol },
          query: {
            start: start.toISOString(),
            end: end.toISOString(),
            interval: range.interval,
            limit: 500,
          },
        },
      })
      .then(({ data, error }) => {
        if (cancelled) return;
        if (error || !data) {
          setState({
            status: "error",
            message: readableError(error, "The price history could not be loaded."),
          });
          return;
        }
        setState({ status: "done", history: data, candles: sortCandles(data.items) });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "error", message: "The price history could not be loaded." });
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, range.days, range.interval, retryCount]);

  return (
    <section className={styles.chartSection} aria-labelledby="chart-heading">
      <div className={styles.chartHeader}>
        <h2 id="chart-heading" className={styles.chartTitle}>
          Price history <span className={styles.chartUnit}>(closing price, {currency || "USD"})</span>
        </h2>
        <div className={styles.rangeButtons} role="group" aria-label="Time range">
          {RANGES.map((r) => (
            <button
              key={r.key}
              type="button"
              className={`${styles.rangeButton} ${r.key === rangeKey ? styles.rangeButtonActive : ""}`}
              aria-pressed={r.key === rangeKey}
              aria-label={`Show ${r.label}`}
              onClick={() => setRangeKey(r.key)}
            >
              {r.key}
            </button>
          ))}
        </div>
      </div>

      {state.status === "loading" && (
        <div className={styles.chartBox}>
          <LoadingState label="Loading price history…" />
        </div>
      )}

      {state.status === "error" && (
        <MessageBox
          variant="error"
          title="Price history is not available"
          message={state.message}
          actionLabel="Try again"
          onAction={() => setRetryCount((n) => n + 1)}
        />
      )}

      {state.status === "done" && state.candles.length === 0 && (
        <MessageBox
          title="No price history for this range"
          message="Try a longer time range."
        />
      )}

      {state.status === "done" && state.candles.length > 0 && (
        <>
          {state.history.availability !== "available" && (
            <p className={styles.sourceWarning} role="status">
              ! This price history is {state.history.availability}; it may be incomplete or out of
              date.
            </p>
          )}
          <ChartCanvas candles={state.candles} intraday={range.interval !== "1d"} currency={currency} />
          <p className={styles.chartSummary}>
            {summarize(symbol, state.candles, currency)}
          </p>
        </>
      )}
    </section>
  );
}

/** Draws the area chart. The library touches `window`, so it is loaded only in the browser. */
function ChartCanvas({
  candles,
  intraday,
  currency,
}: {
  candles: Candle[];
  intraday: boolean;
  currency: string | null | undefined;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let chart: IChartApi | null = null;
    let disposed = false;

    import("lightweight-charts").then(({ createChart, AreaSeries }) => {
      if (disposed) return;
      chart = createChart(container, {
        autoSize: true,
        layout: { background: { color: "#ffffff" }, textColor: "#333333", attributionLogo: true },
        grid: { vertLines: { color: "#eeeeee" }, horzLines: { color: "#eeeeee" } },
        timeScale: { timeVisible: intraday, borderColor: "#cccccc" },
        rightPriceScale: { borderColor: "#cccccc" },
        localization: { priceFormatter: (price: number) => formatPrice(String(price), currency) },
      });
      const series = chart.addSeries(AreaSeries, {
        lineColor: "#1a1a1a",
        lineWidth: 2,
        topColor: "rgba(26, 26, 26, 0.25)",
        bottomColor: "rgba(26, 26, 26, 0.02)",
      });
      series.setData(
        candles.map((c) => ({
          time: Math.floor(Date.parse(c.timestamp) / 1000) as UTCTimestamp,
          value: Number(c.close),
        })),
      );
      chart.timeScale().fitContent();
    });

    return () => {
      disposed = true;
      chart?.remove();
    };
  }, [candles, intraday, currency]);

  // The chart itself is hidden from screen readers; the text summary below describes it.
  return <div ref={containerRef} className={styles.chartCanvas} aria-hidden="true" />;
}

/** The chart library needs strictly increasing times, so sort and drop duplicates. */
function sortCandles(items: Candle[]): Candle[] {
  const sorted = [...items].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
  return sorted.filter(
    (c, i) =>
      i === 0 ||
      Math.floor(Date.parse(c.timestamp) / 1000) !==
        Math.floor(Date.parse(sorted[i - 1].timestamp) / 1000),
  );
}

/**
 * One sentence describing what the chart shows (for everyone, and for screen readers).
 * It names the actual first and last dates, because the provider may return less
 * history than the selected range.
 */
function summarize(
  symbol: string,
  candles: Candle[],
  currency: string | null | undefined,
): string {
  const first = candles[0];
  const last = candles[candles.length - 1];
  const lows = candles.map((c) => Number(c.low));
  const highs = candles.map((c) => Number(c.high));
  const day = (iso: string) =>
    new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" }).format(new Date(iso));
  const price = (v: string | number) => formatPrice(String(v), currency);

  return (
    `${symbol} moved from ${price(first.close)} on ${day(first.timestamp)} ` +
    `to ${price(last.close)} on ${day(last.timestamp)}, trading between ` +
    `${price(Math.min(...lows))} and ${price(Math.max(...highs))}.`
  );
}
