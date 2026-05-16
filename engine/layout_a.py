"""
Layout A — Standard GAAP ILPA
Convention fund: Veritas Capital Fund V, LP

Rules:
  - Row 11 Distributions: POSITIVE
  - Row 25 Other+: professional fees / misc operating
  - Row 26 Offsets: monitoring & transaction fees applied
  - Row 32 Monitoring Fee Offset sub-category
  - Row 36 Other Offset: zero
  - Row 46 Other Income: standard
  - Row 49 Realized G/L: standard
  - Row 50 Unrealised: GAAP unrealised G/L
  - Rows 52-54 Carry: fully disclosed
  - E51 reconciles: YES
  - Checks: standard 15
"""

from .extractor import extract


def build_data(pdf_path: str) -> dict:
    """
    Return a flat dict: {row_number: {"E": qtd, "F": ytd, "G": si}}
    Only INPUT rows. Formula rows are left untouched in the template.
    """
    raw = extract(pdf_path)
    n   = raw["numbers"]

    def get(key, col):
        """Pull column index 0=QTD, 1=YTD, 2=SI from parsed list."""
        vals = n.get(key, [])
        return vals[col] if col < len(vals) else 0

    rows = {}

    # Row 9 — Beginning NAV
    rows[9] = {"E": get("beginning_nav", 0),
               "F": get("beginning_nav", 1),
               "G": get("beginning_nav", 2)}

    # Row 10 — Contributions (positive)
    rows[10] = {"E": get("contributions", 0),
                "F": get("contributions", 1),
                "G": get("contributions", 2)}

    # Row 11 — Distributions (POSITIVE for Layout A)
    rows[11] = {"E": abs(get("distributions", 0)),
                "F": abs(get("distributions", 1)),
                "G": abs(get("distributions", 2))}

    # Row 14 — Management Fees (negative)
    rows[14] = {"E": -abs(get("management_fee", 0)),
                "F": -abs(get("management_fee", 1)),
                "G": -abs(get("management_fee", 2))}

    # Row 15 — Mgmt Fee Rebate
    rows[15] = {"E": 0, "F": 0, "G": 0}

    # Rows 17-24 — Partnership Expense sub-rows (zeroed unless data available)
    for r in range(17, 25):
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # Row 25 — Other+ (Professional Fees, Misc Operating)
    rows[25] = {"E": -abs(get("partnership_expenses", 0)) if get("partnership_expenses", 0) else 0,
                "F": -abs(get("partnership_expenses", 1)) if get("partnership_expenses", 1) else 0,
                "G": -abs(get("partnership_expenses", 2)) if get("partnership_expenses", 2) else 0}

    # Row 26 — Total Offsets Applied (positive)
    rows[26] = {"E": abs(get("total_offsets", 0)),
                "F": abs(get("total_offsets", 1)),
                "G": abs(get("total_offsets", 2))}

    # Rows 28-31, 33-35 — zero
    for r in [28, 29, 30, 31, 33, 34, 35, 36]:
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # Row 32 — Monitoring Fee Offset (source of offsets)
    rows[32] = {"E": abs(get("monitoring_fee_offset", 0)) or abs(get("total_offsets", 0)),
                "F": abs(get("monitoring_fee_offset", 1)) or abs(get("total_offsets", 1)),
                "G": abs(get("monitoring_fee_offset", 2)) or abs(get("total_offsets", 2))}

    # Row 37 — Unapplied Offset Beginning Balance
    rows[37] = {"E": 0, "F": 0, "G": 0}

    # Row 42 — Fee Waiver
    rows[42] = {"E": 0, "F": 0, "G": 0}

    # Row 43 — Interest Income
    rows[43] = {"E": get("interest_income", 0),
                "F": get("interest_income", 1),
                "G": get("interest_income", 2)}

    # Row 44 — Dividend Income
    rows[44] = {"E": get("dividend_income", 0),
                "F": get("dividend_income", 1),
                "G": get("dividend_income", 2)}

    # Row 45 — Interest Expense (negative)
    rows[45] = {"E": -abs(get("interest_expense", 0)) if get("interest_expense", 0) else 0,
                "F": -abs(get("interest_expense", 1)) if get("interest_expense", 1) else 0,
                "G": -abs(get("interest_expense", 2)) if get("interest_expense", 2) else 0}

    # Row 46 — Other Income
    rows[46] = {"E": 0, "F": 0, "G": 0}

    # Row 48 — Placement Fees (negative)
    rows[48] = {"E": -abs(get("placement_fees", 0)) if get("placement_fees", 0) else 0,
                "F": -abs(get("placement_fees", 1)) if get("placement_fees", 1) else 0,
                "G": -abs(get("placement_fees", 2)) if get("placement_fees", 2) else 0}

    # Row 49 — Realized Gain/Loss
    rows[49] = {"E": get("realized_gain", 0),
                "F": get("realized_gain", 1),
                "G": get("realized_gain", 2)}

    # Row 50 — Change in Unrealized
    rows[50] = {"E": get("unrealized_gain", 0),
                "F": get("unrealized_gain", 1),
                "G": get("unrealized_gain", 2)}

    # Rows 52-54 — Carry
    rows[52] = {"E": get("carry_start", 0),
                "F": get("carry_start", 1),
                "G": get("carry_start", 2)}
    rows[53] = {"E": get("carry_paid", 0),
                "F": get("carry_paid", 1),
                "G": get("carry_paid", 2)}
    rows[54] = {"E": get("carry_periodic", 0),
                "F": get("carry_periodic", 1),
                "G": get("carry_periodic", 2)}

    # Row 59 — Total Commitment
    rows[59] = {"E": get("total_commitment", 0), "F": None, "G": None}

    # Row 60 — Beginning Unfunded (G = formula =E59)
    rows[60] = {"E": get("beginning_unfunded", 0),
                "F": get("beginning_unfunded", 1),
                "G": None}

    # Rows 61-64 — Commitment sub-rows
    rows[61] = {"E": 0, "F": 0, "G": -abs(get("contributions", 2)) if get("contributions", 2) else 0}
    rows[62] = {"E": 0, "F": 0, "G": abs(get("recallable_distributions", 2)) if get("recallable_distributions", 2) else 0}
    rows[63] = {"E": 0, "F": 0, "G": 0}
    rows[64] = {"E": 0, "F": 0, "G": 0}

    # Row 68 — IA Earned (E=QTD; F=formula; G=SI if different)
    carry_paid_qtd = get("carry_paid", 0)
    carry_paid_si  = get("carry_paid", 2)
    rows[68] = {"E": abs(carry_paid_qtd),
                "F": None,   # formula =E68
                "G": abs(carry_paid_si) if abs(carry_paid_si) != abs(carry_paid_qtd) else None}

    # Row 69 — Escrow
    rows[69] = {"E": 0, "F": None, "G": None}

    # Rows 70-72
    for r in [70, 71, 72]:
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # B.1 input rows
    rows[78] = {"E": 0, "F": 0, "G": 0}
    rows[80] = {"E": 0, "F": 0, "G": 0}

    # Row 83-89 — Portfolio company fees (negative)
    for r in range(83, 90):
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # Row 87 — Monitoring fees (source of offsets)
    rows[87] = {"E": -abs(get("total_offsets", 0)) if get("total_offsets", 0) else 0,
                "F": -abs(get("total_offsets", 1)) if get("total_offsets", 1) else 0,
                "G": -abs(get("total_offsets", 2)) if get("total_offsets", 2) else 0}

    rows[90] = {"E": 0, "F": 0, "G": 0}

    return rows


