#!/usr/bin/env python3
"""Build the local stockroom app: one self-contained HTML file, no internet needed.

Usage:
    python3 build_inventory_app.py [input_hex.csv] [output.html]

Defaults: swagelok_inventory_checklist_hex.csv -> fittings_stockroom.html
Needs fitting_drawings_hex.py, svg_canvas.py and build_checklist_pdf_hex.py in
the same folder (for the drawings and the description-to-drawing map).

The parts list, hex sizes and drawings are baked into the HTML. Quantities,
locations, mins and notes are saved by the app in the browser and in backup
files, keyed by part number, so rebuilding the HTML after changing the parts
CSV keeps everything already entered.
"""

import datetime
import json
import sys

import build_checklist_pdf_hex as builder
import fitting_drawings_hex as fd
from svg_canvas import SvgCanvas

IMG_W, IMG_H = 70, 40


def svg_for(kind, bt):
    c = SvgCanvas(IMG_W, IMG_H)
    fd.draw_fitting(c, kind, 0, 0, IMG_W, IMG_H, bt)
    return c.svg()


def build(csv_path, out_path):
    rows = builder.load_rows(csv_path)
    catalog = []
    for r in rows:
        catalog.append({
            "pn": r["Part Number"].strip(),
            "cat": r["Category"].strip(),
            "desc": r["base_description"],
            "bt": r["bored_through"],
            "od": r["Tube OD"].strip(),
            "end": r["Second End"].strip(),
            "mat": r["Material"].strip(),
            "nutHex": r["Nut Hex (in)"].strip(),
            "bodyHex": r["Body Hex (in)"].strip(),
            "hexNote": r["Hex Note"].strip(),
            "hexSource": r["Hex Source"].strip(),
            "kind": r["kind"],
        })

    drawings = {}
    for kind in fd.DRAWINGS:
        drawings[kind] = svg_for(kind, False)
    for kind in sorted({p["kind"] for p in catalog if p["bt"]}):
        drawings[kind + "|bt"] = svg_for(kind, True)

    labels = {}
    for desc, kind in builder.KIND_BY_DESCRIPTION.items():
        labels.setdefault(kind, desc.split(" - ")[0])
    kinds = sorted(labels.items(), key=lambda kv: kv[1])

    info = {
        "built": datetime.date.today().isoformat(),
        "parts": len(catalog),
        "sources": "Swagelok catalogs MS-01-140 Rev AJ and MS-01-24 Rev X (VCR)",
    }

    def js(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = (TEMPLATE
            .replace("__CATALOG__", js(catalog))
            .replace("__DRAWINGS__", js(drawings))
            .replace("__KINDS__", js(kinds))
            .replace("__INFO__", js(info)))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {out_path}: {len(catalog)} parts, {len(drawings)} drawings, "
          f"{len(html) // 1024} KB")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fittings Stockroom</title>
<style>
:root {
  --paper: #edf0f2;
  --panel: #ffffff;
  --ink: #1c2226;
  --muted: #5e6a73;
  --rule: #cbd2d8;
  --rule-soft: #e3e7ea;
  --tile: #f3f5f7;
  --accent: #1f6fb2;
  --s116: #6a4fb3;
  --s18: #0e7c8a;
  --s14: #a26b00;
  --sx: #8a949c;
  --out: #b42318;
  --low-bg: #fdecea;
  --ok: #2f7d4a;
  --band: #e6eaed;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #14181b;
    --panel: #1d2327;
    --ink: #e6eaed;
    --muted: #9aa6af;
    --rule: #39434a;
    --rule-soft: #2b3338;
    --band: #252c31;
    --low-bg: #3a1f1c;
    --out: #f07467;
    --ok: #6fc28f;
    --accent: #6aa9e0;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-variant-numeric: tabular-nums;
}
.wrap { max-width: 1400px; margin: 0 auto; padding: 22px 20px 48px; }
header.top { display: flex; flex-wrap: wrap; gap: 16px 24px; align-items: flex-end; justify-content: space-between; }
h1 { margin: 0; font-size: 30px; line-height: 1.1; font-weight: 750; letter-spacing: -0.015em; }
.sub { margin: 6px 0 0; color: var(--muted); max-width: 70ch; }
.actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
button, .btn {
  font: inherit; color: var(--ink); background: var(--panel); border: 1px solid var(--rule);
  border-radius: 7px; padding: 7px 12px; cursor: pointer; line-height: 1.2;
}
button:hover, .btn:hover { border-color: var(--muted); }
button.primary { background: var(--ink); color: var(--panel); border-color: var(--ink); }
button.primary:hover { opacity: .9; }
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 1px;
}
.count-badge {
  display: inline-block; min-width: 20px; padding: 0 6px; margin-left: 6px; border-radius: 10px;
  background: var(--out); color: #fff; font-size: 12px; font-weight: 700; text-align: center;
}
.count-badge.zero { background: var(--rule); color: var(--muted); }
.menu { position: relative; }
.menu > summary { list-style: none; }
.menu > summary::-webkit-details-marker { display: none; }
.menu-list {
  position: absolute; right: 0; top: calc(100% + 6px); z-index: 20; width: 270px;
  background: var(--panel); border: 1px solid var(--rule); border-radius: 9px; padding: 6px;
  box-shadow: 0 8px 24px rgba(20, 30, 40, .16);
}
.menu-list button { display: block; width: 100%; text-align: left; border: 0; border-radius: 6px; padding: 8px 10px; }
.menu-list button:hover { background: var(--band); }
.menu-list hr { border: 0; border-top: 1px solid var(--rule-soft); margin: 6px 4px; }
.menu-list .hint { color: var(--muted); font-size: 12px; padding: 4px 10px 6px; margin: 0; }

.controls { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center; }
.search { flex: 1 1 320px; max-width: 460px; position: relative; }
.search input {
  width: 100%; font: inherit; padding: 9px 12px; border: 1px solid var(--rule); border-radius: 8px;
  background: var(--panel); color: var(--ink);
}
.seg { display: inline-flex; border: 1px solid var(--rule); border-radius: 8px; overflow: hidden; background: var(--panel); }
.seg button { border: 0; border-radius: 0; padding: 7px 11px; border-right: 1px solid var(--rule-soft); }
.seg button:last-child { border-right: 0; }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--panel); }
.seg .dot { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 6px; vertical-align: 0; }
.seg button[aria-pressed="true"] .n { color: inherit; opacity: .8; }
.seg .n { color: var(--muted); margin-left: 5px; }
select {
  font: inherit; padding: 7px 10px; border: 1px solid var(--rule); border-radius: 8px;
  background: var(--panel); color: var(--ink);
}
label.check { display: inline-flex; gap: 6px; align-items: center; color: var(--muted); cursor: pointer; }

