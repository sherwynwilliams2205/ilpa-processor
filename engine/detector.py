"""
Layout Detector
Reads extracted PDF text and routes to Layout A or Layout B.
Returns: layout ("A" | "B" | "UNKNOWN"), fund_name, lp_name, confidence score.
"""

LAYOUT_B_SIGNALS = [
    "income tax basis",
    "tax basis",
    "kelso investment associates",
    "did not track detailed expense",
    "net long term capital gain",
    "net short term capital gain",
    "ordinary business income",
    "intangible drilling",
    "depletion",
    "net section 1231",
    "opening balance",       # Kelso uses "Opening Balance" not "Beginning NAV"
    "remaining commitment",
]

LAYOUT_A_SIGNALS = [
    "accrued incentive allocation",
    "monitoring fee",
    "transaction fee",
    "change in unrealized",
    "ending nav",
    "beginning nav",
    "unapplied offset",
    "partnership expenses",
    "management fee rebate",
]

FUND_NAMES = {
    "A": [
        "veritas capital",
        "veritas fund",
    ],
    "B": [
        "kelso investment associates",
        "kelso investment associates viii",
    ],
}


def detect(text: str) -> dict:
    t = text.lower()

    # Score each layout
    score_b = sum(1 for kw in LAYOUT_B_SIGNALS if kw in t)
    score_a = sum(1 for kw in LAYOUT_A_SIGNALS if kw in t)

    # Determine layout
    if score_b >= 2:
        layout = "B"
        confidence = min(100, score_b * 15)
    elif score_a >= 2:
        layout = "A"
        confidence = min(100, score_a * 12)
    else:
        layout = "UNKNOWN"
        confidence = 0

    # Extract fund name (first line that looks like a fund name)
    fund_name = _extract_fund_name(text)
    lp_name   = _extract_lp_name(text)

    return {
        "layout":     layout,
        "confidence": confidence,
        "fund_name":  fund_name,
        "lp_name":    lp_name,
        "score_a":    score_a,
        "score_b":    score_b,
    }


def _extract_fund_name(text: str) -> str:
    keywords = ["fund", "associates", "partners", "capital", "investment"]
    for line in text.split("\n"):
        line = line.strip()
        if any(k in line.lower() for k in keywords) and len(line) > 10:
            return line[:80]
    return "Unknown Fund"


def _extract_lp_name(text: str) -> str:
    triggers = ["for:", "investor:", "lp:", "limited partner:"]
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if any(t in line.lower() for t in triggers):
            # Name is often on the same line or next line
            candidate = line.split(":")[-1].strip()
            if len(candidate) > 5:
                return candidate[:100]
            if i + 1 < len(lines):
                return lines[i + 1].strip()[:100]
    return "Unknown LP"
