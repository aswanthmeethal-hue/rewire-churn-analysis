import sys
from pathlib import Path
import openpyxl
import pandas as pd

ROOT = Path(r"C:\Users\aswanth.meethal\rewire-assignment\assignment")
DATA_PATH = ROOT / "data" / "Insurance_Customer_Churn_Assignment_Pack.xlsx"
TEMPLATE_PATH = ROOT / "outputs" / "artifacts" / "Insurance_Churn_Analytics_Output_Template.xlsx"

TOOLKIT_ASSETS = ROOT / "skills" / "insurance-eda-toolkit" / "assets"
sys.path.insert(0, str(TOOLKIT_ASSETS))
import eda_utils as eda

wb = openpyxl.load_workbook(TEMPLATE_PATH)
cm = pd.read_excel(DATA_PATH, sheet_name="Customer_Master")

# 1. Executive_Summary
ws_exec = wb["Executive_Summary"]
total_cust = len(cm)
churned_cust = int(cm["Historical_Churn_Flag"].sum())
churn_rate = churned_cust / total_cust
avg_prem = cm["Annual_Premium"].mean()
avg_prem_churn = cm[cm["Historical_Churn_Flag"] == 1]["Annual_Premium"].mean()

exec_data = {
    "Overall Historical Churn Rate": (f"{churn_rate:.2%}", "Baseline portfolio churn rate across 2,500 policyholders."),
    "Total Customers": (total_cust, "Full customer population evaluated across regions and segments."),
    "Customers Churned": (churned_cust, "Total historical policy terminations."),
    "Average Annual Premium": (f"INR {avg_prem:,.2f}", "Portfolio-wide mean premium value."),
    "Average Premium - Churned": (f"INR {avg_prem_churn:,.2f}", "Mean premium among churned policyholders (higher premium exposure)."),
    "Top Churn Driver #1": ("Complaints >= 1", "Lift: 1.565x (13.72% churn vs 8.77% comparison). Strongest single risk indicator."),
    "Top Churn Driver #2": ("Days to Renewal <= 60", "Lift: 1.519x (13.38% churn vs 8.81% comparison). Near-term renewal vulnerability."),
    "Top Churn Driver #3": ("Payment Missed >= 1", "Lift: 1.479x (13.31% churn vs 9.00% comparison). Operational and financial friction signal."),
    "Priority Retention Opportunity": ("Tier 1 (333 high-risk customers)", "15.92% churn rate; targeted outreach before the 60-day renewal cutoff.")
}

for row in ws_exec.iter_rows(min_row=2, max_col=3):
    metric = row[0].value
    if metric in exec_data:
        row[1].value = exec_data[metric][0]
        row[2].value = exec_data[metric][1]

# 2. Churn_Analysis
ws_churn = wb["Churn_Analysis"]
while ws_churn.max_row > 1:
    ws_churn.delete_rows(2)

ws_churn.append(["Overall", "All Customers", total_cust, churned_cust, f"{churn_rate:.2%}", "100.00%", "Baseline benchmark for the total book of business."])

dims = [
    ("Region", "Region"),
    ("Customer Segment", "Customer_Segment"),
    ("Acquisition Channel", "Acquisition_Channel"),
    ("Product Count", "Active_Product_Count")
]

for label, col in dims:
    seg_df = eda.rate_by_segment(cm, col, outcome_col="Historical_Churn_Flag")
    for _, r in seg_df.iterrows():
        cat = str(r[col])
        cnt = int(r["total_count"])
        ev = int(r["event_count"])
        crate = f"{r['rate_%']:.2f}%"
        share = f"{r['share_of_total_events_%']:.2f}%"
        insight = f"Segment represents {cnt} customers with a {crate} churn rate."
        ws_churn.append([label, cat, cnt, ev, crate, share, insight])

# 3. Driver_Analysis
ws_driver = wb["Driver_Analysis"]
while ws_driver.max_row > 1:
    ws_driver.delete_rows(2)

