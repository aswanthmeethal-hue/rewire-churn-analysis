# ApexSure Churn Analysis Skill

This directory contains the custom domain skill for end-to-end churn analysis on the ApexSure personal lines insurance portfolio.

## Structure

```
lkills/churn-analysis/
|-- skill.md       # Complete business framing, data architecture, and analytical protocol
|-- README.md      # Skill usage instructions and implementation overview
```

## Overview

The `churn-analysis` skill implements an AI-native diagnostic pipeline built upon `insurance-eda-toolkit`. It automates:
1. **Referential and Derived Integrity Checks:** Identification of cross-table orphans and ETL roll-up discrepancies.
2. **Portfolio Baseline Computation:** Core churn rates, exposure volumes, and financial aggregates.
3. **Sub-Cohort Segmentation:** Dimensional churn rates across geography, demographic segment, and acquisition channels.
4. **Multivariate Driver Lift Ranking:** Statistical evaluation of behavioral and operational risk factors.
5. **Compounded Risk Tiering:** Tier-based risk categorization based on empirical risk-stack monotonicity.

## How to Execute the Analysis

From the `starter-code/` directory:

1. **Run the full analytical pipeline:**
   ```powershell
   python .\src\churn_analysis.py
   ```

2. **Execute and log the test suite:**
   ```powershell
   python -m pytest -v | Out-File -FilePath ..\outputs\artifacts\test_results.txt -Encoding utf8
   ```

3. **Populate the Excel delivery workbook:**
   ``powershell
   python .\populate_template.py
   ```

## Dependencies

- Python 3.10+
- `pandas`, `openpyxl`, `pytest`, `numpy`
- `insurance-eda-toolkit` (provided under `skills/insurance-eda-toolkit/assets`)
