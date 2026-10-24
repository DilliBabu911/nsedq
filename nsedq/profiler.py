"""
NSEDQ Module 1: Column Profiler
Computes per-column statistics used by NCP and CTS scoring.
"""
import re
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def profile_dataframe(df: pd.DataFrame) -> dict:
    """
    Returns a dict keyed by column name, each value is a profile dict.
    """
    profiles = {}
    n = len(df)

    for col in df.columns:
        series = df[col]
        dtype  = str(series.dtype)
        is_num = pd.api.types.is_numeric_dtype(series)
        is_str = pd.api.types.is_string_dtype(series) or dtype == "object"

        null_count = int(series.isna().sum())
        null_rate  = null_count / n if n > 0 else 0.0
        non_null   = series.dropna()
        cardinality = int(non_null.nunique())
        cardinality_ratio = cardinality / len(non_null) if len(non_null) > 0 else 0.0

        p = {
            "column":           col,
            "dtype":            dtype,
            "n_rows":           n,
            "null_count":       null_count,
            "null_rate":        round(null_rate, 6),
            "cardinality":      cardinality,
            "cardinality_ratio": round(cardinality_ratio, 6),
            "top_values":       non_null.value_counts().head(5).to_dict(),
        }

        if is_num and len(non_null) > 0:
            vals = non_null.astype(float)
            p.update({
                "min":    float(vals.min()),
                "max":    float(vals.max()),
                "mean":   float(vals.mean()),
                "std":    float(vals.std()),
                "p05":    float(np.percentile(vals, 5)),
                "p25":    float(np.percentile(vals, 25)),
                "p50":    float(np.percentile(vals, 50)),
                "p75":    float(np.percentile(vals, 75)),
                "p95":    float(np.percentile(vals, 95)),
                "skew":   float(scipy_stats.skew(vals)),
            })
            # Detect likely range constraints
            p["suggested_range"] = {
                "lower": float(np.percentile(vals, 1)),
                "upper": float(np.percentile(vals, 99)),
            }

        if is_str and len(non_null) > 0:
            str_vals = non_null.astype(str)
            # Check common patterns
            patterns = {
                "date_iso":    r"^\d{4}-\d{2}-\d{2}$",
                "date_slash":  r"^\d{2}/\d{2}/\d{4}$",
                "icd_code":    r"^ICD-\d{3}$",
                "email":       r"^[^@]+@[^@]+\.[^@]+$",
                "phone":       r"^\+?[\d\s\-]{7,15}$",
                "alpha_only":  r"^[A-Za-z]+$",
                "alphanum":    r"^[A-Za-z0-9_\-\.]+$",
                "integer_str": r"^\d+$",
                "uuid":        r"^[0-9a-fA-F\-]{36}$",
            }
            conformance = {}
            for name, pat in patterns.items():
                matched = str_vals.str.match(pat).sum()
                conformance[name] = round(matched / len(str_vals), 4)
            p["pattern_conformance"] = conformance
            # Best pattern
            best = max(conformance, key=conformance.get)
            p["best_pattern"]     = best
            p["best_conformance"] = conformance[best]

        profiles[col] = p

    # Inter-column correlations (numeric only)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr(method="pearson").round(4)
        profiles["__correlations__"] = corr_matrix.to_dict()

    return profiles


def profile_summary_text(profiles: dict) -> str:
    """
    Renders profiles as a compact text block for LLM prompting.
    """
    lines = []
    for col, p in profiles.items():
        if col == "__correlations__":
            continue
        line = f"  {col} [{p['dtype']}]: nulls={p['null_rate']:.3f}, card={p['cardinality']}"
        if "min" in p:
            line += f", range=[{p['min']:.2f}, {p['max']:.2f}], mean={p['mean']:.2f}"
        if "best_pattern" in p and p["best_conformance"] > 0.5:
            line += f", pattern≈{p['best_pattern']}({p['best_conformance']:.2f})"
        lines.append(line)
    return "\n".join(lines)