drivers_dict = {
    "Complaints": (cm["Complaints_12M"] >= 1, "Complaints_12M >= 1", "Unresolved service friction strongly predicts policy cancellation.", "High"),
    "Near Renewal": (cm["Days_To_Renewal"] <= 60, "Days_To_Renewal <= 60", "Approaching policy expiration window accelerates shopping behavior.", "High"),
    "Missed Payment": (cm["Payment_Missed_12M"] >= 1, "Payment_Missed_12M >= 1", "Payment friction or financial stress precedes churn.", "High"),
    "Premium Increase": (cm["Premium_Increase_Pct"] >= 12.0, "Premium_Increase_Pct >= 12.0%", "Price elasticity triggers quote comparisons and switching.", "Medium"),
    "Service Contacts": (cm["Service_Contacts_12M"] >= 3, "Service_Contacts_12M >= 3", "Elevated operational inquiries indicate customer dissatisfaction.", "Medium"),
    "Multiple Claims": (cm["Claims_Count_12M"] >= 2, "Claims_Count_12M >= 2", "Post-claim dissatisfaction and deductible friction elevate risk.", "Medium"),
    "Low Digital Engagement": (cm["Digital_Logins_90D"] <= 2, "Digital_Logins_90D <= 2", "Disengaged customers lack sticky touchpoints with the brand.", "Low"),
    "Low Tenure": (cm["Tenure_Years"] <= 1, "Tenure_Years <= 1", "New policyholders have lower brand loyalty and weaker retention.", "Low"),
}

rank_df = eda.multi_driver_ranking(cm, {k: v[0] for k, v in drivers_dict.items()}, outcome_col="Historical_Churn_Flag")
for _, r in rank_df.iterrows():
    lbl = r["condition_label"]
    rule = drivers_dict[lbl][1]
    n_cond = int(r["n_condition"])
    r_cond = f"{r['rate_condition_%']:.2f}%"
    r_comp = f"{r['rate_comparison_%']:.2f}%"
    lift = f"{r['lift']:.3f}x"
    interp = drivers_dict[lbl][2]
    prio = drivers_dict[lbl][3]
    ws_driver.append([lbl, rule, n_cond, r_cond, r_comp, lift, interp, prio])

# 4. Retention_Prioritization
ws_ret = wb["Retention_Prioritization"]
while ws_ret.max_row > 1:
    ws_ret.delete_rows(2)

f_complaint = cm["Complaints_12M"] >= 1
f_renewal = cm["Days_To_Renewal"] <= 60
f_missed = cm["Payment_Missed_12M"] >= 1
f_premium = cm["Premium_Increase_Pct"] >= 12.0
flag_count = f_complaint.astype(int) + f_missed.astype(int) + f_premium.astype(int)

cm["Priority_Tier"] = "Tier 3"
cm.loc[(flag_count == 1) & (~f_renewal), "Priority_Tier"] = "Tier 2"
cm.loc[(flag_count >= 2) | ((flag_count >= 1) & f_renewal), "Priority_Tier"] = "Tier 1"

tier_summary = eda.rate_by_segment(cm, "Priority_Tier", outcome_col="Historical_Churn_Flag")
tier_meta = {
    "Tier 1": ("Immediate High Risk", ">=2 risk flags OR (1 flag and Renewal <= 60 days)", "Outbound phone calls by dedicated retention specialists; premium relief/discounts", "Within 7-14 days", "Highest churn rate (15.92%); immediate intervention protects high-premium revenue."),
    "Tier 2": ("Proactive Watchlist", "1 risk flag and Renewal > 60 days", "Proactive digital check-ins, automated billing resolution, customer service outreach", "30-45 days before renewal", "Elevated churn rate (11.05%); pre-emptive outreach before entering renewal window."),
    "Tier 3": ("Standard Loyalty", "0 risk flags", "Standard renewal notices, automated digital nudges, cross-sell offers", "Standard renewal cycle (30 days)", "Lowest churn rate (7.22%); cost-effective digital engagement maintains satisfaction.")
}

