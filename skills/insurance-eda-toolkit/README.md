# Insurance EDA Toolkit

## Overview
A reusable Python library of exploratory-data-analysis building blocks for insurance
customer/policy/claims data: data-quality profiling, demography and segmentation
analysis, group-level rate comparisons, driver/lift analysis, and cross-table
validation. It is deliberately use-case-agnostic -- it contains no churn-specific (or
any other use-case-specific) business rules. You supply those in your own analysis plan.

## Files in This Skill
- `skill.md` -- what this skill does, when to use it, and how (read this first)
- `assets/eda_utils.py` -- the actual Python module. Import it directly:
  `import sys; sys.path.insert(0, "assets"); import eda_utils as eda`
- `assets/function_reference.md` -- full function signatures, parameters, and return
  shapes for all 16 functions in `eda_utils.py`

## How Learners Should Use This
Use this skill for every generic calculation in the assignment: data-quality checks,
baseline metrics, segment comparisons, and driver/lift analysis (Learner Tasks 2-5 in
the Assignment Document). Do not re-implement profiling, segmentation, or lift logic
from scratch -- call into `eda_utils` instead, and reserve your own code for the
business-specific parts (defining thresholds, building priority tiers, writing
recommendations). The starter code in `starter-code/src/` shows where each toolkit
function is expected to be called.

## Evidence to Submit
Your `outputs/artifacts/` folder should include evidence that you used this toolkit
correctly and that its outputs were validated -- for example, a screenshot or exported
CSV of `eda.data_quality_report(...)` results, and the output of
`eda.multi_driver_ranking(...)` before you transferred those numbers into the output
template. Your `tests/` results (see `starter-code/tests/`) should also demonstrate that
key toolkit calls (e.g. referential integrity checks) ran clean against the provided
data.

## Notes for Evaluators
Check that segment and driver calculations in the learner's output actually trace back
to a call into `eda_utils` (via their `src/` code or notebook), not a hand-typed or
hardcoded number. A learner who reimplements `rate_by_segment` or `condition_lift`
themselves instead of using the toolkit has not failed the assignment, but it's worth
flagging under Rubric Section "Tool/Framework Integration" -- part of the intended
learning outcome is reusing a shared, correct component rather than re-deriving common
analytics logic per task.
