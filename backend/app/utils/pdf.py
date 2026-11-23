import re


def build_brief_pdf(ticker: str, company_name: str, brief_text: str, fetched_at: str) -> bytes:
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
        return (
            text
            .replace("—", "-")
            .replace("–", "-")
            .replace("‘", "'")
            .replace("’", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("•", "-")
            .replace("±", "+/-")
            .encode("latin-1", errors="replace")
            .decode("latin-1")
        )

    BLUE = (26, 35, 126)
    LIGHT_BLUE = (230, 235, 255)
    DARK = (30, 30, 30)
    GREY = (120, 120, 120)

    pdf = FPDF()
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

    # Body — walk line by line
    for raw in brief_text.splitlines():
        stripped = raw.strip()
        cleaned = _clean(raw)

        if not cleaned:
            pdf.ln(2)
            continue

        # Section heading (## or ###)
        if re.match(r"^#{1,6}\s", raw):
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
            # strip the leading marker
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
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", stripped, count=1)
            rest = re.sub(r"^\*\*.*?\*\*:?\s*", "", stripped)
            rest = _clean(rest)
            label = re.search(r"\*\*(.*?)\*\*", stripped)
            pdf.set_x(18)
            if label:
                # print label in bold, rest in regular
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

    # Footer
    pdf.set_y(-16)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY)
    pdf.cell(
        0, 6,
        "Educational only - not financial advice. Data sourced from Yahoo Finance via yfinance.",
        align="C",
    )

    return bytes(pdf.output())
