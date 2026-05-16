#!/bin/bash
# ─────────────────────────────────────────────
#  ILPA Processor — double-click to launch
# ─────────────────────────────────────────────

# Go to the folder this script lives in
cd "$(dirname "$0")"

echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │   ILPA Processor — Starting…    │"
echo "  └─────────────────────────────────┘"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "  ✗  Python 3 not found."
  echo "     Install from https://python.org then try again."
  read -p "  Press Enter to close…"
  exit 1
fi

echo "  ✓  Python found: $(python3 --version)"

# Install / upgrade dependencies silently
echo "  →  Checking dependencies…"
python3 -m pip install streamlit pdfplumber openpyxl pandas --quiet --disable-pip-version-check 2>/dev/null
echo "  ✓  Dependencies ready"

# Find streamlit executable
STREAMLIT=$(python3 -c "import sys,os; print(os.path.join(sys.prefix,'bin','streamlit'))" 2>/dev/null)

if [ ! -f "$STREAMLIT" ]; then
  # Try common user-install paths
  STREAMLIT="$HOME/Library/Python/3.9/bin/streamlit"
fi

if [ ! -f "$STREAMLIT" ]; then
  STREAMLIT=$(which streamlit 2>/dev/null)
fi

if [ -z "$STREAMLIT" ] || [ ! -f "$STREAMLIT" ]; then
  echo "  ✗  Could not find streamlit binary."
  echo "     Run: pip3 install streamlit"
  read -p "  Press Enter to close…"
  exit 1
fi

echo "  ✓  Streamlit found"
echo ""
echo "  → Opening at http://localhost:8501"
echo "  → Keep this window open while using the app"
echo "  → Press Ctrl+C here to stop"
echo ""

# Open browser after short delay
(sleep 3 && open http://localhost:8501) &

# Launch app
"$STREAMLIT" run app.py \
  --server.port 8501 \
  --server.headless false \
  --browser.gatherUsageStats false
