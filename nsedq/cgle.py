"""
NSEDQ Module 7: Continuous Governance Learning Engine (CGLE)
KS drift detection, ARIMA forecasting, ridge-regression weight adaptation.
"""
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings("ignore")


KS_ALPHA          = 0.05
PROACTIVE_DPS_THR = 0.20


def ks_drift_detection(prev_series: np.ndarray,
                        curr_series: np.ndarray) -> dict:
    """
    Two-sample KS test between two column value arrays.
    Returns detection dict.
    """
    if len(prev_series) < 5 or len(curr_series) < 5:
        return {"ks_stat": 0.0, "p_value": 1.0, "drift_detected": False}

    stat, p_val = scipy_stats.ks_2samp(prev_series, curr_series)
    critical    = scipy_stats.ks_2samp(prev_series, curr_series,
                                        alternative="two-sided")[0]
    # Critical value approximation for alpha=0.05
    n1, n2      = len(prev_series), len(curr_series)
    c_alpha     = 1.358 * np.sqrt((n1 + n2) / (n1 * n2))

    return {
        "ks_stat":        round(float(stat), 4),
        "critical_value": round(float(c_alpha), 4),
        "p_value":        round(float(p_val), 6),
        "drift_detected": bool(stat > c_alpha),
    }


def js_divergence(p: np.ndarray, q: np.ndarray, bins: int = 20) -> float:
    """Jensen-Shannon divergence between two samples."""
    p_hist, edges = np.histogram(p, bins=bins, density=True)
    q_hist, _     = np.histogram(q, bins=edges, density=True)
    # Smooth zeros
    p_hist = p_hist + 1e-10
    q_hist = q_hist + 1e-10
    p_hist /= p_hist.sum()
    q_hist /= q_hist.sum()
    m = 0.5 * (p_hist + q_hist)
    js = 0.5 * (scipy_stats.entropy(p_hist, m) + scipy_stats.entropy(q_hist, m))
    return round(float(js), 6)


def arima_forecast_dps(time_series: list, horizon: int = 1) -> dict:
    """
    Fit ARIMA(1,1,1) to a univariate time series and forecast DPS.
    Returns dict with forecast and DPS.
    """
    ts = np.array(time_series, dtype=float)
    if len(ts) < 4:
        return {"forecast": float(ts[-1]) if len(ts) > 0 else 0.0,
                "dps": 0.10, "order": "insufficient_data"}
    try:
        model  = ARIMA(ts, order=(1, 1, 1))
        fitted = model.fit()
        fc     = fitted.forecast(steps=horizon)
        forecast_val = float(fc.iloc[0] if hasattr(fc, "iloc") else fc[0])
        # DPS = normalised deviation from current mean
        current_mean = float(ts.mean())
        current_std  = float(ts.std()) + 1e-6
        dps = min(1.0, max(0.0, abs(forecast_val - current_mean) / (3 * current_std)))
        return {"forecast": round(forecast_val, 4), "dps": round(dps, 4),
                "order": "ARIMA(1,1,1)"}
    except Exception as e:
        return {"forecast": float(ts[-1]), "dps": 0.10, "order": f"failed:{e}"}


def ridge_adapt_weights(component_scores: np.ndarray,
                         acceptance_labels: np.ndarray,
                         lam: float = 0.01) -> np.ndarray:
    """
    Ridge-regularised least-squares regression to adapt CTS component weights.
    component_scores: shape (n_samples, 5) — NCS, SCS, OCS, HSS, BRC
    acceptance_labels: shape (n_samples,) — binary 1/0
    Returns adapted weight vector (5,).
    """
    X = np.array(component_scores, dtype=float)
    y = np.array(acceptance_labels, dtype=float)

    if X.shape[0] < 5:
        return np.array([0.20, 0.30, 0.20, 0.20, 0.10])

    # Ridge: w = (X'X + λI)^{-1} X'y
    XtX  = X.T @ X
    lam_I = lam * np.eye(XtX.shape[0])
    try:
        w_raw = np.linalg.solve(XtX + lam_I, X.T @ y)
        # Normalise to sum to 1, clip to [0.05, 0.50]
        w_raw = np.clip(w_raw, 0.05, 0.50)
        w_norm = w_raw / w_raw.sum()
        return w_norm.round(4)
    except np.linalg.LinAlgError:
        return np.array([0.20, 0.30, 0.20, 0.20, 0.10])


def bayesian_threshold_update(prior_alpha: float, prior_beta: float,
                               n_accepted: int, n_rejected: int) -> tuple:
    """
    Beta-Binomial Bayesian update of acceptance threshold.
    Returns (posterior_alpha, posterior_beta, updated_threshold).
    """
    post_alpha = prior_alpha + n_accepted
    post_beta  = prior_beta  + n_rejected
    # Posterior mean of Beta distribution
    post_mean  = post_alpha / (post_alpha + post_beta)
    return round(post_alpha, 2), round(post_beta, 2), round(post_mean, 4)


def compute_column_dps(df_segments: list) -> dict:
    """
    Given a list of DataFrame segments (temporal slices),
    compute per-column DPS using ARIMA on column means.
    Returns dict {col: dps_value}.
    """
    if len(df_segments) < 3:
        return {}

    dps_dict = {}
    num_cols = [c for c in df_segments[0].columns
                if np.issubdtype(df_segments[0][c].dtype, np.number)]

    for col in num_cols:
        means = [seg[col].dropna().mean() for seg in df_segments if len(seg[col].dropna()) > 0]
        if len(means) >= 3:
            result = arima_forecast_dps(means)
            dps_dict[col] = result["dps"]

    return dps_dict


def run_drift_evaluation(df: pd.DataFrame, n_segments: int = 10) -> dict:
    """
    Split df into n_segments temporal slices.
    Run KS drift detection between consecutive segments.
    Returns full drift report.
    """
    seg_size = len(df) // n_segments
    segments = [df.iloc[i*seg_size:(i+1)*seg_size].copy()
                for i in range(n_segments)]

    num_cols   = [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
    drift_log  = []
    dps_dict   = compute_column_dps(segments)

    for i in range(1, n_segments):
        for col in num_cols:
            prev = segments[i-1][col].dropna().values
            curr = segments[i][col].dropna().values
            if len(prev) < 5 or len(curr) < 5:
                continue
            ks = ks_drift_detection(prev, curr)
            js = js_divergence(prev, curr)
            drift_log.append({
                "segment_pair": (i-1, i),
                "column":       col,
                "ks_stat":      ks["ks_stat"],
                "drift_detected": ks["drift_detected"],
                "js_div":       js,
                "dps":          dps_dict.get(col, 0.10),
            })

    total_tests    = len(drift_log)
    total_detected = sum(1 for d in drift_log if d["drift_detected"])
    detection_rate = total_detected / total_tests if total_tests > 0 else 0.0

    return {
        "drift_log":      drift_log,
        "total_tests":    total_tests,
        "drifts_detected":total_detected,
        "detection_rate": round(detection_rate, 4),
        "dps_per_col":    dps_dict,
        "proactive_triggers": sum(1 for v in dps_dict.values() if v > PROACTIVE_DPS_THR),
    }
