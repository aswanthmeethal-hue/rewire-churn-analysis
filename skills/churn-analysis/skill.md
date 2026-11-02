---
name: churn-analysis
description: Create and apply a structured, AI-native churn analysis plan for the ApexSure insurance dataset, including business framing, data-quality checks, segmentation, churn-driver investigation, evidence capture, and executive-ready recommendations.
---

# ApexSure Insurance Churn Analysis Plan

## Purpose
The objective of this analysis is to diagnose the structural and behavioral drivers of policyholder churn across ApexSure's portfolio of 2,500 customers. The analysis establishes baseline retention benchmarks, investigates risk signals across service experience, pricing elasticity, and contract renewal horizons, and constructs an evidence-backed retention prioritization framework. The deliverables inform retention operations, executive leadership, and customer care workflows on targeted intervention strategies to protect premium revenue.

## When to Use
This analytical plan applies directly to ApexSure's personal lines insurance portfolio (Auto, Health, Home, Life). If applied to another insurer's customer master and transaction tables:
- Directly Applicable: Grain structures (customer master single-row grain, policy/claims child joins), referential integrity checks, rollup validation protocols, and the condition-lift analytical framework.
- Requires Recalibration: Pricing elasticity thresholds (e.g., Premium Increase >= 12%), renewal operational windows (e.g., Days to Renewal <= 60), contact volume thresholds, and baseline churn benchmarks.

## Inputs Required
- Primary Analytical Table: Customer_Master at customer-level grain (1 row per Customer_ID, 2,500 rows).
- Supporting Tables:
  - Policy_Data: Detail policy records mapped 1-to-many via Customer_ID.
  - Claims_Data: Claims history detail mapped via Customer_ID.
  - Service_Interactions: Contact channel and resolution records mapped via Customer_ID.
- Detail Aggregation & Rollup Validation: Detail tables are aggregated using eda.rollup_to_customer(). Pre-aggregated summary fields in Customer_Master (such as Claims_Count_12M) are cross-validated against underlying details using eda.validate_rollup_against_master().

## Workflow

1. Data-Quality Checks:
   - Verify unique key integrity and absence of nulls on Customer_ID.
   - Run eda.check_referential_integrity() across all childtables (Policy_Data, Claims_Data, Service_Interactions) against Customer_Master.
   - Run eda.check_column_consistency() on Active_Product_Count against the sum of policy flags (Auto_Policy, Health_Policy, Home_Policy, Life_Policy).
   - Validate pre-aggregated metrics using eda.validate_rollup_against_master().

2. Baseline Metrics:
   - Compute total policyholder volume (2,500), churned volume (239), baseline churn rate (9.56%), portfolio mean annual premium (INR 2,324.32), and churned cohort mean premium (INR 2,324.79) using compute_baseline_metrics().

3. Segmentation Plan:
   - Evaluate churn rates across customer segments using eda.rate_by_segment():
     - Region: Geographic variance across North, South, East, and West.
     - Customer_Segment: Mass Market, Preferred, and Wealth tiers.
     - Acquisition_Channel: Broker, Agent, Direct, and Digital acquisitions.
     - Active_Product_Count: Multi-policy holding relationship.
   - Denominator Integrity: Every segment churn rate strictly uses segment population size as denominator.

4. Candidate Churn Drivers:

