import type { components } from "@/lib/api/generated/schema";

type AiBriefResponse = components["schemas"]["AiBriefResponse"];
type RiskProfile = components["schemas"]["RiskProfile"];
type ForecastResponse = components["schemas"]["ForecastResponse"];

/**
 * Example AI responses, copied from what the real backend returned for AAPL on
 * 26 Nov 2026 (demo market data) and adapted to any ticker. They let the AI
 * screens be built and reviewed without login or a running AI provider.
 *
 * Scenarios:
 *  - "full"    every part is available
 *  - "partial" risk indicators are unavailable and the forecast is partial (mockup B4)
 *  - "error"   the brief itself fails to generate
 */
export type FixtureScenario = "full" | "partial" | "error";

const DISCLAIMER = "Statistical estimates only. Not personalized investment advice.";

function minutesAgo(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

export function briefFixture(symbol: string, scenario: FixtureScenario): AiBriefResponse {
  const name = symbol === "AAPL" ? "Apple Inc." : `${symbol} (example company)`;
  const asOf = minutesAgo(2);
  const riskSection =
    scenario === "partial"
      ? "### Composite Risk Score\n- Not available: historical risk metrics could not be loaded, so no risk level is shown.\n"
      : "### Composite Risk Score\n- Score: 5/10 [1]\n  - Annualized volatility: 24.66% [1]\n  - Beta vs market: 1.0 [1]\n  - 52-week position: 88.9% [1]\n";

  return {
    ticker: symbol,
    company_name: name,
    brief_text:
      `## ${name} (${symbol})\n` +
      "- Current price: $104.00, +0.97% today (delayed data) [1]\n" +
      "- 52-week range: $99.60 to $103.20, currently near the top of the range [1]\n" +
      "- Market cap: unavailable\n\n" +
      "### News and sentiment\n" +
      "- Mostly neutral across 1 article in the last 7 days [2]\n\n" +
      riskSection +
      "\n### Scenarios (illustrative, not predictions)\n" +
      "- 1 year: pessimistic $71.29, base $106.95, optimistic $160.45 [1]\n\n" +
      "*All figures are statistical estimates. Results are uncertain and not investment advice.*",
    sources: [
      { index: 1, headline: `${symbol} market data`, publisher: "demo", published_at: asOf, source_url: null },
      {
        index: 2,
        headline: `${symbol} market data demo item`,
        publisher: "WolfStreet Signal Demo",
        published_at: minutesAgo(1),
        source_url: "https://example.com/market-data-demo",
      },
    ],
    as_of: asOf,
    generated_at: minutesAgo(1),
    assumptions: [
      "Scenario model: lognormal with 7% annual drift",
      "Volatility held constant at the trailing one-year figure",
    ],
    limitations: [
      "Market cap unavailable from provider",
      "P/E ratio unavailable from provider",
      ...(scenario === "partial" ? ["Historical risk metrics could not be loaded"] : []),
    ],
    disclaimer: DISCLAIMER,
  };
}

export function riskFixture(scenario: FixtureScenario): RiskProfile {
  const meta = {
    calculated_at: minutesAgo(2),
    calculation_version: "risk-v2",
    assumptions: [
      "At least 21 daily observations are required.",
      "Window: one year of daily closes (252 trading days).",
      "Beta benchmark: the broad market index (provider beta), fallback 1.0.",
    ],
    disclaimer: DISCLAIMER,
  };
  if (scenario === "partial") {
    return { score: null, components: {}, meta: { ...meta, availability: "unavailable" } };
  }
  return {
    score: 5,
    components: {
      "Annualized Volatility": "24.66%",
      "Beta vs Market": 1.0,
      "52-Week Position": "88.9%",
      "Maximum Drawdown": "-3.5%",
      "Liquidity (Avg Daily $ Volume)": "$10,141,472",
    },
    meta: { ...meta, availability: "available" },
  };
}

/** Pessimistic / base / optimistic prices per horizon, as returned by forecast-v2. */
const FORECAST_SCENARIOS: Record<string, { bear: number; base: number; bull: number }> = {
  "1m": { bear: 93.1, base: 104.6, bull: 117.4 },
  "3m": { bear: 84.76, base: 103.82, bull: 127.17 },
  "1y": { bear: 71.29, base: 106.95, bull: 160.45 },
};

export function forecastFixture(horizon: string, scenario: FixtureScenario): ForecastResponse {
  return {
    horizon,
    scenarios: [FORECAST_SCENARIOS[horizon] ?? FORECAST_SCENARIOS["3m"]],
    meta: {
      availability: scenario === "partial" ? "partial" : "available",
      calculated_at: minutesAgo(2),
      calculation_version: "forecast-v2",
      assumptions: ["At least 21 daily observations are required.", "Ranges are not predictions."],
      disclaimer: DISCLAIMER,
    },
  };
}