for _, r in tier_summary.iterrows():
    t_name = r["Priority_Tier"]
    cnt = int(r["total_count"])
    crate = f"{r['rate_%']:.2f}%"
    meta = tier_meta[t_name]
    ws_ret.append([t_name, f"{meta[0]} ({crate} churn)", cnt, meta[1], meta[2], meta[3], meta[4]])

# 5. Recommendations
ws_rec = wb["Recommendations"]
while ws_rec.max_row > 1:
    ws_rec.delete_rows(2)

recs = [
    ("R1", "High churn (13.72%) driven by unresolved customer complaints", "Establish dedicated Rapid Complaint Resolution Desk with 48-hr SLA and retention outreach", "Tier 1 and customers with Complaints >= 1", "Reduce complaint-driven churn by 25-30%", "Medium", "High", "Customer Operations and Care", "First-Contact Resolution Rate and Complaint Churn Rate"),
    ("R2", "Elevated churn (13.38%) within 60 days of renewal", "Launch proactive renewal engagement campaign starting at Day 75 with personalized renewal previews", "Policyholders with Days_To_Renewal <= 60", "Improve renewal conversion by 15%", "Low", "High", "Retention Marketing", "Renewal Retention Rate (60-day cohort)"),
    ("R3", "Payment missed flag creates 1.48x churn lift", "Implement smart automated SMS/WhatsApp payment reminders and flexible split-payment options", "Customers with Payment_Missed_12M >= 1", "Recover 35% of missed-payment customers before cancellation", "Low", "High", "Billing and Payments", "Payment Recovery Rate and Involuntary Churn Rate"),
    ("R4", "Premium increases >= 12% trigger price-driven churn (1.31x lift)", "Deploy targeted loyalty discounts or deductible restructuring options for accounts facing >12% rate hikes", "Customers with Premium_Increase_Pct >= 12%", "Mitigate price shock churn by 20%", "Medium", "Medium", "Pricing and Underwriting", "Retention Rate on Rate-Hiked Accounts"),
    ("R5", "71.32% inconsistency between Active_Product_Count and policy flags", "Correct upstream ETL data aggregation pipeline and implement automated nightly reconciliation tests", "Enterprise Data Architecture and Reporting", "Eliminates reporting errors and ensures cross-sell analytics integrity", "Low", "High", "Data Engineering", "Data Consistency Error Rate (Target: 0%)")
]

for rec in recs:
    ws_rec.append(list(rec))

# 6. Data_Quality
ws_dq = wb["Data_Quality"]
while ws_dq.max_row > 1:
    ws_dq.delete_rows(2)

dq_rows = [
    ("Duplicate Customer_ID", "Pass", "Zero duplicate Customer_IDs found across 2,500 rows.", "None; unique grain confirmed."),
    ("Missing Customer_ID", "Pass", "Zero missing values in primary key.", "None; complete identifier coverage."),
    ("Missing / Invalid Churn Flag", "Pass", "Historical_Churn_Flag strictly contains binary 0 and 1 values.", "None; valid target variable."),
    ("Negative / Implausible Premium", "Pass", "Annual_Premium strictly positive (min INR 300, max INR 5,719).", "None; valid financial data."),
    ("Invalid Days_To_Renewal", "Pass", "Days_To_Renewal ranges between 5 and 365 days; no negative values.", "None; valid temporal field."),
    ("Orphan Policy Records", "Pass", "Referential integrity confirmed: 0 orphan policy records.", "None; child-to-parent foreign key integrity intact."),
    ("Orphan Claim Records", "Pass", "Referential integrity confirmed: 0 orphan claim records.", "None; child-to-parent foreign key integrity intact."),
    ("Orphan Interaction Records", "Pass", "Referential integrity confirmed: 0 orphan service interaction records.", "None; child-to-parent foreign key integrity intact."),
    ("Active_Product_Count vs Policy Flags", "Fail", "71.32% mismatch rate (1,783 rows) between Active_Product_Count and policy flags sum.", "Refactor ETL pipeline logic deriving product count.")
]

for dq in dq_rows:
    ws_dq.append(list(dq))

wb.save(TEMPLATE_PATH)
print("SUCCESS: Insurance_Churn_Analytics_Output_Template.xlsx successfully populated and saved.")
