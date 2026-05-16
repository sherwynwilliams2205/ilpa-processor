"""
PDF Extractor
Pulls raw text and numeric values from any ILPA-style PDF.
Returns a flat dict of labelled values keyed by canonical field name.
"""

import re
import pdfplumber


def extract(pdf_path: str) -> dict:
    """Return full text + parsed numeric fields from the PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    full_text = "\n".join(pages)
    numbers   = _parse_numbers(full_text)
    return {"text": full_text, "numbers": numbers, "pages": pages}


# ── number parser ────────────────────────────────────────────────────────────

def _clean(val: str):
    """Convert a string like '($1,234,567)' or '$1,234,567' to a float."""
    if not val:
        return None
    s = val.strip().replace(",", "").replace("$", "").replace(" ", "")
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
        return -v if negative else v
    except ValueError:
        return None


def _parse_numbers(text: str) -> dict:
    """
    Walk through the text line by line.
    For each line that matches a known label, pull the first 1-3 numbers
    found on that line as (QTD, YTD, SI).
    """
    NUMBER_RE = re.compile(
        r"\(?\$?[\d,]+\.?\d*\)?"          # matches $1,234 or (1,234) or 1,234
    )

    LABEL_MAP = {
        # NAV section
        "beginning nav":                  "beginning_nav",
        "opening balance":                "beginning_nav",
        "contributions":                  "contributions",
        "distributions":                  "distributions",
        "total cash":                     "total_cash_flows",

        # Expenses
        "management fee":                 "management_fee",
        "partnership expenses":           "partnership_expenses",
        "interest expense":               "interest_expense",
        "other expenses":                 "other_expenses",
        "nondeductible":                  "nondeductible_expenses",
        "intangible drilling":            "intangible_drilling",
        "loan amortization":              "loan_amortization",
        "other deductions":               "other_deductions",
        "depletion":                      "depletion",

        # Revenues
        "interest income":                "interest_income",
        "interest\n":                     "interest_income",
        "dividends":                      "dividend_income",
        "other income":                   "other_income",

        # Capital gains
        "net long term capital":          "realized_gain_lt",
        "net short term capital":         "realized_gain_st",
        "net section 1231":               "net_s1231",
        "realized gain":                  "realized_gain",
        "change in unrealized":           "unrealized_gain",
        "other increase":                 "other_increase",

        # Carry
        "accrued incentive":              "carry_start",
        "incentive allocation - paid":    "carry_paid",
        "incentive allocation - periodic":"carry_periodic",
        "incentive allocation - ending":  "carry_ending",

        # Commitment
        "total commitment":               "total_commitment",
        "capital commitment":             "total_commitment",
        "beginning unfunded":             "beginning_unfunded",
        "remaining commitment":           "remaining_commitment",
        "less contributions":             "less_contributions",
        "recallable":                     "recallable_distributions",
        "ending unfunded":                "ending_unfunded",

        # NAV totals
        "ending nav - net":               "ending_nav_net",
        "ending nav - gross":             "ending_nav_gross",
        "closing balance":                "closing_balance",

        # Offsets
        "total offsets":                  "total_offsets",
        "monitoring fee offset":          "monitoring_fee_offset",
        "transaction":                    "transaction_fee_offset",

        # Placement
        "placement fee":                  "placement_fees",
    }

    result: dict[str, list] = {}

    for line in text.split("\n"):
        line_lower = line.lower().strip()
        if not line_lower:
            continue
        for label, key in LABEL_MAP.items():
            if label in line_lower:
                nums = NUMBER_RE.findall(line)
                cleaned = [_clean(n) for n in nums if _clean(n) is not None]
                if cleaned:
                    # Keep first match only (don't overwrite with later lines)
                    if key not in result:
                        result[key] = cleaned   # [QTD, YTD, SI] where available
                break

    return result
