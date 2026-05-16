# ILPA LP Section Population — Skill

## Overview
This skill covers populating the LP section of the ILPA Reporting Template (v1.1)
from quarterly capital account PDFs. Two fund formats are documented:
- **Format A** — Standard ILPA (Veritas Capital, Kohlberg)
- **Format B** — Kelso KIA8 (tax basis, non-standard mapping)

Always copy the EMPTY_ILPA_Template.xlsx. Never work in the master.
File naming: `[FundName]_[Q#]_[YYYY]_ILPA_LP.xlsx`

---

## COLUMN MAPPING (both formats)
| Column | Period |
|---|---|
| E | QTD (Quarter to Date) |
| F | YTD (Year to Date) |
| G | Since Inception |

**When Q1: E = F (QTD = YTD). Enter both from the same PDF column.**

---

## FORMULA MAP — exact strings, no deviation (both formats)

```
R12  =E10-E11              Total Cash Flows
R16  =SUM(E17:E25)         Partnership Expenses Total
R38  =SUM(E28:E36)         Unapplied Offsets Recognised
R39  =E26                  Unapplied Offsets Applied
R40  =E37+E38-E39          Unapplied Offset Ending  ← MINUS, not plus
R41  =E14+E15+E16+E26      Net Mgmt Fees & Expenses
R47  =SUM(E41:E46)         Total Net Operating Income
R51  =E9+E12+E47+E48+E49+E50   Ending NAV Net
R55  =SUM(E52:E54)         Carry Ending Balance
R56  =E51-E55              Ending NAV Gross
R59  F59=E59, G59=E59      Commitment mirrors
R60  G60=E59               SI beg unfunded = commitment
R65  =SUM(E60:E64)         Ending Unfunded
R68  F68=E68, G68=E68      IA Earned mirrors
R69  F69=E69, G69=E69      Escrow mirrors
R73  =IFERROR(H73*E59/H59,0)   Fund of Funds guard
R77  =-(E14+E15)           B.1 Mgmt Fees (sign flip)
R79  =-E26                 B.1 Less Offsets (sign flip)
R81  =-E54                 B.1 Carry Change (sign flip)
R82  =SUM(E83:E89)         B.1 Portfolio Co Fees
R91  =SUM(E77:E82,E90)     B.1 Total Received by GP
```

Apply every formula to columns E, F, and G.

---

---

# FORMAT A — STANDARD ILPA
## Funds: Veritas Capital Fund V · Kohlberg Investors VIII-B

### Input rows (white cells — values from PDF)

| Row | Label | Sign | Notes |
|---|---|---|---|
| 9 | Beginning NAV | As stated | Prior quarter E51 |
| 10 | Contributions | Positive | |
| 11 | Distributions | **Positive** | Template instruction |
| 14 | Management Fees | **Negative** | |
| 15 | Mgmt Fee Rebate | Usually 0 | |
| 17–24 | Expense sub-rows | Negative | Enter detail per template |
| 25 | Other+ | Negative | |
| 26 | Total Offsets Applied | **Positive** | |
| 28–36 | Offset sub-categories | Positive | Feed R38 formula |
| 37 | Unapplied Offset Beg | 0 unless carry-fwd | |
| 43 | Interest Income | Positive | |
| 44 | Dividend Income | Positive | |
| 45 | Interest Expense | **Negative** | |
| 46 | Other Income | As signed | |
| 48 | Placement Fees | Negative | |
| 49 | Realized Gain/Loss | As signed | |
| 50 | Change in Unrealized | As signed | |
| 52 | Carry Starting Balance | Negative (LP owes GP) | |
| 53 | Carry Paid During Period | As signed | |
| 54 | Carry Periodic Change | As signed | |
| 59 | Total Commitment (E col) | Positive | F/G are formulas |
| 60 | Beginning Unfunded E/F | As stated | G60=formula |
| 61 | Less Contributions | Negative | |
| 62 | Plus Recallable Distrib | Positive | |
| 63 | Less Expired/Released | Negative | |
| 68 | IA Earned (E col) | **Positive** | A.3 instruction |

### Format A — Sign conventions
- Mgmt fees: **NEGATIVE** in A.1, **POSITIVE** (auto-formula) in B.1
- Distributions: **POSITIVE** in R11
- Offsets: **POSITIVE** in R26 and R28–36
- B.1 rows 77, 79, 81: formula-driven — never enter manually

