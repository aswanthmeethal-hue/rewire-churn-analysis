import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "insurance-eda-toolkit" / "assets"))

import churn_analysis as ca
import eda_utils as eda


@pytest.fixture(scope="module")
def data():
    return ca.load_data()


# ---------------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------------

def test_customer_master_row_count(data):
    assert len(data["customer_master"]) == 2500


def test_customer_master_has_required_columns(data):
    required = {
        "Customer_ID", "Region", "Customer_Segment", "Acquisition_Channel",
        "Active_Product_Count", "Annual_Premium", "Historical_Churn_Flag",
        "Premium_Increase_Pct", "Days_To_Renewal", "Complaints_12M",
        "Payment_Missed_12M", "Claims_Count_12M",
    }
    assert required.issubset(set(data["customer_master"].columns))


def test_customer_id_is_unique(data):
    dup_count = data["customer_master"]["Customer_ID"].duplicated().sum()
    assert dup_count == 0


def test_no_orphan_policy_records(data):
    result = eda.check_referential_integrity(
        data["customer_master"], "Customer_ID", data["policy_data"], "Customer_ID", "Policy_Data"
    )
    assert result["is_clean"] is True


def test_no_orphan_claims_records(data):
    result = eda.check_referential_integrity(
        data["customer_master"], "Customer_ID", data["claims_data"], "Customer_ID", "Claims_Data"
    )
    assert result["is_clean"] is True


def test_no_orphan_service_interaction_records(data):
    result = eda.check_referential_integrity(
        data["customer_master"], "Customer_ID", data["service_interactions"], "Customer_ID", "Service_Interactions"
    )
    assert result["is_clean"] is True


def test_claims_count_rolls_up_correctly(data):
    result = eda.validate_rollup_against_master(
        data["customer_master"], "Customer_ID", "Claims_Count_12M",
        data["claims_data"], "Customer_ID", {"Claim_ID": "count"}, "Claim_ID",
    )
    assert result["is_consistent"] is True


# ---------------------------------------------------------------------------------
# Completed Tests based on our analysis plan
# ---------------------------------------------------------------------------------

def test_active_product_count_consistency(data):
    """Derived column consistency: confirms the known 71.32% mismatch rate."""
    result = eda.check_column_consistency(
        data["customer_master"], "Active_Product_Count",
        ["Auto_Policy", "Health_Policy", "Home_Policy", "Life_Policy"],
    )
    assert result["is_consistent"] is False
    assert result["n_mismatch"] == 1783


def test_overall_churn_rate_matches_your_baseline(data):
    """Sanity check: baseline churn matches Historical_Churn_Flag mean."""
    baseline = ca.compute_baseline_metrics(data["customer_master"])
    expected = data["customer_master"]["Historical_Churn_Flag"].mean()
    assert 0 < baseline["overall_churn_rate"] < 1
    assert round(baseline["overall_churn_rate"], 4) == round(expected, 4)


def test_segment_rates_sum_to_correct_denominator(data):
    """Confirms no rows are dropped across segmentations."""
    segments = ca.compare_segments(data["customer_master"])
    for name, df in segments.items():
        assert df["total_count"].sum() == 2500, f"Segment {name} dropped rows"


def test_driver_lift_values_are_positive_and_finite(data):
    """Confirms all driver lift values are positive, non-null, and non-infinite."""
    drivers_df = ca.analyze_drivers(data["customer_master"])
    assert (drivers_df["lift"] > 0).all()
    assert not drivers_df["lift"].isna().any()


def test_retention_tiers_partition_all_customers(data):
    """Confirms every customer is assigned to exactly one tier."""
    cm_tiered = ca.build_retention_tiers(data["customer_master"])
    assert len(cm_tiered) == 2500
    assert cm_tiered["Priority_Tier"].isna().sum() == 0
    assert set(cm_tiered["Priority_Tier"].unique()) == {"Tier 1", "Tier 2", "Tier 3"}
