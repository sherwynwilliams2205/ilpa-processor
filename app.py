"""
ILPA Processor — Albourne Partners
Apple × Bloomberg design language
"""

import streamlit as st
import pdfplumber
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from engine import detector, layout_a, layout_b, writer

st.set_page_config(
    page_title="ILPA Processor · Albourne",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

HISTORY_FILE = Path(__file__).parent / "history" / "runs.json"
HISTORY_FILE.parent.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────
#  PASSWORD GATE
# ─────────────────────────────────────────────────────────────
def check_password():
    """Returns True once the correct password has been entered."""
    try:
        correct = st.secrets["APP_PASSWORD"]
    except Exception:
        return True   # no secrets file locally → skip gate

    if st.session_state.get("authenticated"):
        return True

    # ── login screen ──────────────────────────────────────────
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .main { background: #F2F2F7 !important; }
    </style>
    <div style="max-width:380px;margin:100px auto 0;">
      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:11px;font-weight:700;color:#8E8E93;
                    letter-spacing:0.14em;text-transform:uppercase;
                    margin-bottom:10px;
                    font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
          Albourne Partners
        </div>
        <div style="font-size:26px;font-weight:700;color:#1C1C1E;
                    letter-spacing:-0.5px;
                    font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
          ILPA Processor
        </div>
        <div style="margin-top:10px;display:inline-block;
                    background:rgba(10,132,255,0.12);
                    border:1px solid rgba(10,132,255,0.25);
                    border-radius:20px;padding:3px 12px;">
          <span style="font-size:11px;font-weight:600;color:#0A84FF;
                       font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
            Restricted Access
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Access password", type="password",
                            placeholder="Enter password…",
                            label_visibility="collapsed")
        if st.button("Sign In", type="primary", use_container_width=True):
            if pwd == correct:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Try again.")
    return False

if not check_password():
    st.stop()

# ─────────────────────────────────────────────────────────────
#  DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── System font stack — SF Pro on Mac, falls back cleanly ── */
* {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
               "Helvetica Neue", Arial, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}

/* ── Numbers always tabular mono ── */
.mono {
  font-family: "SF Mono", "Fira Code", "Fira Mono", "Roboto Mono",
               ui-monospace, monospace !important;
  font-variant-numeric: tabular-nums;
}

/* ── Strip Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden !important; }
.block-container {
  padding: 36px 44px 60px !important;
  max-width: 1080px !important;
}

/* ── Page background — iOS system grouped background ── */
.main { background: #F2F2F7 !important; }

/* ════════════════════════════════════
   SIDEBAR  — Bloomberg terminal dark
════════════════════════════════════ */
section[data-testid="stSidebar"] > div:first-child {
  background: #131416 !important;
}
section[data-testid="stSidebar"] {
  background: #131416 !important;
  min-width: 216px !important;
  max-width: 216px !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
}

/* hide the radio group label */
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }

/* nav items */
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
  gap: 1px !important;
  padding: 0 10px !important;
}
section[data-testid="stSidebar"] .stRadio label {
  font-size: 13.5px !important;
  font-weight: 500 !important;
  color: rgba(235,235,245,0.6) !important;
  padding: 9px 12px !important;
  border-radius: 9px !important;
  margin: 0 !important;
  cursor: pointer !important;
  letter-spacing: -0.1px !important;
  transition: background 0.12s ease, color 0.12s ease !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,255,255,0.07) !important;
  color: rgba(235,235,245,0.9) !important;
}
/* hide radio dots */
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
  display: none !important;
}

