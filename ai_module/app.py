import streamlit as st
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from stock_data import run_pipeline, validate_ticker
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


# ── PDF builder ───────────────────────────────────────────────────────────────

def build_brief_pdf(ticker: str, company_name: str, brief_text: str, fetched_at: str) -> bytes:
    """
    Renders the research brief as a styled PDF and returns the raw bytes.
    Uses only core fonts (no external font files needed).
    """
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        raise ImportError("fpdf2 is not installed. Run: pip install fpdf2==2.9.0")

    def clean(line: str) -> str:
        line = re.sub(r"^#{1,3}\s*", "", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        return line.strip()

    def safe(text: str) -> str:
        """Replace characters outside latin-1 so core fonts don't crash."""
        return (
            text
            .replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2022", "-")
            .replace("\u00b1", "+/-")
            .encode("latin-1", errors="replace").decode("latin-1")
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    # ── Header bar ────────────────────────────────────────────────────────────
    pdf.set_fill_color(26, 35, 126)
    pdf.rect(0, 0, 210, 32, style="F")

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(18, 8)
    pdf.cell(0, 10, safe(f"Research Brief: {ticker}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(18, 20)
    pdf.cell(0, 6, safe(f"{company_name}  |  Data fetched: {fetched_at}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(30, 30, 30)
    pdf.ln(10)

    # ── Body ──────────────────────────────────────────────────────────────────
    for raw_line in brief_text.splitlines():
        line = clean(raw_line)
        if not line:
            pdf.ln(3)
            continue

        if re.match(r"^#{1,3}\s", raw_line):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_fill_color(230, 235, 255)
            pdf.set_text_color(26, 35, 126)
            pdf.ln(3)
            pdf.set_x(18)
            pdf.cell(0, 8, safe(line), fill=True,
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(1)
        elif raw_line.strip().startswith("- "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(22)
            pdf.multi_cell(0, 6, safe("- " + line.lstrip("- ").strip()))
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(18)
            pdf.multi_cell(0, 6, safe(line))

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 6,
        "Educational only - not financial advice. Data sourced from Yahoo Finance via yfinance.",
        align="C",
    )

    return bytes(pdf.output())


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
    if key in st.session_state:
        return st.session_state.get(key)

    # Step 1 — validate before fetching
    with st.spinner(f"Checking ticker {t}..."):
        valid, error_type = validate_ticker(t)

    if not valid:
        if error_type == "not_found":
            st.error(
                f"**\"{t}\" is not a recognised stock ticker.**\n\n"
                "Please check the symbol and try again. "
                "Examples of valid tickers: AAPL, TSLA, MSFT, AMZN, GOOGL.",
                icon="🔍",
            )
        else:  # no_data
            st.error(
                f"**\"{t}\" exists but its data is currently unavailable.**\n\n"
                "This can happen when a stock is halted, delisted, or the data provider "
                "is temporarily down. Try again in a few minutes.",
                icon="📡",
            )
        return None

    # Step 2 — fetch full pipeline
    with st.spinner(f"Loading data for {t}..."):
        try:
            st.session_state[key] = run_pipeline(t)
        except Exception as e:
            st.error(f"Unexpected error loading data for {t}: {e}", icon="⚠️")
            return None

    return st.session_state.get(key)


pipeline  = load_pipeline(ticker)
pipeline_b = load_pipeline(ticker_b) if (compare_on and ticker_b) else None


# ── Data availability banner ──────────────────────────────────────────────────
def show_data_banner(pip: dict, tkr: str):
    """Shows a small status row so the user knows what data is available."""
    if not pip:
        return

    has_price    = pip["market"].get("current_price") is not None
    has_history  = pip.get("volatility") is not None   # proxy: computed only when >21 days
    has_risk     = pip.get("risk") is not None
    has_scenarios = pip.get("scenarios") is not None
    has_news     = bool(pip.get("news"))

    all_ok = all([has_price, has_history, has_risk, has_scenarios, has_news])
    if all_ok:
        st.success(f"All data loaded for **{tkr}**. All features available.", icon="✅")
        return

    # Something is missing — show a detailed breakdown
    rows = []
    rows.append(f"{'✅' if has_price    else '❌'} Current price & market snapshot")
    rows.append(f"{'✅' if has_history  else '⚠️'} Price history (needed for Volatility & Scenarios)")
    rows.append(f"{'✅' if has_risk     else '⚠️'} Risk score")
    rows.append(f"{'✅' if has_news     else '⚠️'} News headlines")

    missing = []
    if not has_history:
        missing.append("Volatility Forecast and Scenario Analysis")
    if not has_risk:
        missing.append("Risk Score")
    if not has_news:
        missing.append("News Feed")

    with st.expander(f"⚠️ Some data is unavailable for **{tkr}** — click to see details", expanded=True):
        for r in rows:
            st.markdown(r)
        if missing:
            st.info(
                "The following features will show a 'not enough data' message: "
                + ", ".join(missing) + ". "
                "All other features (Research Brief, Chat) still work normally."
            )

if ticker and pipeline:
    show_data_banner(pipeline, ticker)
if compare_on and ticker_b and pipeline_b:
    show_data_banner(pipeline_b, ticker_b)


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
                    pdf_bytes = build_brief_pdf(
                        ticker,
                        pipeline["company"]["name"],
                        st.session_state[f"brief_{ticker}"],
                        pipeline["fetched_at"],
                    )
                    st.download_button(
                        label="⬇️ Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{ticker}_brief_{datetime.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            with col_b:
                if st.button(f"🚀 Generate brief for {ticker_b}", use_container_width=True):
                    with st.spinner("Writing brief..."):
                        st.session_state[f"brief_{ticker_b}"] = generate_research_brief(pipeline_b)
                if f"brief_{ticker_b}" in st.session_state:
                    st.markdown(st.session_state[f"brief_{ticker_b}"])
                    pdf_bytes_b = build_brief_pdf(
                        ticker_b,
                        pipeline_b["company"]["name"],
                        st.session_state[f"brief_{ticker_b}"],
                        pipeline_b["fetched_at"],
                    )
                    st.download_button(
                        label="⬇️ Download as PDF",
                        data=pdf_bytes_b,
                        file_name=f"{ticker_b}_brief_{datetime.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
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
                pdf_bytes = build_brief_pdf(
                    ticker,
                    pipeline["company"]["name"],
                    st.session_state[f"brief_{ticker}"],
                    pipeline["fetched_at"],
                )
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name=f"{ticker}_brief_{datetime.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
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
        def render_scenarios(pip, tkr, compact=False):
            scenarios = pip.get("scenarios")
            if not scenarios:
                st.warning("Not enough data to compute scenarios.")
                return

            current = pip["market"]["current_price"]

            def pct_change(target, base):
                if base and target:
                    return f"{((target - base) / base * 100):+.1f}%"
                return "N/A"

            if compact:
                # Compact table layout — fits inside a narrow comparison column
                rows = ["| Horizon | 😟 Worse | 😐 Middle | 😊 Better |",
                        "|---------|----------|-----------|-----------|"]
                for s in scenarios:
                    yrs = s['horizon_years']
                    label = f"{yrs} year" if yrs == 1 else f"{yrs} years"
                    rows.append(
                        f"| {label} "
                        f"| ${s['bear']} ({pct_change(s['bear'], current)}) "
                        f"| ${s['base']} ({pct_change(s['base'], current)}) "
                        f"| ${s['bull']} ({pct_change(s['bull'], current)}) |"
                    )
                st.markdown("\n".join(rows))
            else:
                # Full layout — 3 metrics per row with % change delta
                for s in scenarios:
                    yrs = s['horizon_years']
                    label = f"In {yrs} year" if yrs == 1 else f"In {yrs} years"
                    st.subheader(label)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("😟 Worse case",  f"${s['bear']}",  pct_change(s['bear'],  current))
                    c2.metric("😐 Middle case", f"${s['base']}",  pct_change(s['base'],  current))
                    c3.metric("😊 Better case", f"${s['bull']}",  pct_change(s['bull'],  current))

                st.caption(f"Current price: ${current}  ·  % change shown relative to today")

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
                render_scenarios(pipeline, ticker, compact=True)
            with col_b:
                render_scenarios(pipeline_b, ticker_b, compact=True)
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
