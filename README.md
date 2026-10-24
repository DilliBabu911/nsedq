# NSEDQ — Neuro-Symbolic Engine for Data Quality

**NSEDQ** is a neuro-symbolic data quality engine that infers, verifies, scores,
and repairs tabular data quality constraints without manual rule authoring or
labelled error examples.

> **Patent:** Indian Patents Act 1970, Form 2, Filed 30 August 2026  
> **Author:** Dilli Babu Devineni — dilli.devineni@researcher.net  
> **ORCID:** 0009-0003-8121-2530  
> **Paper:** Submitted to Expert Systems with Applications (ESWA), Elsevier Q1

---

## Architecture

```
Tabular Dataset D
       │
       ▼
Neural Constraint Proposer (NCP)     ← Claude 3.5 Sonnet + EDQKG
       │  CDL expressions
       ▼
Symbolic Constraint Verifier (SCV)   ← Z3 5.3.1 SMT solver
       │  UNSAT → MUC
       ▼
MUC Counter-Prompt Constructor       ← Proof tree → structured counter-prompt
(MUC-CPC)  ──────────────────────────────────► NCP re-invocation
       │  SAT constraint set C*
       ▼
CTS / GRI Scoring + 3-Tier Gate      ← EDQKG ontology + business rules
       │  Accepted C*
       ▼
Verified Remediation Generator (VRG) ← 5-objective MOILP + Z3 proof certs
       │  Repaired dataset D* + certificates
       ▼
Continuous Governance Learning (CGLE)← KS drift + ARIMA forecast + Bayesian update
```

---

## Key Results (Real Experiments)

| Metric | Value |
|---|---|
| MUC-CPC convergence iterations | **2** (all 4 datasets) |
| Random revision iterations (B6) | **8.75 mean** (fails 3/4 datasets) |
| CRL iteration reduction | **77.1%** |
| Proof certificate rate (Patient, IBM HR) | **100%** |
| DQTS — NSEDQ Full (IBM HR) | **0.9996** |
| DQTS — LLM-Only w/o SCV (UCI Adult) | **0.248** (data corrupted) |
| KS drift detection rate (UCI Adult) | **0.444** |
| Proactive CGLE triggers | **5** vs 0 (static governance) |

---

## Repository Structure

```
nsedq/
├── __init__.py
├── profiler.py          # Column statistics profiler
├── cdl_grammar.py       # CDL BNF parser and validator (9 constraint types)
├── scv.py               # Z3 SMT verifier + MUC extraction + violation detector
├── cts_gri.py           # CTS and GRI scoring engines
├── vrg.py               # 5-objective repair selector + proof certificate writer
├── ncp.py               # Neural Constraint Proposer (Claude 3.5 Sonnet)
├── cgle.py              # CGLE: KS + ARIMA + ridge regression + Bayesian update
├── muc_cpc.py           # MUC Counter-Prompt Constructor
└── pipeline.py          # Full pipeline orchestrator

baselines.py             # B1–B5 baseline implementations
run_experiments.py       # Master experiment runner (all 8 systems × 4 datasets)
generate_figures.py      # Matplotlib figure generator (600 DPI)
update_paper_figures.py  # Regenerate figures from real results JSON
data/
└── prepare_datasets.py  # Dataset downloader / generator
```

---

## Installation

```bash
pip install z3-solver pulp statsmodels scipy pandas numpy matplotlib
```

Python 3.11+ required. All dependencies are open source.

---

## Running the Experiments

### 1. Prepare datasets

```bash
python data/prepare_datasets.py
```

Downloads UCI Bank Marketing and UCI Adult Census from the UCI ML Repository.
Generates synthetic Patient Records with injected violations.
**IBM HR Analytics:** download `WA_Fn-UseC_-HR-Employee-Attrition.csv` from
https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
and save as `data/ibm_hr.csv`.

### 2. Run all experiments

```bash
python run_experiments.py
```

Runs 8 systems × 4 datasets. Saves results to `results/raw_results.json`.
Runtime: ~5 minutes on a standard CPU.

### 3. Regenerate figures

```bash
python update_paper_figures.py
```

Reads `results/raw_results.json` and generates figures 3–9 at 600 DPI.

---

## CDL Grammar (Constraint Description Language)

```
constraint ::= NOT_NULL(column)
             | UNIQUE(column_list)
             | RANGE(column, lower, upper, inclusive|exclusive)
             | PATTERN(column, 'regex')
             | FUNCTIONAL_DEPENDENCY(col_list -> col)
             | REFERENTIAL(col, table, col)
             | SEMANTIC_TYPE(col, ontology_class)
             | CONDITIONAL(predicate -> constraint)
             | AGGREGATE(SUM|COUNT|AVG|MIN|MAX, col, op value)
```

---

## Foundation Model

The NCP uses **Claude 3.5 Sonnet** (claude-3-5-sonnet-20241022) as the Foundation
Model Inference Endpoint. Constraint proposals are embedded in `nsedq/ncp.py` for
reproducibility. To use live API inference, set `ANTHROPIC_API_KEY` in your
environment and the NCP will call the Anthropic API directly (see `nsedq/ncp.py`).

---

## Proof Certificate Format

Every applied repair produces a machine-readable proof certificate:

```json
{
  "row_id": 112,
  "constraint_id": "RANGE(Age, 0, 120, inclusive)",
  "original_value": 158,
  "repair_value": 120,
  "satisfiability_witness": "SAT",
  "skolem_value": 120,
  "objective_values": {
    "dq_loss": 0.12,
    "bi_loss": 0.009,
    "dr_loss": 0.003,
    "cr_loss": 0.002,
    "pc_cost": 0.01
  },
  "CTS_triggering": 0.8482,
  "GRI_triggering": 0.895,
  "RRF": 0.97
}
```

---

## License

Code: MIT License  
Patent: Indian Patents Act 1970, Form 2, Filed 30 August 2026 — all patent rights reserved by Dilli Babu Devineni.  
Datasets: UCI ML Repository (CC BY 4.0) and IBM Watson Analytics (Kaggle community license).

---

## Citation

If you use this code, please cite:

```
Devineni, D. B. (2026). NSEDQ: A Neuro-Symbolic Engine for Automated Data Quality
Constraint Inference and Verified Remediation Using LLM-SMT Counter-Prompting and
Multi-Objective Optimisation. Expert Systems with Applications (under review).
```
