# Insurance EDA Toolkit

## Purpose
This skill gives you a set of reusable, tested Python functions for exploring and
validating insurance customer/policy/claims data: profiling a table, checking data
quality, describing the customer base, comparing segments, testing whether a factor is
associated with an outcome, and validating one table against another. It exists so that
every learner (and every future analyst reusing this skill on a different insurance
dataset) computes these standard operations the same, correct way instead of
re-deriving them from scratch each time -- and, in particular, so that the arithmetic in
this assignment is not something you need to write or debug yourself.

## When to Use
Use this skill any time you are working with an insurance customer-master table (or any
linked policy/claims/service-interaction tables) and need to:
- Profile a new dataset before trusting it (types, missingness, ranges, duplicate keys)
- Check that linked tables are internally consistent (no orphan records, no derived
  field that disagrees with its underlying detail rows)
- Describe the customer base (regional/segment/channel distribution, age bands, tenure)
- Compare a metric or an event rate across segments, using the correct denominator
- Test whether a candidate factor (e.g. a missed payment, a complaint, a large premium
  increase) is associated with an outcome, and rank several candidates by strength
- Check whether several risk factors compound when a customer has more than one

This skill is intentionally generic -- it has no opinion about what "churn" means, what
counts as a "large" premium increase, or how many risk signals should define a priority
tier. Those decisions belong in your own analysis plan (see the `churn-analysis`
skill folder you will build as part of this assignment), not in this toolkit.

## Inputs Required
- A pandas DataFrame loaded from `Insurance_Customer_Churn_Assignment_Pack.xlsx`
  (`Customer_Master` sheet at minimum; `Policy_Data`, `Claims_Data`, and
  `Service_Interactions` for cross-table checks)
- Python 3.9+ with `pandas` and `numpy` installed (see `starter-code/requirements.txt`)
- No API keys, external services, or network access are required -- this skill runs
  entirely on local data

## Workflow
1. Load the relevant sheet(s) with `pandas.read_excel`.
2. Import the toolkit: `import sys; sys.path.insert(0, "<path-to>/assets"); import eda_utils as eda`.
3. Profile and validate the data first -- `eda.profile_dataframe`, `eda.flag_outliers_iqr`,
   `eda.data_quality_report`, `eda.check_referential_integrity`,
   `eda.check_column_consistency`, `eda.validate_rollup_against_master`.
4. Describe the customer base -- `eda.demography_profile`.
5. Compare segments -- `eda.segment_summary` for averages, `eda.rate_by_segment` for
   event rates (always uses the correct denominator: the segment's own population).
6. Test and rank candidate drivers -- `eda.condition_lift` for one driver at a time,
   `eda.multi_driver_ranking` to rank several, `eda.risk_flag_stack` to check whether
   risk factors compound as a customer trips more of them.
7. Optionally tier customers by value -- `eda.value_tiering`.

Full function signatures, parameters, and return shapes are in
`assets/function_reference.md`.

## Output Expectations
Every function returns a pandas DataFrame, Series, or a plain dict -- never a printed
string and never a file. You decide how to display, chart, or write the result. Expect:
- Profiling/quality functions to return one row per column/check, with clear pass/fail
  or count fields
- Segment/rate functions to return one row per segment with count, rate, and share
- Driver/lift functions to return `lift` as condition-group rate divided by
  comparison-group rate, always alongside the two underlying rates and sample sizes

## Guardrails
- **No business logic is baked in.** This skill will not tell you what a "high" claim
  amount is or what churn means for this company -- define those yourself.
- **Lift measures association, not causation.** Never describe a driver's lift value as
  proof that it *causes* churn; describe it as *associated with* churn.
- **Use the correct denominator.** `rate_by_segment` and `condition_lift` compute rates
  against the population actually in that group -- do not divide by the whole book when
  a segment-specific rate is what's needed.
- **No confidential or production data.** This skill and this assignment only ever
  operate on the synthetic `Insurance_Customer_Churn_Assignment_Pack.xlsx` provided --
  do not substitute real customer data.
- **Validate before you trust.** A derived/summary field (e.g. a "count in last 12
  months" column) can silently disagree with the detail table it's supposed to
  summarize -- always run `check_column_consistency` or `validate_rollup_against_master`
  on at least one such field before using it in analysis.

## Validation Checklist
Before relying on this skill's output in your analysis, confirm:
- [ ] `eda.profile_dataframe` has been run on `Customer_Master` and the `Customer_ID`
      column is confirmed unique
- [ ] `eda.check_referential_integrity` has been run for every linked table
      (Policy_Data, Claims_Data, Service_Interactions) against Customer_Master
- [ ] At least one derived/summary field has been cross-checked against its underlying
      detail table with `check_column_consistency` or `validate_rollup_against_master`
- [ ] Every segment-level rate you report used `rate_by_segment` (or the equivalent
      correct denominator), not a hand-computed rate against the wrong population
- [ ] Every driver comparison you report used `condition_lift` or
      `multi_driver_ranking`, with the condition threshold matching what you declared
      in your own `churn-analysis` skill
