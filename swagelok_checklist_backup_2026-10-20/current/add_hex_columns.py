#!/usr/bin/env python3
"""Add across-flats hex sizes to the Swagelok inventory CSV (hex fork).

Usage:
    python3 add_hex_columns.py [input.csv] [output.csv]

Defaults: swagelok_inventory_checklist.csv -> swagelok_inventory_checklist_hex.csv
The input CSV is only read. Four columns are inserted after Part Number:
Nut Hex (in), Body Hex (in), Hex Note, Hex Source.

All sizes are inches across flats, taken from Swagelok catalogs
"Gaugeable Tube Fittings and Adapter Fittings", MS-01-140 Rev AJ (Feb 2026),
and "VCR Metal Gasket Face Seal Fittings", MS-01-24 Rev X (Sep 2026).
"Not listed" means the catalog gives no hex for that part.
"""

import csv
import sys

CATALOG = "MS-01-140 Rev AJ"
VCR_CATALOG = "MS-01-24 Rev X"
NOT_LISTED = "Not listed"

# Tube nut hex by tube OD (catalog p. 57, Nuts, G flat)
NUT_HEX = {"1/16 in": "5/16", "1/8 in": "7/16", "1/4 in": "9/16"}
NUT_PAGE = 57

# Body hex / flats by basic ordering number (no material prefix, no BT).
# value: (body hex, catalog page, note)
BODY_HEX = {
    # Unions p.14 and reducing unions p.15: no hex given for fractional sizes
    "100-6": (NOT_LISTED, 14, "Catalog gives no body hex for fractional unions"),
    "200-6": (NOT_LISTED, 14, "Catalog gives no body hex for fractional unions"),
    "400-6": (NOT_LISTED, 14, "Catalog gives no body hex for fractional unions"),
    "200-6-1": (NOT_LISTED, 15, "Catalog gives no body hex for reducing unions"),
    "400-6-1": (NOT_LISTED, 15, "Catalog gives no body hex for reducing unions"),
    "400-6-2": (NOT_LISTED, 15, "Catalog gives no body hex for reducing unions"),
    # Union elbows p.33, tees p.40, crosses p.46 (F flat on forged body)
    "100-9": ("3/8", 33, "Body flats"),
    "200-9": ("3/8", 33, "Body flats"),
    "400-9": ("1/2", 33, "Body flats"),
    # Reducing elbow p.36 (tube fitting x tube stub)
    "400-2R-4": ("1/2", 36, "Body flats"),
    "100-3": ("3/8", 40, "Body flats"),
    "200-3": ("3/8", 40, "Body flats"),
    "400-3": ("1/2", 40, "Body flats"),
    "100-4": (NOT_LISTED, 46, "No 1/16 in. union cross in catalog; confirm part exists"),
    "200-4": ("3/8", 46, "Body flats"),
    "400-4": ("1/2", 46, "Body flats"),
    # Bulkhead unions p.16 (F flat applies to body hex and lock nut)
    "100-61": ("5/16", 16, "Lock nut is also 5/16"),
    "200-61": ("1/2", 16, "Lock nut is also 1/2"),
    "400-61": ("5/8", 16, "Lock nut is also 5/8"),
    # Male NPT connectors p.17
    "100-1-1": ("5/16", 17, ""),
    "100-1-2": ("7/16", 17, ""),
    "200-1-2": ("7/16", 17, ""),
    "200-1-4": ("9/16", 17, ""),
    "400-1-2": ("1/2", 17, ""),
    "400-1-4": ("9/16", 17, ""),
    # Female NPT connectors p.26
    "100-7-2": ("9/16", 26, ""),
    "200-7-2": ("9/16", 26, ""),
    "200-7-4": ("3/4", 26, ""),
    "400-7-2": ("9/16", 26, ""),
    "400-7-4": ("3/4", 26, ""),
    # Reducers p.29
    "100-R-2": ("5/16", 29, ""),
    "100-R-4": ("5/16", 29, ""),
    "200-R-4": ("7/16", 29, ""),
    "400-R-2": ("1/2", 29, ""),
}