| Driver Name | Condition (Column + Threshold) | Comparison Group | Toolkit Function | Hypothesis | Result Lift |
|---|---|---|---|---|---|
| Complaints | Complaints_12M >= 1 | Everyone else | eda.condition_lift | Unresolved friction drives dissatisfaction and cancellation. | 1.565x (13.72% vs 8.77%) |
| Near Renewal | Days_To_Renewal <= 60 | Everyone else | eda.condition_lift | Imminent contract expiration triggers market comparison. | 1.519x (13.38% vs 8.81%) |
| Missed Payment | Payment_Missed_12M >= 1 | Everyone else | eda.condition_lift | Billing friction or liquidity stress precedes lapse. | 1.479x (13.31% vs 9.00%) |
| Premium Increase | Premium_Increase_Pct >= 12.0% | Everyone else | eda.condition_lift | Significant rate hikes induce price elasticity churn. | 1.313x (11.70% ts 8.91%) |
| Service Contacts | Service_Contacts_12M >= 3 | Everyone else | eda.condition_lift | High contact volume signals unresolved friction. | 1.185x (11.00% vs 9.28%) |
| Multiple Claims | Claims_Count_12M >= 2 | Everyone else | eda.condition_lift | Claim settlement friction and deductible shock raise churn risk. | 1.182x (10.98% ts 9.29%) |
| Low Digital Engagement | Digital_Logins_90D <= 2 | Everyone else | eda.condition_lift | Disengagement correlates with lack of brand attachment. | 1.174x (11.06% vs 9.42%) |
| Low Tenure | Tenure_Years <= 1 | Everyone else | eda.condition_lift | Newer customers lack relationship loyalty. | 1.074x (10.26% vs 9.55%) |

5. Driver Ranking & Stacking:
   - Rank candidate drivers using eda.multi_driver_ranking().
   - Validate risk factor compounding via eda.risk_flag_stack() across the top four flags (Complaints >= 1, Days_To_Renewal <= 60, Payment_Missed >= 1, Premium_Increase_Pct >= 12%). Compounding is verified as churn increases from 6.92% (0 flags) to 10.48% (1 flag), 15.38% (2 flags), 17.24% (3 flags), and 40.00% (4 flags).

6. Retention Prioritization:
   - Tier 1 (Immediate / High Risk - 333 customers): Customers with >= 2 risk flags OR (f renewal and flag count >= 1). Churn rate: 15.92%. Immediate retention specialist outreach within 7-14 days.
   - Tier 2 (Proactive / Medium Risk - 769 customers): Customers with 1 risk flag and Days_To_Renewal > 60. Churn rate: 11.05%. Proactive engagement 30-45 days before entering renewal window.
   - Tier 3 (Standard / Low Risk - 1,398 customers): Customers with 0 risk flags. Churn rate: 7.22%. Standard digital renewal workflows.

## Output Expectations
The deliverables map to the six required outputs:
1. Executive Churn Summary: Headline metrics, top 3 drivers, priority retention segment.
2. Segment-Level Churn Analysis: Churn rate and event share by Region, Customer Segment, Channel, and Product Count.
3. Ranked Churn-Driver Analysis: Condition definition, cohort size, condition rate, comparison rate, and lift factor.
4. Retention Prioritization: Tier sizing, churn rates, compound risk definitions, and operational workflows.
5. Prioritized Recommendations: Five concrete, prioritized initiatives (R1 to R5) detailing target segment, owner, expected impact, and KPIs.
6. Data-Quality Assessment: Validation findings across structural checks and the ETL reconciliation issue on Active_Product_Count.

## Guardrails
- Every segment and driver rate uses the specific group sub-population as the denominator.
- Language standard: Drivers are described as 'associated with' or 'predictive of' churn; causal language is avoided.
- Full traceability: All figures are generated from eda_utils.py functions and logged in test_results.txt.
- Data quality anomalies (e.g., 71.32% mismatch in Active_Product_Count) are formally recorded and flagged for data engineering resolution.

## Validation Checklist
- [x] Every driver threshold is stated as an exact column and condition.
- [x] Every segment and driver rate traces back to specific toolkit function calls.
- [x] High-, medium-, and low-lift candidate drivers were all tested.
- [x] Retention tiers demonstrate clean, monotonic churn rate progression (Tier 1: 15.92% > Tier 2: 11.05% > Tier 3: 7.22%).
- [x] Recommendations are bounded by empirical portfolio evidence.
