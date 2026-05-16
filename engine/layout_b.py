"""
Layout B — Income Tax Basis ILPA
Convention fund: Kelso Investment Associates VIII, L.P.

Key overrides vs Layout A:
  Row 11  Distributions: NEGATIVE
  Row 25  Other+: Partnership Expenses line only
  Row 26  Offsets: always zero
  Row 36  Other Offset+: Other Income/(Loss) from Revenues
  Row 46  Other Income: QTD/YTD=0, SI=Other Expenses SI as positive
  Row 49  QTD/YTD=Net LT Capital G/L; SI=Net ST Capital G/L
  Row 50  Q1-Q2 2021=zero; Q3 2021+=Other Increase/(Decrease)
  Rows 52-54 Carry: always zero
  E51     does NOT reconcile — expected
  Checks: modified 10 (not standard 15)
"""

from .extractor import extract

# Fixed constants for this fund
COMMITMENT         = 225_000_000
REMAINING          = 11_648_638
RECALLABLE_SI      = 132_229_801
MGMT_FEE_SI        = -33_827_374


def build_data(pdf_path: str, quarter: str = "") -> dict:
    """
    Return {row_number: {"E": qtd, "F": ytd, "G": si}}
    quarter format: "Q1_2021", "Q2_2021", "Q3_2021" etc.
    Used to determine Row 50 behaviour.
    """
    raw = extract(pdf_path)
    n   = raw["numbers"]

    def get(key, col):
        vals = n.get(key, [])
        return vals[col] if col < len(vals) else 0

    # Determine if Row 50 should use Other Increase/(Decrease)
    use_other_increase = quarter not in ("Q1_2021", "Q2_2021", "")

    rows = {}

    # Row 9 — Beginning NAV ("Opening Balance" in Kelso PDFs)
    rows[9] = {"E": get("beginning_nav", 0),
               "F": get("beginning_nav", 1),
               "G": get("beginning_nav", 2)}

    # Row 10 — Contributions (positive)
    rows[10] = {"E": get("contributions", 0),
                "F": get("contributions", 1),
                "G": get("contributions", 2)}

    # Row 11 — Distributions ← NEGATIVE for Layout B
    rows[11] = {"E": -abs(get("distributions", 0)) if get("distributions", 0) else 0,
                "F": -abs(get("distributions", 1)) if get("distributions", 1) else 0,
                "G": -abs(get("distributions", 2)) if get("distributions", 2) else 0}

    # Row 14 — Management Fee (negative; QTD/YTD=0; SI=cumulative)
    rows[14] = {"E": 0,
                "F": 0,
                "G": MGMT_FEE_SI}

    # Row 15 — Mgmt Fee Rebate
    rows[15] = {"E": 0, "F": 0, "G": 0}

    # Rows 17-24 — all zero (Kelso limitation)
    for r in range(17, 25):
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # Row 25 — Partnership Expenses line only (negative)
    rows[25] = {"E": -abs(get("partnership_expenses", 0)) if get("partnership_expenses", 0) else 0,
                "F": -abs(get("partnership_expenses", 1)) if get("partnership_expenses", 1) else 0,
                "G": -abs(get("partnership_expenses", 2)) if get("partnership_expenses", 2) else 0}

    # Row 26 — Offsets: always zero
    rows[26] = {"E": 0, "F": 0, "G": 0}

    # Rows 28-35 — all zero
    for r in range(28, 36):
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # Row 36 — Other Income/(Loss) from Revenues ← NON-STANDARD
    other_income_qtd = get("other_income", 0)
    other_income_ytd = get("other_income", 1)
    other_income_si  = get("other_income", 2)
    rows[36] = {"E": other_income_qtd,
                "F": other_income_ytd,
                "G": other_income_si}

    # Row 37 — Unapplied Offset Beginning: always zero
    rows[37] = {"E": 0, "F": 0, "G": 0}

    # Row 42 — Fee Waiver
    rows[42] = {"E": 0, "F": 0, "G": 0}

    # Row 43 — Interest Income (from Revenues section)
    rows[43] = {"E": get("interest_income", 0),
                "F": get("interest_income", 1),
                "G": get("interest_income", 2)}

    # Row 44 — Dividends (can be negative — reversals)
    rows[44] = {"E": get("dividend_income", 0),
                "F": get("dividend_income", 1),
                "G": get("dividend_income", 2)}

    # Row 45 — Interest Expense (negative)
    rows[45] = {"E": -abs(get("interest_expense", 0)) if get("interest_expense", 0) else 0,
                "F": -abs(get("interest_expense", 1)) if get("interest_expense", 1) else 0,
                "G": -abs(get("interest_expense", 2)) if get("interest_expense", 2) else 0}

    # Row 46 — Other Income: QTD/YTD=0; SI=Other Expenses SI as NEGATIVE (Kelso convention)
    other_exp_si = -abs(get("other_expenses", 2)) if get("other_expenses", 2) else 0
    rows[46] = {"E": 0, "F": 0, "G": other_exp_si}

    # Row 48 — Placement Fees: zero for Kelso
    rows[48] = {"E": 0, "F": 0, "G": 0}

    # Row 49 — Realized G/L ← NON-STANDARD
    # QTD/YTD = Net LT Capital G/L; SI = Net ST Capital G/L
    rows[49] = {"E": get("realized_gain_lt", 0),
                "F": get("realized_gain_lt", 1),
                "G": get("realized_gain_st", 2)}

    # Row 50 — ← NON-STANDARD
    # Q1-Q2 2021: zero
    # Q3 2021+: Other Increase/(Decrease) from NAV reconciliation
    if use_other_increase:
        rows[50] = {"E": get("other_increase", 0),
                    "F": get("other_increase", 1),
                    "G": get("other_increase", 2)}
    else:
        rows[50] = {"E": 0, "F": 0, "G": 0}

    # Rows 52-54 — Carry: always zero
    rows[52] = {"E": 0, "F": 0, "G": 0}
    rows[53] = {"E": 0, "F": 0, "G": 0}
    rows[54] = {"E": 0, "F": 0, "G": 0}

    # Row 59 — Commitment (fixed)
    rows[59] = {"E": COMMITMENT, "F": None, "G": None}

    # Row 60 — Beginning Unfunded (fixed); G = formula =E59
    rows[60] = {"E": REMAINING, "F": REMAINING, "G": None}

    # Row 61 — Less Contributions SI (negative of G10)
    contrib_si = get("contributions", 2)
    rows[61] = {"E": 0, "F": 0, "G": -abs(contrib_si) if contrib_si else 0}

    # Row 62 — Recallable Distributions: 0 — Kelso convention, do not enter
    # (G65 will not reconcile as a result — expected and accepted per skill.md)
    rows[62] = {"E": 0, "F": 0, "G": 0}

    rows[63] = {"E": 0, "F": 0, "G": 0}
    rows[64] = {"E": 0, "F": 0, "G": 0}

    # Row 68 — IA Earned: zero (no carry)
    rows[68] = {"E": 0, "F": None, "G": 0}
    rows[69] = {"E": 0, "F": None, "G": None}
    for r in [70, 71, 72]:
        rows[r] = {"E": 0, "F": 0, "G": 0}

    # B.1 — all zeros (no fees)
    rows[78] = {"E": 0, "F": 0, "G": 0}
    rows[80] = {"E": 0, "F": 0, "G": 0}
    for r in range(83, 90):
        rows[r] = {"E": 0, "F": 0, "G": 0}
    rows[90] = {"E": 0, "F": 0, "G": 0}

    return rows


