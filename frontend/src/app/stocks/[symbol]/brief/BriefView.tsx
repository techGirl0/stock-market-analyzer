"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import {
  AI_DATA_SOURCE,
  getBrief,
  getForecast,
  getRisk,
  type AiBriefResponse,
  type AiResult,
  type FixtureScenario,
  type ForecastResponse,
  type RiskProfile,
} from "@/lib/api/ai";
import { formatDateTime } from "@/lib/format";
import { MessageBox } from "@/components/feedback/MessageBox";
import { RiskPanel } from "@/components/ai/RiskPanel";
import { ForecastPanel } from "@/components/ai/ForecastPanel";
import styles from "./brief.module.css";

const LOADING_STEPS = [
  "Gathering quotes and history",
  "Reading news sentiment",
  "Calculating risk indicators",
  "Building forecast scenarios",
];

export function BriefView({ symbol }: { symbol: string }) {
  // With fixtures, ?fixture=partial or ?fixture=error shows the other states (mockup B4).
  const searchParams = useSearchParams();
  const scenario = parseScenario(searchParams.get("fixture"));

  const [brief, setBrief] = useState<AiResult<AiBriefResponse> | null>(null);
  const [risk, setRisk] = useState<AiResult<RiskProfile> | null>(null);
  const [forecast, setForecast] = useState<AiResult<ForecastResponse> | null>(null);
  const [horizon, setHorizon] = useState("3m");
  const [retryCount, setRetryCount] = useState(0);

  // Brief and risk load together; each part shows up as soon as it is ready.
  useEffect(() => {
    let cancelled = false;
    setBrief(null);
    setRisk(null);
    getBrief(symbol, scenario).then((r) => !cancelled && setBrief(r));
    getRisk(symbol, scenario).then((r) => !cancelled && setRisk(r));
    return () => {
      cancelled = true;
    };
  }, [symbol, scenario, retryCount]);

  // The forecast reloads on its own when the horizon changes.
  useEffect(() => {
    let cancelled = false;
    setForecast(null);
    getForecast(symbol, horizon, scenario).then((r) => !cancelled && setForecast(r));
    return () => {
      cancelled = true;
    };
  }, [symbol, horizon, scenario, retryCount]);

  const backLink = (
    <Link href={`/stocks/${encodeURIComponent(symbol)}`} className={styles.backLink}>
      &lt; Back to {symbol} dashboard
    </Link>
  );

  if (brief === null) {
    return (
      <div>
        {backLink}
        <h1 className={styles.title}>Research brief: {symbol}</h1>
        <div className={styles.generating} role="status" aria-live="polite">
          <p className={styles.generatingTitle}>Generating research brief…</p>
          <p className={styles.dots} aria-hidden="true">
            <span />
            <span />
            <span />
          </p>
          <ul className={styles.steps}>
            {LOADING_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  if (!brief.ok) {
    return (
      <div>
        {backLink}
        <h1 className={styles.title}>Research brief: {symbol}</h1>
        <MessageBox
          variant="error"
          title="The research brief could not be generated"
          message={`${brief.message} Please try again in a moment.`}
          actionLabel="Try again"
          onAction={() => setRetryCount((n) => n + 1)}
          secondaryLabel="Back to dashboard"
          secondaryHref={`/stocks/${encodeURIComponent(symbol)}`}
        />
      </div>
    );
  }

  const data = brief.data;
  const somethingMissing =
    isMissing(risk, (r) => r.meta.availability) || isMissing(forecast, (f) => f.meta.availability);

  return (
    <div>
      {backLink}

      {somethingMissing && (
        <p className={styles.partialBanner} role="status">
          ! Some data was unavailable. This brief uses only the data that could be loaded.
        </p>
      )}

      <h1 className={styles.title}>
        Research brief: {data.company_name} ({data.ticker})
      </h1>
      <p className={styles.subtitle}>
        Generated {formatDateTime(data.generated_at)}, using market data from{" "}
        {formatDateTime(data.as_of)}. Figures cite their source in brackets.
        {AI_DATA_SOURCE === "fixtures" && (
          <span className={styles.fixtureNote}> Example data (fixtures), not live results.</span>
        )}
      </p>

      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.wide}`} aria-labelledby="summary-heading">
          <h2 id="summary-heading" className={styles.cardTitle}>
            Summary: snapshot, news and sentiment
          </h2>
          <div className={styles.markdown}>
            {/* skipHtml: the AI text is never allowed to inject HTML into the page. */}
            <ReactMarkdown
              skipHtml
              components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {data.brief_text}
            </ReactMarkdown>
          </div>
        </section>

        <RiskPanel result={risk} />
        <ForecastPanel result={forecast} horizon={horizon} onHorizonChange={setHorizon} />

        <section className={`${styles.card} ${styles.wide}`} aria-labelledby="sources-heading">
          <h2 id="sources-heading" className={styles.cardTitle}>
            Sources and timestamps
          </h2>
          {data.sources && data.sources.length > 0 ? (
            <ol className={styles.sources}>
              {data.sources.map((s) => (
                <li key={s.index}>
                  [{s.index}]{" "}
                  {s.source_url ? (
                    <a href={s.source_url} target="_blank" rel="noopener noreferrer">
                      {s.headline}
                    </a>
                  ) : (
                    s.headline
                  )}
                  {s.publisher && <>, {s.publisher}</>}
                  {s.published_at && <>, {formatDateTime(s.published_at)}</>}
                </li>
              ))}
            </ol>
          ) : (
            <p className={styles.muted}>No sources were returned for this brief.</p>
          )}
        </section>

        <section className={`${styles.card} ${styles.wide}`} aria-labelledby="limits-heading">
          <h2 id="limits-heading" className={styles.cardTitle}>
            Assumptions and limitations
          </h2>
          <div className={styles.twoLists}>
            <div>
              <h3 className={styles.listTitle}>Assumptions</h3>
              <BulletList items={data.assumptions} empty="None stated." />
            </div>
            <div>
              <h3 className={styles.listTitle}>Limitations</h3>
              <BulletList items={data.limitations} empty="None reported." />
            </div>
          </div>
        </section>
      </div>

      <p className={styles.disclaimer}>
        Educational information only. Forecasts are scenarios, not guarantees, and this is not
        investment advice. {data.disclaimer}
      </p>
    </div>
  );
}

function BulletList({ items, empty }: { items?: string[]; empty: string }) {
  if (!items || items.length === 0) return <p className={styles.muted}>{empty}</p>;
  return (
    <ul className={styles.bullets}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

/** True when a part failed or came back without fully available data. */
function isMissing<T>(result: AiResult<T> | null, availability: (data: T) => string): boolean {
  if (result === null) return false; // still loading
  return !result.ok || availability(result.data) !== "available";
}

function parseScenario(value: string | null): FixtureScenario {
  return value === "partial" || value === "error" ? value : "full";
}
