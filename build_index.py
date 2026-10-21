#!/usr/bin/env python3
"""
Build a searchable index of Swagelok catalog PDFs.

    python3 build_index.py [folder]

Reads every .pdf in the folder (default: the folder this script is in) and writes,
next to the PDFs:

  search-data.js        data for search.html (open search.html in a browser)
  swagelok_catalog.db   the same content as a SQLite full-text index

Re-run it whenever you add, remove or replace a PDF.
Requires PyMuPDF:  pip3 install pymupdf
"""
import datetime
import json
import os
import re
import sqlite3
import sys
import unicodedata

import pymupdf

# Swagelok ordering numbers: uppercase/digit groups joined by hyphens, e.g.
# SS-400-6, SS-6M0-1-4, B-43S4, 6LV-DABW4, SS-T4-S-035-20, SS-4-HLN-12.00
PART_RE = re.compile(r"(?<![A-Za-z0-9.\-])([A-Z0-9][A-Z0-9.]*(?:-[A-Z0-9][A-Z0-9.]*)+)(?![A-Za-z0-9\-])")

DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−­"), "-")
DASHES[0x00AD] = None  # soft hyphen: drop
EXTRA = {0x2044: "/", 0x2215: "/", 0x00A0: " ", 0x2009: " ", 0x202F: " ",
         0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}

TEXT_FLAGS = pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP  # ligatures expanded


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)  # ﬁ → fi, ½ → 1⁄2, ″ → ′′ …
    text = text.translate(DASHES).translate(EXTRA)
    text = text.replace("′′", '"').replace("′", "'")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def part_numbers(text: str) -> list:
    out = []
    for m in PART_RE.finditer(text):
        p = m.group(1).rstrip(".")
        if not (5 <= len(p) <= 40):
            continue
        if not re.search(r"[A-Z]", p) or not re.search(r"\d", p):
            continue
        if p not in out:
            out.append(p)
    return out


def tidy_toc(toc: list) -> list:
    """Bookmarks as (depth, title, page), minus wrapper levels holding a single bookmark."""
    entries = [(lvl, clean(title), max(1, pg)) for lvl, title, pg, *_ in toc if pg > 0]
    while entries:
        top = min(e[0] for e in entries)
        roots = [e for e in entries if e[0] == top]
        if len(roots) == 1 and len(entries) > 1:
            entries = [e for e in entries if e is not roots[0]]
        else:
            break
    if not entries:
        return []
    base = min(e[0] for e in entries)
    return [(lvl - base, title, pg) for lvl, title, pg in entries]


def page_sections(toc: list, page_count: int) -> list:
    """Bookmark path (list of titles) in force on each page, 1-based index."""
    entries = tidy_toc(toc)
    if not entries:
        return [[] for _ in range(page_count + 1)]
    order = sorted(range(len(entries)), key=lambda i: (entries[i][2], i))
    result = [[] for _ in range(page_count + 1)]
    stack, k = [], 0
    for page in range(1, page_count + 1):
        while k < len(order) and entries[order[k]][2] <= page:
            depth, title, _ = entries[order[k]]
            stack = stack[:depth] + [title]
            k += 1
        result[page] = list(stack)
    return result


def nice_title(path: str, doc) -> str:
    t = (doc.metadata or {}).get("title") or ""
    t = clean(t)
    if len(t) < 4 or t.lower().startswith(("microsoft", "untitled")) or t.lower().endswith((".indd", ".pdf")):
        t = os.path.splitext(os.path.basename(path))[0]
    return t


def build(folder: str) -> None:
    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf") and not f.startswith("."))
    if not pdfs:
        sys.exit(f"No PDFs found in {folder}")

    db_path = os.path.join(folder, "swagelok_catalog.db")
    tmp_db = db_path + ".tmp"
    if os.path.exists(tmp_db):
        os.remove(tmp_db)
    db = sqlite3.connect(tmp_db)
    db.executescript("""
        CREATE TABLE documents(id INTEGER PRIMARY KEY, file TEXT, title TEXT, page_count INTEGER);
        CREATE TABLE toc(doc_id INTEGER, level INTEGER, title TEXT, page INTEGER);
        CREATE TABLE pages(id INTEGER PRIMARY KEY, doc_id INTEGER, page INTEGER,
                           category TEXT, section TEXT, text TEXT);
        CREATE TABLE part_numbers(part TEXT, page_id INTEGER);
        CREATE VIRTUAL TABLE pages_fts USING fts5(text, section, content='pages', content_rowid='id',
                                                  tokenize="unicode61 remove_diacritics 2");
    """)

    docs, sections, sec_index, toc_out, pages_out = [], [], {}, [], []
    empty_pages, total_pages, page_id = 0, 0, 0

    for d, fname in enumerate(pdfs):
        path = os.path.join(folder, fname)
        doc = pymupdf.open(path)
        n = doc.page_count
        title = nice_title(path, doc)
        toc = doc.get_toc(simple=True)
        secs = page_sections(toc, n)
        docs.append({"file": fname, "title": title, "pages": n})
        db.execute("INSERT INTO documents VALUES(?,?,?,?)", (d, fname, title, n))
        for depth, t, pg in tidy_toc(toc):
            toc_out.append([d, depth, t, pg])
            db.execute("INSERT INTO toc VALUES(?,?,?,?)", (d, depth, t, pg))

        print(f"[{d + 1}/{len(pdfs)}] {fname}: {n} pages, {len(toc)} bookmarks", flush=True)
        for i, page in enumerate(doc, start=1):
            text = clean(page.get_text("text", flags=TEXT_FLAGS))
            if len(text) < 30:
                empty_pages += 1
            path_titles = secs[i]
            section = " › ".join(path_titles)
            category = path_titles[0] if path_titles else ""
            if section not in sec_index:
                sec_index[section] = len(sections)
                sections.append(section)
            page_id += 1
            db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?)", (page_id, d, i, category, section, text))
            db.executemany("INSERT INTO part_numbers VALUES(?,?)", [(p, page_id) for p in part_numbers(text)])
            pages_out.append([d, i, sec_index[section], text])
            if i % 250 == 0:
                print(f"    {i}/{n}", flush=True)
        total_pages += n
        doc.close()

    db.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
    db.execute("CREATE INDEX part_idx ON part_numbers(part)")
    db.commit()
    db.execute("VACUUM")
    db.close()
    os.replace(tmp_db, db_path)

    data = {
        "built": datetime.date.today().isoformat(),
        "docs": docs,
        "sections": sections,
        "toc": toc_out,
        "pages": pages_out,
    }
    js_path = os.path.join(folder, "search-data.js")
    with open(js_path + ".tmp", "w", encoding="utf-8") as f:
        f.write("window.CATALOG = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    os.replace(js_path + ".tmp", js_path)

    print(f"\nIndexed {total_pages} pages from {len(pdfs)} PDF(s).")
    if empty_pages:
        print(f"Note: {empty_pages} page(s) had little or no text (images or blank pages).")
    print(f"Wrote {js_path} ({os.path.getsize(js_path) / 1e6:.1f} MB)")
    print(f"Wrote {db_path} ({os.path.getsize(db_path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
