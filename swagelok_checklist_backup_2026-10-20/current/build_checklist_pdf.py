#!/usr/bin/env python3
"""Build an illustrated PDF inventory checklist from the Swagelok parts CSV.

Usage:
    python3 build_checklist_pdf.py [input.csv] [output.pdf]

Defaults: swagelok_inventory_checklist.csv -> swagelok_inventory_checklist.pdf
Needs reportlab (pip install reportlab) and fitting_drawings.py in the same
folder. The CSV is only read, never changed.

To add a new part type, give it a drawing in fitting_drawings.DRAWINGS and map
its CSV Description to that drawing in KIND_BY_DESCRIPTION below.
"""

import csv
import sys
from collections import Counter, OrderedDict
from fractions import Fraction

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

import fitting_drawings as fd

BT_SUFFIX = " - Bored Through"

KIND_BY_DESCRIPTION = {
    "Straight Union": "union",
    "Reducing Union": "reducing_union",
    "Union Elbow": "union_elbow",
    "Union Tee": "union_tee",
    "Union Cross": "union_cross",
    "Bulkhead Union": "bulkhead_union",
    "Male Connector (Tube x MNPT)": "male_connector",
    "Female Connector (Tube x FNPT)": "female_connector",
    "Reducer (Fitting x Tube Stub)": "reducer",
    "Port Connector": "port_connector",
    "Reducing Port Connector": "reducing_port_connector",
    "Cap": "cap",
    "Plug": "plug",
    "Nut": "nut",
    "Bulkhead Lock Nut": "bulkhead_lock_nut",
    "Front Ferrule": "front_ferrule",
    "Back Ferrule": "back_ferrule",
    "Ferrule Set (Front + Back)": "ferrule_set",
    "Reducing Elbow (Fitting x Tube Stub)": "reducing_elbow",
    "VCR Male Connector (Male VCR x Tube)": "vcr_male_connector",
    "VCR Female Connector (Female VCR x Tube)": "vcr_female_connector",
    "VCR Bulkhead Connector (Male VCR x Tube)": "vcr_bulkhead_connector",
    "VCR Gasket - Silver Plated": "vcr_gasket",
    "VCR Gasket - Unplated": "vcr_gasket",
    "VCR Retainer Gasket - Silver Plated": "vcr_retainer_gasket",
    "VCR Retainer Gasket - Unplated": "vcr_retainer_gasket",
    "VCR Side-Load Retainer Gasket - Unplated": "vcr_side_load_gasket",
}

TITLE = "Swagelok Tube Fitting Inventory Checklist"

PAGE_W, PAGE_H = letter
MARGIN = 0.5 * inch
TITLE_H = 40
HEADER_BAR_H = 18
BAND_H = 16
ROW_H = 34
IMG_W, IMG_H = 62, 32

COLS = [("", 64), ("Part No.", 78), ("Description", 112), ("Tube OD", 40),
        ("Second End", 62), ("Qty on Hand", 46), ("Min Qty", 38),
        ("Location", 70), ("Check", 30)]  # sums to 540 pt = 7.5 in
COL_WIDTHS = [w for _, w in COLS]
TABLE_W = sum(COL_WIDTHS)

INK = HexColor("#2B2F33")
MUTED = HexColor("#6B747C")
GRID = HexColor("#C9CED3")
BAND = HexColor("#EBEEF1")

PN_STYLE = ParagraphStyle("pn", fontName="Helvetica-Bold", fontSize=8.5,
                          leading=10, textColor=INK)
DESC_STYLE = ParagraphStyle("desc", fontName="Helvetica", fontSize=8,
                            leading=9.4, textColor=INK)
END_STYLE = ParagraphStyle("end", parent=DESC_STYLE, alignment=1)
BAND_STYLE = ParagraphStyle("band", fontName="Helvetica-Bold", fontSize=8.5,
                            leading=10, textColor=INK)


class FittingImage(Flowable):
    def __init__(self, kind, bored_through):
        super().__init__()
        self.kind = kind
        self.bored_through = bored_through

    def wrap(self, aw, ah):
        return IMG_W, IMG_H

    def draw(self):
        fd.draw_fitting(self.canv, self.kind, 0, 0, IMG_W, IMG_H,
                        self.bored_through)


class CheckBox(Flowable):
    SIZE = 11

    def wrap(self, aw, ah):
        return self.SIZE, self.SIZE

    def draw(self):
        self.canv.setStrokeColor(INK)
        self.canv.setLineWidth(0.8)
        self.canv.rect(0, 0, self.SIZE, self.SIZE, stroke=1, fill=0)