.banner {
  margin-top: 16px; padding: 10px 14px; border-radius: 8px; border: 1px solid var(--rule);
  background: var(--panel); display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
}
.banner.warn { border-color: var(--out); background: var(--low-bg); }
.banner p { margin: 0; flex: 1 1 300px; }
[hidden] { display: none !important; }

.table-wrap {
  margin-top: 16px; background: var(--panel); border: 1px solid var(--rule); border-radius: 10px;
  overflow-x: auto;
}
table.parts { width: 100%; min-width: 1120px; border-collapse: collapse; }
.parts thead th {
  position: sticky; top: 0; z-index: 2; background: var(--panel); text-align: left; font-weight: 600;
  font-size: 12.5px; color: var(--muted); padding: 10px 8px; border-bottom: 1px solid var(--rule);
}
.parts th.num, .parts td.num { text-align: center; }
.parts tr.group td {
  background: var(--band); font-weight: 650; padding: 7px 12px; border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
}
.parts tr.group .n { font-weight: 400; color: var(--muted); margin-left: 8px; }
.parts tr.part td { padding: 6px 8px; border-bottom: 1px solid var(--rule-soft); vertical-align: middle; }
.parts tr.part.is-hidden td { opacity: .5; }
.parts tr.part.reorder td.status { }
td.tab { width: 6px; padding: 0 !important; }
td.tab span { display: block; width: 6px; min-height: 52px; height: 100%; }
.s116 { background: var(--s116); } .s18 { background: var(--s18); } .s14 { background: var(--s14); } .sx { background: var(--sx); }
td.pic { width: 104px; }
.pic .tile { width: 96px; height: 55px; background: var(--tile); border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.pic .tile svg { width: 96px; height: 55px; display: block; }
.pic .tile svg line[stroke="#1f6fb2"] { vector-effect: non-scaling-stroke; stroke-width: 1.6px; stroke-dasharray: 5 3; }
.pic .tile.empty { color: #8a949c; font-size: 11px; }
td.id { min-width: 210px; }
.pn { font-weight: 700; font-size: 15px; white-space: nowrap; }
.desc { color: var(--ink); }
.desc .bt { color: var(--accent); font-weight: 600; margin-left: 6px; font-size: 12.5px; }
.meta { color: var(--muted); font-size: 12.5px; }
.more-btn { border: 0; background: none; padding: 2px 0; color: var(--accent); font-size: 12.5px; }
.more-btn:hover { text-decoration: underline; }
td.size { white-space: nowrap; font-weight: 600; }
td.end { color: var(--ink); min-width: 110px; }
td.hex { white-space: nowrap; }
.hex .h { display: grid; grid-template-columns: 34px auto; column-gap: 4px; font-size: 13px; }
.hex .h span:nth-child(odd) { color: var(--muted); font-size: 12px; }
.hex .na { color: var(--muted); }
input.cell, textarea.cell {
  font: inherit; color: var(--ink); background: var(--panel); border: 1px solid var(--rule);
  border-radius: 6px; padding: 6px 8px; width: 100%;
}
input.cell::placeholder { color: #9aa4ab; }
input.cell[type=number] { text-align: center; -moz-appearance: textfield; }
input.cell[type=number]::-webkit-inner-spin-button, input.cell[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
td.loc { width: 120px; }
td.min, td.order { width: 74px; }
td.onhand { width: 128px; }
.stepper { display: grid; grid-template-columns: 30px 1fr 30px; gap: 4px; }
.stepper button { padding: 0; height: 32px; font-size: 16px; font-weight: 600; border-radius: 6px; }
td.status { width: 118px; }
.chip { display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 12.5px; font-weight: 650; white-space: nowrap; }
.chip.out { background: var(--out); color: #fff; }
.chip.low { background: var(--low-bg); color: var(--out); border: 1px solid var(--out); }
.chip.ok { color: var(--ok); border: 1px solid currentColor; }
.chip.nomin, .chip.uncounted, .chip.unset { color: var(--muted); border: 1px dashed var(--rule); }
.counted { display: block; color: var(--muted); font-size: 11.5px; margin-top: 3px; white-space: nowrap; }
tr.detail td { background: var(--tile); padding: 12px 16px 14px 120px; border-bottom: 1px solid var(--rule-soft); }
@media (prefers-color-scheme: dark) { tr.detail td { background: #232a2f; } }
.detail-grid { display: grid; grid-template-columns: minmax(240px, 1fr) minmax(260px, 1.2fr); gap: 12px 28px; }
.detail-grid h3 { margin: 0 0 4px; font-size: 13px; color: var(--muted); font-weight: 600; }
.detail-grid p { margin: 0 0 6px; }
.detail-actions { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.danger { color: var(--out); border-color: var(--out); }
.empty-state { padding: 40px 20px; text-align: center; color: var(--muted); }
footer.foot { margin-top: 18px; color: var(--muted); font-size: 12.5px; display: flex; gap: 8px 24px; flex-wrap: wrap; justify-content: space-between; }
footer.foot p { margin: 0; max-width: 90ch; }

dialog {
  border: 1px solid var(--rule); border-radius: 12px; padding: 0; background: var(--panel); color: var(--ink);
  width: min(880px, calc(100vw - 32px)); max-height: calc(100vh - 48px);
}
dialog::backdrop { background: rgba(15, 20, 25, .45); }
.dlg-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 18px 20px 10px; }
.dlg-head h2 { margin: 0; font-size: 20px; }
.dlg-body { padding: 4px 20px 12px; overflow: auto; max-height: calc(100vh - 200px); }
.dlg-foot { display: flex; gap: 8px; justify-content: flex-end; padding: 12px 20px 18px; border-top: 1px solid var(--rule-soft); flex-wrap: wrap; }
table.simple { width: 100%; border-collapse: collapse; }
.simple th, .simple td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--rule-soft); }
.simple th { color: var(--muted); font-weight: 600; font-size: 12.5px; }
.simple td.num, .simple th.num { text-align: center; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; }
.form-grid label { display: grid; gap: 4px; font-size: 13px; color: var(--muted); }
.form-grid label.wide { grid-column: 1 / -1; }
.form-grid input, .form-grid select { font: inherit; color: var(--ink); padding: 8px 10px; border: 1px solid var(--rule); border-radius: 7px; background: var(--panel); }
.form-error { color: var(--out); margin: 8px 0 0; }
.toast {
  position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%); background: var(--ink); color: var(--panel);
  padding: 9px 16px; border-radius: 8px; font-weight: 600; z-index: 50; box-shadow: 0 6px 18px rgba(0,0,0,.2);
}
#print-area { display: none; }

@media (max-width: 720px) {
  h1 { font-size: 25px; }
  .wrap { padding: 16px 12px 40px; }
  .form-grid { grid-template-columns: 1fr; }
  tr.detail td { padding-left: 16px; }
  .detail-grid { grid-template-columns: 1fr; }
}

@media print {
  @page { size: letter; margin: 0.45in; }
  body { background: #fff; color: #000; font-size: 10.5px; }
  body > *:not(#print-area) { display: none !important; }
  #print-area { display: block; }
  #print-area h1 { font-size: 17px; margin: 0 0 2px; }
  #print-area .psub { margin: 0 0 10px; color: #444; }
  #print-area table { width: 100%; border-collapse: collapse; page-break-inside: auto; }
  #print-area tr { page-break-inside: avoid; }
  #print-area th { text-align: left; font-size: 9.5px; color: #333; border-bottom: 1.2px solid #333; padding: 4px; }
  #print-area td { border-bottom: 0.6px solid #bbb; padding: 3px 4px; vertical-align: middle; }
  #print-area td.nw { white-space: nowrap; }
  #print-area .hx { color: #555; font-size: 9px; }
  #print-area tr.pg { page-break-after: avoid; break-after: avoid; }
  #print-area tr.pg td { background: #e9ecef; font-weight: 700; padding: 4px 6px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  #print-area .ptile svg { width: 64px; height: 37px; display: block; }
  #print-area .box { display: inline-block; width: 44px; height: 18px; border: 1px solid #555; }
  #print-area .sq { display: inline-block; width: 12px; height: 12px; border: 1px solid #555; }
  #print-area .num { text-align: center; }
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <h1>Fittings stockroom</h1>
      <p class="sub" id="subtitle"></p>
    </div>
    <div class="actions">
      <button type="button" id="btn-reorder">Reorder list<span class="count-badge zero" id="reorder-count">0</span></button>
      <button type="button" id="btn-add">Add part</button>
      <details class="menu" id="backup-menu">
        <summary class="btn">Backup and print</summary>
        <div class="menu-list" role="menu">
          <button type="button" data-cmd="backup-save">Save backup file</button>
          <button type="button" data-cmd="backup-restore">Restore from backup file…</button>
          <hr>
          <button type="button" data-cmd="csv-export">Export spreadsheet (CSV)</button>
          <button type="button" data-cmd="csv-import">Import quantities from CSV…</button>
          <p class="hint">Fills Location, Min Qty, Qty On Hand, Order Qty and Notes by part number.</p>
          <hr>
          <button type="button" data-cmd="print-count">Print count sheet for this view</button>
          <button type="button" data-cmd="print-reorder">Print reorder list</button>
        </div>
      </details>
      <input type="file" id="file-backup" accept=".json,application/json" hidden>
      <input type="file" id="file-csv" accept=".csv,text/csv" hidden>
    </div>
  </header>

  <div class="banner warn" id="storage-warn" hidden>
    <p><strong>This browser isn't keeping your changes.</strong> Save a backup file before you close this page, or open the file in a different browser.</p>
    <button type="button" data-cmd="backup-save">Save backup file</button>
  </div>
  <div class="banner" id="backup-nudge" hidden>
    <p id="backup-nudge-text"></p>
    <button type="button" data-cmd="backup-save">Save backup file</button>
  </div>

  <div class="controls">
    <div class="search">
      <input type="search" id="q" placeholder="Search part number, description, bin, note" aria-label="Search parts" autocomplete="off">
    </div>
    <div class="seg" id="size-seg" role="group" aria-label="Tube size"></div>
    <select id="cat" aria-label="Category"></select>
  </div>
  <div class="controls">
    <div class="seg" id="show-seg" role="group" aria-label="Show"></div>
    <label class="check"><input type="checkbox" id="show-hidden"> Show hidden parts</label>
  </div>

  <div class="table-wrap">
    <table class="parts" id="parts">
      <thead>
        <tr>
          <th aria-label="Size color"></th>
          <th>Drawing</th>
          <th>Part</th>
          <th>Size</th>
          <th>Other end</th>
          <th>Hex (in)</th>
          <th>Location</th>
          <th class="num">Min</th>
          <th class="num">On hand</th>
          <th class="num">Order qty</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
    <div class="empty-state" id="empty" hidden></div>
  </div>

  <footer class="foot">
    <p id="save-status"></p>
    <p id="build-info"></p>
  </footer>
</div>

<dialog id="dlg-reorder" aria-labelledby="reorder-title">
  <div class="dlg-head">
    <h2 id="reorder-title">Reorder list</h2>
    <span class="meta" id="reorder-meta"></span>
  </div>
  <div class="dlg-body" id="reorder-body"></div>
  <div class="dlg-foot">
    <button type="button" data-cmd="reorder-copy">Copy list</button>
    <button type="button" data-cmd="reorder-csv">Export CSV</button>
    <button type="button" data-cmd="print-reorder">Print</button>
    <button type="button" class="primary" data-close>Done</button>
  </div>
</dialog>

<dialog id="dlg-add" aria-labelledby="add-title">
  <form id="add-form" method="dialog">
    <div class="dlg-head"><h2 id="add-title">Add a part</h2></div>
    <div class="dlg-body">
      <div class="form-grid">
        <label>Part number<input name="pn" required autocomplete="off" placeholder="SS-400-6"></label>
        <label>Category<input name="cat" list="cat-list" required placeholder="Union"></label>
        <label class="wide">Description<input name="desc" required placeholder="Straight Union"></label>
        <label>Tube OD<input name="od" list="od-list" placeholder="1/4 in"></label>
        <label>Other end<input name="end" placeholder="1/4 in tube"></label>
        <label>Material<input name="mat" value="316 SS"></label>
        <label>Drawing<select name="kind" id="kind-select"></select></label>
        <label>Nut hex (in)<input name="nutHex" placeholder="9/16"></label>
        <label>Body hex (in)<input name="bodyHex" placeholder="1/2"></label>
      </div>
      <datalist id="cat-list"></datalist>
      <datalist id="od-list"><option value="1/16 in"><option value="1/8 in"><option value="1/4 in"></datalist>
      <p class="form-error" id="add-error" hidden></p>
    </div>
    <div class="dlg-foot">
      <button type="button" data-close>Cancel</button>
      <button type="submit" class="primary">Add part</button>
    </div>
  </form>
</dialog>

<dialog id="dlg-confirm" aria-labelledby="confirm-title">
  <div class="dlg-head"><h2 id="confirm-title"></h2></div>
  <div class="dlg-body"><p id="confirm-text"></p></div>
  <div class="dlg-foot">
    <button type="button" data-close>Cancel</button>
    <button type="button" class="primary" id="confirm-ok"></button>
  </div>
</dialog>

<div id="print-area"></div>
<div class="toast" id="toast" hidden role="status"></div>

<script>
"use strict";
const CATALOG = __CATALOG__;
const DRAWINGS = __DRAWINGS__;
const KINDS = __KINDS__;
const INFO = __INFO__;
const STORE_KEY = "fittings-stockroom/v1";
const SIZES = [["all", "All sizes"], ["1/16 in", "1/16"], ["1/8 in", "1/8"], ["1/4 in", "1/4"]];
const SHOWS = [["all", "All parts"], ["reorder", "Needs reorder"], ["nomin", "No min yet"], ["uncounted", "Not counted"]];
const STATUS_LABEL = { out: "Out", low: "Low", ok: "OK", nomin: "No min", uncounted: "Not counted", unset: "Not set up" };

const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------------------------------------------------------------- state
let storageOK = true;
function emptyState() { return { version: 1, items: {}, custom: [], hidden: [], lastBackup: null, updated: null }; }
function normalize(s) {
  const d = emptyState();
  if (!s || typeof s !== "object") return d;
  d.items = s.items && typeof s.items === "object" ? s.items : {};
  d.custom = Array.isArray(s.custom) ? s.custom.filter((p) => p && p.pn) : [];
  d.hidden = Array.isArray(s.hidden) ? s.hidden : [];
  d.lastBackup = s.lastBackup || null;
  d.updated = s.updated || null;
  return d;
}
function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? normalize(JSON.parse(raw)) : emptyState();
  } catch (e) { storageOK = false; return emptyState(); }
}
let state = load();
let saveTimer = null;
function saveNow() {
  state.updated = new Date().toISOString();
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); storageOK = true; }
  catch (e) { storageOK = false; }
  renderSaveStatus();
}
function save() { clearTimeout(saveTimer); saveTimer = setTimeout(saveNow, 250); }
window.addEventListener("beforeunload", () => { if (saveTimer) { clearTimeout(saveTimer); saveNow(); } });

const blankItem = () => ({ loc: "", min: null, onHand: null, orderQty: null, counted: null, note: "" });
const getItem = (pn) => state.items[pn] || blankItem();
function editItem(pn) { if (!state.items[pn]) state.items[pn] = blankItem(); return state.items[pn]; }
const toNum = (v) => { if (v === "" || v === null || v === undefined) return null; const n = Math.floor(Number(v)); return Number.isFinite(n) && n >= 0 ? n : null; };

function statusOf(it) {
  const { min, onHand } = it;
  if (onHand == null) return min == null ? "unset" : "uncounted";
  if (min == null) return onHand === 0 ? "out" : "nomin";
  if (onHand === 0 && min > 0) return "out";
  if (onHand < min) return "low";
  return "ok";
}
const needsOrder = (st) => st === "out" || st === "low";
function orderQtyOf(it) {
  if (it.orderQty != null) return it.orderQty;
  if (it.min != null) return Math.max(it.min - (it.onHand || 0), 1);
  return null;
}

// ---------------------------------------------------------------- parts
function allParts() { return CATALOG.concat(state.custom.map((p) => ({ ...p, custom: true }))); }
const isHidden = (pn) => state.hidden.includes(pn);
function sizeClass(od) { return { "1/16 in": "s116", "1/8 in": "s18", "1/4 in": "s14" }[od] || "sx"; }
function drawingFor(p) {
  if (!p.kind) return "";
  return DRAWINGS[p.kind + (p.bt ? "|bt" : "")] || DRAWINGS[p.kind] || "";
}
const hexText = (v) => {
  const t = String(v || "").trim();
  if (!t || t === "—") return '<span class="na">—</span>';
  if (t.toLowerCase() === "not listed") return '<span class="na" title="Not listed in the Swagelok catalog">n/l</span>';
  if (t.toLowerCase() === "none") return '<span class="na">none</span>';
  return esc(t);
};

// ---------------------------------------------------------------- view state
const ui = { q: "", size: "all", cat: "all", show: "all", showHidden: false, open: new Set() };
function matches(p, it, ignoreShow = false) {
  if (!ui.showHidden && isHidden(p.pn)) return false;
  if (ui.size !== "all" && p.od !== ui.size) return false;
  if (ui.cat !== "all" && p.cat !== ui.cat) return false;
  if (!ignoreShow) {
    const st = statusOf(it);
    if (ui.show === "reorder" && !needsOrder(st)) return false;
    if (ui.show === "nomin" && it.min != null) return false;
    if (ui.show === "uncounted" && it.onHand != null) return false;
  }
  if (ui.q) {
    const hay = [p.pn, p.desc, p.cat, p.end, p.od, p.mat, it.loc, it.note, p.bt ? "bored through bt" : ""].join(" ").toLowerCase();
    if (!ui.q.split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}
function visibleParts() { return allParts().filter((p) => matches(p, getItem(p.pn))); }

// ---------------------------------------------------------------- render
function renderControls() {
  const parts = allParts().filter((p) => ui.showHidden || !isHidden(p.pn));
  $("#size-seg").innerHTML = SIZES.map(([v, label]) => {
    const dot = v === "all" ? "" : `<span class="dot ${sizeClass(v)}"></span>`;
    return `<button type="button" data-size="${esc(v)}" aria-pressed="${ui.size === v}">${dot}${esc(label)}</button>`;
  }).join("");
  const counts = { all: 0, reorder: 0, nomin: 0, uncounted: 0 };
  for (const p of parts) {
    const it = getItem(p.pn);
    if (!matches(p, it, true)) continue;
    counts.all++;
    if (needsOrder(statusOf(it))) counts.reorder++;
    if (it.min == null) counts.nomin++;
    if (it.onHand == null) counts.uncounted++;
  }
  $("#show-seg").innerHTML = SHOWS.map(([v, label]) =>
    `<button type="button" data-show="${v}" aria-pressed="${ui.show === v}">${esc(label)}<span class="n">${counts[v]}</span></button>`).join("");
  const cats = [...new Set(parts.map((p) => p.cat))];
  if (ui.cat !== "all" && !cats.includes(ui.cat)) ui.cat = "all";
  $("#cat").innerHTML = `<option value="all">All categories</option>` +
    cats.map((c) => `<option value="${esc(c)}"${ui.cat === c ? " selected" : ""}>${esc(c)}</option>`).join("");
  $("#cat-list").innerHTML = [...new Set(allParts().map((p) => p.cat))].map((c) => `<option value="${esc(c)}">`).join("");
  renderReorderBadge();
}
function renderReorderBadge() {
  const n = reorderParts().length;
  const b = $("#reorder-count");
  b.textContent = n;
  b.classList.toggle("zero", n === 0);
}

function rowHTML(p) {
  const it = getItem(p.pn);
  const st = statusOf(it);
  const svg = drawingFor(p);
  const tile = svg ? `<div class="tile">${svg}</div>` : `<div class="tile empty">No drawing</div>`;
  const meta = [];
  if (p.mat && p.mat !== "316 SS") meta.push(esc(p.mat));
  if (p.custom) meta.push("Added by you");
  if (isHidden(p.pn)) meta.push("Hidden");
  const open = ui.open.has(p.pn);
  const counted = it.counted ? `<span class="counted">Counted ${esc(fmtDate(it.counted))}</span>` : "";
  let html = `<tr class="part${isHidden(p.pn) ? " is-hidden" : ""}" data-pn="${esc(p.pn)}">
    <td class="tab"><span class="${sizeClass(p.od)}"></span></td>
    <td class="pic">${tile}</td>
    <td class="id">
      <div class="pn">${esc(p.pn)}</div>
      <div class="desc">${esc(p.desc)}${p.bt ? '<span class="bt">Bored through</span>' : ""}</div>
      ${meta.length ? `<div class="meta">${meta.join(", ")}</div>` : ""}
      <button type="button" class="more-btn" data-act="toggle" aria-expanded="${open}">${open ? "Hide details" : (it.note ? "Details and note" : "Details")}</button>
    </td>
    <td class="size">${esc(p.od || "—")}</td>
    <td class="end">${esc(p.end || "—")}</td>
    <td class="hex"><div class="h"><span>Nut</span><span>${hexText(p.nutHex)}</span><span>Body</span><span>${hexText(p.bodyHex)}</span></div></td>
    <td class="loc"><input class="cell" data-field="loc" value="${esc(it.loc)}" placeholder="Bin" aria-label="Location for ${esc(p.pn)}"></td>
    <td class="min num"><input class="cell" type="number" min="0" inputmode="numeric" data-field="min" value="${it.min ?? ""}" aria-label="Min qty for ${esc(p.pn)}"></td>
    <td class="onhand num"><div class="stepper">
      <button type="button" data-act="dec" aria-label="One less ${esc(p.pn)}">−</button>
      <input class="cell" type="number" min="0" inputmode="numeric" data-field="onHand" value="${it.onHand ?? ""}" aria-label="On hand for ${esc(p.pn)}">
      <button type="button" data-act="inc" aria-label="One more ${esc(p.pn)}">+</button>
    </div></td>
    <td class="order num"><input class="cell" type="number" min="0" inputmode="numeric" data-field="orderQty" value="${it.orderQty ?? ""}" placeholder="${orderQtyPlaceholder(it)}" aria-label="Order qty for ${esc(p.pn)}"></td>
    <td class="status"><span class="chip ${st}">${STATUS_LABEL[st]}</span>${counted}</td>
  </tr>`;
  if (open) html += detailHTML(p, it);
  return html;
}
function orderQtyPlaceholder(it) { const q = it.min != null ? Math.max(it.min - (it.onHand || 0), 1) : null; return q == null ? "" : `auto ${q}`; }
function detailHTML(p, it) {
  const hexBits = [];
  if (p.hexNote) hexBits.push(`<p>${esc(p.hexNote)}</p>`);
  if (p.hexSource) hexBits.push(`<p class="meta">Source: ${esc(p.hexSource)}</p>`);
  const hideBtn = isHidden(p.pn)
    ? `<button type="button" data-act="unhide">Show this part again</button>`
    : `<button type="button" data-act="hide">Hide this part</button>`;
  const delBtn = p.custom ? `<button type="button" class="danger" data-act="delete">Delete this part</button>` : "";
  return `<tr class="detail" data-pn="${esc(p.pn)}"><td colspan="11"><div class="detail-grid">
    <div>
      <h3>About this part</h3>
      <p>${esc(p.desc)}${p.bt ? ", bored through" : ""}. ${esc(p.od || "")}${p.end && p.end !== "—" ? " to " + esc(p.end) : ""}. ${esc(p.mat || "")}</p>
      ${hexBits.join("")}
      <div class="detail-actions">${hideBtn}${delBtn}</div>
    </div>
    <div>
      <h3><label for="note-${esc(p.pn)}">Note</label></h3>
      <textarea class="cell" id="note-${esc(p.pn)}" rows="3" data-field="note" placeholder="Supplier, lead time, where else it's stored…">${esc(it.note)}</textarea>
    </div>
  </div></td></tr>`;
}

function renderRows() {
  const parts = visibleParts();
  const groups = new Map();
  for (const p of parts) { if (!groups.has(p.cat)) groups.set(p.cat, []); groups.get(p.cat).push(p); }
  let html = "";
  for (const [cat, list] of groups) {
    html += `<tr class="group"><td colspan="11">${esc(cat)}<span class="n">${list.length} part${list.length === 1 ? "" : "s"}</span></td></tr>`;
    html += list.map(rowHTML).join("");
  }
  $("#rows").innerHTML = html;
  const empty = $("#empty");
  if (!parts.length) {
    empty.hidden = false;
    empty.innerHTML = ui.show === "reorder" && !ui.q
      ? "Nothing needs reordering in this view. Parts show up here once their on-hand count drops below their min."
      : `No parts match this view. <button type="button" data-cmd="clear-filters">Clear search and filters</button>`;
  } else empty.hidden = true;
}
function render() { renderControls(); renderRows(); renderSaveStatus(); }

function updateRowStatus(pn) {
  const row = document.querySelector(`tr.part[data-pn="${CSS.escape(pn)}"]`);
  if (!row) return;
  const it = getItem(pn);
  const st = statusOf(it);
  const counted = it.counted ? `<span class="counted">Counted ${esc(fmtDate(it.counted))}</span>` : "";
  row.querySelector("td.status").innerHTML = `<span class="chip ${st}">${STATUS_LABEL[st]}</span>${counted}`;
  const oq = row.querySelector('input[data-field="orderQty"]');
  if (oq) oq.placeholder = orderQtyPlaceholder(it);
  renderControlsCountsOnly();
}
function renderControlsCountsOnly() {
  // refresh filter counts and the reorder badge without rebuilding the table rows
  renderControls();
}

function fmtDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: d.getFullYear() === new Date().getFullYear() ? undefined : "numeric" });
}
function renderSaveStatus() {
  const el = $("#save-status");
  $("#storage-warn").hidden = storageOK;
  const when = state.updated ? `Last change saved ${fmtDate(state.updated)} at ${new Date(state.updated).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}.` : "No changes yet.";
  const backup = state.lastBackup ? `Last backup file saved ${fmtDate(state.lastBackup)}.` : "No backup file saved yet.";
  el.textContent = storageOK ? `Changes save automatically in this browser. ${when} ${backup}` : `Changes are not being saved in this browser. ${backup}`;
  const hasData = Object.keys(state.items).length || state.custom.length || state.hidden.length;
  const days = state.lastBackup ? (Date.now() - new Date(state.lastBackup)) / 864e5 : Infinity;
  const nudge = $("#backup-nudge");
  if (storageOK && hasData && days > 7 && state.updated && (!state.lastBackup || new Date(state.updated) > new Date(state.lastBackup))) {
    nudge.hidden = false;
    $("#backup-nudge-text").textContent = state.lastBackup
      ? `Your last backup file is from ${fmtDate(state.lastBackup)}. Save a new one so this week's counts aren't only in this browser.`
      : "Your counts are only saved in this browser so far. Save a backup file and keep it with this app.";
  } else nudge.hidden = true;
}
$("#subtitle").textContent = `Swagelok tube fittings, 1/16 to 1/4 in, ${CATALOG.length} catalog parts. Set a bin, a min and an on-hand count for each part; anything below its min goes on the reorder list.`;
$("#build-info").textContent = `Parts list built ${INFO.built}. Hex sizes from ${INFO.sources}. Drawings are generic, not to scale.`;

// ---------------------------------------------------------------- events: table
const rowsEl = $("#rows");
rowsEl.addEventListener("input", (e) => {
  const el = e.target;
  const field = el.dataset.field;
  if (!field) return;
  const pn = el.closest("tr").dataset.pn;
  const it = editItem(pn);
  if (field === "loc" || field === "note") it[field] = el.value;
  else {
    it[field] = toNum(el.value);
    if (field === "onHand") it.counted = it.onHand == null ? null : new Date().toISOString();
  }
  save();
  if (field !== "loc" && field !== "note") updateRowStatus(pn);
});
rowsEl.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const pn = btn.closest("tr").dataset.pn;
  const act = btn.dataset.act;
  if (act === "inc" || act === "dec") {
    const it = editItem(pn);
    const cur = it.onHand ?? 0;
    it.onHand = act === "inc" ? cur + 1 : Math.max(cur - 1, 0);
    it.counted = new Date().toISOString();
    const input = btn.parentElement.querySelector("input");
    input.value = it.onHand;
    save(); updateRowStatus(pn);
  } else if (act === "toggle") {
    ui.open.has(pn) ? ui.open.delete(pn) : ui.open.add(pn);
    renderRows();
    const again = document.querySelector(`tr.part[data-pn="${CSS.escape(pn)}"] [data-act="toggle"]`);
    if (again) again.focus();
  } else if (act === "hide") {
    if (!state.hidden.includes(pn)) state.hidden.push(pn);
    ui.open.delete(pn); saveNow(); render(); toast(`${pn} hidden. Turn on "Show hidden parts" to bring it back.`);
  } else if (act === "unhide") {
    state.hidden = state.hidden.filter((x) => x !== pn); saveNow(); render(); toast(`${pn} is back in the list.`);
  } else if (act === "delete") {
    confirmAction(`Delete ${pn}?`, `This removes the part you added and its counts. It can't be undone unless you restore a backup file.`, "Delete part", () => {
      state.custom = state.custom.filter((p) => p.pn !== pn);
      delete state.items[pn];
      state.hidden = state.hidden.filter((x) => x !== pn);
      ui.open.delete(pn); saveNow(); render(); toast(`${pn} deleted.`);
    });
  }
});
rowsEl.addEventListener("keydown", (e) => {
  const el = e.target;
  if (e.key !== "Enter" || !el.matches("input.cell")) return;
  e.preventDefault();
  const field = el.dataset.field;
  const inputs = [...rowsEl.querySelectorAll(`tr.part input[data-field="${field}"]`)];
  const i = inputs.indexOf(el);
  const next = inputs[i + (e.shiftKey ? -1 : 1)];
  if (next) { next.focus(); next.select && next.select(); }
  else el.blur();
});
rowsEl.addEventListener("focusin", (e) => { if (e.target.matches('input.cell[type="number"]')) e.target.select(); });

