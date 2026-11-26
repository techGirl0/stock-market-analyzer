import type { AiResult, ForecastResponse } from "@/lib/api/ai";
import { formatPrice } from "@/lib/format";
import { Term } from "@/components/Term";
import { LoadingState } from "@/components/feedback/LoadingState";
import { PanelFooter } from "./RiskPanel";
import styles from "./ai.module.css";

export const FORECAST_HORIZONS = [
  { key: "1m", label: "1 month" },
  { key: "3m", label: "3 months" },
  { key: "1y", label: "1 year" },
] as const;

/**
 * The backend names its scenarios bear/base/bull. We show neutral names instead
 * of market slang, pessimistic first.
 */
const SCENARIO_NAMES = [
  { key: "bear", label: "Pessimistic" },
  { key: "base", label: "Base" },
  { key: "bull", label: "Optimistic" },
] as const;

interface ForecastPanelProps {
  result: AiResult<ForecastResponse> | null; // null while loading
  horizon: string;
  onHorizonChange: (horizon: string) => void;
  currency?: string | null;
  citation?: string;
}

export function ForecastPanel({
  result,
  horizon,
  onHorizonChange,
  currency,
  citation,
}: ForecastPanelProps) {
  const horizonLabel = FORECAST_HORIZONS.find((h) => h.key === horizon)?.label ?? horizon;
  const forecast = result?.ok ? result.data : null;
  const scenarios = forecast?.scenarios[0];
  const unavailable =
    result !== null && (!forecast || !scenarios || forecast.meta.availability === "unavailable");

  return (
    <section
      className={`${styles.panel} ${unavailable ? styles.panelUnavailable : ""}`}
      aria-labelledby="forecast-heading"
    >
      <div className={styles.panelHeader}>
        <h2 id="forecast-heading" className={styles.panelTitle}>
          Forecast{" "}
          <Term explanation="A possible outcome under stated assumptions. Scenarios are not predictions or price targets.">
            scenarios
          </Term>
        </h2>
        <div className={styles.horizonButtons} role="group" aria-label="Forecast horizon">
          {FORECAST_HORIZONS.map((h) => (
            <button
              key={h.key}
              type="button"
              className={`${styles.horizonButton} ${h.key === horizon ? styles.horizonButtonActive : ""}`}
              aria-pressed={h.key === horizon}
              aria-label={`Show scenarios over ${h.label}`}
              onClick={() => onHorizonChange(h.key)}
            >
              {h.key.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {result === null && <LoadingState label="Building forecast scenarios…" />}

      {unavailable && (
        <p className={styles.unavailableText}>
          Not available. {result && !result.ok ? result.message : "No scenarios could be calculated."}
        </p>
      )}

      {forecast && scenarios && !unavailable && (
        <>
          {forecast.meta.availability !== "available" && (
            <p className={styles.qualityLabel}>
              ! {forecast.meta.availability === "stale" ? "Stale data" : "Partial data"}: these
              scenarios may be less reliable.
            </p>
          )}

          <p>
            Three scenarios over {horizonLabel}, not predictions{citation ? ` ${citation}` : ""}:
          </p>
          <ScenarioRange scenarios={scenarios} currency={currency} />
          <ul className={styles.scenarioList}>
            {SCENARIO_NAMES.map(({ key, label }) => (
              <li key={key}>
                <span>{label}</span>
                <strong>{formatPrice(String(scenarios[key]), currency)}</strong>
              </li>
            ))}
          </ul>

          <PanelFooter
            calculatedAt={forecast.meta.calculated_at}
            version={forecast.meta.calculation_version}
            assumptions={forecast.meta.assumptions}
          />
        </>
      )}
    </section>
  );
}

/** A bar from the pessimistic to the optimistic value, with the base scenario marked. */
function ScenarioRange({
  scenarios,
  currency,
}: {
  scenarios: Record<string, number>;
  currency?: string | null;
}) {
  const low = scenarios.bear;
  const high = scenarios.bull;
  const base = scenarios.base;
  const basePercent = high > low ? ((base - low) / (high - low)) * 100 : 50;

  return (
    <div className={styles.range} aria-hidden="true">
      <div className={styles.rangeBar}>
        <span className={styles.rangeMarker} style={{ left: `${basePercent}%` }} />
      </div>
      <div className={styles.rangeLabels}>
        <span>{formatPrice(String(low), currency)}</span>
        <span>{formatPrice(String(high), currency)}</span>
      </div>
    </div>
  );
}