# VCR to Swagelok tube fitting connectors, MS-01-24.
# value: (tube nut hex, body hex, catalog page, note)
VCR_HEX = {
    "4-VCR-6-200": ("7/16", "5/8", 9, "Body hex is at the male VCR end"),
    "4-VCR-6-400": ("9/16", "5/8", 9, "Body hex is at the male VCR end"),
    "4-WVCR-6-400": ("9/16", "1/2", 13, "VCR female nut is 3/4; welded assembly"),
    "4-VCR-A1-400": ("9/16", "5/8", 9, "Bulkhead nut is also 5/8"),
}

FITTING_CATEGORIES = {"Union", "Reducing Union", "Union Elbow", "Reducing Elbow",
                      "Union Tee", "Union Cross", "Bulkhead Union",
                      "Male Connector", "Female Connector", "Reducer"}


def basic_number(part):
    """'SS-400-1-4BT' -> '400-1-4'."""
    base = part.split("-", 1)[1]
    return base[:-2] if base.endswith("BT") else base


def second_tube(second_end):
    """'1/16 in tube' -> '1/16 in'."""
    return second_end.replace(" tube stub", "").replace(" tube", "").strip()


def hex_for(row):
    """Return (nut hex, body hex, note, source) for one CSV row."""
    cat = row["Category"].strip()
    od = row["Tube OD"].strip()
    part = row["Part Number"].strip()
    desc = row["Description"].strip()

    if cat in FITTING_CATEGORIES:
        basic = basic_number(part)
        if basic not in BODY_HEX:
            sys.exit(f"No body hex entry for {part} ({basic}); add it to BODY_HEX.")
        body, page, note = BODY_HEX[basic]
        nut = NUT_HEX[od]
        if cat == "Reducing Union":
            nut = f"{NUT_HEX[od]} / {NUT_HEX[second_tube(row['Second End'])]}"
        pages = f"pp. {page}, {NUT_PAGE}"
        return nut, body, note, f"{CATALOG} {pages}"

    if cat == "VCR Connector":
        basic = basic_number(part)
        if basic not in VCR_HEX:
            sys.exit(f"No VCR hex entry for {part} ({basic}); add it to VCR_HEX.")
        nut, body, page, note = VCR_HEX[basic]
        return nut, body, note, f"{VCR_CATALOG} p. {page}"
    if cat == "VCR Gasket":
        return "—", "—", "No hex", f"{VCR_CATALOG} p. 17"
    if cat == "Port Connector":
        return ("None", "None",
                "No hex; 1 in. and under supplied without nuts",
                f"{CATALOG} p. 31")
    if cat in ("Cap", "Plug"):
        return (NOT_LISTED, NOT_LISTED, "Catalog gives no hex for caps and plugs",
                f"{CATALOG} p. 32")
    if cat == "Nut" and desc == "Nut":
        return NUT_HEX[od], "—", "", f"{CATALOG} p. {NUT_PAGE}"
    if cat == "Ferrule":
        return "—", "—", "No hex", ""
    sys.exit(f"No hex rule for {part} ({cat} / {desc}).")


def main(src, out):
    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = [r for r in reader if r.get("Part Number", "").strip()]

    new_cols = ["Nut Hex (in)", "Body Hex (in)", "Hex Note", "Hex Source"]
    at = fields.index("Part Number") + 1
    out_fields = fields[:at] + new_cols + fields[at:]

    for r in rows:
        r.update(zip(new_cols, hex_for(r)))

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}: {len(rows)} parts with hex columns")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "swagelok_inventory_checklist.csv",
         sys.argv[2] if len(sys.argv) > 2 else "swagelok_inventory_checklist_hex.csv")
