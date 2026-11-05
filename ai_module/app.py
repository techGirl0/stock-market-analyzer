import streamlit as st
import sys
import os
from datetime import datetime

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

# ── Optional: Compare two stocks ──────────────────────────────────────────────
st.sidebar.divider()
compare_on = st.sidebar.toggle("🔀 Compare two stocks", value=False)
ticker_b = ""
if compare_on:
    ticker_b = st.sidebar.text_input(
        "Second stock symbol", placeholder="e.g. MSFT"
    ).strip().upper()
    if ticker_b:
        st.sidebar.markdown(f"Comparing **{ticker or '?'}** vs **{ticker_b}**")

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


# ── Pipeline loader helper ────────────────────────────────────────────────────
def load_pipeline(t: str):
    if not t:
        return None
    key = f"pipeline_{t}"
    if key not in st.session_state:
        with st.spinner(f"Loading data for {t}..."):
            try:
                st.session_state[key] = run_pipeline(t)
            except Exception as e:
                st.error(f"Could not load data for {t}: {e}")
                return None
    return st.session_state.get(key)


pipeline  = load_pipeline(ticker)
pipeline_b = load_pipeline(ticker_b) if (compare_on and ticker_b) else None


# ── Comparison header helper ──────────────────────────────────────────────────
def comparison_cols(label_a, label_b):
    """Return two columns pre-labelled with the tickers being compared."""
    c1, c2 = st.columns(2)
    c1.subheader(f"📌 {label_a}")
    c2.subheader(f"📌 {label_b}")
    return c1, c2


# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — Research Brief
# ════════════════════════════════════════════════════════════════════════════════
if feature == "📄 Research Brief":
    st.header("📄 Research Brief")
    st.markdown("A full easy-to-read summary — what the company does, how it's performing, news, risks and scenarios.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar to get started.")
    elif pipeline:
        if compare_on and ticker_b and pipeline_b:
            # ── Comparison mode ──
            col_a, col_b = comparison_cols(ticker, ticker_b)
            with col_a:
                if st.button(f"🚀 Generate brief for {ticker}", use_container_width=True):
                    with st.spinner("Writing brief..."):
                        st.session_state[f"brief_{ticker}"] = generate_research_brief(pipeline)
                if f"brief_{ticker}" in st.session_state:
                    st.markdown(st.session_state[f"brief_{ticker}"])
                    # Export button
                    st.download_button(
                        label="⬇️ Download brief (.txt)",
                        data=st.session_state[f"brief_{ticker}"],
                        file_name=f"{ticker}_brief_{datetime.today().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
            with col_b:
                if st.button(f"🚀 Generate brief for {ticker_b}", use_container_width=True):
                    with st.spinner("Writing brief..."):
                        st.session_state[f"brief_{ticker_b}"] = generate_research_brief(pipeline_b)
                if f"brief_{ticker_b}" in st.session_state:
                    st.markdown(st.session_state[f"brief_{ticker_b}"])
                    st.download_button(
                        label="⬇️ Download brief (.txt)",
                        data=st.session_state[f"brief_{ticker_b}"],
                        file_name=f"{ticker_b}_brief_{datetime.today().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
        else:
            # ── Single mode ──
            if st.button(f"🚀 Generate brief for {ticker}", use_container_width=True):
                with st.spinner("Writing your brief..."):
                    st.session_state[f"brief_{ticker}"] = generate_research_brief(pipeline)

            if f"brief_{ticker}" in st.session_state:
                st.success("Done!")
                st.markdown(st.session_state[f"brief_{ticker}"])
                st.divider()
                st.download_button(
                    label="⬇️ Download brief as .txt",
                    data=st.session_state[f"brief_{ticker}"],
                    file_name=f"{ticker}_brief_{datetime.today().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
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
        import html

        def render_news(pip, tkr):
            if st.button(f"🔄 Load news for {tkr}", use_container_width=True):
                with st.spinner("Analysing headlines..."):
                    st.session_state[f"news_{tkr}"] = get_news_feed(pip)

            news = st.session_state.get(f"news_{tkr}", [])
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

        if compare_on and ticker_b and pipeline_b:
            col_a, col_b = comparison_cols(ticker, ticker_b)
            with col_a:
                render_news(pipeline, ticker)
            with col_b:
                render_news(pipeline_b, ticker_b)
        else:
            render_news(pipeline, ticker)


# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — Risk Score
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "⚠️ Risk Score":
    st.header("⚠️ Composite Risk Score")
    st.markdown("How risky is this stock? Score from 1 (very safe) to 10 (very risky), calculated from real data.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        def render_risk(pip, tkr):
            risk = pip.get("risk")
            if not risk:
                st.warning("Not enough data to compute a risk score for this ticker.")
                return

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
                        {pip['company']['name']} · {pip['fetched_at']}
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
            if st.button(f"💬 Explain {tkr} score in plain English", use_container_width=True, key=f"risk_btn_{tkr}"):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"risk_exp_{tkr}"] = get_risk_explanation(pip)
            if f"risk_exp_{tkr}" in st.session_state:
                st.markdown(st.session_state[f"risk_exp_{tkr}"])
            st.caption("📌 Risk score calculated from yfinance data. Educational only — not financial advice.")

        if compare_on and ticker_b and pipeline_b:
            col_a, col_b = comparison_cols(ticker, ticker_b)
            with col_a:
                render_risk(pipeline, ticker)
            with col_b:
                render_risk(pipeline_b, ticker_b)
        else:
            render_risk(pipeline, ticker)


# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — Volatility Forecast
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "📉 Volatility Forecast":
    st.header("📉 Volatility Forecast")
    st.markdown("How bumpy could the ride be in the coming days? Based on recent price history.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        def render_volatility(pip, tkr):
            vol = pip.get("volatility")
            if not vol:
                st.warning("Not enough price history to compute volatility forecasts.")
                return

            price = pip["market"]["current_price"]
            st.subheader("Expected price movement range")
            for days, key in [(5, "forecast_5d"), (10, "forecast_10d"), (20, "forecast_20d")]:
                pct = vol[key]
                dollar = round(price * pct / 100, 2) if price else "N/A"
                low  = round(price - dollar, 2) if price else "N/A"
                high = round(price + dollar, 2) if price else "N/A"
                st.markdown(f"**Next {days} days:** ±{pct}% &nbsp;→&nbsp; roughly ${low} to ${high}")

            st.caption(f"Current 30-day volatility: {vol['current_30d']}% (annualized)")
            st.divider()
            if st.button(f"💬 Explain {tkr} volatility", use_container_width=True, key=f"vol_btn_{tkr}"):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"vol_exp_{tkr}"] = get_volatility_explanation(pip)
            if f"vol_exp_{tkr}" in st.session_state:
                st.markdown(st.session_state[f"vol_exp_{tkr}"])
            st.caption("📌 Statistical forecast based on recent volatility. Not a prediction. Educational only.")

        if compare_on and ticker_b and pipeline_b:
            col_a, col_b = comparison_cols(ticker, ticker_b)
            with col_a:
                render_volatility(pipeline, ticker)
            with col_b:
                render_volatility(pipeline_b, ticker_b)
        else:
            render_volatility(pipeline, ticker)


# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — Scenario Analysis
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "🔮 Scenario Analysis":
    st.header("🔮 Long-Term Scenario Analysis")
    st.markdown("What could this stock look like in 1, 3, or 5 years? Three possible paths — not predictions.")

    if not ticker:
        st.info("👈 Enter a stock symbol in the sidebar.")
    elif pipeline:
        def render_scenarios(pip, tkr):
            scenarios = pip.get("scenarios")
            if not scenarios:
                st.warning("Not enough data to compute scenarios.")
                return

            for s in scenarios:
                st.subheader(f"In {s['horizon_years']} year(s)")
                c1, c2, c3 = st.columns(3)
                c1.metric("😟 Worse case",  f"${s['bear']}")
                c2.metric("😐 Middle case", f"${s['base']}")
                c3.metric("😊 Better case", f"${s['bull']}")

            st.divider()
            if st.button(f"💬 Explain {tkr} scenarios", use_container_width=True, key=f"scen_btn_{tkr}"):
                with st.spinner("Generating explanation..."):
                    st.session_state[f"scen_exp_{tkr}"] = get_scenario_explanation(pip)
            if f"scen_exp_{tkr}" in st.session_state:
                st.markdown(st.session_state[f"scen_exp_{tkr}"])
            st.caption("📌 Scenarios use a standard lognormal model with 7% assumed annual growth. Not predictions. Educational only.")

        if compare_on and ticker_b and pipeline_b:
            col_a, col_b = comparison_cols(ticker, ticker_b)
            with col_a:
                render_scenarios(pipeline, ticker)
            with col_b:
                render_scenarios(pipeline_b, ticker_b)
        else:
            render_scenarios(pipeline, ticker)


# ════════════════════════════════════════════════════════════════════════════════
# FEATURE 6 — Chat
# ════════════════════════════════════════════════════════════════════════════════
elif feature == "💬 Chat with AI":
    st.header("💬 Chat with AI")
    st.markdown("Ask anything about this stock. The AI answers using real data and explains every term.")

    if compare_on and ticker_b:
        st.info("Chat works with one stock at a time. Use the main ticker above.")

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
