"""
NSEDQ Master Experiment Runner
Foundation Model: Claude 3.5 Sonnet (embedded proposals)
Runs all 8 systems × 4 datasets, collects real metrics, writes results JSON.
"""
import os, sys, json, warnings, time
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data")
RES  = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

from nsedq.pipeline import run_nsedq
from baselines      import (run_B1_great_expectations, run_B2_deequ,
                             run_B3_holoclean, run_B4_nsdqa, run_B5_llm_only)


def load_datasets():
    datasets = {}

    # ── Patient Records ───────────────────────────────────────────────────────
    df_pat = pd.read_csv(os.path.join(DATA, "patient_records.csv"))
    with open(os.path.join(DATA, "patient_records_gt_constraints.json")) as f:
        gt_pat = json.load(f)["ground_truth"]
    datasets["patient_records"] = (df_pat, gt_pat)

    # ── IBM HR ────────────────────────────────────────────────────────────────
    df_hr = pd.read_csv(os.path.join(DATA, "ibm_hr.csv"))
    # Fix: convert numeric columns
    for col in ["Age","MonthlyIncome","JobLevel","EmployeeNumber",
                "Education","JobSatisfaction","EnvironmentSatisfaction",
                "WorkLifeBalance","PerformanceRating","StockOptionLevel",
                "TotalWorkingYears","YearsAtCompany","TrainingTimesLastYear"]:
        if col in df_hr.columns:
            df_hr[col] = pd.to_numeric(df_hr[col], errors="coerce")
    gt_hr = [
        "NOT_NULL(Age)", "RANGE(Age, 18, 65, inclusive)",
        "NOT_NULL(EmployeeNumber)", "UNIQUE(EmployeeNumber)",
        "RANGE(MonthlyIncome, 1000, 20000, inclusive)",
        "RANGE(JobLevel, 1, 5, inclusive)",
        "FUNCTIONAL_DEPENDENCY(JobLevel -> MonthlyIncome)",
    ]
    datasets["ibm_hr"] = (df_hr, gt_hr)

    # ── UCI Bank Marketing ────────────────────────────────────────────────────
    df_bank = pd.read_csv(os.path.join(DATA, "uci_bank.csv"), sep=";")
    df_bank["age"]      = pd.to_numeric(df_bank["age"],      errors="coerce")
    df_bank["balance"]  = pd.to_numeric(df_bank["balance"],  errors="coerce")
    df_bank["duration"] = pd.to_numeric(df_bank["duration"], errors="coerce")
    df_bank["campaign"] = pd.to_numeric(df_bank["campaign"], errors="coerce")
    df_bank["day"]      = pd.to_numeric(df_bank["day"],      errors="coerce")
    gt_bank = [
        "NOT_NULL(age)", "RANGE(age, 18, 95, inclusive)",
        "NOT_NULL(balance)", "RANGE(duration, 0, 4918, inclusive)",
        "NOT_NULL(y)", "RANGE(campaign, 1, 63, inclusive)",
    ]
    datasets["uci_bank"] = (df_bank, gt_bank)

    # ── UCI Adult Census ──────────────────────────────────────────────────────
    df_adult = pd.read_csv(os.path.join(DATA, "uci_adult.csv"))
    # Fix Issue 3: convert "?" to NaN (UCI Adult null encoding)
    df_adult.replace(" ?", np.nan, inplace=True)
    df_adult.replace("?", np.nan, inplace=True)
    for col in ["age","education_num","hours_per_week","capital_gain",
                "capital_loss","fnlwgt"]:
        if col in df_adult.columns:
            df_adult[col] = pd.to_numeric(df_adult[col], errors="coerce")
    # Fix Issue 5 (CGLE): sort by age proxy for temporal structure
    if "age" in df_adult.columns:
        df_adult = df_adult.sort_values("age").reset_index(drop=True)
    gt_adult = [
        "NOT_NULL(age)", "RANGE(age, 17, 90, inclusive)",
        "NOT_NULL(income)", "RANGE(hours_per_week, 1, 99, inclusive)",
        "FUNCTIONAL_DEPENDENCY(education -> education_num)",
        "RANGE(education_num, 1, 16, inclusive)",
    ]
    datasets["uci_adult"] = (df_adult, gt_adult)

    # ── Wine Quality (UCI Red Wine) ───────────────────────────────────────────
    df_wine = pd.read_csv(os.path.join(DATA, "wine_quality.csv"))
    for col in df_wine.columns:
        df_wine[col] = pd.to_numeric(df_wine[col], errors="coerce")
    # Sort by quality for temporal CGLE structure
    df_wine = df_wine.sort_values("quality").reset_index(drop=True)
    with open(os.path.join(DATA, "wine_quality_gt.json")) as f:
        gt_wine = json.load(f)["ground_truth"]
    datasets["wine_quality"] = (df_wine, gt_wine)

    # ── German Credit (Statlog) ───────────────────────────────────────────────
    df_credit = pd.read_csv(os.path.join(DATA, "german_credit.csv"))
    for col in ["age", "duration", "credit_amount", "installment_rate",
                "existing_credits", "num_dependents", "residence_since"]:
        if col in df_credit.columns:
            df_credit[col] = pd.to_numeric(df_credit[col], errors="coerce")
    # Sort by age for temporal CGLE structure
    df_credit = df_credit.sort_values("age").reset_index(drop=True)
    with open(os.path.join(DATA, "german_credit_gt.json")) as f:
        gt_credit = json.load(f)["ground_truth"]
    datasets["german_credit"] = (df_credit, gt_credit)

    return datasets


