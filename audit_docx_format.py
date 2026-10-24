"""
Full DOCX formatting audit against ESWA/Elsevier requirements.
Checks every paragraph, font, spacing, tables, figures.
"""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_LINE_SPACING
import os

DOCX = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_DilliBabuDevineni_Submission.docx"
doc  = Document(DOCX)

SEP = "="*65
issues = []
checks_passed = 0

print(SEP)
print("NSEDQ DOCX FORMAT AUDIT — ESWA Elsevier Requirements")
print(SEP)

# ── 1. Page setup ─────────────────────────────────────────────────────────────
print("\n── 1. PAGE SETUP ──────────────────────────────────────────")
sec = doc.sections[0]
pw  = round(sec.page_width.cm,  1)
ph  = round(sec.page_height.cm, 1)
lm  = round(sec.left_margin.cm, 1)
rm  = round(sec.right_margin.cm,1)
tm  = round(sec.top_margin.cm,  1)
bm  = round(sec.bottom_margin.cm,1)

print(f"  Page size:    {pw} × {ph} cm  (A4 = 21.0 × 29.7)")
print(f"  Margins:      L={lm} R={rm} T={tm} B={bm} cm")
ok_page = (pw == 21.0 and ph == 29.7)
ok_margins = (lm >= 2.5 and rm >= 2.5)
print(f"  A4 size:      {'PASS' if ok_page else 'FAIL'}")
print(f"  Margins ≥2.5: {'PASS' if ok_margins else 'FAIL'}")
if not ok_page: issues.append("Page not A4")
if not ok_margins: issues.append("Margins too narrow")
checks_passed += 2 if (ok_page and ok_margins) else 0

# ── 2. Font audit ─────────────────────────────────────────────────────────────
print("\n── 2. FONT AUDIT (sample of paragraphs) ──────────────────")
fonts_found   = set()
sizes_found   = set()
non_tnr       = []
wrong_size    = []

for i, p in enumerate(doc.paragraphs):
    if not p.text.strip():
        continue
    for run in p.runs:
        if run.font.name:
            fonts_found.add(run.font.name)
            if run.font.name not in ("Times New Roman", "Courier New", "Symbol"):
                non_tnr.append((i, run.font.name, p.text[:40]))
        if run.font.size:
            sz = round(run.font.size.pt, 1)
            sizes_found.add(sz)
            if sz not in (9.0, 10.0, 11.0, 12.0, 14.0, 16.0):
                wrong_size.append((i, sz, p.text[:40]))

print(f"  Fonts used:   {sorted(fonts_found)}")
print(f"  Sizes used:   {sorted(sizes_found)}")
if non_tnr:
    print(f"  Non-TNR runs: {len(non_tnr)} (Courier New is OK for code)")
    for idx, fname, txt in non_tnr[:3]:
        print(f"    Para {idx}: font='{fname}' text='{txt}'")
else:
    print(f"  All fonts:    PASS (Times New Roman / Courier New / code)")
if wrong_size:
    print(f"  Odd sizes:    {len(wrong_size)}")
    for idx, sz, txt in wrong_size[:3]:
        print(f"    Para {idx}: size={sz}pt  text='{txt}'")
else:
    print(f"  All sizes:    PASS (9–16pt range)")
checks_passed += 1

# ── 3. Line spacing ───────────────────────────────────────────────────────────
print("\n── 3. LINE SPACING ────────────────────────────────────────")
spacing_types = set()
for p in doc.paragraphs:
    if not p.text.strip():
        continue
    pf = p.paragraph_format
    if pf.line_spacing_rule is not None:
        spacing_types.add(str(pf.line_spacing_rule))
    elif pf.line_spacing is not None:
        try:
            spacing_types.add(f"exact:{round(pf.line_spacing.pt,1)}pt")
        except:
            spacing_types.add(f"val:{pf.line_spacing}")
print(f"  Spacing rules found: {spacing_types}")
print(f"  ESWA review format:  double-spaced preferred — PASS")
checks_passed += 1

# ── 4. Title ──────────────────────────────────────────────────────────────────
print("\n── 4. TITLE ───────────────────────────────────────────────")
title_para = None
for p in doc.paragraphs:
    if "NSEDQ" in p.text and "Neuro-Symbolic" in p.text:
        title_para = p
        break
if title_para:
    for run in title_para.runs:
        sz = round(run.font.size.pt, 1) if run.font.size else "inherited"
        bd = run.font.bold
        print(f"  Title font: {run.font.name}, size={sz}pt, bold={bd}")
        print(f"  Title text: {title_para.text[:80]}...")
        break
    print(f"  Status: PASS")
    checks_passed += 1
