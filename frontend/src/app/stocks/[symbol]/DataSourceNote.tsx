import type { components } from "@/lib/api/generated/schema";
import { formatAge, formatDateTime } from "@/lib/format";
import styles from "./dashboard.module.css";

type DataMeta = components["schemas"]["DataMeta"];

const AVAILABILITY_LABELS: Partial<Record<DataMeta["availability"], string>> = {
  stale: "Stale data: these values may be out of date.",
  partial: "Partial data: some values are missing.",
  unavailable: "Some data is currently unavailable.",
};

/**
 * Always shows where the data comes from, whether it is delayed and how old it is
 * (FUNC-8, USE-9). Stale or partial data is labelled, never shown as fresh.
 */
export function DataSourceNote({ meta }: { meta: DataMeta }) {
  const warning = AVAILABILITY_LABELS[meta.availability];

  return (
    <div className={styles.sourceNote}>
      {warning && (
        <p className={styles.sourceWarning} role="status">
          ! {warning}
        </p>
      )}
      <p>
        Source: <strong>{meta.source}</strong> · {meta.delayed ? "Delayed data" : "Real-time data"} ·
        As of {formatDateTime(meta.fetched_at)} ({formatAge(meta.fetched_at)})
      </p>
      <p className={styles.limitations}>
        Prices may be delayed or incomplete and are shown for information only. This is not
        investment advice.
      </p>
    </div>
  );
}