### Format A — Verification checks (all must pass)
1. E51 = PDF stated ending NAV QTD
2. F51 = PDF stated ending NAV YTD
3. G51 = PDF stated ending NAV SI
4. E56 = PDF stated gross NAV
5. E55 = PDF stated carry ending balance
6. E41 = PDF net fees line
7. E16 = PDF partnership expenses (E16 = E25 if only one sub-row)
8. E40 = PDF unapplied offset balance
9. E38 = E26 when no unapplied carry-forward
10. E65 = PDF unfunded commitment QTD
11. G65 = PDF unfunded commitment SI
12. E59 = PDF total commitment
13. E9 = prior quarter E51 (continuity)
14. F14 = sum of all QTD mgmt fees year to date
15. G10 = PDF cumulative contributions SI

---

---

# FORMAT B — KELSO KIA8
## Fund: Kelso Investment Associates VIII, L.P.
## LP: Teacher Retirement System of Texas
## Commitment: $225,000,000 · Inception: June 21, 2007
## Basis: INCOME TAX BASIS — not GAAP

> ⚠️ **KELSO-ONLY RULES — DO NOT APPLY TO FORMAT A (VERITAS / KOHLBERG)**
> The three rules below override Format A for this fund only:
>
> | # | Rule | Format A | Format B (Kelso) |
> |---|---|---|---|
> | 1 | R11 Distributions | **POSITIVE** | **NEGATIVE** |
> | 2 | R46 G (Other Exp SI) | Positive (per template) | **NEGATIVE** |
> | 3 | R50 Other Inc/(Dec) | GAAP unrealised | **0** (not mapped) |
> | 4 | R62 Recallable SI | Positive (stated/derived) | **0** (not entered) |
>
> For Veritas and Kohlberg: R11 positive, R46 per standard sign,
> R50 = GAAP unrealised, R62 = recallable distributions as positive.

### Critical context
Kelso footnote every quarter: "Kelso did not track detailed expense
level information as requested in the ILPA Template."
Tax basis = no GAAP unrealised gain/loss. Row 50 = 0 always for Kelso.
No carried interest disclosed. Rows 52–54 always zero.

### Kelso KIA8 — Input rows and mapping

| Row | What goes here | QTD/YTD | SI column | Sign |
|---|---|---|---|---|
| 9 | Opening Balance | From PDF Opening Balance | 0 | As stated |
| 10 | Contributions | Contributions line | Cumulative contributions | Positive |
| 11 | Distributions | Distributions line | Cumulative distributions | **NEGATIVE** ← non-standard |
| 14 | Management Fee | $0 QTD/YTD (fee period ended) | ($33,827,374) | Negative |
| 17–24 | Sub-rows | All zero | All zero | — |
| 25 | Other+ (Partnership Exp only) | Partnership Expenses only | Partnership Expenses SI only | Negative |
| 26 | Offsets | 0 | 0 | — no offsets for KIA8 |
| 28–35 | Offset sub-categories | All zero | All zero | — |
| 36 | **Other Income/(Loss)** | From "Other Income/(Loss)" revenue line | SI Other Income/(Loss) | As signed (can be +/-) |
| 37 | Unapplied Offset Beg | 0 | 0 | — |
| 43 | Interest | Interest (Revenues) | SI Interest | Positive |
| 44 | Dividends | Dividends (Revenues) | SI Dividends | As signed (can be negative) |
| 45 | Interest Expense | Interest Expense (Expenses) | SI Interest Expense | Negative |
| 46 | Other Income/(Expense)+ | **0 QTD, 0 YTD** | **Other Expenses SI — NEGATIVE** ← Kelso only | SI = negative |
| 49 | Realized Gain/(Loss) | Net Long Term Capital Gain/(Loss) only | Net Short Term Capital Gain/(Loss) SI only | As signed |
| 50 | Other Increase/(Decrease) | From "Other Increase/(Decrease)" NAV line | SI amount | As signed — 0 if line absent. **Kelso only — Format A uses R50 for GAAP unrealised** |
| 52–54 | Carry | All zero | All zero | — |
| 59 | Total Commitment | $225,000,000 | formula =E59 | — |
| 60 | Beginning Unfunded | Remaining Commitment (PDF header) | formula =E59 | — |
| 61 | Less Contributions | 0 (no new calls usually) | Negative of G10 | Negative |
| 62 | Recallable Distributions | 0 | **0 — do not enter (Kelso only convention)** | — |
| 68 | IA Earned | 0 | 0 | — |