def run_all_experiments():
    datasets = load_datasets()
    all_results = {}

    for ds_name, (df, gt) in datasets.items():
        print(f"\n{'#'*70}")
        print(f"DATASET: {ds_name}  ({len(df)} rows × {len(df.columns)} cols)")
        print(f"{'#'*70}")
        ds_results = {}

        # B8 — NSEDQ Full
        print("\n--- B8: NSEDQ Full ---")
        r = run_nsedq(df, ds_name, gt, use_llm=True)
        r["system"] = "B8_NSEDQ_Full"; ds_results["B8_NSEDQ_Full"] = r

        # B6 — NSEDQ w/o MUC-CPC
        print("\n--- B6: NSEDQ w/o MUC-CPC ---")
        r = run_nsedq(df, ds_name, gt, use_llm=True, ablate_muc_cpc=True)
        r["system"] = "B6_NSEDQ_wo_MUC_CPC"; ds_results["B6_NSEDQ_wo_MUC_CPC"] = r

        # B7 — NSEDQ w/o CGLE
        print("\n--- B7: NSEDQ w/o CGLE ---")
        r = run_nsedq(df, ds_name, gt, use_llm=True, ablate_cgle=True)
        r["system"] = "B7_NSEDQ_wo_CGLE"; ds_results["B7_NSEDQ_wo_CGLE"] = r

        # Ablation: w/o MOILP
        print("\n--- Ablation: w/o 5-obj MOILP ---")
        r = run_nsedq(df, ds_name, gt, use_llm=True, ablate_moilp=True)
        r["system"] = "Ablation_wo_MOILP"; ds_results["Ablation_wo_MOILP"] = r

        # Ablation: w/o EDQKG
        print("\n--- Ablation: w/o EDQKG ---")
        r = run_nsedq(df, ds_name, gt, use_llm=True, ablate_edqkg=True)
        r["system"] = "Ablation_wo_EDQKG"; ds_results["Ablation_wo_EDQKG"] = r

        # B1 — Great Expectations
        print("\n--- B1: Great Expectations ---")
        r = run_B1_great_expectations(df, ds_name, gt); ds_results["B1_GreatExpectations"] = r

        # B2 — Deequ
        print("\n--- B2: Deequ ---")
        r = run_B2_deequ(df, ds_name, gt); ds_results["B2_Deequ"] = r

        # B3 — HoloClean
        print("\n--- B3: HoloClean ---")
        r = run_B3_holoclean(df, ds_name, gt); ds_results["B3_HoloClean"] = r

        # B4 — NS-DQA
        print("\n--- B4: NS-DQA ---")
        r = run_B4_nsdqa(df, ds_name, gt); ds_results["B4_NSDQA"] = r

        # B5 — LLM-Only (Claude proposals, no SCV)
        print("\n--- B5: LLM-Only (no SCV, no MUC-CPC) ---")
        r = run_B5_llm_only(df, ds_name, gt); ds_results["B5_LLM_Only"] = r

        all_results[ds_name] = ds_results

    # Save
    raw_path = os.path.join(RES, "raw_results.json")
    with open(raw_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n[SAVED] {raw_path}")

    summary = build_summary_tables(all_results)
    sum_path = os.path.join(RES, "summary_tables.json")
    with open(sum_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[SAVED] {sum_path}")

    print_summary(summary)
    return all_results, summary


def build_summary_tables(all_results: dict) -> dict:
    systems_main = ["B1_GreatExpectations","B2_Deequ","B3_HoloClean",
                    "B4_NSDQA","B5_LLM_Only","B6_NSEDQ_wo_MUC_CPC",
                    "B7_NSEDQ_wo_CGLE","B8_NSEDQ_Full"]
    datasets = list(all_results.keys())

    def mean_metric(sys_id, metric):
        vals = [float(all_results[ds].get(sys_id, {}).get(metric, 0) or 0)
                for ds in datasets if metric in all_results[ds].get(sys_id, {})]
        return round(np.mean(vals), 4) if vals else None

    tbl2 = {s: {m: mean_metric(s, m)
                for m in ["constraint_precision","constraint_recall","crl_iterations"]}
            for s in systems_main}

    tbl3 = {s: {m: mean_metric(s, m)
                for m in ["repair_accuracy","proof_cert_rate","dqts_post_repair"]}
            for s in systems_main}

    tbl4 = {ds: {m: all_results[ds].get("B8_NSEDQ_Full", {}).get(m)
                 for m in ["mean_cts","mean_gri","acceptance_rate"]}
            for ds in datasets}

    bank_b8  = all_results.get("uci_bank", {}).get("B8_NSEDQ_Full", {})
    bank_b7  = all_results.get("uci_bank", {}).get("B7_NSEDQ_wo_CGLE", {})
    tbl5 = {
        "ks_detection_accuracy":  bank_b8.get("drift_detection_rate"),
        "proactive_triggers":     bank_b8.get("proactive_triggers"),
        "NSEDQ_wo_CGLE_triggers": bank_b7.get("proactive_triggers", 0),
    }

    abl_configs = ["B8_NSEDQ_Full","B6_NSEDQ_wo_MUC_CPC","B7_NSEDQ_wo_CGLE",
                   "Ablation_wo_MOILP","Ablation_wo_EDQKG"]
    tbl6 = {cfg: {m: all_results.get("ibm_hr", {}).get(cfg, {}).get(m)
                  for m in ["repair_accuracy","crl_iterations","proof_cert_rate",
                             "mean_cts","mean_gri","dqts_post_repair"]}
            for cfg in abl_configs}

    return {"table2": tbl2, "table3": tbl3, "table4": tbl4,
            "table5": tbl5, "table6": tbl6}


def print_summary(s: dict):
    print("\n" + "="*70)
    print("TABLE 2 — Constraint Inference")
    print(f"{'System':<30} {'CP':>8} {'CR':>8} {'MUC Iter':>10}")
    print("-"*58)
    for k, v in s["table2"].items():
        cp  = v.get("constraint_precision") or 0
        cr  = v.get("constraint_recall") or 0
        it  = v.get("crl_iterations") or 0
        print(f"{k:<30} {cp:>8.4f} {cr:>8.4f} {it:>10.2f}")

    print("\n" + "="*70)
    print("TABLE 3 — Repair Quality")
    print(f"{'System':<30} {'RA':>8} {'PCR':>8} {'DQTS':>8}")
    print("-"*56)
    for k, v in s["table3"].items():
        print(f"{k:<30} {v.get('repair_accuracy') or 0:>8.4f} "
              f"{v.get('proof_cert_rate') or 0:>8.4f} "
              f"{v.get('dqts_post_repair') or 0:>8.4f}")

    print("\n" + "="*70)
    print("TABLE 4 — CTS/GRI (NSEDQ Full)")
    print(f"{'Dataset':<25} {'CTS':>8} {'GRI':>8} {'Acc%':>8}")
    print("-"*51)
    for k, v in s["table4"].items():
        cts = v.get("mean_cts") or 0
        gri = v.get("mean_gri") or 0
        acc = (v.get("acceptance_rate") or 0)*100
        print(f"{k:<25} {cts:>8.4f} {gri:>8.4f} {acc:>7.1f}%")

    print("\n" + "="*70)
    print("TABLE 5 — CGLE Drift (UCI Bank)")
    for k, v in s["table5"].items():
        print(f"  {k}: {v}")

    print("\n" + "="*70)
    print("TABLE 6 — Ablation (IBM HR)")
    print(f"{'Config':<30} {'RA':>8} {'MUC':>6} {'PCR':>8} {'DQTS':>8}")
    print("-"*62)
    for k, v in s["table6"].items():
        ra   = v.get("repair_accuracy") or 0
        itr  = v.get("crl_iterations") or 0
        pcr  = v.get("proof_cert_rate") or 0
        dqts = v.get("dqts_post_repair") or 0
        print(f"{k:<30} {ra:>8.4f} {itr:>6.1f} {pcr:>8.4f} {dqts:>8.4f}")


if __name__ == "__main__":
    run_all_experiments()
