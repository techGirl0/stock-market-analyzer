import Link from "next/link";
import type { components } from "@/lib/api/generated/schema";
import { formatChange, formatPrice } from "@/lib/format";
import styles from "./search.module.css";

type InstrumentMatch = components["schemas"]["InstrumentMatch"];
type Quote = components["schemas"]["Quote"];

/** Quote for one row: still loading, loaded, or could not be fetched. */
export type RowQuote = "loading" | "unavailable" | Quote;

interface ResultsTableProps {
  results: InstrumentMatch[];
  quotes: Record<string, RowQuote>;
}

const ARROWS = { up: "▲", down: "▼", flat: "■" } as const;
const ARROW_LABELS = { up: "up", down: "down", flat: "unchanged" } as const;

export function ResultsTable({ results, quotes }: ResultsTableProps) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Company</th>
            <th scope="col">Price</th>
            <th scope="col">Change</th>
            <th scope="col">
              <span className={styles.visuallyHidden}>Action</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {results.map((item) => (
            <tr key={item.id}>
              <td className={styles.ticker}>{item.symbol}</td>
              <td>{item.name}</td>
              <PriceCells quote={quotes[item.symbol]} currency={item.currency} />
              <td>
                <Link
                  href={`/stocks/${encodeURIComponent(item.symbol)}`}
                  className={styles.viewButton}
                  aria-label={`View ${item.symbol}, ${item.name}`}
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PriceCells({
  quote,
  currency,
}: {
  quote: RowQuote | undefined;
  currency: string | null | undefined;
}) {
  if (quote === undefined || quote === "loading") {
    return (
      <>
        <td className={styles.muted}>Loading…</td>
        <td className={styles.muted}>—</td>
      </>
    );
  }
  if (quote === "unavailable") {
    return (
      <>
        <td className={styles.muted}>Unavailable</td>
        <td className={styles.muted}>—</td>
      </>
    );
  }

  const change = formatChange(quote.change_percent);
  return (
    <>
      <td>{formatPrice(quote.price, quote.instrument.currency ?? currency)}</td>
      <td>
        {change ? (
          <span className={styles[change.direction]}>
            <span aria-hidden="true">{ARROWS[change.direction]} </span>
            <span className={styles.visuallyHidden}>{ARROW_LABELS[change.direction]} </span>
            {change.text}
          </span>
        ) : (
          <span className={styles.muted}>—</span>
        )}
      </td>
    </>
  );
}
