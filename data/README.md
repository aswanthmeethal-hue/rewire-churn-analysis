# Data

`Insurance_Customer_Churn_Assignment_Pack.xlsx` is the only dataset for this assignment.
It is synthetic data generated for training purposes -- it does not represent any real
insurer, policyholder, or claim.

| Dataset/File | Purpose | Key Fields | Learner Usage |
|---|---|---|---|
| `Customer_Master` (sheet) | Primary analytical table -- one row per customer, including the historical churn outcome and the commercial/behavioral fields used to explain it. | `Customer_ID` (unique key), `Historical_Churn_Flag` (0/1 outcome), `Region`, `Customer_Segment`, `Acquisition_Channel`, `Active_Product_Count`, `Annual_Premium`, `Premium_Increase_Pct`, `Days_To_Renewal`, `Complaints_12M`, `Service_Contacts_12M`, `Digital_Logins_90D`, `Payment_Missed_12M`, `Claims_Count_12M`, `Claim_Amount_12M`, `Tenure_Years`, `Current_Retention_Risk_Score` | This is the table you profile, segment, and test drivers against. Load it first and confirm `Customer_ID` is unique before anything else. |
| `Policy_Data` (sheet) | Policy-level detail -- one row per policy. Use to validate product-holding and premium relationships against Customer_Master. | `Customer_ID` (foreign key), `Policy_ID`, `Policy_Type`, `Annualized_Premium`, `Payment_Frequency`, `Policy_Status` | Use for referential-integrity and consistency checks (e.g. does `Active_Product_Count` in Customer_Master agree with the count of Active policies here?). Do not duplicate customer-level counts by re-aggregating this table into new fields unless your plan specifically calls for it. |
| `Claims_Data` (sheet) | Claim-level detail -- one row per claim. | `Customer_ID` (foreign key), `Claim_ID`, `Claim_Product`, `Severity`, `Claim_Amount`, `Claim_Status`, `Days_To_Resolve` | Use to validate `Claims_Count_12M` / `Claim_Amount_12M` in Customer_Master, and to investigate claims-experience drivers (e.g. multiple claims, high severity, escalation). |
| `Service_Interactions` (sheet) | Interaction-level detail -- one row per service contact. | `Customer_ID` (foreign key), `Interaction_ID`, `Channel`, `Reason`, `Resolution_Status`, `Resolution_Days` | Use to investigate service-experience drivers (e.g. complaint volume, escalation rate) beyond what Customer_Master's `Complaints_12M` and `Service_Contacts_12M` summarize. |
| `Data_Dictionary` (sheet) | Field definitions for the key Customer_Master columns. | `Field_Name`, `Source_Table`, `Definition` | Read this first, before writing your analysis plan -- it tells you what each field means and flags at least one field (`Current_Retention_Risk_Score`) as something to validate/interpret rather than use blindly. |

## Grain
`Customer_Master` is one row per customer. `Policy_Data`, `Claims_Data`, and
`Service_Interactions` are each one row per underlying policy, claim, or interaction --
finer grain than the customer master, joined back to it by `Customer_ID`. Confirming
this grain, and validating that any customer-level summary field agrees with what the
underlying detail tables actually contain, is the first task in the assignment.

## Modifications
Do not edit `Insurance_Customer_Churn_Assignment_Pack.xlsx` in place. If you need a
cleaned or derived version of any sheet for your analysis, save it as a new file and
keep the original untouched, so your data-quality findings remain reproducible against
the source data as provided.

## Row counts (as provided)
- `Customer_Master`: 2,500 rows
- `Policy_Data`: 3,698 rows
- `Claims_Data`: 1,594 rows
- `Service_Interactions`: 4,469 rows
- `Data_Dictionary`: 12 rows

If your own load produces different counts, that's a signal to check your read logic
(e.g. header row handling) before proceeding.