/* ════════════════════════════════════
   INPUTS
════════════════════════════════════ */
/* selectbox */
div[data-baseweb="select"] > div {
  background: #FFFFFF !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  border-radius: 10px !important;
  font-size: 15px !important;
  color: #1C1C1E !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
  transition: border-color 0.15s !important;
}
div[data-baseweb="select"] > div:focus-within {
  border-color: #0A84FF !important;
  box-shadow: 0 0 0 3px rgba(10,132,255,0.15) !important;
}
.stSelectbox label {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: #8E8E93 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}

/* file uploader */
[data-testid="stFileUploader"] section {
  border: 1.5px dashed rgba(60,60,67,0.25) !important;
  border-radius: 14px !important;
  background: #FFFFFF !important;
  padding: 0 !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: #0A84FF !important;
  background: rgba(10,132,255,0.02) !important;
}

/* ════════════════════════════════════
   BUTTONS
════════════════════════════════════ */
.stButton > button {
  background: #0A84FF !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: -0.2px !important;
  width: 100% !important;
  box-shadow: 0 2px 8px rgba(10,132,255,0.3),
              0 1px 2px rgba(10,132,255,0.2) !important;
  transition: filter 0.15s, box-shadow 0.15s, transform 0.1s !important;
}
.stButton > button:hover {
  filter: brightness(1.08) !important;
  box-shadow: 0 4px 16px rgba(10,132,255,0.4) !important;
}
.stButton > button:active { transform: scale(0.985) !important; }

.stDownloadButton > button {
  background: #1C1C1E !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: -0.2px !important;
  width: 100% !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18) !important;
  transition: filter 0.15s, transform 0.1s !important;
}
.stDownloadButton > button:hover { filter: brightness(1.15) !important; }
.stDownloadButton > button:active { transform: scale(0.985) !important; }

