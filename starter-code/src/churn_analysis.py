from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# --- Wire up the insurance-eda-toolkit skill -------------------------------------
TOOLKIT_ASSETS = Path(__file__).resolve().parents[2] / "skills" / "insurance-eda-toolkit" / "assets"
sys.path.insert(0, str(TOOLKIT_ASSETS))
import eda_utils as eda  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "Insurance_Customer_Churn_Assignment_Pack.xlsx"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "artifacts"
TEMPLATE_PATH = ARTIFACTS_DIR / "Insurance_Churn_Analytics_Output_Template.xlsx"


# ---------------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------------
def load_data(path: Path = DATA_PATH) -> dict[str, pd.DataFrame]:
    """Load all five sheets from the assignment pack."""
    return {
        "customer_master": pd.read_excel(path, sheet_name="Customer_Master"),
        "policy_data": pd.read_excel(path, sheet_name="Policy_Data"),
        "claims_data": pd.read_excel(path, sheet_name="Claims_Data"),
        "service_interactions": pd.read_excel(path, sheet_name="Service_Interactions"),
        "data_dictionary": pd.read_excel(path, sheet_name="Data_Dictionary"),
    }


# ---------------------------------------------------------------------------------
# 2. Data-quality checks
# ---------------------------------------------------------------------------------
def run_data_quality_checks(data: dict[str, pd.DataFrame]) -> dict:
    """Run referential integrity, derived column consistency, and rollup checks."""
    cm = data["customer_master"]
    pol = data["policy_data"]
    clm = data["claims_data"]
    srv = data["service_interactions"]

    integrity_policy = eda.check_referential_integrity(cm, "Customer_ID", pol, "Customer_ID", "Policy_Data")
    integrity_claims = eda.check_referential_integrity(cm, "Customer_ID", clm, "Customer_ID", "Claims_Data")
    integrity_service = eda.check_referential_integrity(cm, "Customer_ID", srv, "Customer_ID", "Service_Interactions")

    consistency_product = eda.check_column_consistency(
        cm, "Active_Product_Count", ["Auto_Policy", "Health_Policy", "Home_Policy", "Life_Policy"]
    )

    rollup_claims = eda.validate_rollup_against_master(
        cm, "Customer_ID", "Claims_Count_12M",
        clm, "Customer_ID", {"Claim_ID": "count"}, "Claim_ID"
    )

    dup_id = int(cm["Customer_ID"].duplicated().sum())
    missing_id = int(cm["Customer_ID"].isna().sum())
    invalid_churn = int((~cm["Historical_Churn_Flag"].isin([0, 1])).sum())
    negative_prem = int((cm["Annual_Premium"] <= 0).sum())
    invalid_renewal = int((cm["Days_To_Renewal"] < 0).sum())

    return {
        "integrity_policy": integrity_policy,
        "integrity_claims": integrity_claims,
        "integrity_service": integrity_service,
        "consistency_product": consistency_product,
        "rollup_claims": rollup_claims,
        "checks_summary": {
            "Duplicate Customer_ID": (dup_id, "Pass" if dup_id == 0 else "Fail", "Unique identifier clean; 0 duplicates found", "None"),
            "Missing Customer_ID": (missing_id, "Pass" if missing_id == 0 else "Fail", "No missing IDs in master record", "None"),
            "Missing / Invalid Churn Flag": (invalid_churn, "Pass" if invalid_churn == 0 else "Fail", "All records have binary 0/1 churn flag", "None"),
            "Negative / Implausible Premium": (negative_prem, "Pass" if negative_prem == 0 else "Fail", "All premiums strictly positive (min ₹300)", "None"),
            "Invalid Days_To_Renewal": (invalid_renewal, "Pass" if invalid_renewal == 0 else "Fail", "All renewal windows valid (5 to 365 days)", "None"),
            "Orphan Policy Records": (integrity_policy["orphan_rows"], "Pass" if integrity_policy["is_clean"] else "Fail", f"{integrity_policy['orphan_rows']} orphan policy records", "None"),
            "Orphan Claim Records": (integrity_claims["orphan_rows"], "Pass" if integrity_claims["is_clean"] else "Fail", f"{integrity_claims['orphan_rows']} orphan claims records", "None"),
            "Orphan Interaction Records": (integrity_service["orphan_rows"], "Pass" if integrity_service["is_clean"] else "Fail", f"{integrity_service['orphan_rows']} orphan service interaction records", "None"),
            "Active_Product_Count Consistency": (consistency_product["n_mismatch"], "Fail" if not consistency_product["is_consistent"] else "Pass", f"{consistency_product['pct_mismatch']}% mismatch against policy flags sum", "Audit upstream ETL pipeline")
        }
    }


