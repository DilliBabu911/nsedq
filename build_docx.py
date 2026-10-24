"""
NSEDQ ESWA Paper — DOCX Builder
Generates a properly formatted Elsevier ESWA submission document.
ESWA review format: single-column, double-spaced, 12pt Times New Roman
(Elsevier converts to two-column for publication; review submission is single-column)
"""

import os
import re
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy

ROOT   = os.path.dirname(os.path.abspath(__file__))
MD     = os.path.join(ROOT, "NSEDQ_ESWA_Final.md")
FIGS   = os.path.join(ROOT, "figures")
OUTDIR = ROOT

# ── Styles ────────────────────────────────────────────────────────────────────

def set_font(run, name="Times New Roman", size=12, bold=False,
             italic=False, color=None):
    run.font.name        = name
    run.font.size        = Pt(size)
    run.font.bold        = bold
    run.font.italic      = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def set_para_spacing(para, before=0, after=6, line_rule=None, line=None):
    pf = para.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if line_rule and line:
        pf.line_spacing_rule = line_rule
        pf.line_spacing      = line

def add_heading(doc, text, level=1):
    """Add a section heading."""
    para = doc.add_paragraph()
    run  = para.add_run(text)
    if level == 1:
        set_font(run, size=14, bold=True)
        set_para_spacing(para, before=12, after=6)
    elif level == 2:
        set_font(run, size=12, bold=True)
        set_para_spacing(para, before=8, after=4)
    elif level == 3:
        set_font(run, size=11, bold=True, italic=True)
        set_para_spacing(para, before=6, after=3)
    para.paragraph_format.keep_with_next = True
    return para

def add_body(doc, text, indent=False):
    """Add a body paragraph."""
    para = doc.add_paragraph()
    # Handle inline bold (**text**) and italic (*text*)
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = para.add_run(part[2:-2])
            set_font(run, bold=True)
        elif part.startswith('*') and part.endswith('*'):
            run = para.add_run(part[1:-1])
            set_font(run, italic=True)
        elif part.startswith('`') and part.endswith('`'):
            run = para.add_run(part[1:-1])
            set_font(run, name="Courier New", size=10)
        else:
            run = para.add_run(part)
            set_font(run)
    set_para_spacing(para, before=0, after=6)
    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.line_spacing      = Pt(24)
    if indent:
        pf.first_line_indent = Cm(0.5)
    return para

def add_figure(doc, fig_path, caption, width_cm=14):
    """Insert a figure with caption."""
    if os.path.exists(fig_path):
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        run.add_picture(fig_path, width=Cm(width_cm))
        set_para_spacing(para, before=6, after=3)
    cap_para = doc.add_paragraph()
    cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap_para.add_run(caption)
    set_font(run, size=10, italic=True)
    set_para_spacing(cap_para, before=0, after=10)

def add_code_block(doc, code_text):
    """Add a code block."""
    for line in code_text.strip().split('\n'):
        para = doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(1.0)
        run = para.add_run(line if line else " ")
        set_font(run, name="Courier New", size=9)
        set_para_spacing(para, before=0, after=0)

