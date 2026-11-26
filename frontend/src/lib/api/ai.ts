import { apiClient } from "./client";
import { readableError } from "./errors";
import type { components } from "./generated/schema";
import {
  briefFixture,
  forecastFixture,
  riskFixture,
  type FixtureScenario,
} from "./fixtures/ai";

export type AiBriefResponse = components["schemas"]["AiBriefResponse"];
export type RiskProfile = components["schemas"]["RiskProfile"];
export type ForecastResponse = components["schemas"]["ForecastResponse"];
export type { FixtureScenario };

/** Either the data, or a sentence explaining why it is missing. */
export type AiResult<T> = { ok: true; data: T } | { ok: false; message: string };

/**
 * The one place the AI screens get their data from.
 *
 * NEXT_PUBLIC_AI_DATA_SOURCE=fixtures (default) returns the example responses in
 * ./fixtures/ai.ts; NEXT_PUBLIC_AI_DATA_SOURCE=api calls the real backend endpoints.
 * The screens never need to know which one is used.
 */
export const AI_DATA_SOURCE: "fixtures" | "api" =
  process.env.NEXT_PUBLIC_AI_DATA_SOURCE === "api" ? "api" : "fixtures";

/** Pretend network delay for fixtures, so loading states are visible during review. */
const FIXTURE_DELAY_MS = 1200;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), FIXTURE_DELAY_MS));
}

export async function getBrief(
  symbol: string,
  scenario: FixtureScenario = "full",
): Promise<AiResult<AiBriefResponse>> {
  if (AI_DATA_SOURCE === "fixtures") {
    if (scenario === "error") {
      return delay({ ok: false, message: "The research assistant could not generate a brief." });
    }
    return delay({ ok: true, data: briefFixture(symbol, scenario) });
  }
  return call(
    () => apiClient.POST("/api/v1/instruments/{symbol}/brief", { params: { path: { symbol } } }),
    "The research assistant could not generate a brief.",
  );
}

export async function getRisk(
  symbol: string,
  scenario: FixtureScenario = "full",
): Promise<AiResult<RiskProfile>> {
  if (AI_DATA_SOURCE === "fixtures") return delay({ ok: true, data: riskFixture(scenario) });
  return call(
    () => apiClient.GET("/api/v1/instruments/{symbol}/risk", { params: { path: { symbol } } }),
    "Risk indicators could not be loaded.",
  );
}

export async function getForecast(
  symbol: string,
  horizon: string,
  scenario: FixtureScenario = "full",
): Promise<AiResult<ForecastResponse>> {
  if (AI_DATA_SOURCE === "fixtures") {
    return delay({ ok: true, data: forecastFixture(horizon, scenario) });
  }
  return call(
    () =>
      apiClient.GET("/api/v1/instruments/{symbol}/forecast", {
        params: { path: { symbol }, query: { horizon } },
      }),
    "Forecast scenarios could not be loaded.",
  );
}

/** Runs a real API call and turns any failure into a readable message. */
async function call<T>(
  request: () => Promise<{ data?: T; error?: unknown }>,
  fallback: string,
): Promise<AiResult<T>> {
  try {
    const { data, error } = await request();
    if (error || data === undefined) return { ok: false, message: readableError(error, fallback) };
    return { ok: true, data };
  } catch {
    return { ok: false, message: fallback };
  }
}
