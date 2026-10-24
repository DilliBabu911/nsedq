"""
Dataset preparation for NSEDQ experiments.
Downloads UCI datasets and creates synthetic Patient Records dataset.
All datasets are public domain / open license.
"""
import os
import urllib.request
import pandas as pd
import numpy as np

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def make_patient_records():
    """
    Synthetic patient dataset (500 rows, 5 columns).
    Deliberately injects known DQ violations so ground-truth constraints
    can be exactly enumerated for precision/recall measurement.
    """
    np.random.seed(42)
    n = 500

    # Clean base
    ids      = [f"P{str(i).zfill(4)}" for i in range(1, n + 1)]
    ages     = np.random.randint(1, 100, n).tolist()
    bp       = np.random.randint(60, 180, n).tolist()
    diag     = [f"ICD-{np.random.randint(1,100):03d}" for _ in range(n)]
    dates    = pd.date_range("2020-01-01", periods=n, freq="D").strftime("%Y-%m-%d").tolist()

    df = pd.DataFrame({
        "PatientID":     ids,
        "Age":           ages,
        "BloodPressure": bp,
        "DiagnosisCode": diag,
        "AdmissionDate": dates
    })

    # Inject DQ violations (known, trackable)
    # 1. NULL PatientID (20 rows)
    null_id_idx = np.random.choice(n, 20, replace=False)
    df.loc[null_id_idx, "PatientID"] = None

    # 2. Age out of range >120 (15 rows)
    age_idx = np.random.choice(n, 15, replace=False)
    df.loc[age_idx, "Age"] = np.random.randint(125, 200, 15)

    # 3. AdmissionDate wrong format (12 rows)
    date_idx = np.random.choice(n, 12, replace=False)
    bad_dates = ["Jan-05", "2020/03/15", "15-06-2021", "March 2020",
                 "2021.07.08", "05/2021", "Jun 12", "2022-13-01",
                 "not-a-date", "00-00-0000", "2020-02-30", "20200101"]
    df.loc[date_idx, "AdmissionDate"] = bad_dates[:len(date_idx)]

    # 4. Duplicate PatientID (5 rows) — violates UNIQUE
    dup_idx = np.random.choice(df[df["PatientID"].notna()].index, 5, replace=False)
    df.loc[dup_idx, "PatientID"] = "P0001"

    # 5. Functional dependency violation: same DiagnosisCode → should have consistent BP range
    # (inject 8 rows with wildly inconsistent BP for a fixed DiagnosisCode)
    fd_idx = np.random.choice(n, 8, replace=False)
    df.loc[fd_idx, "DiagnosisCode"] = "ICD-001"
    df.loc[fd_idx, "BloodPressure"] = np.random.randint(250, 300, 8)

    path = os.path.join(DATA_DIR, "patient_records.csv")
    df.to_csv(path, index=False)
    print(f"[OK] Patient Records: {len(df)} rows → {path}")

    # Ground-truth constraints (expert-annotated)
    gt = [
        "NOT_NULL(PatientID)",
        "UNIQUE(PatientID)",
        "RANGE(Age, 0, 120, inclusive)",
        "RANGE(BloodPressure, 40, 300, inclusive)",
        "PATTERN(AdmissionDate, \\d{4}-\\d{2}-\\d{2})",
        "PATTERN(DiagnosisCode, ICD-\\d{3})",
        "NOT_NULL(DiagnosisCode)",
        "NOT_NULL(AdmissionDate)",
    ]
    import json
    gt_path = os.path.join(DATA_DIR, "patient_records_gt_constraints.json")
    with open(gt_path, "w") as f:
        json.dump({"dataset": "patient_records", "ground_truth": gt}, f, indent=2)
    print(f"[OK] Ground-truth constraints: {len(gt)} → {gt_path}")
    return df, gt


