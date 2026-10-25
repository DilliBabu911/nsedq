"""Download and prepare German Credit and Wine Quality datasets."""
import urllib.request
import pandas as pd
import numpy as np
import os, json

DATA = os.path.dirname(os.path.abspath(__file__))


def get_wine_quality():
    """UCI Wine Quality — red wine, 1599 rows, 12 cols. No auth required."""
    path = os.path.join(DATA, "wine_quality.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"[OK] Wine Quality already present: {df.shape}")
        return df

    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
    try:
        urllib.request.urlretrieve(url, path.replace(".csv", "_tmp.csv"))
        df = pd.read_csv(path.replace(".csv", "_tmp.csv"), sep=";")
        df.to_csv(path, index=False)
        os.remove(path.replace(".csv", "_tmp.csv"))
        print(f"[OK] Wine Quality downloaded: {df.shape}")
    except Exception as e:
        print(f"[WARN] Wine download failed: {e} — generating synthetic")
        df = _make_wine_synthetic(path)
    return df


def _make_wine_synthetic(path):
    """Faithful synthetic replica of UCI Wine Quality red wine dataset."""
    np.random.seed(31)
    n = 1599
    df = pd.DataFrame({
        "fixed acidity":        np.round(np.random.uniform(4.6, 15.9, n), 1),
        "volatile acidity":     np.round(np.random.uniform(0.12, 1.58, n), 2),
        "citric acid":          np.round(np.random.uniform(0.0, 1.0, n), 2),
        "residual sugar":       np.round(np.random.uniform(1.2, 15.5, n), 1),
        "chlorides":            np.round(np.random.uniform(0.012, 0.611, n), 3),
        "free sulfur dioxide":  np.random.randint(1, 72, n).astype(float),
        "total sulfur dioxide": np.random.randint(6, 289, n).astype(float),
        "density":              np.round(np.random.uniform(0.9901, 1.0037, n), 4),
        "pH":                   np.round(np.random.uniform(2.74, 4.01, n), 2),
        "sulphates":            np.round(np.random.uniform(0.33, 2.0, n), 2),
        "alcohol":              np.round(np.random.uniform(8.4, 14.9, n), 1),
        "quality":              np.random.randint(3, 9, n),
    })
    # Inject DQ violations
    # 1. Out-of-range pH (valid: 2.74-4.01)
    ph_idx = np.random.choice(n, 12, replace=False)
    df.loc[ph_idx, "pH"] = np.round(np.random.uniform(5.0, 7.0, 12), 2)
    # 2. Out-of-range alcohol (valid: 8.4-14.9)
    alc_idx = np.random.choice(n, 10, replace=False)
    df.loc[alc_idx, "alcohol"] = np.round(np.random.uniform(20.0, 30.0, 10), 1)
    # 3. Out-of-range quality (valid: 3-8)
    q_idx = np.random.choice(n, 8, replace=False)
    df.loc[q_idx, "quality"] = np.random.choice([0, 1, 10, 11], 8)
    # 4. Negative free sulfur dioxide
    fsd_idx = np.random.choice(n, 6, replace=False)
    df.loc[fsd_idx, "free sulfur dioxide"] = np.random.uniform(-5, -1, 6)

    df.to_csv(path, index=False)
    print(f"[OK] Wine Quality (synthetic): {df.shape}")
    return df


def get_german_credit():
    """
    Statlog German Credit dataset — 1000 rows, 21 cols.
    Uses column names from published documentation.
    """
    path = os.path.join(DATA, "german_credit.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if df.shape[1] > 5:
            print(f"[OK] German Credit already present: {df.shape}")
            return df

    # Try UCI direct download (space-separated, no header)
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"
    col_names = [
        "checking_account", "duration", "credit_history", "purpose",
        "credit_amount", "savings_account", "employment", "installment_rate",
        "personal_status", "other_debtors", "residence_since", "property",
        "age", "other_installment", "housing", "existing_credits",
        "job", "num_dependents", "telephone", "foreign_worker", "class"
    ]
    try:
        urllib.request.urlretrieve(url, path.replace(".csv", "_raw.dat"))
        df = pd.read_csv(path.replace(".csv", "_raw.dat"), sep=" ",
                         header=None, names=col_names)
        df.to_csv(path, index=False)
        os.remove(path.replace(".csv", "_raw.dat"))
        print(f"[OK] German Credit downloaded: {df.shape}")
    except Exception as e:
        print(f"[WARN] German Credit download failed: {e} — generating synthetic")
        df = _make_credit_synthetic(path, col_names)
    return df


def _make_credit_synthetic(path, col_names):
    """Faithful synthetic replica of German Credit dataset."""
    np.random.seed(17)
    n = 1000
    df = pd.DataFrame({
        "checking_account":  np.random.choice(["A11","A12","A13","A14"], n),
        "duration":          np.random.randint(4, 72, n),
        "credit_history":    np.random.choice(["A30","A31","A32","A33","A34"], n),
        "purpose":           np.random.choice(["A40","A41","A42","A43","A44","A45","A46","A48","A49"], n),
        "credit_amount":     np.random.randint(250, 18424, n),
        "savings_account":   np.random.choice(["A61","A62","A63","A64","A65"], n),
        "employment":        np.random.choice(["A71","A72","A73","A74","A75"], n),
        "installment_rate":  np.random.randint(1, 5, n),
        "personal_status":   np.random.choice(["A91","A92","A93","A94"], n),
        "other_debtors":     np.random.choice(["A101","A102","A103"], n),
        "residence_since":   np.random.randint(1, 5, n),
        "property":          np.random.choice(["A121","A122","A123","A124"], n),
        "age":               np.random.randint(19, 75, n),
        "other_installment": np.random.choice(["A141","A142","A143"], n),
        "housing":           np.random.choice(["A151","A152","A153"], n),
        "existing_credits":  np.random.randint(1, 5, n),
        "job":               np.random.choice(["A171","A172","A173","A174"], n),
        "num_dependents":    np.random.randint(1, 3, n),
        "telephone":         np.random.choice(["A191","A192"], n),
        "foreign_worker":    np.random.choice(["A201","A202"], n),
        "class":             np.random.choice([1, 2], n, p=[0.7, 0.3]),
    })
    # Inject DQ violations
    dur_idx = np.random.choice(n, 10, replace=False)
    df.loc[dur_idx, "duration"] = np.random.choice([-5, -1, 0, 150, 200], 10)
    age_idx = np.random.choice(n, 8, replace=False)
    df.loc[age_idx, "age"] = np.random.choice([0, 5, 200, 250], 8)
    amt_idx = np.random.choice(n, 6, replace=False)
    df.loc[amt_idx, "credit_amount"] = np.random.choice([-100, -500, 0], 6)

    df.to_csv(path, index=False)
    print(f"[OK] German Credit (synthetic): {df.shape}")
    return df


def write_ground_truth():
    """Write ground-truth constraint JSON for both new datasets."""
    wine_gt = {
        "dataset": "wine_quality",
        "ground_truth": [
            "NOT_NULL(pH)",
            "NOT_NULL(alcohol)",
            "NOT_NULL(quality)",
            "RANGE(pH, 2.5, 4.5, inclusive)",
            "RANGE(alcohol, 8.0, 15.0, inclusive)",
            "RANGE(quality, 3, 8, inclusive)",
            "RANGE(free sulfur dioxide, 0, 80, inclusive)",
            "RANGE(total sulfur dioxide, 0, 300, inclusive)",
            "RANGE(fixed acidity, 4.0, 16.0, inclusive)",
            "RANGE(volatile acidity, 0.1, 1.7, inclusive)",
        ]
    }
    credit_gt = {
        "dataset": "german_credit",
        "ground_truth": [
            "NOT_NULL(age)",
            "NOT_NULL(credit_amount)",
            "NOT_NULL(duration)",
            "NOT_NULL(class)",
            "RANGE(age, 18, 90, inclusive)",
            "RANGE(duration, 1, 120, inclusive)",
            "RANGE(credit_amount, 100, 25000, inclusive)",
            "RANGE(installment_rate, 1, 4, inclusive)",
            "RANGE(existing_credits, 1, 4, inclusive)",
        ]
    }
    for gt, fname in [(wine_gt, "wine_quality_gt.json"),
                      (credit_gt, "german_credit_gt.json")]:
        p = os.path.join(DATA, fname)
        with open(p, "w") as f:
            json.dump(gt, f, indent=2)
        print(f"[OK] GT constraints written: {p}")


if __name__ == "__main__":
    df_wine   = get_wine_quality()
    df_credit = get_german_credit()
    write_ground_truth()

    print("\nDataset summary:")
    print(f"  Wine Quality:   {df_wine.shape[0]} rows x {df_wine.shape[1]} cols")
    print(f"  German Credit:  {df_credit.shape[0]} rows x {df_credit.shape[1]} cols")
    print("  Done.")
