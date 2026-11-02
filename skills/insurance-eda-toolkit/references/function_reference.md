# eda_utils.py -- Function Reference

All functions live in `scripts/eda_utils.py`. Import with:

```python
import sys; sys.path.insert(0, "<skill-path>/scripts")
import eda_utils as eda
```

## 1. Data quality / profiling

### `profile_dataframe(df, id_col=None) -> DataFrame`
One row per column: dtype, missing count/%, unique count, min/max/mean/std (numeric only),
and up to 3 example values. If `id_col` is given, also sets `.attrs["id_duplicate_count"]`
and `.attrs["id_is_unique"]` on the returned DataFrame.

### `flag_outliers_iqr(df, numeric_cols, k=1.5) -> DataFrame`
IQR-rule outlier summary per numeric column (bounds, count below/above, % outliers). Does not
label individual rows -- returns a per-column summary table.

### `check_referential_integrity(parent_df, parent_key, child_df, child_key, child_name="child table") -> dict`
Checks every key in `child_df[child_key]` exists in `parent_df[parent_key]`. Returns counts,
`orphan_pct`, up to 50 sample orphan key values, and `is_clean` (bool).

### `check_column_consistency(df, derived_col, component_cols, comparison="sum") -> dict`
Checks whether `derived_col` equals the row-wise sum of `component_cols`. Returns mismatch
count/% and `is_consistent` (bool).

### `data_quality_report(df, id_col, numeric_range_checks=None) -> DataFrame`
Assembles a standard checklist (duplicate ID, missing ID, optional out-of-range checks) as a
tidy `Check | Result | Passed` table. `numeric_range_checks` is a dict of
`{column: (min_or_None, max_or_None)}`.

## 2. Demography / distribution

### `demography_profile(df, categorical_cols, numeric_cols=None, age_col=None, age_bins=None) -> dict[str, DataFrame]`
Returns a dict keyed by column name: count + % distribution for each categorical column,
`describe().T` for numeric columns under key `"numeric_summary"`, and an age-band breakdown
under key `"age_bands"` if `age_col` is given (default bins `[0,25,35,45,55,65,120]`).

## 3. Segmentation / group comparison

### `segment_summary(df, group_cols, metric_col=None, agg="mean", count_col_name="count") -> DataFrame`
Group-by summary: count, share of total, and (if `metric_col` given) the aggregated metric.
Sorted descending by the metric (or count if no metric). `group_cols` can be a string or list
of strings for multi-column grouping.

### `rate_by_segment(df, group_cols, outcome_col, outcome_value=1) -> DataFrame`
Event RATE per segment with the correct denominator (segment size, not total book). Returns
`total_count`, `event_count`, `rate_%`, `share_of_total_events_%`, sorted descending by rate.
Use this instead of a hand-rolled groupby whenever the question is "what % of group X
experienced Y."

### `value_tiering(df, value_col, n_tiers=3, tier_labels=None) -> Series`
Quantile-based tiering of any numeric column (e.g. premium, claim severity, LTV). Returns a
Series aligned to `df.index` -- assign it as a new column yourself:
`df["Premium_Tier"] = eda.value_tiering(df, "Annual_Premium")`.

## 4. Driver / lift analysis

### `condition_lift(df, condition_mask, outcome_col, outcome_value=1, condition_label="condition") -> dict`
Compares outcome rate for `condition_mask` group vs. everyone else. Returns
`n_condition`, `n_comparison`, `rate_condition_%`, `rate_comparison_%`, `lift`
(condition rate / comparison rate).

### `multi_driver_ranking(df, drivers, outcome_col, outcome_value=1) -> DataFrame`
Runs `condition_lift` across a dict of `{driver_name: boolean_mask}` and returns one table
sorted by lift descending.

### `risk_flag_stack(df, flags, outcome_col, outcome_value=1) -> DataFrame`
Given a dict of boolean flags, counts how many each customer trips and shows
`n_customers` / `n_events` / `event_rate_%` at each flag count (0, 1, 2, ...). A rising,
roughly monotonic `event_rate_%` across flag counts is strong evidence that risk factors
compound -- useful directly as the basis for priority tiers.

## 5. Cross-table roll-ups

### `rollup_to_customer(detail_df, id_col, agg_spec) -> DataFrame`
Aggregates a detail-grain table (policy/claim/interaction) up to one row per `id_col` using
`agg_spec`, a dict like `{"Claim_Amount": "sum", "Claim_ID": "count"}`.

### `validate_rollup_against_master(master_df, master_id_col, master_value_col, detail_df, detail_id_col, detail_agg_spec, rollup_value_col) -> dict`
Compares a pre-aggregated customer-master column against a fresh roll-up computed from the
underlying detail table. Returns mismatch count/%, `is_consistent`, and up to 20 sample
mismatched IDs. One of the highest-value checks on any multi-table insurance dataset --
run it for every "12M count/amount" style field the customer master claims to summarize.

---

## A note on scope

None of these functions encode business thresholds (what counts as "high," "recent," or
"risky") or business outcomes (what "churn" or "conversion" means for a specific dataset).
Those decisions belong in the use-case-specific layer built on top of this toolkit -- see
"Building a use-case skill on top of this toolkit" in SKILL.md.
