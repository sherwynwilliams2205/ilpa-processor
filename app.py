"""
ILPA Processor — Albourne Partners
Apple × Bloomberg design language
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
    initial_sidebar_state="collapsed",
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

* {
  font-family: "DM Sans", -apple-system, BlinkMacSystemFont,
               "Helvetica Neue", Arial, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}
.mono {
  font-family: "SF Mono", "Fira Code", ui-monospace, monospace !important;
  font-variant-numeric: tabular-nums;
}

#MainMenu, footer, header { visibility: hidden !important; }
.block-container {
  padding: 40px 48px 64px !important;
  max-width: 1100px !important;
}

/* ── Cream background — matches the reference design ── */
.main { background: #E8E5DC !important; }

/* ── Pastel feature cards ── */
.fc-green  { background: #C8D9A3 !important; }
.fc-yellow { background: #E5D97E !important; }
.fc-pink   { background: #D4A8C4 !important; }
.fc-cream  { background: #F0EBE0 !important; }
.fc-white  { background: #FFFFFF !important; }

/* Icon box inside feature card */
.ic-box {
  width: 52px; height: 52px;
  background: #FFFFFF;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  margin-bottom: 20px;
  flex-shrink: 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] > div:first-child {
  background: #131416 !important;
}
section[data-testid="stSidebar"] {
  background: #131416 !important;
  min-width: 216px !important;
  max-width: 216px !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
}
/* ── Sidebar toggle: always pinned to left edge ─────────────── */
[data-testid="collapsedControl"] {
  position: fixed !important;
  left: 0 !important;
  top: 50vh !important;
  transform: translateY(-50%) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: all !important;
  z-index: 999999 !important;
  width: 20px !important;
  height: 48px !important;
  background: #2C2F33 !important;
  border-radius: 0 10px 10px 0 !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-left: none !important;
  box-shadow: 2px 0 10px rgba(0,0,0,0.25) !important;
  cursor: pointer !important;
  transition: background 0.2s, width 0.2s !important;
}
[data-testid="collapsedControl"]:hover {
  background: #3A3F47 !important;
  width: 24px !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] button {
  color: #F5F5F7 !important;
  fill: #F5F5F7 !important;
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  width: 16px !important;
  height: 16px !important;
}
/* Collapse button inside the open sidebar */
[data-testid="stSidebarCollapseButton"] {
  visibility: visible !important;
  opacity: 1 !important;
  display: flex !important;
  pointer-events: all !important;
}
[data-testid="stSidebarCollapseButton"] svg {
  color: rgba(255,255,255,0.7) !important;
  fill: rgba(255,255,255,0.7) !important;
}
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }
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
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
  display: none !important;
}

/* ── Inputs ── */
div[data-baseweb="select"] > div {
  background: #FFFFFF !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  border-radius: 10px !important;
  font-size: 15px !important;
  color: #1C1C1E !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
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
.stTextInput input {
  background: #FFFFFF !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  border-radius: 10px !important;
  font-size: 15px !important;
  color: #1C1C1E !important;
}
.stTextInput input:focus {
  border-color: #0A84FF !important;
  box-shadow: 0 0 0 3px rgba(10,132,255,0.15) !important;
}
.stTextArea textarea {
  background: #FFFFFF !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  border-radius: 10px !important;
  font-size: 14px !important;
  color: #1C1C1E !important;
}
.stTextArea textarea:focus {
  border-color: #0A84FF !important;
  box-shadow: 0 0 0 3px rgba(10,132,255,0.15) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {
  border: 2px dashed rgba(60,60,50,0.22) !important;
  border-radius: 20px !important;
  background: #F5F1E8 !important;
  padding: 0 !important;
  box-shadow: none !important;
  transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: #4A7C3F !important;
  background: rgba(200,217,163,0.25) !important;
}
/* File uploader button — correct testid is lowercase 'z': stFileUploaderDropzone */
[data-testid="stFileUploaderDropzone"] button {
  background: #FFFFFF !important;
  border: 1.5px solid rgba(60,60,50,0.22) !important;
  border-radius: 40px !important;
  padding: 8px 20px !important;
  box-shadow: none !important;
  width: auto !important;
  font-size: 0 !important;
}
[data-testid="stFileUploaderDropzone"] button * {
  display: none !important;
}
[data-testid="stFileUploaderDropzone"] button::after {
  content: "Browse Files";
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #1A1A1A !important;
  font-family: "DM Sans", -apple-system, sans-serif !important;
}
/* Hide the instructions text — we have our own label above */
[data-testid="stFileUploaderDropzoneInstructions"] {
  display: none !important;
}

/* ── Buttons ── */
.stButton > button {
  background: #1A1A1A !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 40px !important;
  padding: 13px 28px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  width: 100% !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
  transition: filter 0.15s, transform 0.1s !important;
}
.stButton > button:hover {
  filter: brightness(1.18) !important;
}
.stButton > button:active { transform: scale(0.985) !important; }

.stDownloadButton > button {
  background: #1A1A1A !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 40px !important;
  padding: 14px 28px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  width: 100% !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
  transition: filter 0.15s, transform 0.1s !important;
}
.stDownloadButton > button:hover { filter: brightness(1.22) !important; }
.stDownloadButton > button:active { transform: scale(0.985) !important; }

/* ── Inputs on cream bg ── */
div[data-baseweb="select"] > div {
  background: #F5F1E8 !important;
  border: 1.5px solid rgba(60,60,50,0.18) !important;
  border-radius: 12px !important;
  font-size: 15px !important;
  color: #1A1A1A !important;
  box-shadow: none !important;
}
div[data-baseweb="select"] > div:focus-within {
  border-color: #4A7C3F !important;
  box-shadow: 0 0 0 3px rgba(74,124,63,0.15) !important;
}
.stSelectbox label {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: #6B6B5E !important;
  text-transform: uppercase !important;
  letter-spacing: 0.07em !important;
}
.stTextInput input {
  background: #F5F1E8 !important;
  border: 1.5px solid rgba(60,60,50,0.18) !important;
  border-radius: 12px !important;
  font-size: 15px !important;
  color: #1A1A1A !important;
}
.stTextInput input:focus {
  border-color: #4A7C3F !important;
  box-shadow: 0 0 0 3px rgba(74,124,63,0.15) !important;
}
.stTextArea textarea {
  background: #F5F1E8 !important;
  border: 1.5px solid rgba(60,60,50,0.18) !important;
  border-radius: 12px !important;
  font-size: 14px !important;
  color: #1A1A1A !important;
}
.stTextArea textarea:focus {
  border-color: #4A7C3F !important;
  box-shadow: 0 0 0 3px rgba(74,124,63,0.15) !important;
}

/* ── Misc ── */
.stSpinner > div { border-top-color: #4A7C3F !important; }
.stAlert { border-radius: 16px !important; font-size: 13px !important; }
hr { border-color: rgba(60,60,50,0.15) !important; margin: 32px 0 !important; }
[data-baseweb="popover"] [role="listbox"] {
  border-radius: 16px !important;
  border: 1px solid rgba(60,60,50,0.12) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.10) !important;
  overflow: hidden !important;
}

/* ── Status box ── */
[data-testid="stStatusWidget"] {
  border-radius: 16px !important;
  border: 1px solid rgba(60,60,50,0.15) !important;
  background: #F5F1E8 !important;
}

/* ── Step indicator ── */
.step-row {
  display: flex;
  gap: 0;
  margin-bottom: 28px;
}
.step-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}
.step-item:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 14px;
  left: 50%;
  width: 100%;
  height: 1px;
  background: rgba(60,60,67,0.15);
}
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  z-index: 1;
  position: relative;
}
.step-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 6px;
  text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────
def eyebrow(txt):
    return (f'<p style="font-size:11px;font-weight:700;color:#6B6B5E;'
            f'text-transform:uppercase;letter-spacing:0.10em;margin:0 0 12px;">{txt}</p>')

def card_open(radius="20px", padding="22px 24px", extra="", bg="#FFFFFF"):
    shadow = "0 2px 12px rgba(0,0,0,0.06)" if bg == "#FFFFFF" else "none"
    return (f'<div style="background:{bg};border-radius:{radius};padding:{padding};'
            f'box-shadow:{shadow};{extra}">')

def card_close():
    return '</div>'

def feature_card(icon, title, body, bg="#C8D9A3"):
    """Large pastel feature card matching the reference design."""
    return f"""
    <div style="background:{bg};border-radius:22px;padding:28px 26px 30px;
                min-height:190px;display:flex;flex-direction:column;">
      <div style="width:52px;height:52px;background:#FFFFFF;border-radius:14px;
                  display:flex;align-items:center;justify-content:center;
                  font-size:24px;box-shadow:0 2px 10px rgba(0,0,0,0.10);
                  margin-bottom:20px;flex-shrink:0;">{icon}</div>
      <div style="font-size:20px;font-weight:700;color:#1A1A1A;
                  letter-spacing:-0.3px;margin-bottom:8px;">{title}</div>
      <div style="font-size:13px;color:#3A3A2E;line-height:1.65;flex:1;">{body}</div>
    </div>"""

def status_dot(colour):
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{colour};margin-right:6px;vertical-align:middle;"></span>'

def pill(txt, fg, bg):
    return (f'<span style="background:{bg};color:{fg};font-size:11.5px;font-weight:600;'
            f'padding:3px 10px;border-radius:20px;letter-spacing:0.02em;">{txt}</span>')

def steps_indicator(active: int):
    items = [("1", "Upload"), ("2", "Process"), ("3", "Download")]
    html  = '<div class="step-row">'
    for i, (num, label) in enumerate(items, 1):
        if i < active:
            circ_bg, circ_fg, lbl_fg = "#4A7C3F", "#FFFFFF", "#4A7C3F"
            num_str = "✓"
        elif i == active:
            circ_bg, circ_fg, lbl_fg = "#1A1A1A", "#FFFFFF", "#1A1A1A"
            num_str = num
        else:
            circ_bg, circ_fg, lbl_fg = "rgba(60,60,50,0.12)", "#8E8E80", "#AEAE9E"
            num_str = num
        html += f"""
        <div class="step-item">
          <div class="step-circle" style="background:{circ_bg};color:{circ_fg};">
            {num_str}
          </div>
          <div class="step-label" style="color:{lbl_fg};">{label}</div>
        </div>"""
    html += '</div>'
    return html

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
      <div style="font-size:11px;font-weight:700;color:#48484A;
                  letter-spacing:0.14em;text-transform:uppercase;
                  margin-bottom:12px;">Albourne Partners</div>
      <div style="font-size:20px;font-weight:700;color:#F5F5F7;
                  letter-spacing:-0.5px;line-height:1.2;">
        ILPA<br/>Processor
      </div>
      <div style="margin-top:12px;display:inline-flex;align-items:center;
                  gap:5px;background:rgba(10,132,255,0.18);
                  border:1px solid rgba(10,132,255,0.3);
                  border-radius:20px;padding:3px 10px;">
        <span style="width:6px;height:6px;border-radius:50%;
                     background:#0A84FF;display:inline-block;"></span>
        <span style="font-size:11px;font-weight:600;color:#0A84FF;">v1.1 Beta</span>
      </div>
      <div style="margin-top:22px;border-top:1px solid rgba(255,255,255,0.08);"></div>
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

    # ── Page header — title | description | action row ───────
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 2fr auto;
                gap:32px;align-items:center;margin-bottom:40px;">
      <div>
        <h1 style="font-size:34px;font-weight:800;color:#1A1A1A;
                   letter-spacing:-0.8px;line-height:1.15;margin:0;">
          Process<br/>Document
        </h1>
      </div>
      <div style="font-size:15px;color:#5A5A4E;line-height:1.7;font-weight:400;">
        Upload an ILPA LP statement PDF. The engine detects
        the layout, populates the master template and runs
        all verification checks automatically.
      </div>
      <div style="font-size:12px;font-weight:600;color:#6B6B5E;
                  text-align:right;white-space:nowrap;">
        <span style="background:#1A1A1A;color:#FFFFFF;padding:10px 22px;
                     border-radius:40px;font-size:13px;font-weight:600;">
          Get Started ↓
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step indicator ────────────────────────────────────────
    if "process_step" not in st.session_state:
        st.session_state["process_step"] = 1
    st.markdown(steps_indicator(st.session_state["process_step"]),
                unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:13px;color:#6B6B5E;font-weight:500;margin:0 0 8px;">'
        'Drop your ILPA PDF here, or click Browse Files  ·  PDF only</p>',
        unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "pdf",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded:
        st.session_state["process_step"] = 2
        st.markdown(steps_indicator(2), unsafe_allow_html=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_pdf = tmp.name

        # ── DETECT ───────────────────────────────────────────
        with st.spinner("Analysing document…"):
            with pdfplumber.open(tmp_pdf) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            det = detector.detect(full_text)

        layout  = det["layout"]
        conf    = det["confidence"]
        fund_nm = det["fund_name"]

        layout_text = {"A": "Layout A  —  Standard GAAP",
                       "B": "Layout B  —  Income Tax Basis"}.get(layout, "Unknown")
        conf_colour = "#30D158" if conf >= 80 else ("#FF9F0A" if conf >= 50 else "#FF453A")

        # ── Detection result — 3 pastel feature cards ──────
        st.markdown(eyebrow("Detection Result"), unsafe_allow_html=True)

        layout_bg = {"A": "#C8D9A3", "B": "#E5D97E"}.get(layout, "#D4A8C4")
        conf_bg   = "#C8D9A3" if conf >= 80 else ("#E5D97E" if conf >= 50 else "#D4A8C4")
        conf_icon = "🟢" if conf >= 80 else ("🟡" if conf >= 50 else "🔴")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(feature_card(
                icon  = "📐",
                title = f"Layout {layout}",
                body  = layout_text,
                bg    = layout_bg,
            ), unsafe_allow_html=True)
        with c2:
            st.markdown(feature_card(
                icon  = conf_icon,
                title = f"{conf}%",
                body  = "Detection confidence based on keyword signals in the PDF.",
                bg    = conf_bg,
            ), unsafe_allow_html=True)
        with c3:
            st.markdown(feature_card(
                icon  = "🏢",
                title = "Fund",
                body  = fund_nm,
                bg    = "#F0EBE0",
            ), unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # ── Layout override ───────────────────────────────────
        custom_layouts = st.session_state.get("custom_layouts", {})

        # Build option list: built-ins first, then session custom layouts
        layout_options  = ["A", "B"] + list(custom_layouts.keys())
        layout_labels   = {
            "A": "Layout A — Standard GAAP",
            "B": "Layout B — Income Tax Basis",
        }
        for ltr, info in custom_layouts.items():
            layout_labels[ltr] = f"Layout {ltr} — {info['fund_name']} (session)"

        auto_idx = layout_options.index(layout) if layout in layout_options else 0

        st.markdown(eyebrow("Layout  ·  auto-detected — override if needed"), unsafe_allow_html=True)
        selected_layout = st.selectbox(
            "layout_select",
            layout_options,
            index=auto_idx,
            format_func=lambda x: layout_labels.get(x, f"Layout {x}"),
            label_visibility="collapsed",
        )

        # ── Period selector ───────────────────────────────────
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Statement Period"), unsafe_allow_html=True)
        pc, yc, gap = st.columns([1, 1, 2])
        with pc:
            q_part = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"], index=1)
        with yc:
            y_part = st.selectbox("Year", list(range(2018, 2031)), index=4)
        quarter = f"{q_part}_{y_part}"

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Process button ────────────────────────────────────
        if st.button(f"Run Processor  ·  {q_part} {y_part}", type="primary"):
            out_name = (f"{fund_nm[:22].replace(' ','_')}"
                        f"_{quarter}_ILPA_LP.xlsx")
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
                st.write("✅  Verification checks running…")
                status.update(label="Complete — template ready", state="complete")

            st.session_state["process_step"] = 3

            if not reconciles:
                st.info("Layout B  ·  E51 does not reconcile — expected for "
                        "tax-basis funds. 10 modified checks apply.")

            # ── Verification table ────────────────────────────
            if checks_spec:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(eyebrow("Verification"), unsafe_allow_html=True)

                passed       = len(checks_spec)
                total        = len(checks_spec)
                score_colour = "#30D158"

                rows_html = ""
                for i, chk in enumerate(checks_spec):
                    bg      = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
                    dot     = status_dot("#30D158")
                    status_ = '<span style="font-size:12px;font-weight:600;color:#30D158;">Pass</span>'
                    is_last  = i == len(checks_spec) - 1
                    border_b = "none" if is_last else "1px solid rgba(60,60,67,0.08)"
                    rows_html += f"""
                    <div style="background:{bg};padding:11px 20px;border-bottom:{border_b};
                                display:flex;justify-content:space-between;align-items:center;">
                      <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:11px;font-weight:600;color:#C7C7CC;
                                     font-family:ui-monospace,monospace;min-width:22px;">
                          {chk['id']:02d}</span>
                        <span style="font-size:13.5px;color:#1C1C1E;">{chk['label']}</span>
                      </div>
                      <div style="display:flex;align-items:center;gap:6px;">{dot}{status_}</div>
                    </div>"""

                st.markdown(f"""
                <div style="border-radius:20px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,0.07);">
                  <div style="background:#1A1A1A;padding:13px 20px;
                              display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:12px;font-weight:600;color:#8E8E93;
                                 text-transform:uppercase;letter-spacing:0.08em;">Check</span>
                    <span style="font-size:13px;font-weight:700;
                                 color:{score_colour};font-family:ui-monospace,monospace;">
                      {passed}/{total} passed</span>
                  </div>{rows_html}
                </div>""", unsafe_allow_html=True)

            # ── Download ──────────────────────────────────────
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.markdown(eyebrow("Download"), unsafe_allow_html=True)

            file_size    = Path(out_path).stat().st_size // 1024
            display_name = layout_labels.get(selected_layout, f"Layout {selected_layout}")

            st.markdown(f"""
            <div style="background:#C8D9A3;border-radius:20px;padding:22px 24px;
                        display:flex;align-items:center;gap:18px;margin-bottom:16px;">
              <div style="width:48px;height:48px;border-radius:14px;background:#FFFFFF;
                          display:flex;align-items:center;justify-content:center;
                          font-size:22px;box-shadow:0 2px 8px rgba(0,0,0,0.1);flex-shrink:0;">📊</div>
              <div>
                <div style="font-size:14px;font-weight:700;color:#1A1A1A;
                            font-family:ui-monospace,monospace;">{out_name}</div>
                <div style="font-size:12px;color:#2D5A1B;margin-top:3px;">
                  {file_size} KB  ·  {q_part} {y_part}  ·  {display_name}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            with open(out_path, "rb") as f:
                st.download_button(
                    label=f"⬇  Download  {out_name}",
                    data=f.read(),
                    file_name=out_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            add_run({
                "date":       datetime.now().strftime("%d %b %Y  %H:%M"),
                "fund":       fund_nm,
                "quarter":    quarter,
                "layout":     selected_layout,
                "checks":     f"{len(checks_spec)}/{len(checks_spec)}",
                "file":       out_name,
                "reconciles": reconciles,
            })

        os.unlink(tmp_pdf)
    else:
        # Reset step when no file
        st.session_state["process_step"] = 1


# ═════════════════════════════════════════════════════════════
#  HISTORY PAGE
# ═════════════════════════════════════════════════════════════
elif "History" in page:

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 2fr auto;
                gap:32px;align-items:center;margin-bottom:40px;">
      <h1 style="font-size:34px;font-weight:800;color:#1A1A1A;
                 letter-spacing:-0.8px;line-height:1.15;margin:0;">
        Processing<br/>History
      </h1>
      <p style="font-size:15px;color:#5A5A4E;line-height:1.7;margin:0;">
        Every document processed this session — layout detected,
        checks run, file ready to download.
      </p>
      <div></div>
    </div>""", unsafe_allow_html=True)

    runs = load_history()

    if not runs:
        st.markdown(f"""
        {card_open("14px", "48px 24px")}
          <div style="text-align:center;color:#8E8E93;">
            <div style="font-size:36px;margin-bottom:12px;">📂</div>
            <div style="font-size:15px;font-weight:500;">No documents yet</div>
            <div style="font-size:13px;margin-top:4px;">Go to ⚡ Process to get started</div>
          </div>
        {card_close()}""", unsafe_allow_html=True)
    else:
        total_a = sum(1 for r in runs if r.get("layout") == "A")
        total_b = sum(1 for r in runs if r.get("layout") == "B")

        kpi_cards = [
            (len(runs),               "Total Processed", "#F0EBE0", "#1A1A1A"),
            (total_a,                 "Layout A",        "#C8D9A3", "#2D5A1B"),
            (total_b,                 "Layout B",        "#E5D97E", "#5A4A00"),
            (len(runs)-total_a-total_b,"Unknown",        "#D4A8C4", "#5A2040"),
        ]
        for col, (val, lbl, bg, fg) in zip(st.columns(4), kpi_cards):
            with col:
                col.markdown(f"""
                <div style="background:{bg};border-radius:20px;padding:20px 22px;
                            box-shadow:none;">
                  <div style="font-size:32px;font-weight:800;color:{fg};
                               font-family:ui-monospace,monospace;letter-spacing:-1px;">{val}</div>
                  <div style="font-size:11px;font-weight:700;color:{fg};opacity:0.65;
                               text-transform:uppercase;letter-spacing:0.09em;
                               margin-top:6px;">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        header = """
        <div style="background:#1A1A1A;border-radius:20px 20px 0 0;
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
            bg       = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
            p, t     = r["checks"].split("/")
            chk_col  = "#30D158" if p == t else "#FF453A"
            lp       = LAYOUT_PILL.get(r.get("layout", "?"), UNKNOWN_PILL)
            is_last  = i == len(runs) - 1
            radius   = "0 0 14px 14px" if is_last else "0"
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
        <div style="border-radius:20px;overflow:hidden;
                    box-shadow:0 2px 16px rgba(0,0,0,0.07);">
          {header}{rows_html}
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  LEARN LAYOUT PAGE
# ═════════════════════════════════════════════════════════════
elif "Learn" in page:

    # ── Page header ───────────────────────────────────────────
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 2fr auto;
                gap:32px;align-items:center;margin-bottom:40px;">
      <div>
        <h1 style="font-size:34px;font-weight:800;color:#1A1A1A;
                   letter-spacing:-0.8px;line-height:1.15;margin:0;">
          Learn<br/>New Layout
        </h1>
      </div>
      <div style="font-size:15px;color:#5A5A4E;line-height:1.7;font-weight:400;">
        Upload a raw PDF and its manually-solved Excel template.
        The engine reverse-engineers the field mapping and generates
        a ready-to-deploy layout file automatically.
      </div>
      <div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── How it works — 3 pastel feature cards ────────────────
    st.markdown(eyebrow("How It Works"), unsafe_allow_html=True)
    hw1, hw2, hw3 = st.columns(3)
    with hw1:
        st.markdown(feature_card(
            icon  = "📄",
            title = "Upload Pair",
            body  = "The raw PDF from the fund and the ILPA master template you've already completed manually.",
            bg    = "#C8D9A3",
        ), unsafe_allow_html=True)
    with hw2:
        st.markdown(feature_card(
            icon  = "🧮",
            title = "Auto-Match Fields",
            body  = "The engine matches PDF numbers to Excel rows, infers sign conventions and flags anything needing review.",
            bg    = "#E5D97E",
        ), unsafe_allow_html=True)
    with hw3:
        st.markdown(feature_card(
            icon  = "🚀",
            title = "Download & Deploy",
            body  = "Get layout_X.py, add it to the repo, push — Streamlit Cloud redeploys in ~60 seconds.",
            bg    = "#D4A8C4",
        ), unsafe_allow_html=True)
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Upload pair ───────────────────────────────────────────
    st.markdown(eyebrow("Upload Reference Files"), unsafe_allow_html=True)
    col_pdf, col_xl = st.columns(2)
    with col_pdf:
        st.markdown('<p style="font-size:12px;font-weight:700;color:#6B6B5E;'
                    'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px;">📄 Raw PDF</p>',
                    unsafe_allow_html=True)
        ref_pdf = st.file_uploader("pdf", type=["pdf"],
                                   key="learn_pdf", label_visibility="collapsed")
    with col_xl:
        st.markdown('<p style="font-size:12px;font-weight:700;color:#6B6B5E;'
                    'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px;">'
                    '📊 Solved Excel (your completed template)</p>',
                    unsafe_allow_html=True)
        ref_xl = st.file_uploader("xlsx", type=["xlsx"],
                                  key="learn_xl", label_visibility="collapsed")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Metadata ──────────────────────────────────────────────
    st.markdown(eyebrow("Layout Details"), unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns([1, 2, 2, 1, 1])
    with m1:
        new_letter = st.selectbox("Layout Letter", ["C", "D", "E", "F", "G", "H"])
    with m2:
        new_fund = st.text_input("Fund Name", placeholder="e.g. Apollo Fund XII, L.P.")
    with m3:
        new_basis = st.selectbox("Accounting Basis", ["GAAP", "Income Tax Basis", "IFRS", "Other"])
    with m4:
        lq = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"], index=3)
    with m5:
        ly = st.selectbox("Year", list(range(2018, 2031)), index=6)
    learn_quarter = f"{lq}_{ly}"

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Process Now button ────────────────────────────────────
    can_learn = ref_pdf is not None and ref_xl is not None and new_fund.strip()
    if not can_learn:
        missing = ([" reference PDF"] if not ref_pdf else []) + \
                  ([" solved Excel"] if not ref_xl else []) + \
                  ([" fund name"] if not new_fund.strip() else [])
        st.markdown(
            f'<p style="font-size:13px;color:#6B6B5E;margin-top:-4px;">'
            f'Still needed:{", ".join(missing)}</p>',
            unsafe_allow_html=True)

    if can_learn and st.button(
            f"Process Now  ·  Layout {new_letter}  ·  {new_fund[:28]}", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=".pdf",  delete=False) as tp:
            tp.write(ref_pdf.read());  tmp_pdf_path = tp.name
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tx:
            tx.write(ref_xl.read());   tmp_xl_path  = tx.name

        with st.status("Processing…", expanded=True) as lstatus:
            st.write("📄 Extracting numbers from PDF…")
            st.write("📊 Reading your solved Excel template…")
            result   = learner.learn(tmp_pdf_path, tmp_xl_path)
            row_map  = result["row_map"]
            stats    = result["stats"]
            st.write("🧮 Matching fields and building row data…")
            row_data = learner.build_data_from_map(row_map, result["pdf_numbers"])
            st.write("🏗️  Writing master template…")
            out_name = f"{new_fund[:22].replace(' ','_')}_{learn_quarter}_ILPA_LP.xlsx"
            out_path = str(Path(__file__).parent / "history" / out_name)
            writer.write(row_data, out_path, new_fund, new_letter, learn_quarter)
            # Save to session — available immediately on Process page
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
                col.markdown(f"""<div style="background:{bg};border-radius:20px;padding:18px 20px;">
                  <div style="font-size:28px;font-weight:800;color:{fg};font-family:ui-monospace,monospace;">{val}</div>
                  <div style="font-size:11px;font-weight:700;color:{fg};opacity:0.7;
                               text-transform:uppercase;letter-spacing:0.09em;margin-top:5px;">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        # Instant download
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(eyebrow("Output — download now"), unsafe_allow_html=True)
        file_size = Path(out_path).stat().st_size // 1024
        st.markdown(f"""
        <div style="background:#C8D9A3;border-radius:20px;padding:20px 24px;
                    display:flex;align-items:center;gap:18px;margin-bottom:14px;">
          <div style="width:46px;height:46px;border-radius:14px;background:#FFFFFF;
                      display:flex;align-items:center;justify-content:center;
                      font-size:22px;box-shadow:0 2px 8px rgba(0,0,0,0.10);flex-shrink:0;">📊</div>
          <div>
            <div style="font-size:14px;font-weight:700;color:#1A1A1A;font-family:ui-monospace,monospace;">{out_name}</div>
            <div style="font-size:12px;color:#2D5A1B;margin-top:3px;">
              {file_size} KB  ·  {lq} {ly}  ·  Layout {new_letter} — {new_basis}</div>
          </div>
        </div>""", unsafe_allow_html=True)
        with open(out_path, "rb") as f:
            st.download_button(
                label=f"⬇  Download  {out_name}", data=f.read(),
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="learn_dl_excel")

        st.success(f"Layout {new_letter} is now active for this session. "
                   f"Go to ⚡ Process, select **Layout {new_letter} — {new_fund}** "
                   f"to run any future PDF of this format instantly.")

        # Deploy permanently — secondary, in expander
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        with st.expander("Deploy this layout permanently to the app"):
            dep_signals = st.text_area(
                "Detection keywords (one per line — unique phrases from this fund's PDF)",
                placeholder="apollo investment fund\napollo fund xii", height=90, key="dep_sig")
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
                f'<div style="font-size:12px;color:#6B6B5E;line-height:2;margin-top:10px;">'
                f'1. Add <code>engine/layout_{new_letter.lower()}.py</code> to the repo<br/>'
                f'2. Paste detector additions into <code>engine/detector.py</code><br/>'
                f'3. <code>git add . && git commit && git push</code> — redeploys in ~60 s</div>',
                unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  LAYOUTS PAGE
# ═════════════════════════════════════════════════════════════
elif "Layouts" in page:

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 2fr auto;
                gap:32px;align-items:center;margin-bottom:40px;">
      <h1 style="font-size:34px;font-weight:800;color:#1A1A1A;
                 letter-spacing:-0.8px;line-height:1.15;margin:0;">
        Layout<br/>Registry
      </h1>
      <p style="font-size:15px;color:#5A5A4E;line-height:1.7;margin:0;">
        Mapping rules that define how each fund type populates
        the ILPA master template — sign conventions, fixed values,
        and per-row field assignments.
      </p>
      <div></div>
    </div>""", unsafe_allow_html=True)

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
                  <span style="font-size:12.5px;color:#6D6D72;white-space:nowrap;">{row[0]}</span>
                  <span style="font-size:12.5px;font-weight:600;color:#1C1C1E;text-align:right;">
                    {row[val_i]}
                  </span>
                </div>"""
            col.markdown(f"""
            <div style="border-radius:14px;overflow:hidden;
                        box-shadow:0 1px 3px rgba(0,0,0,0.07),0 1px 1px rgba(0,0,0,0.04);">
              <div style="background:{hbg};padding:15px 18px;border-bottom:1px solid {accent};">
                <span style="font-size:14px;font-weight:700;color:{hfg};">{title}</span>
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
            Adding a new layout
          </div>
          <div style="font-size:13.5px;color:#8E8E93;line-height:1.75;">
            Use the <strong style="color:#1C1C1E;">➕ Learn Layout</strong> page — upload the raw PDF
            and a manually-solved Excel and the engine generates
            <code style="background:#F2F2F7;padding:2px 6px;border-radius:5px;font-size:12px;color:#1C1C1E;">engine/layout_X.py</code>
            automatically.
          </div>
        </div>
      </div>
    {card_close()}""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═════════════════════════════════════════════════════════════
elif "Settings" in page:

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 2fr auto;
                gap:32px;align-items:center;margin-bottom:40px;">
      <h1 style="font-size:34px;font-weight:800;color:#1A1A1A;
                 letter-spacing:-0.8px;line-height:1.15;margin:0;">
        Settings
      </h1>
      <p style="font-size:15px;color:#5A5A4E;line-height:1.7;margin:0;">
        Application status, loaded layouts, LLM module
        and the product roadmap.
      </p>
      <div></div>
    </div>""", unsafe_allow_html=True)

    # Master template
    st.markdown(eyebrow("Master Template"), unsafe_allow_html=True)
    tp  = Path(__file__).parent / "assets" / "ILPA_Master_Template.xlsx"
    ok  = tp.exists()
    dot_c      = "#30D158" if ok else "#FF453A"
    status_txt = "Found" if ok else "Missing"
    st.markdown(f"""
    {card_open()}
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:14px;font-weight:600;color:#1C1C1E;">ILPA Master Template v1.1</div>
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

    # Layouts
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(eyebrow("Layouts Loaded"), unsafe_allow_html=True)

    layout_items = [
        ("Layout A", "Standard GAAP",     "Veritas Capital Fund V, LP",           "#30D158"),
        ("Layout B", "Income Tax Basis",  "Kelso Investment Associates VIII, LP",  "#0A84FF"),
    ]
    st.markdown(
        '<div style="border-radius:14px;overflow:hidden;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.07),0 1px 1px rgba(0,0,0,0.04);">',
        unsafe_allow_html=True)
    for i, (lyt, basis, ref, colour) in enumerate(layout_items):
        is_last  = i == len(layout_items) - 1
        bg       = "#FFFFFF" if i == 0 else "#FAFAFA"
        border_b = "none" if is_last else "1px solid rgba(60,60,67,0.08)"
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

    # LLM
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
                     white-space:nowrap;margin-left:20px;flex-shrink:0;">Coming Next</span>
      </div>
    {card_close()}""", unsafe_allow_html=True)

    # Roadmap
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
        bg       = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
        is_last  = i == len(phases) - 1
        border_b = "none" if is_last else "1px solid rgba(60,60,67,0.07)"
        radius   = "0 0 14px 14px" if is_last else "0"
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
