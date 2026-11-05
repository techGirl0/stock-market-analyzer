import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from stock_data import run_pipeline
from ai_engine import (
    generate_research_brief,
    get_news_feed,
    get_risk_explanation,
    get_volatility_explanation,
    get_scenario_explanation,
    chat_with_ai,
)

st.set_page_config(page_title="Stock Market AI", page_icon="📈", layout="centered")

st.title("📈 Stock Market AI Assistant")
st.markdown("Not sure what a stock is doing? Just ask. Everything explained in plain English.")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔍 Get Started")
st.sidebar.markdown("Type a company's stock symbol below.")
st.sidebar.markdown("- AAPL = Apple\n- TSLA = Tesla\n- MSFT = Microsoft\n- AMZN = Amazon\n- GOOGL = Google")

ticker = st.sidebar.text_input("Stock symbol", placeholder="e.g. AAPL").strip().upper()

st.sidebar.divider()
feature = st.sidebar.radio(
    label="feature",
    options=[
        "📄 Research Brief",
        "📰 News Feed",
        "⚠️ Risk Score",
        "📉 Volatility Forecast",
        "🔮 Scenario Analysis",
        "💬 Chat with AI",
    ],
    label_visibility="collapsed",
)

# ── Run pipeline once per ticker and cache it ─────────────────────────────────
pipeline = None
if ticker:
    cache_key = f"pipeline_{ticker}"
    if cache_key not in st.session_state:
        with st.spinner(f"Loading data for {ticker}..."):
            try:
                st.session_state[cache_key] = run_pipeline(ticker)
            except Exception as e:
                st.error(f"Could not load data for {ticker}: {e}")
    pipeline = st.session_state.get(cache_key)

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — Research Brief
# ════════════════════════════════════════════════════════════════════════════════
if feature == "📄 Research Brief":
    st.header("📄 Research Brief")
    st.markdown("A full easy-to-read summary — what the company does, how it's performing, news, risks and scenarios.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar to get started.")
    elif pipeline:
        if st.button(f"🚀 Generate brief for {ticker}", use_container_width=True):
            with st.spinner("Writing your brief..."):
                st.session_state[f"brief_{ticker}"] = generate_research_brief(pipeline)

        if f"brief_{ticker}" in st.session_state:
            st.success("Done!")
            st.markdown(st.session_state[f"brief_{ticker}"])
            st.divider()
            st.caption("📌 All data from Yahoo Finance via yfinance. Educational only — not financial advice.")

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — News Feed
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "📰 News Feed":
    st.header("📰 News Feed")
    st.markdown("Latest news labelled 🟢 Good / 🔴 Bad / 🟡 Neutral with a plain English explanation.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        if st.button(f"🔄 Load news for {ticker}", use_container_width=True):
            with st.spinner("Analysing headlines..."):
                st.session_state[f"news_{ticker}"] = get_news_feed(pipeline)

        news = st.session_state.get(f"news_{ticker}", [])
        if news:
            good    = sum(1 for n in news if n["sentiment"] == "GOOD")
            bad     = sum(1 for n in news if n["sentiment"] == "BAD")
            neutral = sum(1 for n in news if n["sentiment"] == "NEUTRAL")

            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 Good", good)
            c2.metric("🔴 Bad", bad)
            c3.metric("🟡 Neutral", neutral)
            st.divider()

            style = {
                "GOOD":    ("🟢", "GOOD",    "#1a3d1a", "#2d6a2d"),
                "BAD":     ("🔴", "BAD",     "#3d1a1a", "#6a2d2d"),
                "NEUTRAL": ("🟡", "NEUTRAL", "#3d3a1a", "#6a652d"),
            }
            import html
            for item in news:
                emoji, label, bg, border = style.get(item["sentiment"], style["NEUTRAL"])
                safe_title = html.escape(item["title"])
                safe_exp   = html.escape(item["explanation"])
                pub = item["published"] or "recently"
                st.markdown(
                    f"""<div style="background:{bg}; border-left:4px solid {border};
                                padding:12px 16px; border-radius:6px; margin-bottom:10px;">
                        <div style="font-size:0.75rem; color:#aaa;">{emoji} {label} · {pub}</div>
                        <div style="font-size:1rem; font-weight:600; margin:4px 0;">{safe_title}</div>
                        <div style="font-size:0.875rem; color:#ccc;">{safe_exp}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.caption("📌 News from Yahoo Finance. Sentiment labels by AI — educational only.")

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — Risk Score
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "⚠️ Risk Score":
    st.header("⚠️ Composite Risk Score")
    st.markdown("How risky is this stock? Score from 1 (very safe) to 10 (very risky), calculated from real data.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        risk = pipeline.get("risk")
        if not risk:
            st.warning("Not enough data to compute a risk score for this ticker.")
        else:
            score = risk["score"]
            if score <= 3:   color, label, emoji = "#2d6a2d", "Low Risk",    "🟢"
            elif score <= 6: color, label, emoji = "#6a5a1a", "Medium Risk", "🟡"
            else:            color, label, emoji = "#6a2d2d", "High Risk",   "🔴"

            st.markdown(
                f"""<div style="background:{color}; border-radius:12px; padding:24px;
                            text-align:center; margin-bottom:20px;">
                    <div style="font-size:4rem; font-weight:800;">{score}/10</div>
                    <div style="font-size:1.2rem;">{emoji} {label}</div>
                    <div style="font-size:0.8rem; color:#ccc; margin-top:8px;">
                        {pipeline['company']['name']} · {pipeline['fetched_at']}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.subheader("What makes up this score?")
            for comp in risk["components"].values():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{comp['label']}** — {comp['value']}")
                c2.markdown(f"**{comp['score']}/10**")

            st.divider()
            st.subheader("What does this mean?")
            if st.button("💬 Explain this score in plain English", use_container_width=True):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"risk_exp_{ticker}"] = get_risk_explanation(pipeline)
            if f"risk_exp_{ticker}" in st.session_state:
                st.markdown(st.session_state[f"risk_exp_{ticker}"])

            st.caption("📌 Risk score calculated from yfinance data. Educational only — not financial advice.")

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — Volatility Forecast
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "📉 Volatility Forecast":
    st.header("📉 Volatility Forecast")
    st.markdown("How bumpy could the ride be in the coming days? Based on recent price history.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        vol = pipeline.get("volatility")
        if not vol:
            st.warning("Not enough price history to compute volatility forecasts.")
        else:
            price = pipeline["market"]["current_price"]
            st.subheader("Expected price movement range")

            for days, key in [(5, "forecast_5d"), (10, "forecast_10d"), (20, "forecast_20d")]:
                pct = vol[key]
                dollar = round(price * pct / 100, 2) if price else "N/A"
                low  = round(price - dollar, 2) if price else "N/A"
                high = round(price + dollar, 2) if price else "N/A"
                st.markdown(f"**Next {days} days:** ±{pct}% &nbsp;→&nbsp; roughly ${low} to ${high}")

            st.caption(f"Current 30-day volatility: {vol['current_30d']}% (annualized)")
            st.divider()

            if st.button("💬 Explain what this means", use_container_width=True):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"vol_exp_{ticker}"] = get_volatility_explanation(pipeline)
            if f"vol_exp_{ticker}" in st.session_state:
                st.markdown(st.session_state[f"vol_exp_{ticker}"])

            st.caption("📌 Statistical forecast based on recent volatility. Not a prediction. Educational only.")

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — Scenario Analysis
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "🔮 Scenario Analysis":
    st.header("🔮 Long-Term Scenario Analysis")
    st.markdown("What could this stock look like in 1, 3, or 5 years? Three possible paths — not predictions.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        scenarios = pipeline.get("scenarios")
        if not scenarios:
            st.warning("Not enough data to compute scenarios.")
        else:
            for s in scenarios:
                st.subheader(f"In {s['horizon_years']} year(s)")
                c1, c2, c3 = st.columns(3)
                c1.metric("😟 Worse case",  f"${s['bear']}")
                c2.metric("😐 Middle case", f"${s['base']}")
                c3.metric("😊 Better case", f"${s['bull']}")

            st.divider()
            if st.button("💬 Explain these scenarios in plain English", use_container_width=True):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"scen_exp_{ticker}"] = get_scenario_explanation(pipeline)
            if f"scen_exp_{ticker}" in st.session_state:
                st.markdown(st.session_state[f"scen_exp_{ticker}"])

            st.caption("📌 Scenarios use a standard lognormal model with 7% assumed annual growth. Not predictions. Educational only.")

# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 6 — Chat
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "💬 Chat with AI":
    st.header("💬 Chat with AI")
    st.markdown("Ask anything about this stock. The AI answers using real data and explains every term.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        st.caption(f"Chatting about: **{ticker}**")

        with st.expander("💡 Not sure what to ask? Try one of these"):
            st.markdown(
                "- What does this company actually do?\n"
                "- Is the stock price high or low compared to this year?\n"
                "- What's been in the news recently?\n"
                "- Is this considered a risky stock?\n"
                "- What does the risk score mean?\n"
                "- What could happen to the price in 5 years?"
            )

        history_key = f"history_{ticker}"
        if history_key not in st.session_state:
            st.session_state[history_key] = []

        for msg in st.session_state[history_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input(f"Ask something about {ticker}...")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply, updated = chat_with_ai(pipeline, user_input, st.session_state[history_key])
                    st.session_state[history_key] = updated
                st.markdown(reply)

        if st.session_state.get(history_key):
            if st.button("🗑️ Clear conversation", use_container_width=True):
                st.session_state[history_key] = []
                st.rerun()

        st.caption("📌 All data from Yahoo Finance. Educational only — not financial advice.")