def set_table_style(table, doc):
    """Apply clean table formatting."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style     = doc.styles['Table Grid']

def add_table_from_md(doc, md_rows):
    """
    Parse markdown table rows and create a docx table.
    md_rows: list of strings like '| col1 | col2 | col3 |'
    """
    # Filter out separator rows (|---|---|)
    data_rows = []
    for row in md_rows:
        row = row.strip()
        if not row or not row.startswith('|'):
            continue
        if re.match(r'^\|[\s\-\|]+\|$', row):
            continue
        cells = [c.strip() for c in row.strip('|').split('|')]
        data_rows.append(cells)

    if not data_rows:
        return

    ncols = max(len(r) for r in data_rows)
    table = doc.add_table(rows=len(data_rows), cols=ncols)
    set_table_style(table, doc)

    for i, row_data in enumerate(data_rows):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            if j >= ncols:
                break
            cell = row.cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            # Strip bold markers for cell text
            clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell_text)
            clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
            clean = re.sub(r'`([^`]+)`', r'\1', clean)
            para = cell.paragraphs[0]
            para.clear()
            run  = para.add_run(clean)
            is_bold = '**' in cell_text
            is_header = (i == 0)
            set_font(run, size=9, bold=(is_bold or is_header))
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after  = Pt(2)

    # Set column widths roughly equal
    total_width = Cm(16)
    col_width   = total_width / ncols
    for col in table.columns:
        for cell in col.cells:
            cell.width = int(col_width)

    # Space after table
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


# ── Main builder ──────────────────────────────────────────────────────────────

def build_docx():
    doc = Document()

    # ── Page setup ───────────────────────────────────────────────────────────
    section = doc.sections[0]
    section.page_height    = Cm(29.7)
    section.page_width     = Cm(21.0)
    section.left_margin    = Cm(3.0)
    section.right_margin   = Cm(3.0)
    section.top_margin     = Cm(2.5)
    section.bottom_margin  = Cm(2.5)

    # Set default font
    doc.styles['Normal'].font.name = 'Times New Roman'
    doc.styles['Normal'].font.size = Pt(12)

    # ── Title ─────────────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(
        "NSEDQ: A Neuro-Symbolic Engine for Automated Data Quality Constraint "
        "Inference and Verified Remediation Using LLM-SMT Counter-Prompting "
        "and Multi-Objective Optimisation"
    )
    set_font(title_run, size=16, bold=True)
    set_para_spacing(title_para, before=0, after=12)

    # ── Author ────────────────────────────────────────────────────────────────
    auth_para = doc.add_paragraph()
    auth_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    auth_run = auth_para.add_run("Dilli Babu Devineni")
    set_font(auth_run, size=12, bold=True)
    set_para_spacing(auth_para, before=0, after=2)

    for line in [
        "Independent Researcher, Enterprise Data Engineering, Business Intelligence and Generative AI",
        "Bengaluru, Karnataka, India",
        "ORCID: 0009-0003-8121-2530  |  Email: dilli.devineni@researcher.net",
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        set_font(r, size=10, italic=True)
        set_para_spacing(p, before=0, after=2)

    doc.add_paragraph()

    # ── Abstract ──────────────────────────────────────────────────────────────
    add_heading(doc, "Abstract", level=1)
    abstract = (
        "Enterprise data pipelines routinely accumulate errors spanning null values, range violations, "
        "format inconsistencies, referential failures, and functional dependency breakdowns that erode "
        "analytical quality, degrade machine learning model performance, and introduce regulatory "
        "compliance exposure. This paper presents NSEDQ, a neuro-symbolic engine that infers data "
        "quality constraints in a formally specified typed Constraint Description Language (CDL) by "
        "invoking a Foundation Model Inference Endpoint (Claude 3.5 Sonnet) enriched by a seven-layer "
        "Data Quality Knowledge Graph (EDQKG), verifies the candidate constraint set through "
        "Satisfiability Modulo Theories (SMT) solving and Datalog reasoning, and resolves logical "
        "contradictions through a novel Minimal Unsatisfiable Core Counter-Prompt Constructor "
        "(MUC-CPC) that transforms solver resolution proof trees into structured revision instructions. "
        "Accepted constraints are scored through a five-component Constraint Trust Score (CTS) and "
        "Governance Reliability Index (GRI) governing a three-tier acceptance gate. Repairs are "
        "selected through a five-objective Multi-Objective Integer Linear Program (MOILP) with each "
        "repair backed by a solver-verified formal proof certificate. A Continuous Governance Learning "
        "Engine (CGLE) detects distribution shift through Kolmogorov-Smirnov testing and forecasts "
        "drift through ARIMA models. Evaluation on four publicly available datasets — Patient Records "
        "(500), IBM HR Analytics (1,470), UCI Bank Marketing (4,521), and UCI Adult Census (32,561) "
        "— demonstrates that NSEDQ converges in 2 CRL iterations across all datasets (77.1% reduction "
        "vs random revision), achieves 100% proof certificate coverage on violated datasets, and "
        "prevents the DQTS degradation to 0.248 observed when unverified LLM constraints are applied "
        "without SMT verification."
    )
    add_body(doc, abstract)

    # Keywords
    kw_para = doc.add_paragraph()
    kw_run  = kw_para.add_run("Keywords: ")
    set_font(kw_run, bold=True, size=11)
    kw_body = kw_para.add_run(
        "Data Quality, Neuro-Symbolic AI, Constraint Inference, Satisfiability Modulo Theories, "
        "Counter-Prompt Engineering, Multi-Objective Optimisation, AI Governance, "
        "Proof Certificates, Knowledge Graph, Large Language Models"
    )
    set_font(kw_body, size=11)
    set_para_spacing(kw_para, before=0, after=12)

    doc.add_paragraph()

    # ── Now parse the MD and render each section ──────────────────────────────
    with open(MD, encoding="utf-8") as f:
        raw = f.read()

    # Strip the submission metadata header block (up to and including first ---)
    # Keep from "## 1. Introduction" onwards
    intro_match = re.search(r'^## 1\. Introduction', raw, re.MULTILINE)
    if intro_match:
        body_md = raw[intro_match.start():]
    else:
        body_md = raw

    # Also grab abstract keywords separately (already done above)
    # Split into lines and process
    lines = body_md.split('\n')
    render_lines(doc, lines)

    # ── Acknowledgements ──────────────────────────────────────────────────────
    add_heading(doc, "Acknowledgements", level=1)
    add_body(doc,
        "This work presents experimental evaluation supporting Indian Patent Application "
        "filed under the Indian Patents Act 1970, Form 2, on 30 August 2026 (NSEDQ). "
        "The author declares no competing interests. No external funding was received. "
        "All experiments were conducted on personal computing infrastructure. "
        "The Foundation Model Inference Endpoint used Claude 3.5 Sonnet "
        "(claude-3-5-sonnet-20241022, Anthropic) with embedded constraint proposals. "
        "All datasets are publicly available; no personally identifiable information was used."
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = os.path.join(OUTDIR,
        "NSEDQ_ESWA_DilliBabuDevineni_Submission.docx")
    doc.save(out_path)
    print(f"\n[OK] DOCX saved → {out_path}")
    size_kb = os.path.getsize(out_path) // 1024
    print(f"     File size: {size_kb} KB")
    return out_path


def render_lines(doc, lines):
    """
    Parse markdown lines and render into the doc.
    Handles: ## headings, tables, code blocks, bullet lists,
    figure references, and body paragraphs.
    """
    i = 0
    in_code   = False
    code_buf  = []
    tbl_buf   = []
    in_table  = False

    while i < len(lines):
        line = lines[i]

        # ── Code block ───────────────────────────────────────────────────────
        if line.strip().startswith('```'):
            if not in_code:
                in_code  = True
                code_buf = []
            else:
                in_code = False
                add_code_block(doc, '\n'.join(code_buf))
                code_buf = []
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # ── Table detection ──────────────────────────────────────────────────
        if line.strip().startswith('|') and '|' in line[1:]:
            tbl_buf.append(line)
            i += 1
            # Collect all table lines
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl_buf.append(lines[i])
                i += 1
            add_table_from_md(doc, tbl_buf)
            tbl_buf = []
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        h_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if h_match:
            level = len(h_match.group(1))
            text  = h_match.group(2).strip()
            # Skip submission metadata headings
            if text in ("Submission Target", "Author", "Abstract",
                        "Acknowledgements", "Paper Metadata",
                        "Submission Checklist", "Word Count Breakdown",
                        "Page Count Reference", "Figure Index"):
                i += 1
                continue
            add_heading(doc, text, level=min(level, 3))
            i += 1
            continue

        # ── Figure references (![...](figures/...)) ──────────────────────────
        fig_match = re.match(r'!\[([^\]]*)\]\(figures/([^)]+)\)', line.strip())
        if fig_match:
            fig_file = os.path.join(FIGS, fig_match.group(2).strip())
            # Caption comes from the next italics line (*...*) if present
            caption = fig_match.group(1)
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.startswith('*') and next_line.endswith('*'):
                    caption = next_line.strip('*').strip()
                    i += 1  # consume caption line
            add_figure(doc, fig_file, caption, width_cm=13)
            i += 1
            continue

        # ── Bullet / numbered lists ───────────────────────────────────────────
        bullet = re.match(r'^[\-\*]\s+(.*)', line.strip())
        if bullet:
            para = doc.add_paragraph(style='List Bullet')
            txt  = bullet.group(1)
            parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', txt)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r = para.add_run(part[2:-2]); set_font(r, bold=True)
                elif part.startswith('*') and part.endswith('*'):
                    r = para.add_run(part[1:-1]); set_font(r, italic=True)
                elif part.startswith('`') and part.endswith('`'):
                    r = para.add_run(part[1:-1]); set_font(r, name="Courier New", size=10)
                else:
                    r = para.add_run(part); set_font(r)
            set_para_spacing(para, before=0, after=3)
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────────────────────────
        if line.strip() == '---':
            i += 1
            continue

        # ── Skip pure metadata lines ──────────────────────────────────────────
        if line.strip().startswith('| **Journal**') or \
           line.strip().startswith('*Status:') or \
           line.strip().startswith('*File created') or \
           line.strip().startswith('*Last updated') or \
           line.strip().startswith('*Author:') or \
           line.strip().startswith('*Patent:'):
            i += 1
            continue

        # ── Skip submission checklist items ───────────────────────────────────
        if line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
            i += 1
            continue

        # ── Empty line ────────────────────────────────────────────────────────
        if not line.strip():
            i += 1
            continue

        # ── Default: body paragraph ───────────────────────────────────────────
        text = line.strip()
        if text:
            add_body(doc, text, indent=True)
        i += 1


if __name__ == "__main__":
    print("Building ESWA DOCX submission...\n")
    path = build_docx()
    print("\nDone.")
