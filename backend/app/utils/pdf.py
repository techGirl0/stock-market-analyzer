import re


def build_brief_pdf(
    ticker: str,
    company_name: str,
    brief_text: str,
    fetched_at: str,
    sources: list[dict] | None = None,
) -> bytes:
    """Render a research brief as a styled PDF and return raw bytes."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError as exc:
        raise RuntimeError("fpdf2 is required: pip install fpdf2") from exc

    def _clean(line: str) -> str:
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        line = re.sub(r"`(.*?)`", r"\1", line)
        return line.strip()

    def _safe(text: str) -> str:
        replacements = {
            "’": "'",   # right single quotation mark '
            "‘": "'",   # left single quotation mark '
            "“": '"',   # left double quotation mark "
            "”": '"',   # right double quotation mark "
            "—": "-",   # em dash —
            "–": "-",   # en dash –
            "•": "-",   # bullet •
            "·": "-",   # middle dot ·
            "±": "+/-", # plus-minus ±
            "é": "e",   # é
            "è": "e",   # è
            "à": "a",   # à
            "ü": "u",   # ü
            "ö": "o",   # ö
            "ä": "a",   # ä
            "ß": "ss",  # ß
            "…": "...", # ellipsis …
            " ": " ",   # non-breaking space
            "′": "'",   # prime ′
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _is_table_row(line: str) -> bool:
        return bool(re.match(r"^\s*\|", line))

    def _is_separator_row(line: str) -> bool:
        return bool(re.match(r"^\s*\|[\s:|-]+\|\s*$", line))

    def _parse_table_row(line: str) -> list[str]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        return cells

    def _render_table(pdf: "FPDF", rows: list[list[str]]) -> None:  # type: ignore[name-defined]
        if not rows:
            return
        usable = pdf.w - pdf.l_margin - pdf.r_margin
        col_count = max(len(r) for r in rows)
        if col_count == 0:
            return
        col_w = usable / col_count
        row_h = 6.0
        HEADER_BG = (26, 35, 126)
        HEADER_FG = (255, 255, 255)
        ROW_ALT = (240, 243, 255)
        DARK = (30, 30, 30)

        for i, row in enumerate(rows):
            # Pad row to col_count
            while len(row) < col_count:
                row.append("")
            x_start = pdf.l_margin
            # Determine height needed (multi-line cells)
            max_lines = 1
            for cell in row:
                words = _safe(_clean(cell))
                approx_lines = max(1, int(len(words) * 2.5 / col_w) + 1)
                max_lines = max(max_lines, approx_lines)
            cell_h = row_h * max_lines

            if i == 0:
                pdf.set_fill_color(*HEADER_BG)
                pdf.set_text_color(*HEADER_FG)
                pdf.set_font("Helvetica", "B", 9)
            elif i % 2 == 0:
                pdf.set_fill_color(*ROW_ALT)
                pdf.set_text_color(*DARK)
                pdf.set_font("Helvetica", "", 9)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(*DARK)
                pdf.set_font("Helvetica", "", 9)

            y_before = pdf.get_y()
            for j, cell in enumerate(row):
                pdf.set_xy(x_start + j * col_w, y_before)
                pdf.multi_cell(
                    col_w,
                    row_h,
                    _safe(_clean(cell)),
                    border=1,
                    fill=True,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                    max_line_height=row_h,
                )
            pdf.set_xy(pdf.l_margin, y_before + cell_h)
        pdf.ln(3)

    BLUE = (26, 35, 126)
    LIGHT_BLUE = (230, 235, 255)
    DARK = (30, 30, 30)

    class BriefPDF(FPDF):
        def footer(self) -> None:
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(
                0, 6,
                "Educational only - not financial advice. Data sourced from Yahoo Finance via yfinance.",
                align="C",
            )

    pdf = BriefPDF()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    # Header bar
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(18, 7)
    pdf.cell(0, 10, _safe(f"Research Brief: {ticker}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(18, 21)
    pdf.cell(0, 6, _safe(f"{company_name}  |  Data fetched: {fetched_at}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(12)

    # Collect lines and batch table rows together
    lines = brief_text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        cleaned = _clean(raw)

        # --- Markdown table block ---
        if _is_table_row(raw):
            table_lines = []
            while i < len(lines) and _is_table_row(lines[i]):
                table_lines.append(lines[i])
                i += 1
            # Build rows list, skipping separator rows
            rows = []
            for tl in table_lines:
                if not _is_separator_row(tl):
                    rows.append(_parse_table_row(tl))
            pdf.ln(2)
            _render_table(pdf, rows)
            continue

        if not cleaned:
            pdf.ln(2)

        # Section heading (## or ###)
        elif re.match(r"^#{1,6}\s", raw):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(*LIGHT_BLUE)
            pdf.set_text_color(*BLUE)
            pdf.ln(3)
            pdf.set_x(18)
            pdf.cell(0, 8, _safe(cleaned), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*DARK)
            pdf.ln(1)

        # Bullet (- or * or numbered like "1.")
        elif re.match(r"^[-*]\s|^\d+\.\s", stripped):
            text = re.sub(r"^[-*]\s|^\d+\.\s", "", stripped)
            text = _clean(text)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(23)
            pdf.multi_cell(
                pdf.w - pdf.r_margin - 23,
                5.5,
                _safe("- " + text),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

        # Bold-prefixed key-value line like "**Beta:** 1.089"
        elif re.match(r"^\*\*.*\*\*", stripped):
            rest = re.sub(r"^\*\*.*?\*\*:?\s*", "", stripped)
            rest = _clean(rest)
            label = re.search(r"\*\*(.*?)\*\*", stripped)
            pdf.set_x(18)
            if label:
                pdf.set_font("Helvetica", "B", 10)
                pdf.write(5.5, _safe(label.group(1) + ": "))
                pdf.set_font("Helvetica", "", 10)
                pdf.write(5.5, _safe(rest))
                pdf.ln(6)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5.5, _safe(_clean(stripped)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Normal paragraph
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(18)
            pdf.multi_cell(0, 5.5, _safe(cleaned), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        i += 1

    # --- Sources section ---
    if sources:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_text_color(*BLUE)
        pdf.set_x(18)
        pdf.cell(0, 8, "Sources", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
        pdf.ln(2)
        for src in sources:
            index = src.get("index", "")
            headline = _safe(src.get("headline", ""))
            publisher = _safe(src.get("publisher") or "")
            published_at = src.get("published_at", "")
            # published_at may be a datetime object or ISO string
            if hasattr(published_at, "isoformat"):
                published_at = published_at.isoformat()
            source_url = src.get("source_url") or ""
            # Format: [n] Headline — Publisher (date)
            date_str = published_at[:10] if published_at else ""
            meta = " — ".join(filter(None, [publisher, date_str]))
            label = f"[{index}] {headline}"
            if meta:
                label += f"  ({meta})"
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(18)
            pdf.multi_cell(
                pdf.w - pdf.l_margin - pdf.r_margin,
                5,
                _safe(label),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            if source_url:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(70, 100, 200)
                pdf.set_x(22)
                pdf.multi_cell(
                    pdf.w - pdf.l_margin - pdf.r_margin - 4,
                    4.5,
                    _safe(source_url),
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                pdf.set_text_color(*DARK)
            pdf.ln(1)

    # --- Glossary page ---
    pdf.add_page()

    # Glossary header bar
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, 210, 20, style="F")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(18, 5)
    pdf.cell(0, 10, "Glossary of Terms", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(6)

    GLOSSARY: list[tuple[str, str]] = [
        (
            "Current Price",
            "The last traded price of the stock as reported by the data provider. "
            "May be delayed by 15-20 minutes for most exchanges.",
        ),
        (
            "Day Change (%)",
            "The percentage difference between today's current price and the previous "
            "trading session's closing price. A positive value means the stock is up today.",
        ),
        (
            "Market Capitalisation",
            "Total market value of all outstanding shares. Calculated as share price x total "
            "shares outstanding. Used to classify company size: under $2B = small-cap, "
            "$2B-$10B = mid-cap, $10B-$200B = large-cap, over $200B = mega-cap.",
        ),
        (
            "P/E Ratio (Price-to-Earnings)",
            "Stock price divided by earnings per share (EPS). Indicates how much investors "
            "pay for each dollar of profit. A high P/E suggests growth expectations; a low P/E "
            "may indicate the stock is cheap or the company is struggling.",
        ),
        (
            "Annualised Volatility",
            "A measure of how much the stock price fluctuates over a year, expressed as a "
            "percentage. Calculated from the standard deviation of daily returns scaled to 252 "
            "trading days. Higher volatility = larger swings in either direction. "
            "Under 20% = low, 20-40% = moderate, over 40% = high.",
        ),
        (
            "Beta",
            "Measures how much the stock moves relative to the broader market (typically S&P 500). "
            "Beta = 1.0 means it moves in line with the market. Beta = 2.0 means it tends to move "
            "twice as much. Beta < 1.0 means it is less sensitive to market swings. "
            "Negative beta means it tends to move opposite to the market.",
        ),
        (
            "52-Week Position",
            "Where the current price sits within its 52-week trading range, expressed as a "
            "percentage from 0% (at the 52-week low) to 100% (at the 52-week high). "
            "Above 70% = near recent highs; below 30% = near recent lows.",
        ),
        (
            "News Sentiment Score",
            "An aggregate score from -1.0 (very negative) to +1.0 (very positive) summarising "
            "the tone of recent news headlines. Scores near 0 are neutral. This is based on "
            "headline text only and does not reflect full article content or market impact.",
        ),
        (
            "Composite Risk Score (1-10)",
            "A weighted score combining volatility (40%), beta (25%), 52-week position (20%), "
            "and news sentiment (15%). A score of 1-3 = low risk, 4-6 = moderate, 7-10 = high. "
            "This is a statistical estimate based on historical data, not a prediction.",
        ),
        (
            "Forecast Scenarios (Bear / Base / Bull)",
            "Illustrative price ranges at future horizons generated by a lognormal model. "
            "Bear = 5th percentile (worse than 95% of simulated outcomes). "
            "Base = 50th percentile (median outcome). "
            "Bull = 95th percentile (better than 95% of simulated outcomes). "
            "Assumes 7% annual drift and constant volatility. These are NOT price targets or predictions.",
        ),
        (
            "Lognormal Model",
            "A mathematical model that assumes stock prices follow a log-normal distribution — "
            "i.e. the logarithm of the price change is normally distributed. Widely used in "
            "finance (e.g. Black-Scholes). Key limitation: assumes constant volatility and "
            "drift, which does not hold in practice.",
        ),
        (
            "Drift (7% annual assumption)",
            "The expected average annual return used in the forecast model. The 7% figure "
            "is a common long-run average for equities (US market historical average). "
            "It does not represent a prediction for any specific stock.",
        ),
    ]

    for term, definition in GLOSSARY:
        # Term label
        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 6, _safe(term), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Definition
        pdf.set_x(22)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(
            pdf.w - pdf.l_margin - pdf.r_margin - 4,
            5,
            _safe(definition),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(2)

    return bytes(pdf.output())
