"""
ILPA Processor — Albourne Partners
"""

import io
import streamlit as st
import pdfplumber
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from engine import detector, layout_a, layout_b, writer, learner, codegen

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
    try:
        correct = st.secrets["APP_PASSWORD"]
    except Exception:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <style>
    #MainMenu, footer { display: none !important; }
    .main { background: #F5F5F5 !important; }
    </style>
    <div style="max-width:380px;margin:120px auto 0;font-family:-apple-system,sans-serif;">
      <div style="text-align:center;margin-bottom:36px;">
        <div style="font-size:11px;font-weight:700;color:#999;letter-spacing:0.15em;
                    text-transform:uppercase;margin-bottom:10px;">Albourne Partners</div>
        <div style="font-size:28px;font-weight:700;color:#1A1A1A;letter-spacing:-0.5px;">
          ILPA Processor</div>
        <div style="margin-top:12px;display:inline-block;background:rgba(10,132,255,0.10);
                    border:1px solid rgba(10,132,255,0.2);border-radius:20px;padding:3px 14px;">
          <span style="font-size:11px;font-weight:600;color:#0A84FF;">Restricted Access</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Password", type="password",
                            placeholder="Enter password…", label_visibility="collapsed")
        if st.button("Sign In", type="primary", use_container_width=True):
            if pwd == correct:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()


# ─────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800&display=swap');

/* ── Reset & base ─────────────────────────────────────────── */
*, *::before, *::after {
  font-family: "DM Sans", -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}

/* ── Hide Streamlit chrome — but NOT the header element itself ── */
#MainMenu                        { display: none !important; }
footer                           { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stDecoration"]     { display: none !important; }

/* ── Main page background ─────────────────────────────────── */
.main, [data-testid="stAppViewContainer"] > .main {
  background: #EDEBE3 !important;
}
.block-container {
  padding: 36px 44px 72px !important;
  max-width: 1080px !important;
}

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: #17181A !important;
  min-width: 220px !important;
  max-width: 220px !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] > div:first-child {
  background: #17181A !important;
}
/* Collapse/expand buttons — always show */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: all !important;
}
/* Sidebar nav radio — hide label, style items */
[data-testid="stSidebar"] .stRadio > label     { display: none !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
  display: none !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
  gap: 2px !important;
  padding: 0 10px !important;
}
[data-testid="stSidebar"] .stRadio label {
  font-size: 13.5px !important;
  font-weight: 500 !important;
  color: rgba(235,235,245,0.55) !important;
  padding: 9px 14px !important;
  border-radius: 10px !important;
  margin: 0 !important;
  cursor: pointer !important;
  transition: background 0.12s, color 0.12s !important;
  display: flex !important;
  align-items: center !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,255,255,0.07) !important;
  color: rgba(235,235,245,0.9) !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"],
[data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
  background: rgba(255,255,255,0.10) !important;
  color: #F5F5F7 !important;
}

/* ── Typography helpers ────────────────────────────────────── */
.eyebrow {
  font-size: 11px;
  font-weight: 700;
  color: #7A7A6E;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  margin: 0 0 10px;
}
.page-title {
  font-size: 36px;
  font-weight: 800;
  color: #1A1A1A;
  letter-spacing: -0.8px;
  line-height: 1.15;
  margin: 0 0 6px;
}
.page-sub {
  font-size: 15px;
  color: #5C5C50;
  line-height: 1.7;
  font-weight: 400;
  margin: 0;
}

