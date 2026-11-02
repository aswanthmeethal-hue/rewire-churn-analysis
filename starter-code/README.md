# Starter Code

This is scaffolding, not a solution. It gives you the function shape the assignment
expects and wires up the `insurance-eda-toolkit` skill correctly, but every function
body that requires a business decision raises `NotImplementedError` until you fill it
in based on your own `skills/churn-analysis/skill.md`.

## Structure
```
starter-code/
  src/
    churn_analysis.py   -- function scaffold: load_data, run_data_quality_checks,
                            compute_baseline_metrics, compare_segments,
                            analyze_drivers, build_retention_tiers, main()
  tests/
    test_data_quality.py -- 7 ready-to-run structural tests + 5 TODO tests you complete
  outputs/
    artifacts/            -- put your evidence (screenshots, exports, test results) here
  requirements.txt
  .env.example             -- not needed for this assignment; kept for structural consistency
```

## Setup
```bash
cd starter-code
pip install -r requirements.txt
```

No API keys or external services are required -- see `.env.example` for why it's
included anyway.

## Running the starter script
```bash
python src/churn_analysis.py
```
As provided, this loads the data and prints shapes, then stops -- the analysis
functions raise `NotImplementedError` until you implement them.

## Running the tests
```bash
pytest tests/ -v
```
7 tests should pass unmodified (they check structural facts about the provided data
that don't depend on your analysis choices). 5 are skipped with `pytest.skip(...)` and
marked TODO -- complete them as you implement the corresponding functions in
`churn_analysis.py`. Save your final test run's output into `outputs/artifacts/`.

## How this connects to the rest of the package
1. Write your analysis plan first: `skills/churn-analysis/skill.md` (Learner Task 1).
2. Implement `churn_analysis.py`'s functions using `insurance-eda-toolkit` (see
   `skills/insurance-eda-toolkit/skill.md`) and the exact thresholds/rules from your plan.
3. Complete the TODO tests in `tests/test_data_quality.py` as each function is done.
4. Save evidence to `outputs/artifacts/` as you go.
5. Transfer your final numbers into `Insurance_Churn_Analytics_Output_Template.xlsx`
   (from the `data/` folder's sibling deliverable -- see the Assignment Document).