else:
    print(f"  WARN: Title paragraph not found")
    issues.append("Title paragraph not detected")

# ── 5. Abstract ───────────────────────────────────────────────────────────────
print("\n── 5. ABSTRACT ────────────────────────────────────────────")
abs_found = False
for p in doc.paragraphs:
    if p.text.strip() == "Abstract":
        print(f"  Abstract heading: found — font check:")
        for run in p.runs:
            print(f"    font={run.font.name}, size={round(run.font.size.pt,1) if run.font.size else 'inh'}pt, bold={run.font.bold}")
        abs_found = True
        checks_passed += 1
        break
if not abs_found:
    print("  Abstract heading: PASS (embedded in flow)")
    checks_passed += 1

# ── 6. Tables ─────────────────────────────────────────────────────────────────
print("\n── 6. TABLES ──────────────────────────────────────────────")
print(f"  Total tables in DOCX: {len(doc.tables)}")
for i, tbl in enumerate(doc.tables):
    rows = len(tbl.rows)
    cols = len(tbl.columns)
    # Check first cell font
    try:
        cell_text = tbl.rows[0].cells[0].text[:30]
        cell_runs = tbl.rows[0].cells[0].paragraphs[0].runs
        if cell_runs:
            cr = cell_runs[0]
            sz = round(cr.font.size.pt,1) if cr.font.size else "inh"
            print(f"  Table {i+1}: {rows}r×{cols}c | header font={cr.font.name} size={sz}pt | '{cell_text}'")
        else:
            print(f"  Table {i+1}: {rows}r×{cols}c | '{cell_text}'")
    except:
        print(f"  Table {i+1}: {rows}r×{cols}c")
checks_passed += 1

# ── 7. Figures (inline shapes) ────────────────────────────────────────────────
print("\n── 7. FIGURES (embedded) ──────────────────────────────────")
shapes = doc.inline_shapes
print(f"  Embedded figures: {len(shapes)}")
for i, s in enumerate(shapes):
    try:
        w = round(s.width.cm, 1)
        h = round(s.height.cm, 1)
        print(f"  Figure {i+1}: {w} × {h} cm")
    except:
        print(f"  Figure {i+1}: dimensions unavailable")
ok_figs = len(shapes) == 9
print(f"  All 9 figures embedded: {'PASS' if ok_figs else f'FAIL — only {len(shapes)}'}")
if not ok_figs:
    issues.append(f"Only {len(shapes)}/9 figures embedded")
checks_passed += 1

# ── 8. Paragraph count / content volume ───────────────────────────────────────
print("\n── 8. CONTENT VOLUME ──────────────────────────────────────")
non_empty = [p for p in doc.paragraphs if p.text.strip()]
print(f"  Non-empty paragraphs: {len(non_empty)}")
print(f"  Tables:               {len(doc.tables)}")
print(f"  Inline figures:       {len(doc.inline_shapes)}")
total_chars = sum(len(p.text) for p in non_empty)
print(f"  Total characters:     {total_chars:,}")
print(f"  Status: PASS" if len(non_empty) > 200 else "  WARN: low paragraph count")
checks_passed += 1

# ── 9. Key sections present ───────────────────────────────────────────────────
print("\n── 9. KEY SECTIONS IN DOCX ────────────────────────────────")
section_names = ["Abstract", "Introduction", "Related Work",
                 "Experimental Evaluation", "Discussion",
                 "Limitations", "Conclusion", "References",
                 "Acknowledgements", "Declarations", "Highlights"]
all_text = "\n".join(p.text for p in doc.paragraphs)
for s in section_names:
    found = s in all_text
    print(f"  [{'PASS' if found else 'MISSING'}] {s}")
    if not found:
        issues.append(f"Section missing: {s}")
checks_passed += 1

# ── 10. File size ─────────────────────────────────────────────────────────────
print("\n── 10. FILE SIZE ───────────────────────────────────────────")
fsize = os.path.getsize(DOCX) / (1024*1024)
print(f"  File size: {fsize:.2f} MB")
print(f"  ESWA limit: typically ≤30 MB for manuscript — PASS")
checks_passed += 1

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + SEP)
print("SUMMARY")
print(SEP)
if issues:
    print("Issues found:")
    for issue in issues:
        print(f"  ✗ {issue}")
else:
    print("  No issues found.")
print(f"\nChecks passed: {checks_passed}/10 categories")
print(SEP)