class NumberedCanvas(pdfcanvas.Canvas):
    """Canvas that writes 'Page X of Y' once the page count is known."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            self.setFont("Helvetica", 7)
            self.setFillColor(MUTED)
            self.drawRightString(PAGE_W - MARGIN, MARGIN - 14,
                                 f"Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pn_cell(part_number, col_w):
    """Part number on one line, shrinking the font for long numbers."""
    avail = col_w - 10
    size = PN_STYLE.fontSize
    while size > 6 and stringWidth(part_number, PN_STYLE.fontName, size) > avail:
        size -= 0.25
    style = ParagraphStyle("pn_fit", parent=PN_STYLE, fontSize=size, leading=size + 1.5)
    return Paragraph(esc(part_number), style)


def desc_cell(r, main_material):
    """Description, with a ' - variant' suffix and BT shown as a second line."""
    base = r["base_description"]
    variant = ""
    if " - " in base:
        base, variant = base.split(" - ", 1)
    html = esc(base)
    if r["bored_through"]:
        html += "<br/><font size='7.5' color='#1F6FB2'>Bored through</font>"
    mat = r["Material"].strip()
    extra = [variant] if variant else []
    if mat and mat != main_material:
        extra.append(mat)
    if extra:
        html += f"<br/><font size='7.5' color='#6B747C'>{esc('  \u00b7  '.join(extra))}</font>"
    return Paragraph(html, DESC_STYLE)


def tube_size_key(od):
    try:
        return Fraction(od.split()[0])
    except (ValueError, ZeroDivisionError):
        return Fraction(10 ** 6)


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("Part Number", "").strip()]
    for r in rows:
        desc = r["Description"].strip()
        r["bored_through"] = desc.endswith(BT_SUFFIX)
        base = desc[: -len(BT_SUFFIX)] if r["bored_through"] else desc
        if base not in KIND_BY_DESCRIPTION:
            sys.exit(f"No drawing mapped for description {desc!r} "
                     f"(part {r['Part Number']}). Add it to KIND_BY_DESCRIPTION.")
        r["base_description"] = base
        r["kind"] = KIND_BY_DESCRIPTION[base]
    return rows


def build(csv_path, pdf_path):
    rows = load_rows(csv_path)
    counts = Counter(r["Material"].strip() for r in rows if r["Material"].strip())
    main_material = counts.most_common(1)[0][0] if counts else None
    sizes = sorted({r["Tube OD"].strip() for r in rows}, key=tube_size_key)

    subtitle_bits = [f"{len(rows)} parts", "Tube OD " + ", ".join(sizes)]
    if main_material and len(counts) == 1:
        subtitle_bits.append(f"All parts {main_material}")
    elif main_material:
        subtitle_bits.append(f"{main_material} unless noted")
    subtitle = "  ·  ".join(subtitle_bits)

    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r["Category"].strip(), []).append(r)

    story = []
    for category, items in groups.items():
        n = len(items)
        band = Paragraph(f"{esc(category)}  <font name='Helvetica' color='#6B747C'>"
                         f"{n} part{'s' if n != 1 else ''}</font>", BAND_STYLE)
        data = [[band] + [""] * (len(COLS) - 1)]
        for r in items:
            data.append([
                FittingImage(r["kind"], r["bored_through"]),
                pn_cell(r["Part Number"], COL_WIDTHS[1]),
                desc_cell(r, main_material),
                r["Tube OD"],
                Paragraph(esc(r["Second End"]), END_STYLE),
                r.get("Qty On Hand", ""),
                r.get("Min Qty", ""),
                r.get("Location", ""),
                CheckBox(),
            ])
        t = Table(data, colWidths=COL_WIDTHS, repeatRows=1,
                  rowHeights=[BAND_H] + [ROW_H] * n)
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), BAND),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
            ("TEXTCOLOR", (0, 1), (-1, -1), INK),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (3, 1), (6, -1), "CENTER"),
            ("ALIGN", (8, 1), (8, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 1), (0, -1), 1),
            ("RIGHTPADDING", (0, 1), (0, -1), 1),
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("BOX", (0, 0), (-1, -1), 0.6, MUTED),
        ]))
        story.append(KeepTogether([t, Spacer(1, 6)]))

    def draw_page(c, doc):
        c.saveState()
        top = PAGE_H - MARGIN
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(MARGIN, top - 14, TITLE)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN, top - 28, subtitle)

        # fill-in fields, top right
        c.setFont("Helvetica", 8.5)
        c.setFillColor(INK)
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.5)
        right = MARGIN + TABLE_W
        for i, label in enumerate(("Date", "Checked by")):
            y = top - 12 - i * 15
            line_x = right - 110
            c.drawRightString(line_x - 4, y, label)
            c.line(line_x, y - 2, right, y - 2)

        # column header bar
        bar_y = top - TITLE_H - HEADER_BAR_H
        c.setFillColor(INK)
        c.rect(MARGIN, bar_y, TABLE_W, HEADER_BAR_H, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 7.5)
        x = MARGIN
        for label, w in COLS:
            c.drawCentredString(x + w / 2, bar_y + 6, label)
            x += w

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        c.drawString(MARGIN, MARGIN - 14,
                     "Drawings are generic and not to scale. BT = bored through. "
                     "Verify part numbers against the Swagelok catalog before ordering.")
        c.restoreState()

    frame_h = PAGE_H - 2 * MARGIN - TITLE_H - HEADER_BAR_H
    frame = Frame(MARGIN, MARGIN, TABLE_W, frame_h, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(pdf_path, pagesize=letter, title=TITLE,
                          author="", leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN, bottomMargin=MARGIN)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=draw_page)])
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Wrote {pdf_path}: {len(rows)} parts in {len(groups)} categories")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "swagelok_inventory_checklist.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "swagelok_inventory_checklist.pdf"
    build(src, out)