### Row 36 — the non-standard placement
Other Income/(Loss) from the PDF Revenues section goes into **Row 36**
(the Offset Roll section), NOT Row 46. This is the established convention
from the uploaded Q2 2021 reference file. Row 36 feeds R38 (=SUM(E28:E36))
which feeds R40 (unapplied balance only) — it does NOT flow through to R47
or R51. This means Other Income/(Loss) does not affect the computed NAV.

### Row 46 G column
G46 = Other Expenses SI entered as **NEGATIVE**.
Source: "Other Expenses" line from the PDF Expenses section, SI column.
E46 = 0, F46 = 0. Only the G column has a value.

### Row 11 — distributions sign
Distributions are entered as **NEGATIVE** for KIA8.
The formula R12 = E10 - E11 therefore adds them back positively.
This is non-standard vs Format A (where distributions are positive).
Follow this convention for all KIA8 quarters without exception.

### Row 50 — Other Increase/(Decrease)
Present from Q3 2021 onwards in the PDF NAV reconciliation section.
Enter QTD, YTD and SI exactly as stated (usually negative).
If the line does not appear in the PDF, leave R50 = 0.

### Row 62 — Recallable Distributions
**Do not enter.** Leave G62 = 0.
The commitment reconciliation (G65) will not match the stated
remaining commitment as a result. This is expected and accepted.

### Kelso KIA8 — Since Inception (G column) special items

Items in R46 G:
- Other Expenses SI — **NEGATIVE** (cost convention)

Items NOT mapped (Kelso limitation — absent from all SI columns):
- Nondeductible Expenses
- Intangible Drilling Costs
- Loan Amortization Fees
- Other Deductions
- Transfer of Interest
- Royalties
- First Closing Reallocation Interest
- Ordinary Business Income/(Loss)
- Net Section 1231 Gain/(Loss)

### Kelso KIA8 — Mandatory checks (replaces standard list)
1. E9 = prior quarter E51 computed value (continuity check)
2. E65 = Remaining Commitment stated in PDF header
3. F65 = same as E65
4. G10 = PDF contributions SI column (cumulative, never decreases)
5. G11 = PDF distributions SI as negative (never positive)
6. E59 = $225,000,000 (never changes)
7. E16 = E25 (since rows 17–24 are always zero)
8. E36 = Other Income/(Loss) QTD from PDF Revenue section
9. G46 = Other Expenses SI as negative from PDF Expenses section
10. Depletion Costs SI footnote = ($132,187) — verify each quarter

**Do NOT run the standard E51 reconciliation check.**
E51 will not match the PDF closing balance due to unmapped items.
This is expected and consistent with the reference convention file.

### Fixed SI values — never change across any Kelso quarter
| Item | Value | Source |
|---|---|---|
| Depletion Costs SI | ($132,187) | Stated in PDF footnote row |
| Recallable Distributions G62 | **0** | Not entered — Kelso convention (Format A = positive stated value) |
| Other Increase/(Decrease) R50 | **0** | Not mapped for Kelso (Format A uses R50 for GAAP unrealised) |
| Management Fee SI | ($33,827,374) | Stated in PDF SI column |

---

## PROCESS ORDER (both formats)

1. Read full PDF before entering any value
2. Confirm QTD / YTD / SI column positions
3. Identify fund format (A = standard, B = Kelso)
4. Copy master template, name correctly
5. Set B3 = fund name, P2–P5 = period dates
6. Enter all input rows top to bottom
7. Apply all formula cells
8. Run mandatory verification checks
9. Confirm zero formula errors
10. Deliver with check results stated

---

## DOUBLE-COUNT RULES (both formats)

1. R16 is a formula — enter expenses in R17–R25 only, never in R16
2. R26 (offsets applied) and R28–R36 (sub-categories) are both inputs
   with different purposes — do not assume they equal each other
3. A.3 R68 (IA Earned) is a separate disclosure of R53 (carry paid)
   — never add them together
4. B.1 rows 77, 79, 81 are auto-formulas — entering values there
   double-counts with A.1
5. Kelso: R36 (Other Income) does not flow to R47 or R51
   — it only affects R40 (unapplied balance)

---

## REFERENCE FILES
- `The_Veritas_Capital_Fund_V__LP_Q4.xlsx` — Format A formula reference
- `Kelso_KIA8_Q4_2024_ILPA_LP.xlsx` — Format B convention reference (user's version)
- `EMPTY_ILPA_Template.xlsx` — blank template for copying