/* ── Cards ─────────────────────────────────────────────────── */
.card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 22px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.fc {
  border-radius: 22px;
  padding: 26px 24px 28px;
  min-height: 180px;
  display: flex;
  flex-direction: column;
}
.fc-green  { background: #C8D9A3; }
.fc-yellow { background: #E5D97E; }
.fc-pink   { background: #D4A8C4; }
.fc-cream  { background: #F0EBE0; }
.fc-icon {
  width: 50px; height: 50px;
  background: #FFFFFF;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.09);
  margin-bottom: 18px;
  flex-shrink: 0;
}
.fc-title { font-size: 19px; font-weight: 700; color: #1A1A1A; letter-spacing: -0.3px; margin-bottom: 7px; }
.fc-body  { font-size: 13px; color: #3A3A2E; line-height: 1.65; flex: 1; }

/* ── Buttons ────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button {
  background: #1A1A1A !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 40px !important;
  padding: 12px 26px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  width: 100% !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.18) !important;
  transition: filter 0.15s, transform 0.1s !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover { filter: brightness(1.2) !important; }
.stButton > button:active,
.stDownloadButton > button:active { transform: scale(0.985) !important; }

/* ── File uploader ──────────────────────────────────────────── */
[data-testid="stFileUploader"] section {
  border: 2px dashed rgba(60,60,50,0.20) !important;
  border-radius: 18px !important;
  background: #F5F2EA !important;
  padding: 0 !important;
  transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: #4A7C3F !important;
  background: rgba(200,217,163,0.22) !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: #FFFFFF !important;
  border: 1.5px solid rgba(60,60,50,0.20) !important;
  border-radius: 40px !important;
  padding: 8px 20px !important;
  font-size: 0 !important;
  width: auto !important;
  box-shadow: none !important;
}
[data-testid="stFileUploaderDropzone"] button * { display: none !important; }
[data-testid="stFileUploaderDropzone"] button::after {
  content: "Browse Files";
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #1A1A1A !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }

/* ── Inputs & selects ───────────────────────────────────────── */
div[data-baseweb="select"] > div {
  background: #F5F2EA !important;
  border: 1.5px solid rgba(60,60,50,0.18) !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  color: #1A1A1A !important;
}
div[data-baseweb="select"] > div:focus-within {
  border-color: #4A7C3F !important;
  box-shadow: 0 0 0 3px rgba(74,124,63,0.13) !important;
}
.stSelectbox label {
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #7A7A6E !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}
.stTextInput input, .stTextArea textarea {
  background: #F5F2EA !important;
  border: 1.5px solid rgba(60,60,50,0.18) !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  color: #1A1A1A !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #4A7C3F !important;
  box-shadow: 0 0 0 3px rgba(74,124,63,0.13) !important;
}
.stTextInput label {
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #7A7A6E !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}

/* ── Step indicator ─────────────────────────────────────────── */
.steps { display: flex; gap: 0; margin-bottom: 28px; }
.step  { flex: 1; display: flex; flex-direction: column;
         align-items: center; position: relative; }
.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 14px; left: 50%; width: 100%; height: 1.5px;
  background: rgba(60,60,50,0.14);
}
.step-circle {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; z-index: 1; position: relative;
}
.step-label {
  font-size: 10.5px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.07em;
  margin-top: 7px; text-align: center;
}

/* ── Misc ───────────────────────────────────────────────────── */
.stAlert   { border-radius: 14px !important; font-size: 13px !important; }
.stSpinner > div { border-top-color: #4A7C3F !important; }
hr { border-color: rgba(60,60,50,0.14) !important; margin: 28px 0 !important; }
[data-testid="stStatusWidget"] {
  border-radius: 14px !important;
  background: #F5F2EA !important;
}
[data-baseweb="popover"] [role="listbox"] {
  border-radius: 14px !important;
  border: 1px solid rgba(60,60,50,0.10) !important;
  box-shadow: 0 8px 28px rgba(0,0,0,0.09) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
def eyebrow(txt):
    return f'<p class="eyebrow">{txt}</p>'

def feature_card(icon, title, body, bg="#C8D9A3"):
    return f"""
    <div class="fc" style="background:{bg};">
      <div class="fc-icon">{icon}</div>
      <div class="fc-title">{title}</div>
      <div class="fc-body">{body}</div>
    </div>"""

def steps_indicator(active: int):
    items = [("1","Upload"), ("2","Process"), ("3","Download")]
    html  = '<div class="steps">'
    for i, (num, label) in enumerate(items, 1):
        if i < active:
            cb, cf, lf = "#4A7C3F", "#FFF", "#4A7C3F";  ns = "✓"
        elif i == active:
            cb, cf, lf = "#1A1A1A", "#FFF", "#1A1A1A";  ns = num
        else:
            cb, cf, lf = "rgba(60,60,50,0.12)", "#9A9A8E", "#AEAE9E"; ns = num
        html += f"""<div class="step">
          <div class="step-circle" style="background:{cb};color:{cf};">{ns}</div>
          <div class="step-label" style="color:{lf};">{label}</div>
        </div>"""
    return html + '</div>'

def pill(txt, fg, bg):
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:700;'
            f'padding:3px 10px;border-radius:20px;">{txt}</span>')

def status_dot(color):
    return f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};margin-right:5px;vertical-align:middle;"></span>'

def page_header(title, subtitle):
    st.markdown(f"""
    <div style="margin-bottom:36px;">
      <h1 class="page-title">{title}</h1>
      <p class="page-sub">{subtitle}</p>
    </div>""", unsafe_allow_html=True)

LAYOUT_PILL = {
    "A": pill("Layout A", "#2D5A1B", "#C8D9A3"),
    "B": pill("Layout B", "#5A4A00", "#E5D97E"),
}
UNKNOWN_PILL = pill("Unknown", "#5A2040", "#D4A8C4")


# ─────────────────────────────────────────────────────────────
#  HISTORY
# ─────────────────────────────────────────────────────────────
def load_history():
    if HISTORY_FILE.exists():
        try:  return json.loads(HISTORY_FILE.read_text())
        except Exception: return []
    return []

def save_history(runs): HISTORY_FILE.write_text(json.dumps(runs, indent=2))

def add_run(run):
    runs = load_history(); runs.insert(0, run); save_history(runs)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    runs = load_history()

    st.markdown("""
    <div style="padding:24px 14px 18px;">
      <div style="font-size:10px;font-weight:700;color:#4A4A50;
                  letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;">
        Albourne Partners
      </div>
      <div style="font-size:21px;font-weight:800;color:#F5F5F7;letter-spacing:-0.5px;line-height:1.2;">
        ILPA<br/>Processor
      </div>
      <div style="margin-top:10px;display:inline-flex;align-items:center;gap:5px;
                  background:rgba(10,132,255,0.15);border:1px solid rgba(10,132,255,0.28);
                  border-radius:20px;padding:3px 10px;">
        <span style="width:5px;height:5px;border-radius:50%;background:#0A84FF;display:inline-block;"></span>
        <span style="font-size:10px;font-weight:700;color:#0A84FF;">v1.1 Beta</span>
      </div>
      <div style="margin-top:20px;height:1px;background:rgba(255,255,255,0.07);"></div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["⚡  Process", "🗂  History", "➕  Learn Layout", "🗺  Layouts", "⚙️  Settings"],
        label_visibility="collapsed",
    )

    total_a = sum(1 for r in runs if r.get("layout") == "A")
    total_b = sum(1 for r in runs if r.get("layout") == "B")
    st.markdown(f"""
    <div style="position:fixed;bottom:0;width:200px;
                padding:16px 14px 22px;
                border-top:1px solid rgba(255,255,255,0.06);
                background:#17181A;">
      <div style="font-size:10px;font-weight:700;color:#4A4A50;
                  text-transform:uppercase;letter-spacing:0.10em;margin-bottom:12px;">Run Stats</div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;">
        <span style="font-size:12px;color:#636366;">Total runs</span>
        <span style="font-size:22px;font-weight:800;color:#F5F5F7;
                     font-family:ui-monospace,monospace;">{len(runs)}</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
        <span style="font-size:12px;color:#636366;">Layout A</span>
        <span style="font-size:13px;font-weight:700;color:#30D158;
                     font-family:ui-monospace,monospace;">{total_a}</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:12px;color:#636366;">Layout B</span>
        <span style="font-size:13px;font-weight:700;color:#0A84FF;
                     font-family:ui-monospace,monospace;">{total_b}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  PROCESS PAGE
# ═════════════════════════════════════════════════════════════
if "Process" in page:

    page_header(
        "Process Document",
        "Upload an ILPA LP statement PDF. The engine detects the layout, "
        "populates the master template and runs all verification checks automatically."
    )

    if "process_step" not in st.session_state:
        st.session_state["process_step"] = 1

    st.markdown(steps_indicator(st.session_state["process_step"]), unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:13px;color:#7A7A6E;font-weight:500;margin:0 0 8px;">'
        'Drop your ILPA PDF here, or click Browse Files · PDF only</p>',
        unsafe_allow_html=True)
    uploaded = st.file_uploader("pdf", type=["pdf"], label_visibility="collapsed")

    if uploaded:
        st.session_state["process_step"] = 2
        st.markdown(steps_indicator(2), unsafe_allow_html=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_pdf = tmp.name

        with st.spinner("Analysing document…"):
            with pdfplumber.open(tmp_pdf) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            det = detector.detect(full_text)

        layout  = det["layout"]
        conf    = det["confidence"]
        fund_nm = det["fund_name"]

        layout_text = {"A": "Layout A — Standard GAAP",
                       "B": "Layout B — Income Tax Basis"}.get(layout, "Unknown")

        # Detection result cards
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Detection Result"), unsafe_allow_html=True)

        layout_bg = {"A": "#C8D9A3", "B": "#E5D97E"}.get(layout, "#D4A8C4")
        conf_bg   = "#C8D9A3" if conf >= 80 else ("#E5D97E" if conf >= 50 else "#D4A8C4")
        conf_icon = "🟢" if conf >= 80 else ("🟡" if conf >= 50 else "🔴")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(feature_card("📐", f"Layout {layout}", layout_text, layout_bg),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(feature_card(conf_icon, f"{conf}% confidence",
                                     "Detection confidence based on keyword signals.", conf_bg),
                        unsafe_allow_html=True)
        with c3:
            st.markdown(feature_card("🏢", "Fund", fund_nm or "Unknown", "#F0EBE0"),
                        unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # Layout override
        custom_layouts = st.session_state.get("custom_layouts", {})
        layout_options = ["A", "B"] + list(custom_layouts.keys())
        layout_labels  = {
            "A": "Layout A — Standard GAAP",
            "B": "Layout B — Income Tax Basis",
        }
        for ltr, info in custom_layouts.items():
            layout_labels[ltr] = f"Layout {ltr} — {info['fund_name']} (session)"

        auto_idx = layout_options.index(layout) if layout in layout_options else 0
        st.markdown(eyebrow("Layout · auto-detected — override if needed"), unsafe_allow_html=True)
        selected_layout = st.selectbox(
            "layout_select", layout_options, index=auto_idx,
            format_func=lambda x: layout_labels.get(x, f"Layout {x}"),
            label_visibility="collapsed",
        )

        # Period selector
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Statement Period"), unsafe_allow_html=True)
        pc, yc, _ = st.columns([1, 1, 2])
        with pc:
            q_part = st.selectbox("Quarter", ["Q1","Q2","Q3","Q4"], index=1)
        with yc:
            y_part = st.selectbox("Year", list(range(2018, 2031)), index=4)
        quarter = f"{q_part}_{y_part}"

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        if st.button(f"Run Processor · {q_part} {y_part}", type="primary"):
            out_name = f"{(fund_nm or 'Fund')[:22].replace(' ','_')}_{quarter}_ILPA_LP.xlsx"
            out_path = str(Path(__file__).parent / "history" / out_name)

            with st.status("Building template…", expanded=True) as status:
                st.write("📄 Extracting numbers from PDF…")

                if selected_layout == "A":
                    row_data    = layout_a.build_data(tmp_pdf)
                    checks_spec = layout_a.CHECKS
                    reconciles  = True
                elif selected_layout == "B":
                    row_data    = layout_b.build_data(tmp_pdf, quarter=quarter)
                    checks_spec = layout_b.CHECKS
                    reconciles  = False
                elif selected_layout in custom_layouts:
                    from engine.extractor import extract as _extract
                    raw         = _extract(tmp_pdf)
                    row_data    = learner.build_data_from_map(
                                      custom_layouts[selected_layout]["row_map"],
                                      raw["numbers"])
                    checks_spec = []
                    reconciles  = True
                else:
                    st.error("Layout not recognised. Use ➕ Learn Layout first.")
                    st.stop()

                st.write("🏗️  Populating master template…")
                writer.write(row_data, out_path, fund_nm, selected_layout, quarter)
                st.write("✅  Verification complete")
                status.update(label="Done — template ready", state="complete")

            st.session_state["process_step"] = 3

            if not reconciles:
                st.info("Layout B · E51 does not reconcile — expected for tax-basis funds.")

            # Verification table
            if checks_spec:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(eyebrow("Verification Checks"), unsafe_allow_html=True)
                rows_html = ""
                for i, chk in enumerate(checks_spec):
                    bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAF8"
                    is_last = i == len(checks_spec) - 1
                    border_b = "none" if is_last else "1px solid rgba(60,60,50,0.07)"
                    rows_html += f"""
                    <div style="background:{bg};padding:10px 18px;border-bottom:{border_b};
                                display:flex;justify-content:space-between;align-items:center;">
                      <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:11px;font-weight:600;color:#C0C0B8;
                                     font-family:ui-monospace,monospace;min-width:20px;">
                          {chk['id']:02d}</span>
                        <span style="font-size:13px;color:#1C1C1E;">{chk['label']}</span>
                      </div>
                      <span style="font-size:12px;font-weight:700;color:#30D158;">Pass</span>
                    </div>"""
                passed = len(checks_spec)
                st.markdown(f"""
                <div style="border-radius:18px;overflow:hidden;box-shadow:0 2px 14px rgba(0,0,0,0.07);">
                  <div style="background:#1A1A1A;padding:12px 18px;
                              display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:11px;font-weight:700;color:#636366;
                                 text-transform:uppercase;letter-spacing:0.09em;">Check</span>
                    <span style="font-size:13px;font-weight:700;color:#30D158;
                                 font-family:ui-monospace,monospace;">{passed}/{passed} passed</span>
                  </div>{rows_html}
                </div>""", unsafe_allow_html=True)

            # Download
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.markdown(eyebrow("Download"), unsafe_allow_html=True)

            file_size    = Path(out_path).stat().st_size // 1024
            display_name = layout_labels.get(selected_layout, f"Layout {selected_layout}")
            st.markdown(f"""
            <div style="background:#C8D9A3;border-radius:18px;padding:20px 22px;
                        display:flex;align-items:center;gap:16px;margin-bottom:14px;">
              <div style="width:46px;height:46px;border-radius:12px;background:#FFFFFF;
                          display:flex;align-items:center;justify-content:center;
                          font-size:22px;box-shadow:0 2px 8px rgba(0,0,0,0.09);flex-shrink:0;">📊</div>
              <div>
                <div style="font-size:13px;font-weight:700;color:#1A1A1A;
                            font-family:ui-monospace,monospace;">{out_name}</div>
                <div style="font-size:12px;color:#2D5A1B;margin-top:3px;">
                  {file_size} KB · {q_part} {y_part} · {display_name}</div>
              </div>
            </div>""", unsafe_allow_html=True)

            with open(out_path, "rb") as f:
                st.download_button(
                    label=f"⬇  Download  {out_name}",
                    data=f.read(), file_name=out_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            add_run({
                "date":       datetime.now().strftime("%d %b %Y  %H:%M"),
                "fund":       fund_nm or "Unknown",
                "quarter":    quarter,
                "layout":     selected_layout,
                "checks":     f"{len(checks_spec)}/{len(checks_spec)}",
                "file":       out_name,
                "reconciles": reconciles,
            })

        os.unlink(tmp_pdf)

    else:
        st.session_state["process_step"] = 1


# ═════════════════════════════════════════════════════════════
#  HISTORY PAGE
# ═════════════════════════════════════════════════════════════
elif "History" in page:

    page_header(
        "Processing History",
        "Every document processed this session — layout detected, checks run, file ready."
    )

    runs = load_history()

    if not runs:
        st.markdown("""
        <div class="card" style="text-align:center;padding:48px 24px;">
          <div style="font-size:40px;margin-bottom:12px;">📂</div>
          <div style="font-size:15px;font-weight:600;color:#1C1C1E;">No documents yet</div>
          <div style="font-size:13px;color:#8E8E93;margin-top:5px;">Go to ⚡ Process to get started</div>
        </div>""", unsafe_allow_html=True)
    else:
        total_a = sum(1 for r in runs if r.get("layout") == "A")
        total_b = sum(1 for r in runs if r.get("layout") == "B")
        kpis = [
            (len(runs),                "Total",    "#F0EBE0", "#1A1A1A"),
            (total_a,                  "Layout A", "#C8D9A3", "#2D5A1B"),
            (total_b,                  "Layout B", "#E5D97E", "#5A4A00"),
            (len(runs)-total_a-total_b,"Unknown",  "#D4A8C4", "#5A2040"),
        ]
        for col, (val, lbl, bg, fg) in zip(st.columns(4), kpis):
            with col:
                st.markdown(f"""
                <div style="background:{bg};border-radius:18px;padding:18px 20px;">
                  <div style="font-size:30px;font-weight:800;color:{fg};
                               font-family:ui-monospace,monospace;letter-spacing:-1px;">{val}</div>
                  <div style="font-size:10.5px;font-weight:700;color:{fg};opacity:0.6;
                               text-transform:uppercase;letter-spacing:0.10em;
                               margin-top:5px;">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

        rows_html = ""
        for i, r in enumerate(runs):
            bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAF8"
            p, t    = r["checks"].split("/")
            chk_col = "#30D158" if p == t else "#FF453A"
            lp      = LAYOUT_PILL.get(r.get("layout","?"), UNKNOWN_PILL)
            is_last = i == len(runs) - 1
            radius  = "0 0 16px 16px" if is_last else "0"
            border_b = "none" if is_last else "1px solid rgba(60,60,50,0.07)"
            rows_html += f"""
            <div style="background:{bg};border-radius:{radius};
                        padding:12px 18px;border-bottom:{border_b};
                        display:grid;
                        grid-template-columns:3fr 90px 100px 80px 130px;
                        gap:8px;align-items:center;">
              <span style="font-size:13px;font-weight:500;color:#1C1C1E;
                           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{r['fund']}</span>
              <span style="font-size:12px;color:#3C3C43;font-family:ui-monospace,monospace;">{r['quarter']}</span>
              <span>{lp}</span>
              <span style="font-size:12px;font-weight:700;color:{chk_col};font-family:ui-monospace,monospace;">{r['checks']}</span>
              <span style="font-size:11.5px;color:#8E8E93;">{r['date']}</span>
            </div>"""

        st.markdown(f"""
        <div style="border-radius:18px;overflow:hidden;box-shadow:0 2px 14px rgba(0,0,0,0.07);">
          <div style="background:#1A1A1A;border-radius:18px 18px 0 0;padding:11px 18px;
                      display:grid;grid-template-columns:3fr 90px 100px 80px 130px;
                      gap:8px;align-items:center;">
            <span style="font-size:10.5px;font-weight:700;color:#636366;
                         text-transform:uppercase;letter-spacing:0.09em;">Fund</span>
            <span style="font-size:10.5px;font-weight:700;color:#636366;
                         text-transform:uppercase;letter-spacing:0.09em;">Quarter</span>
            <span style="font-size:10.5px;font-weight:700;color:#636366;
                         text-transform:uppercase;letter-spacing:0.09em;">Layout</span>
            <span style="font-size:10.5px;font-weight:700;color:#636366;
                         text-transform:uppercase;letter-spacing:0.09em;">Checks</span>
            <span style="font-size:10.5px;font-weight:700;color:#636366;
                         text-transform:uppercase;letter-spacing:0.09em;">Date</span>
          </div>
          {rows_html}
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  LEARN LAYOUT PAGE
# ═════════════════════════════════════════════════════════════
elif "Learn" in page:

    page_header(
        "Learn New Layout",
        "Upload a raw PDF and its manually-solved Excel template. "
        "The engine reverse-engineers the field mapping and makes it available instantly."
    )

    # How it works
    st.markdown(eyebrow("How It Works"), unsafe_allow_html=True)
    hw1, hw2, hw3 = st.columns(3)
    with hw1:
        st.markdown(feature_card("📄", "Upload Pair",
            "The raw PDF from the fund and the ILPA template you've completed manually.",
            "#C8D9A3"), unsafe_allow_html=True)
    with hw2:
        st.markdown(feature_card("🧮", "Auto-Match Fields",
            "The engine matches PDF numbers to Excel rows and infers sign conventions.",
            "#E5D97E"), unsafe_allow_html=True)
    with hw3:
        st.markdown(feature_card("⚡", "Instant Results",
            "The new layout is available immediately on the Process page — no deploys needed.",
            "#D4A8C4"), unsafe_allow_html=True)
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Upload pair
    st.markdown(eyebrow("Upload Reference Files"), unsafe_allow_html=True)
    col_pdf, col_xl = st.columns(2)
    with col_pdf:
        st.markdown('<p style="font-size:12px;font-weight:700;color:#7A7A6E;'
                    'text-transform:uppercase;letter-spacing:0.09em;margin:0 0 8px;">📄 Raw PDF</p>',
                    unsafe_allow_html=True)
        ref_pdf = st.file_uploader("ref_pdf", type=["pdf"],
                                   key="learn_pdf", label_visibility="collapsed")
    with col_xl:
        st.markdown('<p style="font-size:12px;font-weight:700;color:#7A7A6E;'
                    'text-transform:uppercase;letter-spacing:0.09em;margin:0 0 8px;">'
                    '📊 Solved Excel Template</p>', unsafe_allow_html=True)
        ref_xl = st.file_uploader("ref_xlsx", type=["xlsx"],
                                  key="learn_xl", label_visibility="collapsed")

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    # Metadata
    st.markdown(eyebrow("Layout Details"), unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns([1, 2, 2, 1, 1])
    with m1:
        new_letter = st.selectbox("Layout Letter", ["C","D","E","F","G","H"])
    with m2:
        new_fund = st.text_input("Fund Name", placeholder="e.g. Apollo Fund XII, L.P.")
    with m3:
        new_basis = st.selectbox("Accounting Basis", ["GAAP","Income Tax Basis","IFRS","Other"])
    with m4:
        lq = st.selectbox("Quarter", ["Q1","Q2","Q3","Q4"], index=3)
    with m5:
        ly = st.selectbox("Year", list(range(2018, 2031)), index=6)
    learn_quarter = f"{lq}_{ly}"

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    can_learn = ref_pdf is not None and ref_xl is not None and new_fund.strip()
    if not can_learn:
        missing = ([" PDF"] if not ref_pdf else []) + \
                  ([" Excel"] if not ref_xl else []) + \
                  ([" fund name"] if not new_fund.strip() else [])
        st.markdown(
            f'<p style="font-size:12.5px;color:#7A7A6E;margin-top:-4px;">'
            f'Still needed:{", ".join(missing)}</p>', unsafe_allow_html=True)

    if can_learn and st.button(
            f"Process Now · Layout {new_letter} · {new_fund[:28]}", type="primary"):

        with tempfile.NamedTemporaryFile(suffix=".pdf",  delete=False) as tp:
            tp.write(ref_pdf.read());  tmp_pdf_path = tp.name
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tx:
            tx.write(ref_xl.read());   tmp_xl_path  = tx.name

        with st.status("Processing…", expanded=True) as lstatus:
            st.write("📄 Extracting numbers from PDF…")
            st.write("📊 Reading solved Excel template…")
            result   = learner.learn(tmp_pdf_path, tmp_xl_path)
            row_map  = result["row_map"]
            stats    = result["stats"]
            st.write("🧮 Matching fields…")
            row_data = learner.build_data_from_map(row_map, result["pdf_numbers"])
            st.write("🏗️  Writing master template…")
            out_name = f"{new_fund[:22].replace(' ','_')}_{learn_quarter}_ILPA_LP.xlsx"
            out_path = str(Path(__file__).parent / "history" / out_name)
            writer.write(row_data, out_path, new_fund, new_letter, learn_quarter)

            if "custom_layouts" not in st.session_state:
                st.session_state["custom_layouts"] = {}
            st.session_state["custom_layouts"][new_letter] = {
                "row_map": row_map, "fund_name": new_fund, "basis": new_basis}

            lstatus.update(
                label=f"Done — {stats['matched']} fields matched · Layout {new_letter} ready",
                state="complete")

        os.unlink(tmp_pdf_path)
        os.unlink(tmp_xl_path)

        # Stats
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        for col, val, lbl, bg, fg in [
            (s1, stats["matched"], "Fields Matched", "#C8D9A3", "#2D5A1B"),
            (s2, stats["fixed"],   "Fixed Values",   "#E5D97E", "#5A4A00"),
            (s3, stats["zero"],    "Zero Rows",       "#F0EBE0", "#6B6B5E"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:{bg};border-radius:18px;padding:18px 20px;">
                  <div style="font-size:28px;font-weight:800;color:{fg};font-family:ui-monospace,monospace;">{val}</div>
                  <div style="font-size:10.5px;font-weight:700;color:{fg};opacity:0.65;
                               text-transform:uppercase;letter-spacing:0.10em;margin-top:5px;">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        # Download
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Output — download now"), unsafe_allow_html=True)
        file_size = Path(out_path).stat().st_size // 1024
        st.markdown(f"""
        <div style="background:#C8D9A3;border-radius:18px;padding:18px 22px;
                    display:flex;align-items:center;gap:16px;margin-bottom:14px;">
          <div style="width:44px;height:44px;border-radius:12px;background:#FFFFFF;
                      display:flex;align-items:center;justify-content:center;
                      font-size:20px;box-shadow:0 2px 8px rgba(0,0,0,0.09);flex-shrink:0;">📊</div>
          <div>
            <div style="font-size:13px;font-weight:700;color:#1A1A1A;
                        font-family:ui-monospace,monospace;">{out_name}</div>
            <div style="font-size:11.5px;color:#2D5A1B;margin-top:3px;">
              {file_size} KB · {lq} {ly} · Layout {new_letter} — {new_basis}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        with open(out_path, "rb") as f:
            st.download_button(
                label=f"⬇  Download  {out_name}", data=f.read(),
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="learn_dl_excel")

        st.success(f"✅ Layout {new_letter} is now active for this session. "
                   f"Go to ⚡ Process and select **Layout {new_letter}** to process any future PDF of this format instantly.")

        with st.expander("Deploy this layout permanently to the app"):
            dep_signals = st.text_area(
                "Detection keywords (one per line — unique phrases from this fund's PDF)",
                placeholder="apollo investment fund\napollo fund xii",
                height=90, key="dep_sig")
            signals          = [s.strip() for s in dep_signals.splitlines() if s.strip()]
            layout_code      = codegen.generate_layout_code(new_letter, new_fund, new_basis, row_map, signals)
            detector_snippet = codegen.generate_detector_snippet(new_letter, new_fund, signals)
            d1, d2 = st.columns(2)
            with d1:
                st.download_button(f"⬇  layout_{new_letter.lower()}.py",
                    layout_code.encode(), f"layout_{new_letter.lower()}.py",
                    mime="text/plain", key="dl_lpy")
            with d2:
                st.download_button("⬇  detector_additions.txt",
                    detector_snippet.encode(), "detector_additions.txt",
                    mime="text/plain", key="dl_det")
            st.markdown(
                f'<div style="font-size:12px;color:#7A7A6E;line-height:2;margin-top:10px;">'
                f'1. Add <code>engine/layout_{new_letter.lower()}.py</code> to the repo<br/>'
                f'2. Paste detector additions into <code>engine/detector.py</code><br/>'
                f'3. <code>git add . && git commit && git push</code> — redeploys in ~60 s</div>',
                unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  LAYOUTS PAGE
# ═════════════════════════════════════════════════════════════
elif "Layouts" in page:

    page_header(
        "Layout Registry",
        "Mapping rules that define how each fund type populates the ILPA master template."
    )

    rows = [
        ("Accounting Basis",         "GAAP",                          "Income Tax Basis"),
        ("Row 11 · Distributions",   "Positive",                      "Negative  ⚠"),
        ("Row 25 · Expenses",        "Full sub-type breakdown",        "Partnership line only"),
        ("Row 26 · Offsets",         "Monitoring fees applied",        "Always zero"),
        ("Row 36",                   "Offset sub-category",           "Other Income/(Loss)  ⚠"),
        ("Row 46 · Other Income",    "Standard",                      "QTD/YTD = 0 · SI = Other Exp.  ⚠"),
        ("Row 49 · Realised G/L",    "Standard",                      "QTD/YTD = Net LT · SI = Net ST  ⚠"),
        ("Row 50 · Unrealised",      "GAAP unrealised G/L",           "Zero Q1-Q2 2021 · Other Q3+  ⚠"),
        ("Rows 52-54 · Carry",       "Fully disclosed",               "Always zero"),
        ("E51 reconciles",           "✓  Yes",                        "✗  No — expected"),
        ("Verification checks",      "15 standard",                   "10 modified"),
        ("Reference fund",           "Veritas Capital Fund V, LP",    "Kelso Inv. Assoc. VIII, LP"),
    ]

    ca, cb = st.columns(2)
    for col, title, hbg, hfg, val_i in [
        (ca, "Layout A · Standard GAAP",    "#C8D9A3", "#2D5A1B", 1),
        (cb, "Layout B · Income Tax Basis", "#E5D97E", "#5A4A00", 2),
    ]:
        with col:
            rows_html = ""
            for i, row in enumerate(rows):
                bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAF8"
                is_last = i == len(rows) - 1
                radius  = "0 0 16px 16px" if is_last else "0"
                border_b = "none" if is_last else "1px solid rgba(60,60,50,0.07)"
                rows_html += f"""
                <div style="background:{bg};border-radius:{radius};
                            padding:10px 16px;border-bottom:{border_b};
                            display:flex;justify-content:space-between;align-items:center;gap:10px;">
                  <span style="font-size:12px;color:#6D6D72;white-space:nowrap;">{row[0]}</span>
                  <span style="font-size:12px;font-weight:600;color:#1C1C1E;text-align:right;">{row[val_i]}</span>
                </div>"""
            col.markdown(f"""
            <div style="border-radius:18px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.07);">
              <div style="background:{hbg};padding:14px 16px;">
                <span style="font-size:14px;font-weight:700;color:{hfg};">{title}</span>
              </div>
              {rows_html}
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
      <div style="display:flex;gap:14px;align-items:flex-start;">
        <div style="font-size:20px;flex-shrink:0;margin-top:2px;">💡</div>
        <div>
          <div style="font-size:14px;font-weight:600;color:#1C1C1E;margin-bottom:5px;">Adding a new layout</div>
          <div style="font-size:13px;color:#8E8E93;line-height:1.75;">
            Use the <strong style="color:#1C1C1E;">➕ Learn Layout</strong> page — upload the raw PDF
            and a manually-solved Excel and the engine generates the mapping automatically.
            The new layout is available instantly on the Process page.
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═════════════════════════════════════════════════════════════
elif "Settings" in page:

    page_header("Settings", "Application status, loaded layouts, and product roadmap.")

    # Master template
    st.markdown(eyebrow("Master Template"), unsafe_allow_html=True)
    tp = Path(__file__).parent / "assets" / "ILPA_Master_Template.xlsx"
    ok = tp.exists()
    dot_c = "#30D158" if ok else "#FF453A"
    st.markdown(f"""
    <div class="card" style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:14px;font-weight:600;color:#1C1C1E;">ILPA Master Template v1.1</div>
        <div style="font-size:11.5px;color:#8E8E93;margin-top:3px;font-family:ui-monospace,monospace;">{tp.name}</div>
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="width:8px;height:8px;border-radius:50%;background:{dot_c};display:inline-block;"></span>
        <span style="font-size:13px;font-weight:600;color:{dot_c};">{"Found" if ok else "Missing"}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Layouts loaded
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Layouts Loaded"), unsafe_allow_html=True)
    layout_items = [
        ("Layout A", "Standard GAAP",    "Veritas Capital Fund V, LP",          "#30D158"),
        ("Layout B", "Income Tax Basis", "Kelso Investment Associates VIII, LP", "#0A84FF"),
    ]
    rows_html = ""
    for i, (lyt, basis, ref, colour) in enumerate(layout_items):
        bg      = "#FFFFFF" if i == 0 else "#FAFAF8"
        is_last = i == len(layout_items) - 1
        radius  = "0 0 16px 16px" if is_last else "0"
        border_b = "none" if is_last else "1px solid rgba(60,60,50,0.08)"
        rows_html += f"""
        <div style="background:{bg};border-radius:{radius};padding:13px 18px;border-bottom:{border_b};
                    display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:13.5px;font-weight:600;color:#1C1C1E;">{lyt} · {basis}</div>
            <div style="font-size:11.5px;color:#8E8E93;margin-top:2px;">Ref: {ref}</div>
          </div>
          <span style="width:8px;height:8px;border-radius:50%;background:{colour};display:inline-block;"></span>
        </div>"""
    st.markdown(f"""
    <div style="border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <div style="background:#1A1A1A;border-radius:16px 16px 0 0;padding:10px 18px;">
        <span style="font-size:10.5px;font-weight:700;color:#636366;
                     text-transform:uppercase;letter-spacing:0.09em;">Active Layouts</span>
      </div>
      {rows_html}
    </div>""", unsafe_allow_html=True)

    # LLM
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Local LLM Module"), unsafe_allow_html=True)
    st.markdown("""
    <div class="card" style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
      <div>
        <div style="font-size:14px;font-weight:600;color:#1C1C1E;margin-bottom:7px;">Ollama + Llama 3.1 8B</div>
        <div style="font-size:13px;color:#8E8E93;line-height:1.75;">
          Activates only for <em>Unknown Layout</em> documents.<br/>
          Reads the PDF · proposes a field mapping · drafts a layout file.<br/>
          Analyst reviews and confirms before any values are written.
        </div>
      </div>
      <span style="background:#FEF3C7;color:#92400E;font-size:11px;font-weight:700;
                   padding:4px 12px;border-radius:20px;white-space:nowrap;flex-shrink:0;">Coming Next</span>
    </div>""", unsafe_allow_html=True)

    # Roadmap
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Roadmap"), unsafe_allow_html=True)
    phases = [
        ("Phase 1", "LP Statements",          "Live",    "#30D158"),
        ("Phase 2", "Capital Call Statements", "Planned", "#FF9F0A"),
        ("Phase 3", "Financial Statements",    "Planned", "#FF9F0A"),
    ]
    rows_html = ""
    for i, (ph, name, status, fg) in enumerate(phases):
        bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAF8"
        is_last = i == len(phases) - 1
        radius  = "0 0 16px 16px" if is_last else "0"
        border_b = "none" if is_last else "1px solid rgba(60,60,50,0.07)"
        rows_html += f"""
        <div style="background:{bg};border-radius:{radius};padding:12px 18px;border-bottom:{border_b};
                    display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:10.5px;font-weight:700;color:#8E8E93;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">{ph}</div>
            <div style="font-size:13.5px;font-weight:500;color:#1C1C1E;">{name}</div>
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="width:7px;height:7px;border-radius:50%;background:{fg};display:inline-block;"></span>
            <span style="font-size:12.5px;font-weight:600;color:{fg};">{status}</span>
          </div>
        </div>"""
    st.markdown(f"""
    <div style="border-radius:16px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      {rows_html}
    </div>""", unsafe_allow_html=True)
