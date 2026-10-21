# Swagelok Inventory Checklist: Handoff Notes

Backup made 2026-10-20. Attach this file and the backup zip to a new chat to pick up where this one left off.

## What this is

An inventory checklist of common Swagelok tube fittings, 1/16 in to 1/4 in tube, in 316 SS (316L SS for VCR parts). There are 90 parts in 17 categories. Each part has a generic line drawing, and the hex version adds wrench sizes across flats.

## Files (in `current/`)

| File | What it is |
|---|---|
| `swagelok_inventory_checklist.csv` | **Master list. Edit only this file.** Columns: Category, Description, Tube OD, Second End, Material, Part Number, Qty On Hand, Min Qty, Location, Checked |
| `swagelok_inventory_checklist.pdf` | Printable checklist with drawings (6 pages) |
| `swagelok_inventory_checklist_hex.csv` | Generated from the master. Adds Nut Hex (in), Body Hex (in), Hex Note, Hex Source. Do not edit by hand, and do not open and save it in Excel (it turns "5/16" into dates) |
| `swagelok_inventory_checklist_hex.pdf` | Printable checklist with Nut Hex and Body Hex columns (6 pages) |
| `fitting_drawings.py` / `fitting_drawings_hex.py` | Drawing code (currently the same apart from the header comment) |
| `build_checklist_pdf.py` | Master CSV to plain PDF |
| `add_hex_columns.py` | Master CSV to hex CSV. The hex lookup tables, with catalog page refs, are in this file |
| `build_checklist_pdf_hex.py` | Hex CSV to hex PDF |

`v1_as_is/` is the frozen first version (81 parts, before hex sizes, reducing elbow, VCR parts and removal of the lock nuts).

## How to rebuild

Needs Python 3 and `pip install reportlab`. Keep all scripts in the same folder as the CSV.

```
python3 build_checklist_pdf.py          # plain PDF
python3 add_hex_columns.py              # hex CSV
python3 build_checklist_pdf_hex.py      # hex PDF
```

When editing the master CSV in Excel, save as **CSV UTF-8** (keeps the "—" characters). Min Qty and Location are printed on the PDFs whenever they are filled in. Qty On Hand is left blank for counting.

To add a new part type:
1. Give it a drawing in `DRAWINGS` (both drawing files).
2. Map its Description in `KIND_BY_DESCRIPTION` (both builders).
3. Give it a hex entry in `add_hex_columns.py`.

The scripts stop with a message naming anything that is missing.

## Rules and decisions so far

- Sizes are 1/16, 1/8 and 1/4 in only (3/16 in was skipped as uncommon).
- NPT parts are straight tube-to-NPT only (male and female connectors). No NPT tees or elbows.
- No tools or accessories (no gap gauge, SWAK, Snoop).
- Bored-through (BT) versions are included for unions, reducing unions, bulkhead unions, male connectors, union tees and reducers.
  - SS-400-R-2 has no BT version (a 1/4 in tube can't pass through a 1/8 in stub).
- Bulkhead lock nuts were removed.
- Reducing elbow: SS-400-2R-4 is the only one from 1/16 to 1/4 in (the rest start at 3/8 in).
- VCR to tube fitting connectors:
  - SS-4-VCR-6-200, SS-4-VCR-6-400 (male VCR)
  - SS-4-WVCR-6-400 (female VCR, welded)
  - SS-4-VCR-A1-400 (bulkhead)
  - There is no VCR x 1/16 in tube connector. The short bulkhead SS-4-VCR-A1S-400 was not added.
- VCR gaskets, 316L SS:
  - SS-2-VCR-2 and SS-4-VCR-2 (silver-plated); SS-2-VCR-2-VS and SS-4-VCR-2-VS (unplated)
  - SS-4-VCR-2-GR and SS-4-VCR-2-GR-VS (retainer)
  - SS-4-VCR-2-ZC-VS (side-load retainer)
  - No 1/16 in gaskets in the catalog. Blind (-BL) gaskets were not added.
- Drawings are generic, not to scale. One drawing per part type; BT parts get a blue through-line and a "BT" tag.

## Things to confirm with a distributor

- **SS-100-4** (1/16 in union cross) is not in the catalog. The smallest union cross listed is 1/8 in.
- **Bored-through union tees** (SS-x00-3BT) are not described in the catalog. It describes BT male connectors and reducers, and pairs standard tees with BT reducers.
- **Hex sizes the catalog doesn't list (shown as "n/l"):** body hex for fractional unions and reducing unions, and caps and plugs.
- **Port connectors** (1 in and under) have no hex and come without nuts.

## Sources

- Swagelok, *Gaugeable Tube Fittings and Adapter Fittings*, MS-01-140 Rev AJ (Feb 2026): https://www.swagelok.com/downloads/webcatalogs/en/ms-01-140.pdf
- Swagelok, *VCR Metal Gasket Face Seal Fittings*, MS-01-24 Rev X (Sep 2026): https://www.swagelok.com/downloads/webcatalogs/en/ms-01-24.pdf

## Local stockroom app (added 2026-10-20)

`fittings_stockroom.html` is a single offline file. Double-click it to open it in a browser; it doesn't use the internet.
- It shows all 90 parts with drawings, sizes and hex, grouped by category, with size color tabs (purple 1/16, teal 1/8, ochre 1/4).
- Editable per part: Location, Min, On hand (with − / + buttons), Order qty and a note. Enter jumps to the same field on the next row, which makes counting quick.
- Status for each part: Out, Low, OK, No min, Not counted, Not set up. Anything that is Out or Low goes on the **Reorder list**, which can be copied, exported to CSV or printed. Order qty left blank means enough to get back to the min.
- Filters: search, size, category, Needs reorder, No min yet, Not counted. Parts can be hidden (and shown again), and you can add your own parts with a chosen drawing.
- **Backup and print** menu:
  - Save backup file (.json) and Restore from backup file.
  - Export spreadsheet (CSV).
  - Import quantities from CSV, which fills Location, Min Qty, Qty On Hand, Order Qty and Notes by Part Number, so mins can be set in Excel and loaded in.
  - Print count sheet (current view) and Print reorder list.
- **Where data lives:** entries save automatically in the browser that opened the file, on that Mac. They are not saved inside the HTML file. Save a backup file regularly (the app reminds you after 7 days), always open the app from the same place in the same browser, and restore from a backup file if you move it or switch browsers.
- **Rebuilding after the parts CSV changes:** run `python3 add_hex_columns.py`, then `python3 build_inventory_app.py`. Entries are keyed by part number, so everything already entered carries over.
- Files: `build_inventory_app.py` (makes the HTML) and `svg_canvas.py` (turns the PDF drawing code into the app's drawings). Both need the other scripts in the same folder.
- Tested in Chromium (Chrome engine). Safari should work; if the footer ever says changes aren't being saved, use another browser.

## Next steps that were proposed (not started)

1. **Master Excel workbook for the stockroom.** Mostly covered now by the local app plus its CSV export/import. A workbook is still an option if purchasing wants one.
2. **Bin labels from the same data:** part number, drawing, size, hex, min qty. Label stock still to be chosen (for example, Avery 5160 or Brother tape).
3. **Min qty.**
   - Rule of thumb: Min = (usage during supplier lead time) + safety buffer.
   - Ferrules and VCR gaskets are single-use, so stock more.
   - Rare parts (crosses, bulkheads, BT, VCR connectors) can sit at 1–2.
   - Suggested numbers per part are waiting on rough monthly usage and lead time.
