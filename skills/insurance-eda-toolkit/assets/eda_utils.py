"""
eda_utils.py -- Reusable exploratory-data-analysis helpers for insurance analytics.

These functions are deliberately generic: they work on ANY insurer customer/policy/claims
dataset, not just a churn use case. Typical uses across an insurance analytics curriculum:

    - Customer churn analysis
    - Customer segmentation / persona building
    - Cross-sell / next-best-product analysis
    - Claims frequency & severity analysis
    - Pricing / underwriting exploratory work
    - New-business / acquisition-channel performance

Design principles:
    1. Every function takes a pandas DataFrame (or several) and returns a DataFrame or dict
       of DataFrames -- never prints-and-forgets. Callers decide how to display/export.
    2. Every function is a pure, side-effect-free calculation. No file I/O, no plotting.
       Plotting/export is left to the caller (or the notebook/report layer) on purpose,
       so the same helpers work in a script, notebook, or report-generation pipeline.
    3. Functions accept explicit column-name arguments rather than hardcoding field names,
       so they work across differently-named datasets (e.g. "Churn_Flag" vs "Lapsed_Flag").
    4. No function invents business logic (e.g. "what counts as a high claim") --
       thresholds and rules are always passed in by the caller, who owns the business
       interpretation. This keeps the toolkit reusable across use cases with very
       different definitions of "risk" or "value."

Dependencies: pandas, numpy (both pre-installed in most analytics environments).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. DATA-QUALITY / PROFILING
# ---------------------------------------------------------------------------

def profile_dataframe(df: pd.DataFrame, id_col: str | None = None) -> pd.DataFrame:
    """
    Produce a one-row-per-column profile: dtype, missing count/%, unique count,
    min/max (numeric), and a few example values. This is the first thing to run
    on any new table -- it is the spreadsheet equivalent of "scroll through and
    eyeball the columns," done systematically and completely.

    Parameters
    ----------
    df : the table to profile
    id_col : optional column name to also report a uniqueness / duplicate check on

    Returns
    -------
    DataFrame with one row per column of `df`.
    """
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        missing = s.isna().sum()
        row = {
            "column": col,
            "dtype": str(s.dtype),
            "n_missing": missing,
            "pct_missing": round(missing / n * 100, 2) if n else np.nan,
            "n_unique": s.nunique(dropna=True),
        }
        if pd.api.types.is_numeric_dtype(s):
            row.update({
                "min": s.min(),
                "max": s.max(),
                "mean": round(s.mean(), 2) if s.notna().any() else np.nan,
                "std": round(s.std(), 2) if s.notna().any() else np.nan,
            })
        else:
            row.update({"min": None, "max": None, "mean": None, "std": None})
        example_vals = s.dropna().unique()[:3]
        row["example_values"] = ", ".join(str(v) for v in example_vals)
        rows.append(row)

    profile = pd.DataFrame(rows)

    if id_col and id_col in df.columns:
        dup_count = df[id_col].duplicated().sum()
        profile.attrs["id_column"] = id_col
        profile.attrs["id_duplicate_count"] = int(dup_count)
        profile.attrs["id_is_unique"] = bool(dup_count == 0)

    return profile


def flag_outliers_iqr(df: pd.DataFrame, numeric_cols: list[str], k: float = 1.5) -> pd.DataFrame:
    """
    Flag statistical outliers per numeric column using the IQR rule
    (below Q1 - k*IQR or above Q3 + k*IQR). Returns a summary table, not a
    row-level mask, so the caller can decide row-level treatment separately.

    This does NOT decide whether an outlier is "bad data" vs. a genuinely
    unusual-but-valid customer (e.g. a very high-net-worth policyholder) --
    that judgment belongs to the analyst.
    """
    rows = []
    for col in numeric_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - k * iqr, q3 + k * iqr
        n_low = (s < lower).sum()
        n_high = (s > upper).sum()
        rows.append({
            "column": col, "Q1": q1, "Q3": q3, "IQR": iqr,
            "lower_bound": lower, "upper_bound": upper,
            "n_below_lower": int(n_low), "n_above_upper": int(n_high),
            "pct_outliers": round((n_low + n_high) / len(s) * 100, 2),
        })
    return pd.DataFrame(rows)


def check_referential_integrity(
    parent_df: pd.DataFrame, parent_key: str,
    child_df: pd.DataFrame, child_key: str,
    child_name: str = "child table",
) -> dict:
    """
    Check that every key in `child_df[child_key]` exists in `parent_df[parent_key]`
    (e.g. every Policy_Data row maps to a valid Customer_ID in Customer_Master).
    Common building block for any multi-table insurance dataset (policy, claims,
    service-interaction, or billing tables against a customer master).

    Returns a dict with counts and the actual orphaned key values (capped at 50
    for readability) so the analyst can investigate specific bad records.
    """
    parent_keys = set(parent_df[parent_key].dropna())
    child_keys = child_df[child_key]
    is_orphan = ~child_keys.isin(parent_keys)
    orphan_values = child_keys[is_orphan].unique()
    return {
        "child_table": child_name,
        "child_rows": len(child_df),
        "orphan_rows": int(is_orphan.sum()),
        "orphan_pct": round(is_orphan.sum() / len(child_df) * 100, 2) if len(child_df) else np.nan,
        "orphan_keys_sample": list(orphan_values[:50]),
        "is_clean": bool(is_orphan.sum() == 0),
    }


def check_column_consistency(
    df: pd.DataFrame, derived_col: str, component_cols: list[str], comparison: str = "sum",
) -> dict:
    """
    Check whether a "derived" column (e.g. Active_Product_Count) is internally
    consistent with the columns it's supposed to summarize (e.g. Auto_Policy +
    Health_Policy + Home_Policy + Life_Policy flags). This kind of check catches
    stale or mismatched fields that would otherwise silently bias segment cuts.

    comparison="sum": derived_col should equal the row-wise sum of component_cols.
    """
    if comparison == "sum":
        computed = df[component_cols].sum(axis=1)
    else:
        raise ValueError(f"Unsupported comparison: {comparison}")

    mismatch = computed != df[derived_col]
    return {
        "derived_column": derived_col,
        "component_columns": component_cols,
        "n_rows": len(df),
        "n_mismatch": int(mismatch.sum()),
        "pct_mismatch": round(mismatch.sum() / len(df) * 100, 2) if len(df) else np.nan,
        "is_consistent": bool(mismatch.sum() == 0),
    }


def data_quality_report(
    df: pd.DataFrame,
    id_col: str,
    numeric_range_checks: dict[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """
    Convenience wrapper that assembles a standard data-quality checklist:
    duplicate IDs, missing IDs, and (optionally) implausible-range checks for
    named numeric columns, e.g. {"Age": (0, 100), "Annual_Premium": (0, None)}.

    Returns a tidy DataFrame: Check | Result | Passed -- ready to drop into a
    Data_Quality sheet or report table.
    """
    rows = []
    rows.append({
        "Check": f"Duplicate {id_col}",
        "Result": int(df[id_col].duplicated().sum()),
        "Passed": df[id_col].duplicated().sum() == 0,
    })
    rows.append({
        "Check": f"Missing {id_col}",
        "Result": int(df[id_col].isna().sum()),
        "Passed": df[id_col].isna().sum() == 0,
    })
    if numeric_range_checks:
        for col, (lo, hi) in numeric_range_checks.items():
            if col not in df.columns:
                continue
            mask = pd.Series(False, index=df.index)
            if lo is not None:
                mask |= df[col] < lo
            if hi is not None:
                mask |= df[col] > hi
            rows.append({
                "Check": f"Out-of-range {col} (expected [{lo}, {hi}])",
                "Result": int(mask.sum()),
                "Passed": mask.sum() == 0,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. DEMOGRAPHY / DISTRIBUTION PROFILING
# ---------------------------------------------------------------------------

def demography_profile(
    df: pd.DataFrame,
    categorical_cols: list[str],
    numeric_cols: list[str] | None = None,
    age_col: str | None = None,
    age_bins: list[int] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Standard demographic/portfolio profile: distribution (count + %) for each
    categorical column, descriptive stats for each numeric column, and an
    optional age-band breakdown. Works for any customer base -- retail,
    small-business, or mixed.

    Returns a dict keyed by column name (or "age_bands" / "numeric_summary"),
    each value a DataFrame ready to display or export.
    """
    result = {}

    for col in categorical_cols:
        counts = df[col].value_counts(dropna=False)
        pct = (counts / len(df) * 100).round(2)
        result[col] = pd.DataFrame({"count": counts, "pct_of_total": pct})

    if numeric_cols:
        result["numeric_summary"] = df[numeric_cols].describe().T.round(2)

    if age_col and age_col in df.columns:
        bins = age_bins or [0, 25, 35, 45, 55, 65, 120]
        labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins) - 1)]
        bands = pd.cut(df[age_col], bins=bins, labels=labels, right=False)
        counts = bands.value_counts().sort_index()
        pct = (counts / len(df) * 100).round(2)
        result["age_bands"] = pd.DataFrame({"count": counts, "pct_of_total": pct})

    return result


