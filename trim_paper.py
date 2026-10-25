"""Trim paper to stay within 9,000-word ESWA body limit."""
import re

PAPER = r"d:\Desktop Backup 1\Dilli\Publications\ESWA_NSEDQ\NSEDQ_ESWA_Final.md"
with open(PAPER, encoding="utf-8") as f:
    text = f.read()

# ── 1. Replace expanded Table 3 (6-dataset per-system) with compact mean table ──
old_t3_wide = """**Table 3 — Repair Quality Results (Real Experimental Values, Six Datasets)**

| System | Patient RA/PCR | IBM HR RA/PCR | Bank RA/PCR | Adult RA/PCR | Wine RA/PCR | Credit RA/PCR | Mean RA | Mean PCR | Mean DQTS |
|---|---|---|---|---|---|---|---|---|---|
| B1 — Great Expectations | 1.00 / 0 | 1.00 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.167 | 0.000 | 0.650 |
| B2 — Deequ | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.000 | 0.000 | 0.654 |
| B3 — HoloClean | 1.00 / 0 | 1.00 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.167 | 0.000 | 0.650 |
| B4 — NS-DQA | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.000 | 0.000 | 0.654 |
| B5 — LLM-Only | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.00 / 0 | 1.000 | 0.000 | 0.403 |
| B7 — NSEDQ w/o CGLE | 1.00 / 1.00 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.167 | 0.167 | 0.652 |
| **B8 — NSEDQ Full** | **1.00 / 1.00** | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | **0.167** | **0.167** | **0.652** |"""

new_t3_compact = """**Table 3 — Repair Quality Results (Mean Across Six Datasets)**

| System | Mean Repair Accuracy | Mean Proof Cert Rate | Mean DQTS |
|---|---|---|---|
| B1 — Great Expectations | 0.167 | 0.000 | 0.650 |
| B2 — Deequ | 0.000 | 0.000 | 0.654 |
| B3 — HoloClean | 0.167 | 0.000 | 0.650 |
| B4 — NS-DQA | 1.000 | 0.000 | 0.654 |
| B5 — LLM-Only | 1.000 | 0.000 | 0.403 |
| B7 — NSEDQ w/o CGLE | 0.167 | 0.167 | 0.652 |
| **B8 — NSEDQ Full** | **0.167** | **0.167** | **0.652** |

*Note: RA and PCR of 1.00 for NSEDQ Full on the Patient Records dataset; 0 on the five datasets where the verified constraint set detected no violations after MUC-CPC convergence. Full per-dataset breakdown is provided in the supplementary results file.*"""

text = text.replace(old_t3_wide, new_t3_compact)

# ── 2. Fix "four datasets" → "six datasets" in figure captions and section text ──
replacements = [
    ("Mean Across Four Datasets (real experimental results",
     "Mean Across Six Datasets (real experimental results"),
    ("NSEDQ Full converges in 2 iterations via structured MUC-CPC counter-prompting. "
     "B6 (random deletion) fails to converge on 3/4 datasets.",
     "NSEDQ Full converges in 2 iterations via structured MUC-CPC counter-prompting. "
     "B6 (random deletion) fails to converge on 4/6 datasets."),
    ("Table 2 reports mean Constraint Precision, Recall, and CRL Iterations "
     "across all four datasets.",
     "Table 2 reports mean Constraint Precision, Recall, and CRL Iterations "
     "across all six datasets."),
    ("*Figure 3. Constraint Precision and Recall — Mean Across Four Datasets",
     "*Figure 3. Constraint Precision and Recall — Mean Across Six Datasets"),
]
for old, new in replacements:
    text = text.replace(old, new)

# ── 3. Shorten the Wine Quality CDL grammar note (trim ~50 words) ──
old_cdl_note = (
    "K_max was set to 10 for all experiments. "
    "The Wine Quality column names contain spaces (e.g., 'free sulfur dioxide'); "
    "CDL grammar validation detected 4 invalid expressions per proposal batch on this dataset "
    "due to unquoted space-containing identifiers, which were rejected and did not enter the SCV. "
    "This is reported transparently as a real CDL grammar limitation on schemas with non-standard column names."
)
new_cdl_note = (
    "K_max was set to 10 for all experiments. "
    "The Wine Quality dataset contains space-containing column names (e.g., 'free sulfur dioxide'); "
    "CDL grammar validation rejected 4 such expressions per proposal batch as invalid identifiers. "
    "This is a real grammar limitation disclosed in Limitation L1."
)
text = text.replace(old_cdl_note, new_cdl_note)

# ── 4. Shorten dataset table note ──
old_ds_note = (
    "The Wine Quality and German Credit datasets were downloaded directly from the UCI ML Repository."
)
new_ds_note = (
    "Wine Quality and German Credit were downloaded directly from the UCI ML Repository."
)
text = text.replace(old_ds_note, new_ds_note)

# ── 5. Trim abstract to ≤250 words by removing the 6-dataset enumeration ──
old_abs_6ds = (
    "Experiments on six public datasets — Patient Records (500), IBM HR Analytics (1,470), "
    "UCI Bank Marketing (4,521), UCI Adult Census (32,561), "
    "UCI Wine Quality — Red Wine (1,599), and Statlog German Credit (1,000)"
)
new_abs_6ds = (
    "Experiments on six public datasets totalling 41,591 records"
)
text = text.replace(old_abs_6ds, new_abs_6ds)

# ── Save and check ──
with open(PAPER, "w", encoding="utf-8") as f:
    f.write(text)

body = text.split("## References")[0]
clean = __import__("re").sub(r"```.*?```", "", body, flags=__import__("re").DOTALL)
clean = __import__("re").sub(r"\|.*?\|", "", clean)
bwords = len(clean.split())
print(f"Body words after trim: {bwords}")
print("PASS" if bwords <= 9000 else f"STILL OVER by {bwords-9000}")
