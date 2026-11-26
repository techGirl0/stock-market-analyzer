"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/generated/schema";
import { readableError } from "@/lib/api/errors";
import { LoadingState } from "@/components/feedback/LoadingState";
import { MessageBox } from "@/components/feedback/MessageBox";
import { ResultsTable, type RowQuote } from "./ResultsTable";
import styles from "./search.module.css";

type InstrumentMatch = components["schemas"]["InstrumentMatch"];

type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "done"; results: InstrumentMatch[] };

const MAX_LENGTH = 100; // same limit as the backend

export function SearchView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // The query lives in the URL (?q=AAPL) so the back button and shared links work.
  const query = (searchParams.get("q") ?? "").trim();

  const [input, setInput] = useState(query);
  const [validation, setValidation] = useState<string | null>(null);
  const [state, setState] = useState<SearchState>({ status: "idle" });
  const [quotes, setQuotes] = useState<Record<string, RowQuote>>({});
  const [retryCount, setRetryCount] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep the input in sync when the URL changes (e.g. browser back button).
  useEffect(() => {
    setInput(query);
  }, [query]);

  // Run the search whenever the query in the URL changes.
  useEffect(() => {
    if (!query) {
      setState({ status: "idle" });
      return;
    }

    let cancelled = false; // ignore answers from an older search
    setState({ status: "loading" });
    setQuotes({});

    (async () => {
      try {
        const { data, error } = await apiClient.GET("/api/v1/instruments/search", {
          params: { query: { q: query, limit: 10 } },
        });
        if (cancelled) return;
        if (error || !data) {
          setState({
            status: "error",
            message: readableError(error, "The search service could not be reached."),
          });
          return;
        }
        setState({ status: "done", results: data.items });
        loadQuotes(data.items, () => cancelled, setQuotes);
      } catch {
        if (!cancelled) {
          setState({ status: "error", message: "The search service could not be reached." });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [query, retryCount]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      setValidation("Please enter a ticker symbol or company name.");
      inputRef.current?.focus();
      return;
    }
    setValidation(null);
    if (trimmed === query) {
      setRetryCount((n) => n + 1); // same text again: search again
    } else {
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  }

  function startOver() {
    setInput("");
    router.push("/search");
    inputRef.current?.focus();
  }

  return (
    <div>
      <h1 className={styles.heading}>Search for a stock</h1>

      <form className={styles.form} onSubmit={handleSubmit} role="search" noValidate>
        <label htmlFor="stock-search" className={styles.visuallyHidden}>
          Ticker symbol or company name
        </label>
        <input
          id="stock-search"
          ref={inputRef}
          className={styles.input}
          type="search"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ticker or company name, e.g. AAPL or Apple"
          maxLength={MAX_LENGTH}
          autoComplete="off"
          aria-invalid={validation ? true : undefined}
          aria-describedby={validation ? "stock-search-error" : undefined}
        />
        <button type="submit" className={styles.searchButton}>
          Search
        </button>
      </form>

      {validation && (
        <p id="stock-search-error" className={styles.validation} role="alert">
          {validation}
        </p>
      )}

      {state.status === "loading" && <LoadingState label="Searching…" />}

      {state.status === "error" && (
        <MessageBox
          variant="error"
          title="Search is not available right now"
          message={state.message}
          actionLabel="Try again"
          onAction={() => setRetryCount((n) => n + 1)}
        />
      )}

      {state.status === "done" && state.results.length === 0 && (
        <MessageBox
          title={`No stock found for "${query}"`}
          message="Check the spelling of the ticker or try the company name."
          actionLabel="Try again"
          onAction={startOver}
        />
      )}

      {state.status === "done" && state.results.length > 0 && (
        <>
          <p className={styles.count} aria-live="polite">
            {state.results.length} {state.results.length === 1 ? "result" : "results"} for &quot;
            {query}&quot;
          </p>
          <ResultsTable results={state.results} quotes={quotes} />
          <p className={styles.hint}>Press &quot;View&quot; to open a stock.</p>
        </>
      )}
    </div>
  );
}

/**
 * The search endpoint only returns ticker and name, so the price and change
 * columns are filled from each result's quote. Requests run in parallel and
 * each row updates on its own, so one slow or failing quote does not block
 * the table.
 */
function loadQuotes(
  items: InstrumentMatch[],
  isCancelled: () => boolean,
  setQuotes: React.Dispatch<React.SetStateAction<Record<string, RowQuote>>>,
) {
  setQuotes(Object.fromEntries(items.map((item) => [item.symbol, "loading" as const])));

  for (const item of items) {
    apiClient
      .GET("/api/v1/instruments/{symbol}/quote", {
        params: { path: { symbol: item.symbol } },
      })
      .then(({ data }) => data ?? ("unavailable" as const))
      .catch(() => "unavailable" as const)
      .then((quote) => {
        if (!isCancelled()) {
          setQuotes((prev) => ({ ...prev, [item.symbol]: quote }));
        }
      });
  }
}