# ---------------------------------------------------------------------------
# 3. SEGMENTATION / GROUP COMPARISON
# ---------------------------------------------------------------------------

def segment_summary(
    df: pd.DataFrame,
    group_cols: list[str] | str,
    metric_col: str | None = None,
    agg: str = "mean",
    count_col_name: str = "count",
) -> pd.DataFrame:
    """
    Generic "group by X, summarize Y" helper -- the single most common EDA
    operation in insurance analytics (churn by region, average premium by
    segment, claim frequency by product, etc).

    Parameters
    ----------
    group_cols : one or more columns to group by (e.g. "Region" or
                 ["Region", "Customer_Segment"])
    metric_col : numeric column to aggregate. If None, only counts + share of
                 total are returned (useful for pure distribution questions).
    agg : pandas-supported aggregation ("mean", "sum", "median", etc.)

    Returns
    -------
    DataFrame sorted descending by the aggregated metric (or count if no
    metric given), with a share-of-total column added.
    """
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    grouped = df.groupby(group_cols, dropna=False)
    out = grouped.size().reset_index(name=count_col_name)

    if metric_col:
        agg_vals = grouped[metric_col].agg(agg).reset_index(name=f"{metric_col}_{agg}")
        out = out.merge(agg_vals, on=group_cols)
        out["share_of_total_%"] = (out[count_col_name] / out[count_col_name].sum() * 100).round(2)
        out = out.sort_values(f"{metric_col}_{agg}", ascending=False)
    else:
        out["share_of_total_%"] = (out[count_col_name] / out[count_col_name].sum() * 100).round(2)
        out = out.sort_values(count_col_name, ascending=False)

    return out.reset_index(drop=True)


