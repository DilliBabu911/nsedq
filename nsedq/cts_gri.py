"""
NSEDQ Module 4: CTS and GRI Scoring Engine
Computes Constraint Trust Score and Governance Reliability Index.
"""
import math
import numpy as np
from .cdl_grammar import CDLConstraint


W_CTS = {"NCS": 0.20, "SCS": 0.30, "OCS": 0.20, "HSS": 0.20, "BRC": 0.10}
W_GRI = {"CAR": 0.25, "DRS": 0.25, "RRF": 0.25, "CES": 0.25}

# Acceptance thresholds
THETA_A  = 0.82   # CTS accept
THETA_H  = 0.60   # CTS hold threshold
GAMMA_A  = 0.78   # GRI accept


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_ncs(token_logprob: float = None) -> float:
    """
    Neural Confidence Score.
    sigmoid of token-level log-probability from Foundation Model.
    Claude proposals carry logprob values from LOGPROB_MAP.
    """
    if token_logprob is None:
        return 0.70
    return round(sigmoid(token_logprob), 4)


def compute_scs(constraint: CDLConstraint, profile: dict) -> float:
    """
    Statistical Confidence Score — type-specific formula.
    """
    ctype = constraint.constraint_type
    col   = constraint.columns[0] if constraint.columns else None

    if col is None or not profile:
        return 0.50

    if ctype == "NOT_NULL":
        return max(0.0, 1.0 - profile.get("null_rate", 0.0))

    if ctype == "UNIQUE":
        return min(1.0, profile.get("cardinality_ratio", 0.5))

    if ctype == "RANGE":
        lo = constraint.params["lower"]
        hi = constraint.params["upper"]
        col_min = profile.get("min", lo)
        col_max = profile.get("max", hi)
        col_vals_in = 0
        total_non_null = profile.get("n_rows", 1) * (1 - profile.get("null_rate", 0))
        if total_non_null == 0:
            return 0.5
        # Fraction of values within proposed range
        # Approximate from percentile info
        p01 = profile.get("p05", col_min)
        p99 = profile.get("p95", col_max)
        # If proposed range is tighter than p01-p99, score is lower
        range_coverage = min(1.0, (min(hi, p99) - max(lo, p01)) /
                             max(p99 - p01, 1e-6))
        return max(0.0, min(1.0, range_coverage))

    if ctype == "PATTERN":
        best_conf = profile.get("best_conformance", 0.5)
        regex = constraint.params.get("regex", "")
        pattern_name = profile.get("best_pattern", "")
        # If the proposed regex matches the best detected pattern, give higher SCS
        if pattern_name in regex or regex in pattern_name:
            return min(1.0, best_conf + 0.1)
        return best_conf

    if ctype == "FUNCTIONAL_DEPENDENCY":
        # Use normalised conditional entropy approximation
        # Without running full entropy: use cardinality of consequent as proxy
        return 0.72  # default for FDs without full data scan

    return 0.65


def compute_ocs(constraint: CDLConstraint, edqkg_match: str = "none") -> float:
    """
    Ontology Confidence Score.
    edqkg_match: "direct" | "indirect:N" | "none"
    """
    if edqkg_match == "direct":
        return 1.0
    if edqkg_match.startswith("indirect"):
        parts = edqkg_match.split(":")
        dist  = int(parts[1]) if len(parts) > 1 else 2
        return 1.0 / (1.0 + dist)
    # Use constraint type as heuristic
    type_scores = {
        "NOT_NULL":              0.80,
        "UNIQUE":                0.75,
        "RANGE":                 0.70,
        "PATTERN":               0.65,
        "FUNCTIONAL_DEPENDENCY": 0.70,
        "REFERENTIAL":           0.72,
        "SEMANTIC_TYPE":         0.68,
        "CONDITIONAL":           0.60,
        "AGGREGATE":             0.62,
    }
    return type_scores.get(constraint.constraint_type, 0.60)


def compute_hss(history: list = None) -> float:
    """
    Historical Stability Score.
    history: list of 1 (accepted) / 0 (rejected) over recent N cycles.
    First cycle: initialise from constraint type prior.
    """
    if not history:
        return 0.75  # prior for new schema
    if len(history) == 0:
        return 0.75
    return float(sum(history)) / len(history)


def compute_brc(constraint: CDLConstraint, business_rules: list = None) -> float:
    """
    Business Rule Confidence.
    1.0 if mandated by EDQKG business rule, else 0.0.
    """
    if not business_rules:
        return 0.0
    for rule in business_rules:
        if constraint.raw in rule or constraint.constraint_type in rule:
            return 1.0
    return 0.0


def compute_cts(constraint: CDLConstraint, profile: dict,
                token_logprob: float = None,
                edqkg_match: str = "none",
                history: list = None,
                business_rules: list = None,
                weights: dict = None) -> tuple:
    """
    Returns (CTS_score, component_dict).
    """
    w = weights if weights else W_CTS
    ncs = compute_ncs(token_logprob)
    scs = compute_scs(constraint, profile)
    ocs = compute_ocs(constraint, edqkg_match)
    hss = compute_hss(history)
    brc = compute_brc(constraint, business_rules)

    cts = (w["NCS"] * ncs + w["SCS"] * scs + w["OCS"] * ocs +
           w["HSS"] * hss + w["BRC"] * brc)

    return round(cts, 4), {"NCS": ncs, "SCS": scs, "OCS": ocs, "HSS": hss, "BRC": brc}


def compute_gri(cycle_history: list = None,
                staleness_events: int = 0,
                drift_prob: float = 0.1,
                drift_sensitivity: float = 0.2,
                revision_events: int = 0,
                weights: dict = None) -> tuple:
    """
    Returns (GRI_score, component_dict).
    """
    w = weights if weights else W_GRI
    n_cycles = len(cycle_history) if cycle_history else 1

    car = float(sum(cycle_history)) / n_cycles if cycle_history else 0.80
    drs = max(0.0, 1.0 - (staleness_events / max(n_cycles, 1)))
    rrf = max(0.0, 1.0 - drift_prob * drift_sensitivity)
    ces = max(0.0, 1.0 - (revision_events / max(n_cycles, 1)))

    gri = (w["CAR"] * car + w["DRS"] * drs +
           w["GRI_RRF"] * rrf + w["CES"] * ces) if "GRI_RRF" in w else (
           w["CAR"] * car + w["DRS"] * drs +
           w["RRF"] * rrf + w["CES"] * ces)

    return round(gri, 4), {"CAR": car, "DRS": drs, "RRF": rrf, "CES": ces}


def apply_acceptance_gate(cts: float, gri: float,
                          theta_a: float = None, gamma_a: float = None) -> str:
    """Returns 'accepted', 'held', or 'rejected'."""
    _ta = theta_a if theta_a is not None else THETA_A
    _ga = gamma_a if gamma_a is not None else GAMMA_A
    if cts >= _ta and gri >= _ga:
        return "accepted"
    if cts >= THETA_H:
        return "held"
    return "rejected"