CHECKS = [
    {"id": 1,  "label": "E9 = prior quarter E51 (continuity)",  "cell": "E9",  "expected": "prior_e51",    "fixed": None},
    {"id": 2,  "label": "E65 = $11,648,638 (ending unfunded)",  "cell": "E65", "expected": "fixed",         "fixed": 11_648_638},
    {"id": 3,  "label": "G65 = $11,648,638 (SI unfunded)",      "cell": "G65", "expected": "fixed",         "fixed": 11_648_638},
    {"id": 4,  "label": "G10 = cumulative contributions SI",    "cell": "G10", "expected": "pdf_si_contrib", "fixed": None},
    {"id": 5,  "label": "G11 = cumulative distributions SI (−)","cell": "G11", "expected": "pdf_si_distrib", "fixed": None},
    {"id": 6,  "label": "E59 = $225,000,000 (commitment)",      "cell": "E59", "expected": "fixed",         "fixed": 225_000_000},
    {"id": 7,  "label": "E36 = Other Income/(Loss) QTD",         "cell": "E36", "expected": "pdf_other_income", "fixed": None},
    {"id": 8,  "label": "G46 = Other Expenses SI (negative)",   "cell": "G46", "expected": "pdf_other_exp_si", "fixed": None},
    {"id": 9,  "label": "E16 = E25 (rows 17-24 all zero)",      "cell": "E16", "expected": "equals_e25",    "fixed": None},
    {"id": 10, "label": "Depletion SI = -$132,187 (footnote)",  "cell": "footnote", "expected": "fixed",    "fixed": -132_187},
]

E51_RECONCILES = False