def rate_by_segment(
    df: pd.DataFrame,
    group_cols: list[str] | str,
    outcome_col: str,
    outcome_value=1,
) -> pd.DataFrame:
    """
    Compute an event RATE by segment -- e.g. churn rate by region, claim rate
    by product, complaint rate by channel. This is distinct from
    segment_summary's plain averaging because it explicitly frames the
    numerator/denominator (customers meeting the outcome / total customers
    in the segment), which is the calculation learners most often get wrong
    by using the wrong denominator.

    Parameters
    ----------
    outcome_col : binary (0/1 or True/False) column marking the event
    outcome_value : the value that counts as "event occurred" (default 1)

    Returns
    -------
    DataFrame with segment, total count, event count, rate, and share of all
    events -- sorted descending by rate.
    """
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    grouped = df.groupby(group_cols, dropna=False)
    total = grouped.size().reset_index(name="total_count")
    events = grouped.apply(
        lambda g: (g[outcome_col] == outcome_value).sum(), include_groups=False
    ).reset_index(name="event_count")

    out = total.merge(events, on=group_cols)
    out["rate_%"] = (out["event_count"] / out["total_count"] * 100).round(2)
    total_events = out["event_count"].sum()
    out["share_of_total_events_%"] = (
        (out["event_count"] / total_events * 100).round(2) if total_events else 0
    )
    return out.sort_values("rate_%", ascending=False).reset_index(drop=True)


def value_tiering(
    df: pd.DataFrame,
    value_col: str,
    n_tiers: int = 3,
    tier_labels: list[str] | None = None,
) -> pd.Series:
    """
    Split customers into value tiers (e.g. Bronze/Silver/Gold, or High/Medium/Low
    premium) using quantile bins on any numeric value column (premium, lifetime
    value, claim amount, etc). Returns a Series aligned to df.index that the
    caller can assign as a new column.

    This is a general-purpose value-segmentation primitive -- useful far beyond
    churn (e.g. cross-sell prioritization, claims severity tiers).
    """
    if tier_labels is None:
        tier_labels = [f"Tier {i+1}" for i in range(n_tiers)][::-1]  # Tier 1 = highest
    return pd.qcut(df[value_col], q=n_tiers, labels=tier_labels, duplicates="drop")


# ---------------------------------------------------------------------------
# 4. CONDITION / LIFT ANALYSIS (generic "does X associate with outcome Y")
# ---------------------------------------------------------------------------

def condition_lift(
    df: pd.DataFrame,
    condition_mask: pd.Series,
    outcome_col: str,
    outcome_value=1,
    condition_label: str = "condition",
) -> dict:
    """
    Compare the outcome rate for customers meeting a condition vs. everyone
    else, and compute lift = condition-group rate / comparison-group rate.

    This is the general form behind ANY "driver analysis" -- churn drivers,
    cross-sell propensity drivers, claims-severity drivers, complaint drivers,
    etc. The caller supplies the condition (any boolean Series over df's
    index, built however the use case needs -- a single-column threshold or
    a complex multi-column rule) and the outcome; this function only does the
    arithmetic and returns clearly-labeled results.

    IMPORTANT: lift measures association, not causation. Document that
    distinction wherever this function's output is reported.
    """
    cond = df[condition_mask]
    comp = df[~condition_mask]

    n_cond, n_comp = len(cond), len(comp)
    rate_cond = (cond[outcome_col] == outcome_value).mean() if n_cond else np.nan
    rate_comp = (comp[outcome_col] == outcome_value).mean() if n_comp else np.nan
    lift = rate_cond / rate_comp if rate_comp else np.nan

    return {
        "condition_label": condition_label,
        "n_condition": n_cond,
        "n_comparison": n_comp,
        "rate_condition_%": round(rate_cond * 100, 2) if pd.notna(rate_cond) else np.nan,
        "rate_comparison_%": round(rate_comp * 100, 2) if pd.notna(rate_comp) else np.nan,
        "lift": round(lift, 3) if pd.notna(lift) else np.nan,
    }