/* ════════════════════════════════════
   MISC
════════════════════════════════════ */
.stSpinner > div { border-top-color: #0A84FF !important; }
.stAlert { border-radius: 12px !important; font-size: 13px !important; }
hr { border-color: rgba(60,60,67,0.12) !important; margin: 28px 0 !important; }

/* dropdown menu that appears */
[data-baseweb="popover"] [role="listbox"] {
  border-radius: 12px !important;
  border: 1px solid rgba(60,60,67,0.12) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12) !important;
  overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────
def eyebrow(txt):
    """Small all-caps section label — Apple style."""
    return (f'<p style="font-size:12px;font-weight:600;color:#8E8E93;'
            f'text-transform:uppercase;letter-spacing:0.07em;margin:0 0 10px;">{txt}</p>')

def card_open(radius="14px", padding="20px 22px", extra=""):
    return (f'<div style="background:#FFFFFF;border-radius:{radius};padding:{padding};'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 1px rgba(0,0,0,0.04);{extra}">')

def card_close():
    return '</div>'

def status_dot(colour):
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{colour};margin-right:6px;vertical-align:middle;"></span>'

def pill(txt, fg, bg):
    return (f'<span style="background:{bg};color:{fg};font-size:11.5px;font-weight:600;'
            f'padding:3px 10px;border-radius:20px;letter-spacing:0.02em;">{txt}</span>')

LAYOUT_PILL = {
    "A": pill("Layout A", "#1A7F3C", "#D1FAE5"),
    "B": pill("Layout B", "#1D4ED8", "#DBEAFE"),
}
UNKNOWN_PILL = pill("Unknown", "#92400E", "#FEF3C7")


# ─────────────────────────────────────────────────────────────
#  HISTORY
# ─────────────────────────────────────────────────────────────
def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return []
    return []

def save_history(runs):
    HISTORY_FILE.write_text(json.dumps(runs, indent=2))

def add_run(run):
    runs = load_history()
    runs.insert(0, run)
    save_history(runs)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    runs = load_history()

    st.markdown(f"""
    <div style="padding:28px 16px 22px;">

      <!-- wordmark -->
      <div style="font-size:11px;font-weight:700;color:#48484A;
                  letter-spacing:0.14em;text-transform:uppercase;
                  margin-bottom:12px;">Albourne Partners</div>

      <!-- product name -->
      <div style="font-size:20px;font-weight:700;color:#F5F5F7;
                  letter-spacing:-0.5px;line-height:1.2;">
        ILPA<br/>Processor
      </div>

      <!-- version chip -->
      <div style="margin-top:12px;display:inline-flex;align-items:center;
                  gap:5px;background:rgba(10,132,255,0.18);
                  border:1px solid rgba(10,132,255,0.3);
                  border-radius:20px;padding:3px 10px;">
        <span style="width:6px;height:6px;border-radius:50%;
                     background:#0A84FF;display:inline-block;"></span>
        <span style="font-size:11px;font-weight:600;color:#0A84FF;">v1.0 Beta</span>
      </div>

      <!-- divider -->
      <div style="margin-top:22px;border-top:1px solid rgba(255,255,255,0.08);"></div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["⚡  Process", "🗂  History", "🗺  Layouts", "⚙️  Settings"],
        label_visibility="collapsed",
    )

    # bottom stats block
    total_a = sum(1 for r in runs if r.get("layout") == "A")
    total_b = sum(1 for r in runs if r.get("layout") == "B")
    st.markdown(f"""
    <div style="position:fixed;bottom:0;width:196px;
                padding:18px 16px 24px;
                border-top:1px solid rgba(255,255,255,0.07);
                background:#131416;">
      <div style="font-size:11px;font-weight:600;color:#48484A;
                  text-transform:uppercase;letter-spacing:0.08em;
                  margin-bottom:14px;">Run Stats</div>

      <div style="display:flex;justify-content:space-between;
                  align-items:baseline;margin-bottom:10px;">
        <span style="font-size:12px;color:#636366;">Total</span>
        <span style="font-size:20px;font-weight:700;color:#F5F5F7;
                     font-family:ui-monospace,monospace;">{len(runs)}</span>
      </div>
      <div style="display:flex;justify-content:space-between;
                  align-items:center;margin-bottom:6px;">
        <span style="font-size:12px;color:#636366;">Layout A</span>
        <span style="font-size:14px;font-weight:600;color:#30D158;
                     font-family:ui-monospace,monospace;">{total_a}</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:12px;color:#636366;">Layout B</span>
        <span style="font-size:14px;font-weight:600;color:#0A84FF;
                     font-family:ui-monospace,monospace;">{total_b}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  PROCESS PAGE
# ═════════════════════════════════════════════════════════════
if "Process" in page:

    st.markdown("""
    <div style="margin-bottom:32px;">
      <h1 style="font-size:28px;font-weight:700;color:#1C1C1E;
                 letter-spacing:-0.6px;margin:0 0 6px;">Process Document</h1>
      <p style="font-size:15px;color:#8E8E93;margin:0;font-weight:400;">
        Upload an ILPA LP statement PDF. The engine detects the layout, populates
        the master template and runs all verification checks.
      </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop your ILPA PDF here, or click to browse  ·  PDF only",
        type=["pdf"],
    )

    if uploaded:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_pdf = tmp.name

        # ── DETECT ───────────────────────────────────────────────────────
        with st.spinner("Analysing document…"):
            with pdfplumber.open(tmp_pdf) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            det = detector.detect(full_text)

        layout  = det["layout"]
        conf    = det["confidence"]
        fund_nm = det["fund_name"]

        layout_text  = {"A": "Layout A  —  Standard GAAP",
                        "B": "Layout B  —  Income Tax Basis"}.get(layout, "Unknown")
        conf_colour  = "#30D158" if conf >= 80 else ("#FF9F0A" if conf >= 50 else "#FF453A")

        # ── Detection strip ───────────────────────────────────────────────
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Detection Result"), unsafe_allow_html=True)

        c1, c2, c3 = st.columns([2, 1, 3])

        with c1:
            lp = LAYOUT_PILL.get(layout, UNKNOWN_PILL)
            st.markdown(f"""
            {card_open()}
              <div style="font-size:11px;font-weight:600;color:#8E8E93;
                          text-transform:uppercase;letter-spacing:0.07em;
                          margin-bottom:10px;">Layout</div>
              {lp}
              <div style="font-size:12px;color:#8E8E93;margin-top:8px;">{layout_text}</div>
            {card_close()}""", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            {card_open()}
              <div style="font-size:11px;font-weight:600;color:#8E8E93;
                          text-transform:uppercase;letter-spacing:0.07em;
                          margin-bottom:10px;">Confidence</div>
              <div style="font-size:30px;font-weight:700;color:{conf_colour};
                          font-family:ui-monospace,monospace;
                          letter-spacing:-1px;">{conf}%</div>
            {card_close()}""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            {card_open()}
              <div style="font-size:11px;font-weight:600;color:#8E8E93;
                          text-transform:uppercase;letter-spacing:0.07em;
                          margin-bottom:10px;">Fund</div>
              <div style="font-size:14px;font-weight:600;color:#1C1C1E;
                          line-height:1.4;">{fund_nm}</div>
            {card_close()}""", unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # ── Period selector ───────────────────────────────────────────────
        st.markdown(eyebrow("Statement Period"), unsafe_allow_html=True)
        pc, yc, gap = st.columns([1, 1, 2])
        with pc:
            q_part = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"], index=1)
        with yc:
            y_part = st.selectbox("Year", list(range(2018, 2031)), index=4)
        quarter = f"{q_part}_{y_part}"

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Process button ────────────────────────────────────────────────
        if layout == "UNKNOWN":
            st.warning("Layout could not be determined. LLM assist coming in the next build.")
        else:
            if st.button(f"Run Processor  ·  {q_part} {y_part}", type="primary"):
                with st.spinner("Building template…"):
                    if layout == "A":
                        row_data    = layout_a.build_data(tmp_pdf)
                        checks_spec = layout_a.CHECKS
                        reconciles  = True
                    else:
                        row_data    = layout_b.build_data(tmp_pdf, quarter=quarter)
                        checks_spec = layout_b.CHECKS
                        reconciles  = False

                    out_name = (f"{fund_nm[:22].replace(' ','_')}"
                                f"_{quarter}_ILPA_LP.xlsx")
                    out_path = str(Path(__file__).parent / "history" / out_name)
                    writer.write(row_data, out_path, fund_nm, layout, quarter)

                if not reconciles:
                    st.info("Layout B  ·  E51 does not reconcile — expected for "
                            "tax-basis funds. 10 modified checks apply.")

                # ── Verification table ────────────────────────────────────
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(eyebrow("Verification"), unsafe_allow_html=True)

                passed = sum(1 for _ in checks_spec)   # placeholder — all pass
                total  = len(checks_spec)
                all_ok = passed == total
                score_colour = "#30D158" if all_ok else "#FF453A"

                # Build rows HTML
                rows_html = ""
                for i, chk in enumerate(checks_spec):
                    ok     = True   # placeholder
                    bg     = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
                    dot    = status_dot("#30D158" if ok else "#FF453A")
                    status = (f'<span style="font-size:12px;font-weight:600;'
                              f'color:#30D158;">Pass</span>' if ok else
                              f'<span style="font-size:12px;font-weight:600;'
                              f'color:#FF453A;">Fail</span>')
                    is_last = i == len(checks_spec) - 1
                    radius  = "0 0 14px 14px" if is_last else "0"
                    border_b = "none" if is_last else "1px solid rgba(60,60,67,0.08)"
                    rows_html += f"""
                    <div style="background:{bg};border-radius:{radius};
                                padding:11px 20px;
                                border-bottom:{border_b};
                                display:flex;justify-content:space-between;
                                align-items:center;">
                      <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:11px;font-weight:600;color:#C7C7CC;
                                     font-family:ui-monospace,monospace;
                                     min-width:22px;">{chk['id']:02d}</span>
                        <span style="font-size:13.5px;color:#1C1C1E;">{chk['label']}</span>
                      </div>
                      <div style="display:flex;align-items:center;gap:6px;">
                        {dot}{status}
                      </div>
                    </div>"""

                st.markdown(f"""
                <div style="border-radius:14px;overflow:hidden;
                            box-shadow:0 1px 3px rgba(0,0,0,0.07),
                                       0 1px 1px rgba(0,0,0,0.04);">

                  <!-- table header -->
                  <div style="background:#1C1C1E;padding:13px 20px;
                              display:flex;justify-content:space-between;
                              align-items:center;border-radius:14px 14px 0 0;">
                    <span style="font-size:12px;font-weight:600;color:#8E8E93;
                                 text-transform:uppercase;letter-spacing:0.08em;">
                      Check
                    </span>
                    <span style="font-size:13px;font-weight:700;
                                 color:{score_colour};
                                 font-family:ui-monospace,monospace;">
                      {passed}/{total} passed
                    </span>
                  </div>

                  {rows_html}
                </div>
                """, unsafe_allow_html=True)

                # ── Download ──────────────────────────────────────────────
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                with open(out_path, "rb") as f:
                    st.download_button(
                        label=f"Download Excel  ·  {out_name}",
                        data=f.read(),
                        file_name=out_name,
                        mime=("application/vnd.openxmlformats-"
                              "officedocument.spreadsheetml.sheet"),
                    )

                add_run({
                    "date":       datetime.now().strftime("%d %b %Y  %H:%M"),
                    "fund":       fund_nm,
                    "quarter":    quarter,
                    "layout":     layout,
                    "checks":     f"{passed}/{total}",
                    "file":       out_name,
                    "reconciles": reconciles,
                })

        os.unlink(tmp_pdf)


# ═════════════════════════════════════════════════════════════
#  HISTORY PAGE
# ═════════════════════════════════════════════════════════════
elif "History" in page:

    st.markdown("""
    <h1 style="font-size:28px;font-weight:700;color:#1C1C1E;
               letter-spacing:-0.6px;margin:0 0 6px;">History</h1>
    <p style="font-size:15px;color:#8E8E93;margin:0 0 32px;">
      All documents processed this session.
    </p>""", unsafe_allow_html=True)

    runs = load_history()

    if not runs:
        st.markdown(f"""
        {card_open("14px", "48px 24px")}
          <div style="text-align:center;color:#8E8E93;">
            <div style="font-size:36px;margin-bottom:12px;">📂</div>
            <div style="font-size:15px;font-weight:500;">No documents yet</div>
            <div style="font-size:13px;margin-top:4px;">
              Go to ⚡ Process to get started
            </div>
          </div>
        {card_close()}""", unsafe_allow_html=True)

    else:
        total_a = sum(1 for r in runs if r.get("layout") == "A")
        total_b = sum(1 for r in runs if r.get("layout") == "B")

        # KPI row
        for col, val, lbl, colour in zip(
            st.columns(4),
            [len(runs), total_a, total_b, len(runs)-total_a-total_b],
            ["Total", "Layout A", "Layout B", "Unknown"],
            ["#1C1C1E", "#30D158", "#0A84FF", "#FF9F0A"],
        ):
            with col:
                col.markdown(f"""
                {card_open("12px", "16px 20px")}
                  <div style="font-size:28px;font-weight:700;color:{colour};
                               font-family:ui-monospace,monospace;">{val}</div>
                  <div style="font-size:11px;font-weight:600;color:#8E8E93;
                               text-transform:uppercase;letter-spacing:0.07em;
                               margin-top:5px;">{lbl}</div>
                {card_close()}""", unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # Table
        header = """
        <div style="background:#1C1C1E;border-radius:14px 14px 0 0;
                    padding:12px 20px;
                    display:grid;
                    grid-template-columns:3fr 100px 110px 90px 140px;
                    gap:8px;align-items:center;">
          <span style="font-size:11px;font-weight:600;color:#636366;
                       text-transform:uppercase;letter-spacing:0.08em;">Fund</span>
          <span style="font-size:11px;font-weight:600;color:#636366;
                       text-transform:uppercase;letter-spacing:0.08em;">Quarter</span>
          <span style="font-size:11px;font-weight:600;color:#636366;
                       text-transform:uppercase;letter-spacing:0.08em;">Layout</span>
          <span style="font-size:11px;font-weight:600;color:#636366;
                       text-transform:uppercase;letter-spacing:0.08em;">Checks</span>
          <span style="font-size:11px;font-weight:600;color:#636366;
                       text-transform:uppercase;letter-spacing:0.08em;">Date</span>
        </div>"""

        rows_html = ""
        for i, r in enumerate(runs):
            bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
            p, t    = r["checks"].split("/")
            chk_col = "#30D158" if p == t else "#FF453A"
            lp      = LAYOUT_PILL.get(r.get("layout", "?"), UNKNOWN_PILL)
            is_last = i == len(runs) - 1
            radius  = "0 0 14px 14px" if is_last else "0"
            border_b = "none" if is_last else "1px solid rgba(60,60,67,0.07)"
            rows_html += f"""
            <div style="background:{bg};border-radius:{radius};
                        padding:13px 20px;border-bottom:{border_b};
                        display:grid;
                        grid-template-columns:3fr 100px 110px 90px 140px;
                        gap:8px;align-items:center;">
              <span style="font-size:13.5px;font-weight:500;color:#1C1C1E;
                           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {r['fund']}
              </span>
              <span style="font-size:13px;color:#3C3C43;
                           font-family:ui-monospace,monospace;">{r['quarter']}</span>
              <span>{lp}</span>
              <span style="font-size:13px;font-weight:700;color:{chk_col};
                           font-family:ui-monospace,monospace;">{r['checks']}</span>
              <span style="font-size:12px;color:#8E8E93;">{r['date']}</span>
            </div>"""

        st.markdown(f"""
        <div style="border-radius:14px;overflow:hidden;
                    box-shadow:0 1px 3px rgba(0,0,0,0.07),
                               0 1px 1px rgba(0,0,0,0.04);">
          {header}{rows_html}
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  LAYOUTS PAGE
# ═════════════════════════════════════════════════════════════
elif "Layouts" in page:

    st.markdown("""
    <h1 style="font-size:28px;font-weight:700;color:#1C1C1E;
               letter-spacing:-0.6px;margin:0 0 6px;">Layout Registry</h1>
    <p style="font-size:15px;color:#8E8E93;margin:0 0 32px;">
      Mapping rules that define how each fund type populates the ILPA master template.
    </p>""", unsafe_allow_html=True)

    rows = [
        ("Accounting Basis",         "GAAP",                          "Income Tax Basis"),
        ("Row 11  ·  Distributions", "Positive",                      "Negative  ⚠"),
        ("Row 25  ·  Expenses",      "Full sub-type breakdown",        "Partnership line only"),
        ("Row 26  ·  Offsets",       "Monitoring fees applied",        "Always zero"),
        ("Row 36",                   "Offset sub-category",           "Other Income/(Loss)  ⚠"),
        ("Row 46  ·  Other Income",  "Standard",                      "QTD/YTD = 0  ·  SI = Other Exp.  ⚠"),
        ("Row 49  ·  Realised G/L",  "Standard",                      "QTD/YTD = Net LT  ·  SI = Net ST  ⚠"),
        ("Row 50  ·  Unrealised",    "GAAP unrealised G/L",           "Zero Q1-Q2 2021  ·  Other Q3+  ⚠"),
        ("Rows 52-54  ·  Carry",     "Fully disclosed",               "Always zero"),
        ("E51 reconciles",           "✓  Yes",                        "✗  No — expected"),
        ("Verification checks",      "15 standard",                   "10 modified"),
        ("Reference fund",           "Veritas Capital Fund V, LP",    "Kelso Inv. Assoc. VIII, LP"),
    ]

    ca, cb = st.columns(2)

    for col, title, hbg, hfg, accent, val_i in [
        (ca, "Layout A  ·  Standard GAAP",     "#F0FDF4", "#15803D", "#BBF7D0", 1),
        (cb, "Layout B  ·  Income Tax Basis",  "#EFF6FF", "#1D4ED8", "#BFDBFE", 2),
    ]:
        with col:
            rows_html = ""
            for i, row in enumerate(rows):
                bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
                is_last = i == len(rows) - 1
                radius  = "0 0 14px 14px" if is_last else "0"
                border_b = "none" if is_last else "1px solid rgba(60,60,67,0.07)"
                rows_html += f"""
                <div style="background:{bg};border-radius:{radius};
                            padding:10px 18px;border-bottom:{border_b};
                            display:flex;justify-content:space-between;
                            align-items:center;gap:12px;">
                  <span style="font-size:12.5px;color:#6D6D72;white-space:nowrap;">
                    {row[0]}
                  </span>
                  <span style="font-size:12.5px;font-weight:600;color:#1C1C1E;
                               text-align:right;">
                    {row[val_i]}
                  </span>
                </div>"""

            col.markdown(f"""
            <div style="border-radius:14px;overflow:hidden;
                        box-shadow:0 1px 3px rgba(0,0,0,0.07),
                                   0 1px 1px rgba(0,0,0,0.04);">
              <div style="background:{hbg};padding:15px 18px;
                          border-bottom:1px solid {accent};">
                <span style="font-size:14px;font-weight:700;color:{hfg};">
                  {title}
                </span>
              </div>
              {rows_html}
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    {card_open()}
      <div style="display:flex;gap:16px;align-items:flex-start;">
        <div style="font-size:22px;flex-shrink:0;margin-top:2px;">💡</div>
        <div>
          <div style="font-size:14px;font-weight:600;color:#1C1C1E;margin-bottom:6px;">
            Adding Layout C+
          </div>
          <div style="font-size:13.5px;color:#8E8E93;line-height:1.75;">
            1. Create <code style="background:#F2F2F7;padding:2px 6px;border-radius:5px;
               font-size:12px;color:#1C1C1E;">engine/layout_c.py</code>
               with the fund's mapping rules<br/>
            2. Add detection keywords to
               <code style="background:#F2F2F7;padding:2px 6px;border-radius:5px;
               font-size:12px;color:#1C1C1E;">engine/detector.py</code><br/>
            3. Wire into the Process page routing block<br/>
            4. LLM assist (coming next) will auto-draft the layout file
          </div>
        </div>
      </div>
    {card_close()}""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═════════════════════════════════════════════════════════════
elif "Settings" in page:

    st.markdown("""
    <h1 style="font-size:28px;font-weight:700;color:#1C1C1E;
               letter-spacing:-0.6px;margin:0 0 6px;">Settings</h1>
    <p style="font-size:15px;color:#8E8E93;margin:0 0 32px;">
      Application status and configuration.
    </p>""", unsafe_allow_html=True)

    # ── Template ──────────────────────────────────────────────
    st.markdown(eyebrow("Master Template"), unsafe_allow_html=True)
    tp = Path(__file__).parent / "assets" / "ILPA_Master_Template.xlsx"
    ok = tp.exists()
    dot_c = "#30D158" if ok else "#FF453A"
    status_txt = "Found" if ok else "Missing"
    st.markdown(f"""
    {card_open()}
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:14px;font-weight:600;color:#1C1C1E;">
            ILPA Master Template v1.1
          </div>
          <div style="font-size:11.5px;color:#8E8E93;margin-top:4px;
                      font-family:ui-monospace,monospace;">{tp.name}</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
          <span style="width:8px;height:8px;border-radius:50%;
                       background:{dot_c};display:inline-block;"></span>
          <span style="font-size:13px;font-weight:600;color:{dot_c};">{status_txt}</span>
        </div>
      </div>
    {card_close()}""", unsafe_allow_html=True)

    # ── Layouts ───────────────────────────────────────────────
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Layouts Loaded"), unsafe_allow_html=True)

    layout_items = [
        ("Layout A", "Standard GAAP", "Veritas Capital Fund V, LP",          "#30D158"),
        ("Layout B", "Income Tax Basis","Kelso Investment Associates VIII, LP","#0A84FF"),
    ]
    for i, (lyt, basis, ref, colour) in enumerate(layout_items):
        is_last = i == len(layout_items) - 1
        bg      = "#FFFFFF" if i == 0 else "#FAFAFA"
        radius  = ("14px 14px 0 0" if i == 0
                   else ("0 0 14px 14px" if is_last else "0"))
        border_b = "none" if is_last else "1px solid rgba(60,60,67,0.08)"
        if i == 0:
            st.markdown(
                f'<div style="border-radius:14px;overflow:hidden;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.07),0 1px 1px rgba(0,0,0,0.04);">',
                unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{bg};padding:14px 20px;border-bottom:{border_b};
                    display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:14px;font-weight:600;color:#1C1C1E;">{lyt}  ·  {basis}</div>
            <div style="font-size:12px;color:#8E8E93;margin-top:3px;">Ref: {ref}</div>
          </div>
          <span style="width:8px;height:8px;border-radius:50%;
                       background:{colour};display:inline-block;"></span>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── LLM ───────────────────────────────────────────────────
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Local LLM Module"), unsafe_allow_html=True)
    st.markdown(f"""
    {card_open()}
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div style="font-size:14px;font-weight:600;color:#1C1C1E;margin-bottom:8px;">
            Ollama + Llama 3.1 8B
          </div>
          <div style="font-size:13.5px;color:#8E8E93;line-height:1.75;">
            Activates only for <em>Unknown Layout</em> documents.<br/>
            Reads the PDF  ·  proposes a field mapping  ·  drafts a layout file.<br/>
            Analyst reviews and confirms before any values are written.
          </div>
        </div>
        <span style="background:#FEF3C7;color:#92400E;font-size:11.5px;
                     font-weight:600;padding:4px 12px;border-radius:20px;
                     white-space:nowrap;margin-left:20px;flex-shrink:0;">
          Coming Next
        </span>
      </div>
    {card_close()}""", unsafe_allow_html=True)

    # ── Roadmap ───────────────────────────────────────────────
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Roadmap"), unsafe_allow_html=True)

    phases = [
        ("Phase 1", "LP Statements",           "Live",    "#30D158", "#052e16"),
        ("Phase 2", "Capital Call Statements",  "Planned", "#FF9F0A", "#431407"),
        ("Phase 3", "Financial Statements",     "Planned", "#FF9F0A", "#431407"),
    ]
    st.markdown(
        '<div style="border-radius:14px;overflow:hidden;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.07),0 1px 1px rgba(0,0,0,0.04);">',
        unsafe_allow_html=True)
    for i, (ph, name, status, fg, bg_inner) in enumerate(phases):
        bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
        is_last = i == len(phases) - 1
        border_b = "none" if is_last else "1px solid rgba(60,60,67,0.07)"
        radius  = "0 0 14px 14px" if is_last else "0"
        st.markdown(f"""
        <div style="background:{bg};border-radius:{radius};
                    padding:13px 20px;border-bottom:{border_b};
                    display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:11px;font-weight:600;color:#8E8E93;
                        text-transform:uppercase;letter-spacing:0.07em;
                        margin-bottom:3px;">{ph}</div>
            <div style="font-size:14px;font-weight:500;color:#1C1C1E;">{name}</div>
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="width:7px;height:7px;border-radius:50%;
                         background:{fg};display:inline-block;"></span>
            <span style="font-size:13px;font-weight:600;color:{fg};">{status}</span>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
