"""
NSEDQ Module 2: CDL Grammar Validator
Parses and validates CDL constraint expressions against the BNF spec.
Returns structured constraint objects or raises CDLParseError.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Any


class CDLParseError(Exception):
    pass


@dataclass
class CDLConstraint:
    constraint_type: str          # NOT_NULL, UNIQUE, RANGE, PATTERN, etc.
    columns:         List[str]
    params:          dict = field(default_factory=dict)
    raw:             str  = ""

    def __str__(self):
        return self.raw


# ── Regex patterns for each constraint type ─────────────────────────────────

_ID     = r"[A-Za-z_][A-Za-z0-9_]*"
_IDS    = rf"{_ID}(?:\s*,\s*{_ID})*"
_NUM    = r"-?\d+(?:\.\d+)?"
_QUOTED = r"'[^']*'|\"[^\"]*\""
_INCL   = r"inclusive|exclusive"
_AGG    = r"SUM|COUNT|AVG|MIN|MAX"
_CMP    = r"<=|>=|!=|<|>|="

PATTERNS = {
    "NOT_NULL":             re.compile(rf"^NOT_NULL\(\s*({_ID})\s*\)$", re.I),
    "UNIQUE":               re.compile(rf"^UNIQUE\(\s*({_IDS})\s*\)$", re.I),
    "RANGE":                re.compile(rf"^RANGE\(\s*({_ID})\s*,\s*({_NUM})\s*,\s*({_NUM})\s*,\s*({_INCL})\s*\)$", re.I),
    "PATTERN":              re.compile(rf"^PATTERN\(\s*({_ID})\s*,\s*({_QUOTED})\s*\)$", re.I),
    "FUNCTIONAL_DEPENDENCY":re.compile(rf"^FUNCTIONAL_DEPENDENCY\(\s*({_IDS})\s*->\s*({_ID})\s*\)$", re.I),
    "REFERENTIAL":          re.compile(rf"^REFERENTIAL\(\s*({_ID})\s*,\s*({_ID})\s*,\s*({_ID})\s*\)$", re.I),
    "SEMANTIC_TYPE":        re.compile(rf"^SEMANTIC_TYPE\(\s*({_ID})\s*,\s*({_ID})\s*\)$", re.I),
    "NOT_NULL_MULTI":       re.compile(rf"^NOT_NULL\(\s*({_IDS})\s*\)$", re.I),
    # CONDITIONAL and AGGREGATE — structural check only (nested)
    "CONDITIONAL":          re.compile(r"^CONDITIONAL\(.*->.*\)$", re.I),
    "AGGREGATE":            re.compile(rf"^AGGREGATE\(\s*({_AGG})\s*,\s*({_ID})\s*,\s*({_CMP})\s*({_NUM})\s*\)$", re.I),
}


def parse_cdl(expr: str) -> CDLConstraint:
    """
    Parse a single CDL expression string into a CDLConstraint.
    Raises CDLParseError on failure.
    """
    expr = expr.strip()

    for ctype, pat in PATTERNS.items():
        m = pat.match(expr)
        if m:
            g = m.groups()
            if ctype == "NOT_NULL":
                return CDLConstraint("NOT_NULL", [g[0].strip()], raw=expr)
            if ctype == "NOT_NULL_MULTI":
                cols = [c.strip() for c in g[0].split(",")]
                return CDLConstraint("NOT_NULL", cols, raw=expr)
            if ctype == "UNIQUE":
                cols = [c.strip() for c in g[0].split(",")]
                return CDLConstraint("UNIQUE", cols, raw=expr)
            if ctype == "RANGE":
                return CDLConstraint("RANGE", [g[0].strip()],
                                     {"lower": float(g[1]), "upper": float(g[2]),
                                      "inclusivity": g[3].lower()}, raw=expr)
            if ctype == "PATTERN":
                regex_str = g[1].strip().strip("'\"")
                return CDLConstraint("PATTERN", [g[0].strip()],
                                     {"regex": regex_str}, raw=expr)
            if ctype == "FUNCTIONAL_DEPENDENCY":
                antecedents = [c.strip() for c in g[0].split(",")]
                return CDLConstraint("FUNCTIONAL_DEPENDENCY", antecedents,
                                     {"consequent": g[1].strip()}, raw=expr)
            if ctype == "REFERENTIAL":
                return CDLConstraint("REFERENTIAL", [g[0].strip()],
                                     {"ref_table": g[1].strip(), "ref_col": g[2].strip()},
                                     raw=expr)
            if ctype == "SEMANTIC_TYPE":
                return CDLConstraint("SEMANTIC_TYPE", [g[0].strip()],
                                     {"ontology_class": g[1].strip()}, raw=expr)
            if ctype == "CONDITIONAL":
                return CDLConstraint("CONDITIONAL", [], raw=expr)
            if ctype == "AGGREGATE":
                return CDLConstraint("AGGREGATE", [g[1].strip()],
                                     {"func": g[0], "op": g[2], "value": float(g[3])},
                                     raw=expr)

    raise CDLParseError(f"Cannot parse CDL expression: '{expr}'")


def validate_cdl_batch(expressions: List[str]) -> tuple:
    """
    Returns (valid_constraints, invalid_expressions).
    """
    valid   = []
    invalid = []
    for expr in expressions:
        try:
            c = parse_cdl(expr)
            valid.append(c)
        except CDLParseError as e:
            invalid.append({"expr": expr, "error": str(e)})
    return valid, invalid


def columns_exist_in_schema(constraint: CDLConstraint, schema_cols: List[str]) -> bool:
    """Check all referenced columns exist in dataset schema."""
    for col in constraint.columns:
        if col not in schema_cols:
            return False
    if constraint.constraint_type == "FUNCTIONAL_DEPENDENCY":
        if constraint.params.get("consequent") not in schema_cols:
            return False
    return True