def multi_driver_ranking(
    df: pd.DataFrame,
    drivers: dict[str, pd.Series],
    outcome_col: str,
    outcome_value=1,
) -> pd.DataFrame:
    """
    Run condition_lift() across several named drivers at once and return a
    single ranked table sorted by lift descending -- the standard
    "which factor matters most" output used across churn, claims, cross-sell,
    and complaint-driver analyses alike.

    Parameters
    ----------
    drivers : dict mapping a driver name to a boolean condition Series
              (e.g. {"Missed Payment": df["Payment_Missed_12M"] == 1, ...})
    """
    rows = [
        condition_lift(df, mask, outcome_col, outcome_value, condition_label=name)
        for name, mask in drivers.items()
    ]
    result = pd.DataFrame(rows)
    return result.sort_values("lift", ascending=False).reset_index(drop=True)


def risk_flag_stack(
    df: pd.DataFrame,
    flags: dict[str, pd.Series],
    outcome_col: str,
    outcome_value=1,
) -> pd.DataFrame:
    """
    Given several individual risk flags (each a boolean Series), compute how
    many flags each customer trips, then show the outcome rate at each flag
    count (0, 1, 2, 3, ...). This "stacking" view is often the strongest
    single piece of evidence in a driver analysis: it shows whether risk
    factors compound, which directly supports building priority tiers.

    Returns a DataFrame: flag_count | n_customers | event_rate_% -- monotonic
    increase in event_rate_% across flag_count is the signal to look for.
    """
    flag_df = pd.DataFrame({name: mask.astype(int) for name, mask in flags.items()}, index=df.index)
    flag_count = flag_df.sum(axis=1)
    tmp = pd.DataFrame({"flag_count": flag_count, "outcome": (df[outcome_col] == outcome_value).astype(int)})
    out = tmp.groupby("flag_count").agg(
        n_customers=("outcome", "size"),
        n_events=("outcome", "sum"),
    ).reset_index()
    out["event_rate_%"] = (out["n_events"] / out["n_customers"] * 100).round(2)
    return out


# ---------------------------------------------------------------------------
# 5. CROSS-TABLE ROLL-UPS (policy / claims / interaction tables -> customer grain)
# ---------------------------------------------------------------------------

def rollup_to_customer(
    detail_df: pd.DataFrame,
    id_col: str,
    agg_spec: dict[str, str],
) -> pd.DataFrame:
    """
    Aggregate a policy-, claim-, or interaction-grain table up to one row per
    customer, for validation against (or enrichment of) a customer-master
    table. E.g. rollup_to_customer(claims_df, "Customer_ID",
    {"Claim_Amount": "sum", "Claim_ID": "count"}).

    This is the standard building block for "does the customer-master's
    pre-aggregated field actually match the underlying detail records"
    checks, and for building new customer-level features from detail tables
    when the customer master doesn't already have them.
    """
    return detail_df.groupby(id_col).agg(agg_spec).reset_index()


def validate_rollup_against_master(
    master_df: pd.DataFrame, master_id_col: str, master_value_col: str,
    detail_df: pd.DataFrame, detail_id_col: str, detail_agg_spec: dict[str, str],
    rollup_value_col: str,
) -> dict:
    """
    Compare a pre-aggregated customer-master column (e.g. Claims_Count_12M)
    against a fresh roll-up computed from the underlying detail table (e.g.
    counting rows in Claims_Data per customer). Flags customers where the
    two disagree, which is one of the highest-value data-quality checks on
    any multi-table insurance dataset.
    """
    rollup = rollup_to_customer(detail_df, detail_id_col, detail_agg_spec)
    rollup = rollup.rename(columns={detail_id_col: master_id_col})

    merged = master_df[[master_id_col, master_value_col]].merge(
        rollup[[master_id_col, rollup_value_col]], on=master_id_col, how="left"
    )
    merged[rollup_value_col] = merged[rollup_value_col].fillna(0)
    mismatch = merged[master_value_col] != merged[rollup_value_col]

    return {
        "n_customers": len(merged),
        "n_mismatch": int(mismatch.sum()),
        "pct_mismatch": round(mismatch.sum() / len(merged) * 100, 2) if len(merged) else np.nan,
        "is_consistent": bool(mismatch.sum() == 0),
        "mismatch_sample": merged.loc[mismatch, master_id_col].head(20).tolist(),
    }
