"""
Template Writer
Copies the master template and populates INPUT cells from a row_data dict.
Leaves all formula cells untouched.
"""

import shutil
import openpyxl
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "ILPA_Master_Template.xlsx"
COL = {"E": 5, "F": 6, "G": 7,
       "H": 8, "I": 9, "J": 10,
       "K": 11, "L": 12, "M": 13}


def write(row_data: dict, output_path: str, fund_name: str = "", layout: str = "") -> str:
    """
    row_data format: {row_int: {"E": val, "F": val, "G": val}}
    None values = leave cell alone (formula stays).
    Returns output_path.
    """
    shutil.copy2(TEMPLATE_PATH, output_path)
    wb = openpyxl.load_workbook(output_path)
    ws = wb["Reporting Template"]

    # Write fund name to B3 if provided
    if fund_name:
        try:
            ws["B3"] = fund_name
        except Exception:
            pass

    for row_num, cols in row_data.items():
        for col_letter, value in cols.items():
            if value is None:
                continue   # leave formula intact
            col_idx = COL.get(col_letter)
            if col_idx is None:
                continue
            try:
                ws.cell(row=row_num, column=col_idx).value = value
            except AttributeError:
                pass       # merged cell slave — skip

    wb.save(output_path)
    return output_path