// ---------------------------------------------------------------- events: controls
$("#q").addEventListener("input", (e) => { ui.q = e.target.value.trim().toLowerCase(); renderControls(); renderRows(); });
$("#size-seg").addEventListener("click", (e) => { const b = e.target.closest("button[data-size]"); if (!b) return; ui.size = b.dataset.size; render(); });
$("#show-seg").addEventListener("click", (e) => { const b = e.target.closest("button[data-show]"); if (!b) return; ui.show = b.dataset.show; render(); });
$("#cat").addEventListener("change", (e) => { ui.cat = e.target.value; render(); });
$("#show-hidden").addEventListener("change", (e) => { ui.showHidden = e.target.checked; render(); });
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-cmd]");
  if (b) { const menu = $("#backup-menu"); menu.open = false; runCommand(b.dataset.cmd); }
  const closer = e.target.closest("[data-close]");
  if (closer) closer.closest("dialog").close();
  const menu = $("#backup-menu");
  if (menu.open && !e.target.closest("#backup-menu")) menu.open = false;
});
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !e.target.matches("input, textarea, select")) { e.preventDefault(); $("#q").focus(); }
  if (e.key === "Escape" && $("#backup-menu").open) $("#backup-menu").open = false;
});

function runCommand(cmd) {
  if (cmd === "backup-save") saveBackup();
  else if (cmd === "backup-restore") $("#file-backup").click();
  else if (cmd === "csv-export") exportCSV();
  else if (cmd === "csv-import") $("#file-csv").click();
  else if (cmd === "print-count") printCount();
  else if (cmd === "print-reorder") printReorder();
  else if (cmd === "reorder-copy") copyReorder();
  else if (cmd === "reorder-csv") exportReorderCSV();
  else if (cmd === "clear-filters") { ui.q = ""; $("#q").value = ""; ui.size = "all"; ui.cat = "all"; ui.show = "all"; render(); }
}

