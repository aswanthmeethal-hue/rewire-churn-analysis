# ApexSure Insurance — Customer Churn Analysis & Retention Strategy

An end-to-end data analytics and decision intelligence pipeline built for ApexSure Insurance. This project investigates customer retention patterns, quantifies churn risk across policy cohorts, develops automated analytical skills, and populates the executive decision framework.

---

## Executive Summary

- Objective: Identify core drivers behind policyholder lapse/churn and model actionable retention interventions.
- Dataset: Comprehensive customer demographic, policy tier, premium pricing, claims history, and service interaction data.
- Key Deliverables:
  - Automated EDA toolkit and exploratory statistical pipelines.
  - Custom agent skills for repeatable metric calculation and cohort slicing.
  - Fully populated executive Excel financial and retention model (outputs/artifacts/).
  - Unit test suite validating core analytical logic and data consistency.

---

## Repository Structure

rewire-churn-analysis/
|-- data/                  # Raw and preprocessed policyholder datasets
|-- outputs/artifacts/     # Populated Excel models, figures, and reporting summaries
|-- skills/                # Modular analytics and evaluation agent skills
|-- starter-code/          # Core Python pipelines, feature engineering, and modeling scripts
|-- .gitignore             # Environment and temporary file exclusion rules
|-- Helper Guide.docx      # Project briefing and rubric references
`-- README.md              # Project documentation and reproduction guide

---

## Environment Setup & Installation

### Prerequisites
- Python 3.10+
- Git

### Setup Instructions

1. Clone the repository:
   git clone git@github.com:aswanthmeethal-hue/rewire-churn-analysis.git
   cd rewire-churn-analysis

2. Create and activate a virtual environment:
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate

3. Install dependencies:
   pip install -r starter-code/requirements.txt

---

## Testing & Validation

Run unit tests to verify data transformations and metric calculation pipelines:

pytest

---

## Key Findings & Strategic Recommendations

1. Tenure & Risk Correlation: Early-stage policyholders exhibit highest sensitivity within the first 12–18 months; onboarding interventions produce the highest retention ROI.
2. Claims Friction: Delays in initial claim resolutions act as a leading churn indicator.
3. Actionable Retention Strategy: Implement proactive tier adjustments and proactive touchpoints prior to annual policy renewals.
