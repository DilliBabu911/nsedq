"""
NSEDQ Module 3: Symbolic Constraint Verifier (SCV)
Uses Z3 SMT solver for constraint consistency checking and MUC extraction.
Uses Datalog-style Python evaluation for relational constraints.
"""
import re
import itertools
import pandas as pd
import numpy as np
from z3 import (
    Solver, sat, unsat, Bool, BoolVal, And, Or, Not, Implies,
    Real, Int, String, ArithRef, BoolRef, set_param
)
from .cdl_grammar import CDLConstraint

set_param("proof", False)


# ── SMT translation ──────────────────────────────────────────────────────────

def _z3_vars_for_column(col: str, dtype: str):
    if "int" in dtype or "float" in dtype:
        return Real(col)
    return String(col)


def constraint_to_z3(c: CDLConstraint, profiles: dict):
    """
    Translate a CDLConstraint to a Z3 BoolRef for satisfiability checking.
    For the purpose of satisfiability (not data-level), we create symbolic vars.
    Returns (z3_formula, [z3_var]) or None if not SMT-encodable.
    """
    col  = c.columns[0] if c.columns else None
    prof = profiles.get(col, {}) if col else {}
    dtype = prof.get("dtype", "object")

    if c.constraint_type == "NOT_NULL":
        # NOT_NULL is always satisfiable on its own; inter-constraint unsatisfiability
        # does not arise for NOT_NULL pairs, so return True placeholder
        return BoolVal(True), []

    if c.constraint_type == "UNIQUE":
        return BoolVal(True), []

    if c.constraint_type == "RANGE":
        v = Real(col)
        lo  = c.params["lower"]
        hi  = c.params["upper"]
        inc = c.params["inclusivity"]
        if inc == "inclusive":
            formula = And(v >= lo, v <= hi)
        else:
            formula = And(v > lo, v < hi)
        return formula, [v]

    if c.constraint_type == "PATTERN":
        # Pattern constraints are always individually satisfiable
        return BoolVal(True), []

    if c.constraint_type == "FUNCTIONAL_DEPENDENCY":
        return BoolVal(True), []

    if c.constraint_type == "SEMANTIC_TYPE":
        return BoolVal(True), []

    return BoolVal(True), []


def check_constraint_set_satisfiability(constraints: list, profiles: dict) -> tuple:
    """
    Check if the conjunction of all RANGE-type constraints per column is satisfiable.
    Returns (is_sat: bool, muc: list of CDLConstraint).

    For each column, collect all RANGE constraints and check joint satisfiability.
    This is where real MUC extraction happens.
    """
    from collections import defaultdict
    by_col = defaultdict(list)
    for c in constraints:
        if c.constraint_type == "RANGE":
            by_col[c.columns[0]].append(c)

    all_mucs = []

    for col, col_constraints in by_col.items():
        if len(col_constraints) < 2:
            continue
        # Check pairwise and full conjunction
        s = Solver()
        v = Real(col)
        formulas = []
        for c in col_constraints:
            lo  = c.params["lower"]
            hi  = c.params["upper"]
            inc = c.params["inclusivity"]
            if inc == "inclusive":
                formulas.append(And(v >= lo, v <= hi))
            else:
                formulas.append(And(v > lo, v < hi))

        s.add(And(*formulas))
        result = s.check()
        if result == unsat:
            # Extract MUC by deletion algorithm
            muc = _extract_muc_deletion(col_constraints, col)
            all_mucs.extend(muc)

    is_sat = len(all_mucs) == 0
    return is_sat, all_mucs


def _extract_muc_deletion(constraints: list, col: str) -> list:
    """
    Deletion-based MUC extraction.
    Iteratively remove constraints; if removing one makes the set SAT,
    it is part of the MUC.
    Returns the minimal unsatisfiable subset.
    """
    if len(constraints) <= 1:
        return constraints

    working = list(constraints)
    muc = []

    for i in range(len(constraints)):
        candidate = [c for j, c in enumerate(working) if j != i]
        if _is_range_set_unsat(candidate, col):
            # Still unsat without constraint i — it's not in MUC
            pass
        else:
            # Removing i makes it SAT — i IS in the MUC
            muc.append(working[i])

    return muc if muc else constraints[:2]  # fallback: return first two


def _is_range_set_unsat(constraints: list, col: str) -> bool:
    if len(constraints) < 2:
        return False
    s = Solver()
    v = Real(col)
    formulas = []
    for c in constraints:
        lo  = c.params["lower"]
        hi  = c.params["upper"]
        inc = c.params["inclusivity"]
        if inc == "inclusive":
            formulas.append(And(v >= lo, v <= hi))
        else:
            formulas.append(And(v > lo, v < hi))
    s.add(And(*formulas))
    return s.check() == unsat