// ---------------------------------------------------------------- reorder
function reorderParts() {
  return allParts().filter((p) => !isHidden(p.pn) && needsOrder(statusOf(getItem(p.pn))));
}
function reorderRows() {
  return reorderParts().map((p) => { const it = getItem(p.pn); return { p, it, qty: orderQtyOf(it) }; });
}
$("#btn-reorder").addEventListener("click", () => {
  const list = reorderRows();
  $("#reorder-meta").textContent = list.length ? `${list.length} part${list.length === 1 ? "" : "s"} below min` : "";
  $("#reorder-body").innerHTML = list.length ? `<table class="simple"><thead><tr>
      <th>Part number</th><th>Description</th><th>Location</th><th class="num">On hand</th><th class="num">Min</th><th class="num">Order</th></tr></thead><tbody>
      ${list.map(({ p, it, qty }) => `<tr><td><strong>${esc(p.pn)}</strong></td><td>${esc(p.desc)}${p.bt ? ", bored through" : ""}</td><td>${esc(it.loc || "—")}</td>
        <td class="num">${it.onHand ?? "—"}</td><td class="num">${it.min ?? "—"}</td><td class="num"><strong>${qty ?? "set a min"}</strong></td></tr>`).join("")}
      </tbody></table>`
    : `<p class="empty-state">Nothing to reorder. A part lands here when its on-hand count is below its min, or at zero.</p>`;
  $("#dlg-reorder").showModal();
});
function copyReorder() {
  const lines = [["Part number", "Description", "Location", "On hand", "Min", "Order qty"].join("\t")]
    .concat(reorderRows().map(({ p, it, qty }) => [p.pn, p.desc + (p.bt ? ", bored through" : ""), it.loc, it.onHand ?? "", it.min ?? "", qty ?? ""].join("\t")));
  const text = lines.join("\n");
  const done = () => toast("Reorder list copied. Paste it into an email or spreadsheet.");
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, () => fallbackCopy(text, done));
  else fallbackCopy(text, done);
}
function fallbackCopy(text, done) {
  const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); done(); } catch (e) { toast("Couldn't copy. Use Export CSV instead."); }
  ta.remove();
}

