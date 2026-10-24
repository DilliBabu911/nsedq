"""Build Cover Letter DOCX for ESWA submission."""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

OUT = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\Cover_Letter_ESWA_NSEDQ.docx"

doc = Document()
sec = doc.sections[0]
sec.page_height   = Cm(29.7)
sec.page_width    = Cm(21.0)
sec.left_margin   = Cm(3.0)
sec.right_margin  = Cm(3.0)
sec.top_margin    = Cm(2.5)
sec.bottom_margin = Cm(2.5)

def para(text, bold=False, italic=False, size=12, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=0, after=6):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after  = Pt(after)
    r = p.add_run(text)
    r.font.name   = "Times New Roman"
    r.font.size   = Pt(size)
    r.font.bold   = bold
    r.font.italic = italic
    return p

def mixed(parts, before=0, after=6):
    """parts = list of (text, bold, italic)"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after  = Pt(after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        r.font.name   = "Times New Roman"
        r.font.size   = Pt(12)
        r.font.bold   = bold
        r.font.italic = italic
    return p

# ── Sender ────────────────────────────────────────────────────────────────────
para("Dilli Babu Devineni", bold=True, after=2)
para("Independent Researcher", after=2)
para("Enterprise Data Engineering, Business Intelligence and Generative AI", after=2)
para("Bengaluru, Karnataka, India", after=2)
para("ORCID: 0009-0003-8121-2530", after=2)
para("Email: dilli.devineni@researcher.net", after=12)

para("24 October 2026", after=12)

para("The Editor-in-Chief", bold=True, after=2)
para("Expert Systems with Applications", italic=True, after=2)
para("Elsevier", after=16)

para("Dear Editor-in-Chief,", after=10)

# ── Opening ───────────────────────────────────────────────────────────────────
mixed([
    ("I am submitting the manuscript titled ", False, False),
    ('"NSEDQ: Neuro-Symbolic Data Quality Engine with LLM-SMT Counter-Prompting '
     'and Multi-Objective Verified Remediation"', True, False),
    (" for consideration as a Research Paper in ", False, False),
    ("Expert Systems with Applications", False, True),
    (".", False, False),
], after=10)

# ── Section 1 ─────────────────────────────────────────────────────────────────
para("What this paper contributes", bold=True, after=4)
para(
    "Enterprise data quality remains an unsolved problem at scale. Existing systems "
    "require manual constraint authoring, produce unverified repairs, or depend on "
    "labelled error examples unavailable in production. This paper presents NSEDQ, "
    "a neuro-symbolic engine that addresses all four limitations simultaneously. "
    "The primary technical contribution is the Minimal Unsatisfiable Core "
    "Counter-Prompt Constructor (MUC-CPC) — the first mechanism in the data quality "
    "literature to encode SMT solver resolution proof trees as structured Foundation "
    "Model re-prompting input. This closes the feedback loop between symbolic "
    "verification and neural inference in a way no prior system has achieved.",
    after=6
)
para(
    "The paper demonstrates experimentally that this mechanism reduces constraint "
    "refinement iterations by 77.1% compared to random revision, achieves 100% "
    "Z3-verified proof certificate coverage on all applied repairs, and prevents "
    "the severe data quality degradation (DQTS to 0.248 on 32,561 records) that "
    "occurs when unverified LLM-generated constraints are applied without SMT "
    "verification.",
    after=10
)

# ── Section 2 ─────────────────────────────────────────────────────────────────
para("Fit with ESWA scope", bold=True, after=4)
para(
    "ESWA publishes applied intelligent systems evaluated on real datasets with "
    "rigorous comparative experiments. This paper presents a working system "
    "evaluated on four publicly available datasets across eight comparative systems "
    "with ablation studies, statistical significance testing, and a live code "
    "repository (https://github.com/DilliBabu911/nsedq). The topic — neuro-symbolic "
    "AI applied to enterprise data governance — sits squarely within ESWA's core scope.",
    after=10
)

# ── Section 3 ─────────────────────────────────────────────────────────────────
para("Relationship to prior work", bold=True, after=4)
para(
    "This paper substantially extends a prior conference paper (NS-DQA, ICIIPC 2026) "
    "by replacing statistical rule inference with LLM-based CDL constraint generation, "
    "adding Z3 SMT solver verification with MUC extraction, introducing the MUC-CPC "
    "counter-prompting mechanism, implementing five-objective MOILP repair selection "
    "with formal proof certificates, and adding the Continuous Governance Learning "
    "Engine. The conference paper is cited as reference [13] and the extension is "
    "disclosed in the text.",
    after=10
)

# ── Section 4 ─────────────────────────────────────────────────────────────────
para("Patent disclosure", bold=True, after=4)
para(
    "The system described in this paper is the subject of an Indian patent application "
    "filed under the Indian Patents Act 1970, Form 2, on 30 August 2026. "
    "This is disclosed in the Acknowledgements section.",
    after=10
)

# ── Declarations ─────────────────────────────────────────────────────────────
para("Declarations", bold=True, after=4)
declarations = [
    "This manuscript has not been submitted to any other journal and is not under consideration elsewhere.",
    "All authors have approved the manuscript and agree with its submission to ESWA.",
    "The author declares no competing financial or non-financial interests.",
    "No external funding was received.",
    "All datasets used are publicly available; no personally identifiable information was used.",
    "I am submitting under the Subscription (Traditional) route. I am not requesting open access.",
]
for d in declarations:
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(d)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    p.paragraph_format.space_after = Pt(3)

doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ── Closing ───────────────────────────────────────────────────────────────────
para(
    "I would be grateful for the opportunity to have this work reviewed by experts "
    "in neuro-symbolic AI, data quality, and formal methods. I am happy to respond "
    "to reviewer comments promptly.",
    before=6, after=10
)
para("Thank you for your consideration.", after=16)
para("Yours sincerely,", after=16)
para("Dilli Babu Devineni", bold=True, after=2)
para("dilli.devineni@researcher.net", after=2)
para("ORCID: 0009-0003-8121-2530", after=0)

doc.save(OUT)
size = os.path.getsize(OUT) // 1024
print(f"[OK] Cover letter → {OUT}  ({size} KB)")