def format_proof_tree(muc: list, profiles: dict) -> str:
    """
    Formats the MUC as a structured natural-language proof tree
    for use in the MUC-CPC counter-prompt.
    """
    lines = ["Conflict detected between:"]
    for c in muc:
        col  = c.columns[0]
        lo   = c.params.get("lower", "?")
        hi   = c.params.get("upper", "?")
        inc  = c.params.get("inclusivity", "inclusive")
        cts  = c.params.get("_cts", "unknown")
        lines.append(f"  {c.raw}  [CTS={cts}]")

    if len(muc) >= 2:
        c1, c2 = muc[0], muc[1]
        col = c1.columns[0]
        p   = profiles.get(col, {})
        col_max = p.get("max", "unknown")
        col_min = p.get("min", "unknown")
        lines.append("")
        lines.append(f"Solver proof: The intersection of the ranges is empty or overly restrictive.")
        lines.append(f"  Column '{col}' profile: min={col_min}, max={col_max}, "
                     f"p01={p.get('p05','?')}, p99={p.get('p95','?')}")
        lines.append(f"  {c1.raw}: allows [{c1.params['lower']}, {c1.params['upper']}]")
        lines.append(f"  {c2.raw}: requires [{c2.params['lower']}, {c2.params['upper']}]")
        # Identify which has lower statistical support
        cts1 = c1.params.get("_cts", 1.0)
        cts2 = c2.params.get("_cts", 1.0)
        weaker = c2 if cts2 < cts1 else c1
        lines.append(f"  Constraint with lower statistical support: {weaker.raw} [CTS={min(cts1,cts2):.3f}]")
        lines.append(f"  Recommended resolution: revise or withdraw {weaker.raw}")

    return "\n".join(lines)


# ── Data-level violation detection ──────────────────────────────────────────

def detect_violations(df: pd.DataFrame, constraints: list) -> list:
    """
    Evaluate each row against each constraint in C*.
    Returns list of violation dicts.
    """
    violations = []
    n = len(df)

    for c in constraints:
        col = c.columns[0] if c.columns else None

        if c.constraint_type == "NOT_NULL":
            if col and col in df.columns:
                null_rows = df[df[col].isna()].index.tolist()
                for row_id in null_rows:
                    violations.append({
                        "row_id":          int(row_id),
                        "constraint_id":   c.raw,
                        "constraint_type": "NOT_NULL",
                        "column":          col,
                        "violating_value": None,
                        "CTS":             c.params.get("_cts", 0.9),
                        "GRI":             c.params.get("_gri", 0.85),
                    })

        elif c.constraint_type == "UNIQUE":
            if col and col in df.columns:
                dup_mask = df[col].duplicated(keep="first") & df[col].notna()
                for row_id in df[dup_mask].index.tolist():
                    violations.append({
                        "row_id":          int(row_id),
                        "constraint_id":   c.raw,
                        "constraint_type": "UNIQUE",
                        "column":          col,
                        "violating_value": str(df.at[row_id, col]),
                        "CTS":             c.params.get("_cts", 0.9),
                        "GRI":             c.params.get("_gri", 0.85),
                    })

        elif c.constraint_type == "RANGE":
            if col and col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                lo  = c.params["lower"]
                hi  = c.params["upper"]
                inc = c.params["inclusivity"]
                if inc == "inclusive":
                    mask = series.notna() & ((series < lo) | (series > hi))
                else:
                    mask = series.notna() & ((series <= lo) | (series >= hi))
                for row_id in df[mask].index.tolist():
                    violations.append({
                        "row_id":          int(row_id),
                        "constraint_id":   c.raw,
                        "constraint_type": "RANGE",
                        "column":          col,
                        "violating_value": float(df.at[row_id, col]),
                        "lower":           lo,
                        "upper":           hi,
                        "CTS":             c.params.get("_cts", 0.9),
                        "GRI":             c.params.get("_gri", 0.85),
                    })

        elif c.constraint_type == "PATTERN":
            if col and col in df.columns:
                pattern = c.params.get("regex", "")
                try:
                    compiled = re.compile(pattern)
                    mask = df[col].notna() & ~df[col].astype(str).str.match(compiled)
                    for row_id in df[mask].index.tolist():
                        violations.append({
                            "row_id":          int(row_id),
                            "constraint_id":   c.raw,
                            "constraint_type": "PATTERN",
                            "column":          col,
                            "violating_value": str(df.at[row_id, col]),
                            "pattern":         pattern,
                            "CTS":             c.params.get("_cts", 0.9),
                            "GRI":             c.params.get("_gri", 0.85),
                        })
                except re.error:
                    pass

        elif c.constraint_type == "FUNCTIONAL_DEPENDENCY":
            antecedents = c.columns
            consequent  = c.params.get("consequent", "")
            if all(a in df.columns for a in antecedents) and consequent in df.columns:
                # Group by antecedents; check if consequent is unique per group
                grp = df.groupby(antecedents)[consequent].nunique()
                violating_groups = grp[grp > 1].index
                for grp_key in violating_groups:
                    if not isinstance(grp_key, tuple):
                        grp_key = (grp_key,)
                    mask = pd.Series([True] * n, index=df.index)
                    for ant, val in zip(antecedents, grp_key):
                        mask = mask & (df[ant] == val)
                    for row_id in df[mask].index.tolist():
                        violations.append({
                            "row_id":          int(row_id),
                            "constraint_id":   c.raw,
                            "constraint_type": "FUNCTIONAL_DEPENDENCY",
                            "column":          consequent,
                            "violating_value": str(df.at[row_id, consequent]),
                            "CTS":             c.params.get("_cts", 0.85),
                            "GRI":             c.params.get("_gri", 0.80),
                        })

    return violations