// ---------------------------------------------------------------- add part
$("#kind-select").innerHTML = `<option value="">No drawing</option>` + KINDS.map(([k, label]) => `<option value="${esc(k)}">${esc(label)}</option>`).join("");
$("#btn-add").addEventListener("click", () => { $("#add-form").reset(); $("#add-error").hidden = true; $("#dlg-add").showModal(); $("#add-form").pn.focus(); });
$("#add-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const f = e.target;
  const pn = f.pn.value.trim().toUpperCase();
  const err = $("#add-error");
  if (!pn || !f.cat.value.trim() || !f.desc.value.trim()) { err.textContent = "Part number, category and description are required."; err.hidden = false; return; }
  if (allParts().some((p) => p.pn.toUpperCase() === pn)) { err.textContent = `${pn} is already in the list. Search for it to update its counts.`; err.hidden = false; return; }
  state.custom.push({
    pn, cat: f.cat.value.trim(), desc: f.desc.value.trim(), bt: false, od: f.od.value.trim(), end: f.end.value.trim() || "—",
    mat: f.mat.value.trim(), nutHex: f.nutHex.value.trim(), bodyHex: f.bodyHex.value.trim(), hexNote: "", hexSource: "Added by you", kind: f.kind.value,
  });
  saveNow(); $("#dlg-add").close(); ui.q = pn.toLowerCase(); $("#q").value = pn; render(); toast(`${pn} added.`);
});