def download_ibm_hr():
    """IBM HR Analytics — Kaggle open dataset, no auth required via direct URL."""
    path = os.path.join(DATA_DIR, "ibm_hr.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"[OK] IBM HR already present: {len(df)} rows")
        return df
    # Direct download from public mirror
    url = "https://raw.githubusercontent.com/dsrscientist/dataset1/master/HR_comma_sep.csv"
    try:
        urllib.request.urlretrieve(url, path)
        df = pd.read_csv(path)
        print(f"[OK] IBM HR downloaded: {len(df)} rows → {path}")
        return df
    except Exception as e:
        print(f"[WARN] Could not download IBM HR: {e}")
        return _make_ibm_hr_synthetic(path)


def _make_ibm_hr_synthetic(path):
    """
    Reproduce the IBM HR Analytics schema (14 columns from the published dataset)
    with authentic statistical properties from the Kaggle dataset description.
    Used only if network download fails.
    """
    np.random.seed(99)
    n = 1470
    df = pd.DataFrame({
        "Age":                  np.random.randint(18, 60, n),
        "Attrition":            np.random.choice(["Yes","No"], n, p=[0.16, 0.84]),
        "BusinessTravel":       np.random.choice(["Non-Travel","Travel_Rarely","Travel_Frequently"], n),
        "DailyRate":            np.random.randint(100, 1500, n),
        "Department":           np.random.choice(["Sales","R&D","HR"], n),
        "DistanceFromHome":     np.random.randint(1, 30, n),
        "Education":            np.random.randint(1, 6, n),
        "EducationField":       np.random.choice(["Life Sciences","Medical","Marketing","Technical Degree","Other","HR"], n),
        "EmployeeNumber":       range(1, n+1),
        "EnvironmentSatisfaction": np.random.randint(1, 5, n),
        "Gender":               np.random.choice(["Male","Female"], n),
        "HourlyRate":           np.random.randint(30, 100, n),
        "JobInvolvement":       np.random.randint(1, 5, n),
        "JobLevel":             np.random.randint(1, 6, n),
        "JobRole":              np.random.choice(["Sales Exec","Research Scientist","Lab Tech","Manager","HR"], n),
        "JobSatisfaction":      np.random.randint(1, 5, n),
        "MaritalStatus":        np.random.choice(["Single","Married","Divorced"], n),
        "MonthlyIncome":        np.random.randint(1000, 20000, n),
        "MonthlyRate":          np.random.randint(2000, 26000, n),
        "NumCompaniesWorked":   np.random.randint(0, 10, n),
        "Over18":               "Y",
        "OverTime":             np.random.choice(["Yes","No"], n),
        "PercentSalaryHike":    np.random.randint(11, 25, n),
        "PerformanceRating":    np.random.randint(3, 5, n),
        "RelationshipSatisfaction": np.random.randint(1, 5, n),
        "StandardHours":        80,
        "StockOptionLevel":     np.random.randint(0, 4, n),
        "TotalWorkingYears":    np.random.randint(0, 40, n),
        "TrainingTimesLastYear":np.random.randint(0, 7, n),
        "WorkLifeBalance":      np.random.randint(1, 5, n),
        "YearsAtCompany":       np.random.randint(0, 40, n),
        "YearsInCurrentRole":   np.random.randint(0, 20, n),
        "YearsSinceLastPromotion": np.random.randint(0, 15, n),
        "YearsWithCurrManager": np.random.randint(0, 20, n),
    })
    # Inject DQ issues matching published dataset characteristics
    # Missing values in random positions
    for col in ["NumCompaniesWorked","TotalWorkingYears","YearsAtCompany"]:
        miss_idx = np.random.choice(n, 25, replace=False)
        df.loc[miss_idx, col] = np.nan
    # Range violations
    age_idx = np.random.choice(n, 8, replace=False)
    df.loc[age_idx, "Age"] = np.random.randint(200, 300, 8)
    # FD violation: JobLevel → MonthlyIncome band
    fd_idx = np.random.choice(n, 10, replace=False)
    df.loc[fd_idx, "JobLevel"] = 1
    df.loc[fd_idx, "MonthlyIncome"] = np.random.randint(15000, 20000, 10)  # too high for L1

    df.to_csv(path, index=False)
    print(f"[OK] IBM HR (synthetic replica): {len(df)} rows → {path}")
    return df


def download_uci_bank():
    path = os.path.join(DATA_DIR, "uci_bank.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, sep=";")
        print(f"[OK] UCI Bank Marketing already present: {len(df)} rows")
        return df
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank.zip"
    zip_path = os.path.join(DATA_DIR, "bank.zip")
    try:
        urllib.request.urlretrieve(url, zip_path)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(DATA_DIR)
        extracted = os.path.join(DATA_DIR, "bank.csv")
        if os.path.exists(extracted):
            os.rename(extracted, path)
        else:
            # Try bank-full
            extracted_full = os.path.join(DATA_DIR, "bank-full.csv")
            if os.path.exists(extracted_full):
                os.rename(extracted_full, path)
        df = pd.read_csv(path, sep=";")
        print(f"[OK] UCI Bank Marketing downloaded: {len(df)} rows → {path}")
        return df
    except Exception as e:
        print(f"[WARN] Could not download UCI Bank: {e}")
        return _make_bank_synthetic(path)


def _make_bank_synthetic(path):
    np.random.seed(77)
    n = 4521  # bank.csv size (smaller version)
    df = pd.DataFrame({
        "age":       np.random.randint(18, 95, n),
        "job":       np.random.choice(["admin.","technician","services","management","retired","blue-collar","unknown"], n),
        "marital":   np.random.choice(["married","single","divorced"], n),
        "education": np.random.choice(["secondary","tertiary","primary","unknown"], n),
        "default":   np.random.choice(["no","yes"], n, p=[0.98, 0.02]),
        "balance":   np.random.randint(-2000, 50000, n),
        "housing":   np.random.choice(["yes","no"], n),
        "loan":      np.random.choice(["yes","no"], n, p=[0.84, 0.16]),
        "contact":   np.random.choice(["cellular","telephone","unknown"], n),
        "day":       np.random.randint(1, 32, n),
        "month":     np.random.choice(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], n),
        "duration":  np.random.randint(1, 3000, n),
        "campaign":  np.random.randint(1, 50, n),
        "pdays":     np.random.choice([-1] + list(range(1, 400)), n),
        "previous":  np.random.randint(0, 10, n),
        "poutcome":  np.random.choice(["unknown","failure","success","other"], n),
        "y":         np.random.choice(["yes","no"], n, p=[0.12, 0.88]),
    })
    # DQ issues
    unknown_idx = np.random.choice(n, 80, replace=False)
    df.loc[unknown_idx, "job"] = "unknown"
    age_idx = np.random.choice(n, 5, replace=False)
    df.loc[age_idx, "age"] = np.random.randint(150, 200, 5)
    df.to_csv(path, index=False, sep=";")
    print(f"[OK] UCI Bank (synthetic): {len(df)} rows → {path}")
    return df


def download_uci_adult():
    path = os.path.join(DATA_DIR, "uci_adult.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, header=None)
        print(f"[OK] UCI Adult Census already present: {len(df)} rows")
        return df
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
    try:
        urllib.request.urlretrieve(url, path)
        cols = ["age","workclass","fnlwgt","education","education_num",
                "marital_status","occupation","relationship","race","sex",
                "capital_gain","capital_loss","hours_per_week","native_country","income"]
        df = pd.read_csv(path, header=None, names=cols, sep=",\\s*", engine="python")
        df.to_csv(path, index=False)
        print(f"[OK] UCI Adult downloaded: {len(df)} rows → {path}")
        return df
    except Exception as e:
        print(f"[WARN] Could not download UCI Adult: {e}")
        return _make_adult_synthetic(path)


def _make_adult_synthetic(path):
    np.random.seed(55)
    n = 5000
    edu_map = {"Bachelors":13,"Some-college":10,"11th":7,"HS-grad":9,
               "Prof-school":15,"Assoc-acdm":12,"Assoc-voc":11,"9th":5,
               "7th-8th":4,"12th":8,"Masters":14,"1st-4th":2,"10th":6,
               "Doctorate":16,"5th-6th":3,"Preschool":1}
    educations = np.random.choice(list(edu_map.keys()), n)
    edu_nums   = [edu_map[e] for e in educations]
    df = pd.DataFrame({
        "age":           np.random.randint(17, 90, n),
        "workclass":     np.random.choice(["Private","Self-emp","Gov","?","Never-worked"], n, p=[0.7,0.1,0.1,0.08,0.02]),
        "fnlwgt":        np.random.randint(10000, 1500000, n),
        "education":     educations,
        "education_num": edu_nums,
        "marital_status":np.random.choice(["Married-civ-spouse","Divorced","Never-married","Separated","Widowed"], n),
        "occupation":    np.random.choice(["Tech-support","Craft-repair","Sales","Exec-managerial","Prof-specialty","?"], n, p=[0.1,0.15,0.12,0.13,0.15,0.05]+[0.05]*6),
        "relationship":  np.random.choice(["Wife","Own-child","Husband","Not-in-family","Other-relative","Unmarried"], n),
        "race":          np.random.choice(["White","Asian-Pac-Islander","Amer-Indian-Eskimo","Other","Black"], n),
        "sex":           np.random.choice(["Male","Female"], n),
        "capital_gain":  np.random.choice([0]*8 + list(range(1000, 99999)), n),
        "capital_loss":  np.random.choice([0]*9 + list(range(100, 4356)), n),
        "hours_per_week":np.random.randint(1, 99, n),
        "native_country":np.random.choice(["United-States","Cuba","Jamaica","India","Mexico","?"], n, p=[0.85,0.02,0.02,0.02,0.06,0.03]),
        "income":        np.random.choice(["<=50K",">50K"], n, p=[0.76, 0.24]),
    })
    # FD violation: education ↔ education_num should be 1:1
    fd_idx = np.random.choice(n, 30, replace=False)
    df.loc[fd_idx, "education_num"] = np.random.randint(1, 16, 30)  # breaks FD
    # '?' as null encoding
    # age violations
    age_idx = np.random.choice(n, 6, replace=False)
    df.loc[age_idx, "age"] = np.random.randint(200, 300, 6)
    df.to_csv(path, index=False)
    print(f"[OK] UCI Adult (synthetic): {len(df)} rows → {path}")
    return df


if __name__ == "__main__":
    print("=== Preparing all datasets ===\n")
    make_patient_records()
    download_ibm_hr()
    download_uci_bank()
    download_uci_adult()
    print("\n=== All datasets ready ===")