CHECKS = [
    {"id": 1,  "label": "Ending NAV Net QTD",       "cell": "E51", "pdf_key": "ending_nav_net",   "col": 0},
    {"id": 2,  "label": "Ending NAV Net YTD",       "cell": "F51", "pdf_key": "ending_nav_net",   "col": 1},
    {"id": 3,  "label": "Ending NAV Net SI",        "cell": "G51", "pdf_key": "ending_nav_net",   "col": 2},
    {"id": 4,  "label": "Ending NAV Gross QTD",     "cell": "E56", "pdf_key": "ending_nav_gross", "col": 0},
    {"id": 5,  "label": "Carry Ending Balance QTD", "cell": "E55", "pdf_key": "carry_ending",     "col": 0},
    {"id": 6,  "label": "Total Net Op Income QTD",  "cell": "E47", "pdf_key": None,               "col": 0},
    {"id": 7,  "label": "Net Mgmt Fees QTD",        "cell": "E41", "pdf_key": None,               "col": 0},
    {"id": 8,  "label": "Pship Expenses QTD",       "cell": "E16", "pdf_key": "partnership_expenses", "col": 0},
    {"id": 9,  "label": "Unapplied Offset End",     "cell": "E40", "pdf_key": None,               "col": 0},
    {"id": 10, "label": "Offset Sub-cats = E26",    "cell": "E38", "pdf_key": "total_offsets",    "col": 0},
    {"id": 11, "label": "Ending Unfunded QTD",      "cell": "E65", "pdf_key": "ending_unfunded",  "col": 0},
    {"id": 12, "label": "Ending Unfunded SI",       "cell": "G65", "pdf_key": "ending_unfunded",  "col": 2},
    {"id": 13, "label": "Total Commitment",         "cell": "E59", "pdf_key": "total_commitment", "col": 0},
    {"id": 14, "label": "Beginning NAV QTD",        "cell": "E9",  "pdf_key": "beginning_nav",    "col": 0},
    {"id": 15, "label": "YTD Mgmt Fee",             "cell": "F14", "pdf_key": "management_fee",   "col": 1},
]