// ---------------------------------------------------------------- confirm + toast
let confirmFn = null;
function confirmAction(title, text, okLabel, fn) {
  $("#confirm-title").textContent = title; $("#confirm-text").textContent = text; $("#confirm-ok").textContent = okLabel;
  confirmFn = fn; $("#dlg-confirm").showModal();
}
$("#confirm-ok").addEventListener("click", () => { $("#dlg-confirm").close(); if (confirmFn) confirmFn(); confirmFn = null; });
let toastTimer = null;
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
}

// ---------------------------------------------------------------- files
const localDate = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const today = () => localDate();
function download(name, text, type) {
  const blob = new Blob([text], { type });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function saveBackup() {
  state.lastBackup = new Date().toISOString();
  const payload = { app: "fittings-stockroom", savedAt: state.lastBackup, partsListBuilt: INFO.built, state };
  download(`fittings-stockroom-backup-${today()}.json`, JSON.stringify(payload, null, 1), "application/json");
  saveNow(); toast("Backup file saved to your Downloads folder.");
}
$("#file-backup").addEventListener("change", async (e) => {
  const file = e.target.files[0]; e.target.value = "";
  if (!file) return;
  let data;
  try { data = JSON.parse(await file.text()); } catch (err) { toast("That file isn't a stockroom backup. Choose a .json file saved by this app."); return; }
  const incoming = data && data.app === "fittings-stockroom" ? normalize(data.state) : null;
  if (!incoming) { toast("That file isn't a stockroom backup. Choose a .json file saved by this app."); return; }
  const n = Object.keys(incoming.items).length;
  confirmAction("Restore this backup?", `The backup from ${fmtDate(data.savedAt)} has entries for ${n} part${n === 1 ? "" : "s"}. It replaces everything currently in this app.`, "Restore backup", () => {
    state = incoming; saveNow(); render(); toast("Backup restored.");
  });
});

function csvCell(v) {
  const s = String(v ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}
const asText = (v) => (v && /^[\d\s/]+$/.test(v) ? `="${v}"` : v || "");  // stop Excel turning 5/16 into a date
function exportCSV() {
  const head = ["Category", "Part Number", "Description", "Bored Through", "Tube OD", "Second End", "Material", "Nut Hex (in)", "Body Hex (in)",
    "Location", "Min Qty", "Qty On Hand", "Order Qty", "Status", "Last Counted", "Notes", "Hidden"];
  const lines = [head.map(csvCell).join(",")];
  for (const p of allParts()) {
    const it = getItem(p.pn);
    lines.push([p.cat, p.pn, p.desc, p.bt ? "Yes" : "", p.od, p.end, p.mat, asText(p.nutHex), asText(p.bodyHex), it.loc, it.min ?? "", it.onHand ?? "",
      it.orderQty ?? "", STATUS_LABEL[statusOf(it)], it.counted ? localDate(new Date(it.counted)) : "", it.note, isHidden(p.pn) ? "Yes" : ""].map(csvCell).join(","));
  }
  download(`fittings-stockroom-${today()}.csv`, "﻿" + lines.join("\r\n"), "text/csv");
  toast("Spreadsheet saved to your Downloads folder.");
}
function exportReorderCSV() {
  const lines = [["Part Number", "Description", "Location", "Qty On Hand", "Min Qty", "Order Qty"].map(csvCell).join(",")]
    .concat(reorderRows().map(({ p, it, qty }) => [p.pn, p.desc + (p.bt ? ", bored through" : ""), it.loc, it.onHand ?? "", it.min ?? "", qty ?? ""].map(csvCell).join(",")));
  download(`fittings-reorder-${today()}.csv`, "﻿" + lines.join("\r\n"), "text/csv");
  toast("Reorder list saved to your Downloads folder.");
}
function parseCSV(text) {
  const rows = []; let row = [], cell = "", q = false;
  text = text.replace(/^﻿/, "");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some((v) => v.trim() !== ""));
}
$("#file-csv").addEventListener("change", async (e) => {
  const file = e.target.files[0]; e.target.value = "";
  if (!file) return;
  const rows = parseCSV(await file.text());
  if (rows.length < 2) { toast("That CSV has no rows to import."); return; }
  const head = rows[0].map((h) => h.trim().toLowerCase());
  const col = (...names) => head.findIndex((h) => names.includes(h));
  const iPn = col("part number", "part no.", "part no", "pn");
  if (iPn < 0) { toast('Import needs a "Part Number" column.'); return; }
  const iLoc = col("location", "bin"), iMin = col("min qty", "min"), iOn = col("qty on hand", "on hand"), iOrd = col("order qty"), iNote = col("notes", "note");
  const known = new Map(allParts().map((p) => [p.pn.toUpperCase(), p.pn]));
  let updated = 0; const missing = [];
  const clean = (v) => String(v ?? "").replace(/^="(.*)"$/, "$1").trim();
  const plan = [];
  for (const r of rows.slice(1)) {
    const raw = clean(r[iPn]).toUpperCase();
    if (!raw) continue;
    const pn = known.get(raw);
    if (!pn) { missing.push(raw); continue; }
    plan.push([pn, r]);
  }
  const apply = () => {
    for (const [pn, r] of plan) {
      const it = editItem(pn); let changed = false;
      if (iLoc >= 0 && clean(r[iLoc]) !== "") { it.loc = clean(r[iLoc]); changed = true; }
      if (iMin >= 0 && clean(r[iMin]) !== "") { it.min = toNum(clean(r[iMin])); changed = true; }
      if (iOn >= 0 && clean(r[iOn]) !== "") { it.onHand = toNum(clean(r[iOn])); it.counted = new Date().toISOString(); changed = true; }
      if (iOrd >= 0 && clean(r[iOrd]) !== "") { it.orderQty = toNum(clean(r[iOrd])); changed = true; }
      if (iNote >= 0 && clean(r[iNote]) !== "") { it.note = clean(r[iNote]); changed = true; }
      if (changed) updated++;
    }
    saveNow(); render();
    toast(`Updated ${updated} part${updated === 1 ? "" : "s"}.` + (missing.length ? ` ${missing.length} part number${missing.length === 1 ? " wasn't" : "s weren't"} in the list: ${missing.slice(0, 4).join(", ")}${missing.length > 4 ? "…" : ""}` : ""));
  };
  confirmAction("Import from this CSV?", `${plan.length} row${plan.length === 1 ? "" : "s"} match parts in the list. Filled-in cells replace what's in the app; blank cells are left alone.`, "Import", apply);
});

// ---------------------------------------------------------------- printing
function printTitle(title, sub) { return `<h1>${esc(title)}</h1><p class="psub">${esc(sub)}</p>`; }
function printCount() {
  const parts = visibleParts();
  const groups = new Map();
  for (const p of parts) { if (!groups.has(p.cat)) groups.set(p.cat, []); groups.get(p.cat).push(p); }
  let body = "";
  for (const [cat, list] of groups) {
    body += `<tr class="pg"><td colspan="9">${esc(cat)}</td></tr>`;
    body += list.map((p) => { const it = getItem(p.pn); return `<tr>
      <td class="ptile">${drawingFor(p)}</td><td><strong>${esc(p.pn)}</strong></td><td>${esc(p.desc)}${p.bt ? ", bored through" : ""}</td>
      <td class="nw">${esc(p.od)}</td><td>${esc(p.end)}</td><td class="nw"><span class="hx">nut</span> ${hexText(p.nutHex)}<br><span class="hx">body</span> ${hexText(p.bodyHex)}</td><td>${esc(it.loc)}</td>
      <td class="num">${it.min ?? ""}</td><td class="num"><span class="box"></span></td></tr>`; }).join("");
  }
  $("#print-area").innerHTML = printTitle("Count sheet", `${parts.length} parts. Printed ${new Date().toLocaleDateString()}. Counted by ____________`) +
    `<table><thead><tr><th></th><th>Part number</th><th>Description</th><th>Size</th><th>Other end</th><th>Hex (in)</th><th>Location</th><th class="num">Min</th><th class="num">Count</th></tr></thead><tbody>${body}</tbody></table>`;
  window.print();
}
function printReorder() {
  const list = reorderRows();
  $("#print-area").innerHTML = printTitle("Reorder list", `${list.length} parts below min. Printed ${new Date().toLocaleDateString()}.`) +
    (list.length ? `<table><thead><tr><th>Part number</th><th>Description</th><th>Location</th><th class="num">On hand</th><th class="num">Min</th><th class="num">Order</th><th class="num">Ordered</th></tr></thead><tbody>
    ${list.map(({ p, it, qty }) => `<tr><td><strong>${esc(p.pn)}</strong></td><td>${esc(p.desc)}${p.bt ? ", bored through" : ""}</td><td>${esc(it.loc)}</td><td class="num">${it.onHand ?? ""}</td><td class="num">${it.min ?? ""}</td><td class="num"><strong>${qty ?? ""}</strong></td><td class="num"><span class="sq"></span></td></tr>`).join("")}
    </tbody></table>` : "<p>Nothing to reorder.</p>");
  window.print();
}

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "swagelok_inventory_checklist_hex.csv",
          sys.argv[2] if len(sys.argv) > 2 else "fittings_stockroom.html")