# ---------------------------------------------------------------------------------
# 3. Baseline metrics
# ---------------------------------------------------------------------------------
def compute_baseline_metrics(customer_master: pd.DataFrame) -> dict:
    """Compute overall portfolio headline numbers."""
    total_customers = len(customer_master)
    churned_customers = int(customer_master["Historical_Churn_Flag"].sum())
    churn_rate = float(churned_customers / total_customers)
    avg_premium_overall = float(customer_master["Annual_Premium"].mean())
    avg_premium_churned = float(customer_master[customer_master["Historical_Churn_Flag"] == 1]["Annual_Premium"].mean())

    return {
        "total_customers": total_customers,
        "churned_customers": churned_customers,
        "overall_churn_rate": churn_rate,
        "avg_annual_premium": avg_premium_overall,
        "avg_premium_churned": avg_premium_churned,
    }


# ---------------------------------------------------------------------------------
# 4. Segment comparisons
# ---------------------------------------------------------------------------------
def compare_segments(customer_master: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calculate churn rates across key customer dimensions."""
    segments = ["Region", "Customer_Segment", "Acquisition_Channel", "Active_Product_Count"]
    results = {}
    for seg in segments:
        results[seg] = eda.rate_by_segment(customer_master, seg, outcome_col="Historical_Churn_Flag")
    return results


# ---------------------------------------------------------------------------------
# 5. Driver analysis
# ---------------------------------------------------------------------------------
def analyze_drivers(customer_master: pd.DataFrame) -> pd.DataFrame:
    """Evaluate condition lift across candidate churn drivers."""
    cm = customer_master
    drivers = {
        "Complaints": cm["Complaints_12M"] >= 1,
        "Near Renewal": cm["Days_To_Renewal"] <= 60,
        "Missed Payment": cm["Payment_Missed_12M"] >= 1,
        "Premium Increase": cm["Premium_Increase_Pct"] >= 12.0,
        "Service Contacts": cm["Service_Contacts_12M"] >= 3,
        "Multiple Claims": cm["Claims_Count_12M"] >= 2,
        "Low Digital Engagement": cm["Digital_Logins_90D"] <= 2,
        "Low Tenure": cm["Tenure_Years"] <= 1,
    }
    ranking = eda.multi_driver_ranking(cm, drivers, outcome_col="Historical_Churn_Flag")
    return ranking


# ---------------------------------------------------------------------------------
# 6. Retention prioritization
# ---------------------------------------------------------------------------------
def build_retention_tiers(customer_master: pd.DataFrame) -> pd.DataFrame:
    """Classify customers into actionable risk tiers based on risk stacking."""
    cm = customer_master.copy()
    f_complaint = cm["Complaints_12M"] >= 1
    f_renewal = cm["Days_To_Renewal"] <= 60
    f_missed = cm["Payment_Missed_12M"] >= 1
    f_premium = cm["Premium_Increase_Pct"] >= 12.0

    flag_count = f_complaint.astype(int) + f_missed.astype(int) + f_premium.astype(int)

    tier = pd.Series("Tier 3", index=cm.index)
    tier[(flag_count == 1) & (~f_renewal)] = "Tier 2"
    tier[(flag_count >= 2) | ((flag_count >= 1) & f_renewal)] = "Tier 1"

    cm["Priority_Tier"] = tier
    return cm


# ---------------------------------------------------------------------------------
# 7. Pipeline runner & export
# ---------------------------------------------------------------------------------
def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    cm = data["customer_master"]

    print("Running Data Quality Checks...")
    dq_results = run_data_quality_checks(data)
    
    print("Computing Baseline Metrics...")
    baseline = compute_baseline_metrics(cm)
    print(f"  Total Customers: {baseline['total_customers']}")
    print(f"  Churn Rate: {baseline['overall_churn_rate']:.2%}")

    print("Comparing Segments...")
    seg_results = compare_segments(cm)
    for name, df in seg_results.items():
        df.to_csv(ARTIFACTS_DIR / f"segment_{name.lower()}.csv", index=False)

    print("Analyzing Drivers...")
    driver_df = analyze_drivers(cm)
    driver_df.to_csv(ARTIFACTS_DIR / "driver_ranking.csv", index=False)

    print("Building Retention Tiers...")
    cm_tiered = build_retention_tiers(cm)
    tier_summary = eda.rate_by_segment(cm_tiered, "Priority_Tier", outcome_col="Historical_Churn_Flag")
    tier_summary.to_csv(ARTIFACTS_DIR / "retention_tiers_summary.csv", index=False)
    print("\nRetention Tiers Summary:")
    print(tier_summary)

    print("\nAll pipeline tasks executed successfully.")


if __name__ == "__main__":
    main()
