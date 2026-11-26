import type { AiResult, RiskProfile } from "@/lib/api/ai";
import { formatDateTime } from "@/lib/format";
import { Term } from "@/components/Term";
import { LoadingState } from "@/components/feedback/LoadingState";
import styles from "./ai.module.css";

/** The backend's risk-v2 score runs from 1 to 10. */
const RISK_SCORE_MAX = 10;

/** Plain-language explanations for the indicators the backend returns. */
const INDICATOR_HELP: Record<string, string> = {
  "Annualized Volatility":
    "How much the price typically moves over a year. Higher means larger swings, up or down.",
  "Beta vs Market":
    "How strongly the price tends to move with the overall market. 1.0 means about the same as the market.",
  "52-Week Position":
    "Where today's price sits between the lowest (0%) and highest (100%) price of the past year.",
  "Maximum Drawdown": "The largest drop from a high point to a later low point in the period.",
  "Liquidity (Avg Daily $ Volume)":
    "Average value traded per day. Higher usually means it is easier to buy or sell.",
};

interface RiskPanelProps {
  result: AiResult<RiskProfile> | null; // null while loading
  citation?: string; // e.g. "[3]" when shown inside a brief
}

export function RiskPanel({ result, citation }: RiskPanelProps) {
  if (result === null) {
    return (
      <section className={styles.panel} aria-labelledby="risk-heading">
        <h2 id="risk-heading" className={styles.panelTitle}>Risk indicators</h2>
        <LoadingState label="Calculating risk indicators…" />
      </section>
    );
  }

  const risk = result.ok ? result.data : null;
  if (!risk || risk.score === null || risk.meta.availability === "unavailable") {
    return (
      <section className={`${styles.panel} ${styles.panelUnavailable}`} aria-labelledby="risk-heading">
        <h2 id="risk-heading" className={styles.panelTitle}>Risk indicators</h2>
        <p className={styles.unavailableText}>
          Not available. {result.ok ? "Historical risk metrics could not be loaded" : result.message}
          {result.ok ? ", so no risk level is shown." : ""}
        </p>
      </section>
    );
  }

  const percent = Math.min(100, Math.max(0, (risk.score / RISK_SCORE_MAX) * 100));

  return (
    <section className={styles.panel} aria-labelledby="risk-heading">
      <h2 id="risk-heading" className={styles.panelTitle}>Risk indicators</h2>

      {risk.meta.availability !== "available" && (
        <p className={styles.qualityLabel}>
          ! {risk.meta.availability === "stale" ? "Stale data" : "Partial data"}: treat with extra care.
        </p>
      )}

      <p className={styles.score}>
        <Term explanation="A combined score from the indicators below, from 1 (lower) to 10 (higher). It describes past price behaviour, not future results.">
          Risk score
        </Term>
        : <strong>{risk.score} out of {RISK_SCORE_MAX}</strong> {citation}
      </p>
      <div
        className={styles.meter}
        role="meter"
        aria-valuemin={1}
        aria-valuemax={RISK_SCORE_MAX}
        aria-valuenow={risk.score}
        aria-label="Risk score"
      >
        <span className={styles.meterFill} style={{ width: `${percent}%` }} />
      </div>

      <dl className={styles.indicators}>
        {Object.entries(risk.components).map(([name, value]) => (
          <div key={name} className={styles.indicatorRow}>
            <dt>
              {INDICATOR_HELP[name] ? (
                <Term explanation={INDICATOR_HELP[name]}>{name}</Term>
              ) : (
                name
              )}
            </dt>
            <dd>{value ?? "—"}</dd>
          </div>
        ))}
      </dl>

      <PanelFooter
        calculatedAt={risk.meta.calculated_at}
        version={risk.meta.calculation_version}
        assumptions={risk.meta.assumptions}
      />
    </section>
  );
}

/** Timestamp, model version, assumptions and the uncertainty note shown on every risk/forecast view. */
export function PanelFooter({
  calculatedAt,
  version,
  assumptions,
}: {
  calculatedAt: string;
  version: string;
  assumptions: string[];
}) {
  return (
    <div className={styles.panelFooter}>
      <p>
        Calculated {formatDateTime(calculatedAt)} · model {version}
      </p>
      {assumptions.length > 0 && (
        <details className={styles.assumptions}>
          <summary>Assumptions ({assumptions.length})</summary>
          <ul>
            {assumptions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </details>
      )}
      <p className={styles.uncertainty}>Results are uncertain and not investment advice.</p>
    </div>
  );
}
