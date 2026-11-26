"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/generated/schema";
import { readableError } from "@/lib/api/errors";
import { formatChange, formatCompact, formatPrice } from "@/lib/format";
import { MessageBox } from "@/components/feedback/MessageBox";
import { DataSourceNote } from "./DataSourceNote";
import { PriceChart } from "./PriceChart";
import styles from "./dashboard.module.css";

type Quote = components["schemas"]["Quote"];

type QuoteState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "done"; quote: Quote };

const ARROWS = { up: "▲", down: "▼", flat: "■" } as const;

export function StockDashboard({ symbol }: { symbol: string }) {
  const router = useRouter();
  const [state, setState] = useState<QuoteState>({ status: "loading" });
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });

    apiClient
      .GET("/api/v1/instruments/{symbol}/quote", { params: { path: { symbol } } })
      .then(({ data, error }) => {
        if (cancelled) return;
        if (error || !data) {
          setState({
            status: "error",
            message: readableError(error, "The market data service could not be reached."),
          });
        } else {
          setState({ status: "done", quote: data });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({ status: "error", message: "The market data service could not be reached." });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, retryCount]);

  function goBack() {
    // Return to the exact search results if we came from there, otherwise open search.
    if (window.history.length > 1) router.back();
    else router.push("/search");
  }

  const quote = state.status === "done" ? state.quote : null;
  const title = quote ? `${quote.instrument.name} (${symbol})` : symbol;

  return (
    <div>
      <button type="button" className={styles.backLink} onClick={goBack}>
        &lt; Back to search results
      </button>

      <div className={styles.titleRow}>
        <h1 className={styles.title}>{title}</h1>
        {state.status === "loading" && (
          <p className={styles.loadingText} role="status">
            Loading stock data…
          </p>
        )}
        {quote && <PriceHeadline quote={quote} />}
      </div>

      {state.status === "error" && (
        <MessageBox
          variant="error"
          title={`No data available for "${symbol}"`}
          message={`${state.message} Please try again later or search for another stock.`}
          actionLabel="Try again"
          onAction={() => setRetryCount((n) => n + 1)}
          secondaryLabel="Back to search"
          secondaryHref="/search"
        />
      )}

      {state.status === "loading" && <LoadingSkeleton />}

      {quote && (
        <>
          {/* Mockup B1: the research brief starts from the dashboard. */}
          <Link
            href={`/stocks/${encodeURIComponent(symbol)}/brief`}
            className={`${styles.watchlistButton} ${styles.briefButton}`}
          >
            Generate research brief
          </Link>

          {quote.meta && <DataSourceNote meta={quote.meta} />}

          <PriceChart symbol={symbol} currency={quote.instrument.currency} />

          <div className={styles.cards}>
            <StatCard
              label="Previous close"
              value={formatPrice(quote.previous_close, quote.instrument.currency)}
            />
            <StatCard label="Volume" value={formatCompact(quote.volume)} />
            <StatCard
              label="Market cap"
              value={formatCompact(quote.market_cap, quote.instrument.currency)}
            />
          </div>

          <div className={styles.actions}>
            {/* The watchlist screens are SCRUM-103; the watchlist page reads ?add= to pre-fill its add dialog. */}
            <Link
              href={`/watchlist?add=${encodeURIComponent(symbol)}`}
              className={styles.watchlistButton}
            >
              + Add to watchlist
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

function PriceHeadline({ quote }: { quote: Quote }) {
  const change = formatChange(quote.change_percent);
  return (
    <p className={styles.priceBlock}>
      <span className={styles.price}>{formatPrice(quote.price, quote.instrument.currency)}</span>
      {change && (
        <span className={`${styles.change} ${styles[change.direction]}`}>
          <span aria-hidden="true">{ARROWS[change.direction]} </span>
          {change.text} today
        </span>
      )}
    </p>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.card}>
      <p className={styles.cardLabel}>{label}</p>
      <p className={styles.cardValue}>{value}</p>
    </div>
  );
}

/** Mockup S5: grey placeholders in the shape of the real page. */
function LoadingSkeleton() {
  return (
    <>
      <div className={styles.chartPlaceholder} aria-hidden="true">
        <p className={styles.placeholderTitle}>Loading…</p>
        <p className={styles.placeholderText}>Fetching quote and price history</p>
      </div>
      <div className={styles.cards} aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <div key={i} className={styles.card}>
            <span className={`${styles.skeleton} ${styles.skeletonShort}`} />
            <span className={`${styles.skeleton} ${styles.skeletonLong}`} />
          </div>
        ))}
      </div>
    </>
  );
}
