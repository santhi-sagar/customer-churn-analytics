# Data dictionary

Source has 21 fields. Scoring CSV must contain exactly the 15 model fields below (case-sensitive). Whitespace or alternate spellings are rejected. All numeric values must be finite and nonmissing; numeric strings parse as numbers. Input order can vary; processing restores the training feature order.

| Model field | Meaning / accepted values |
|---|---|
| tenure | Whole months with company, 0–72 |
| MonthlyCharges | Current monthly charge, sample monetary units, 0–120 |
| TotalCharges | Source cumulative historical charges, sample monetary units, 0–9000. Not true CLV. Missing training values imputed with training median; missing inference values rejected. |
| PhoneService | Yes / No |
| MultipleLines | Yes / No / No phone service; must be No phone service iff PhoneService is No |
| InternetService | DSL / Fiber optic / No |
| OnlineSecurity | Yes / No / No internet service |
| OnlineBackup | Yes / No / No internet service |
| DeviceProtection | Yes / No / No internet service |
| TechSupport | Yes / No / No internet service |
| StreamingTV | Yes / No / No internet service |
| StreamingMovies | Yes / No / No internet service |
| Contract | Month-to-month / One year / Two year |
| PaperlessBilling | Yes / No |
| PaymentMethod | Electronic check / Mailed check / Bank transfer (automatic) / Credit card (automatic). Not payment delay. |

All six internet-dependent service fields must be No internet service iff InternetService is No. When internet service exists they must each be Yes or No. Source currency is not established here; `$` is a display convention for sample monetary units.

## Source fields excluded from scoring/model

customerID (source identifier; never distributed), gender, SeniorCitizen (0/1 source demographic), Partner (Yes/No), Dependents (Yes/No). Churn is the target label and is not an input. No payment-delay, prospectively observed churn window, acquisition-cost, profit, campaign-treatment or true-CLV field is present.

## Scoring output

| Column | Definition |
|---|---|
| input_row | 1-based position in supplied CSV; not a customer ID |
| churn_probability | Logistic model P(Churn=Yes), not independently calibrated |
| review_flag | probability >= frozen validation threshold |
| monthly_charge_exposure_proxy | probability × MonthlyCharges; ranking/exposure proxy, not measured future loss or savings |
| historical_value_proxy | tenure × MonthlyCharges; constant-price historical gross-value approximation, sometimes described as CLV proxy but NOT true CLV |

## Descriptive aggregate assets

`data/aggregates/segments.csv` columns: Dimension, Segment, Customers, Churned, MonthlyCharges, ChurnRate. Each Dimension is an independent partition of the same 7,043 source records. Filter to one Dimension before summing; summing all dimensions multiplies totals fivefold. ChurnRate = Churned / Customers. MonthlyCharges is the whole-segment monthly-charge sum, not churned-group charges. tenure bands are 0–12, 13–24, 25–48 and 49–72 whole months.

`summary.csv` is a metric/value table. customers = 7043; churned = 1869; churn_rate = churned/customers. monthly_charges = whole-sample sum of MonthlyCharges. churned_monthly_charges = sum of MonthlyCharges for known Churn=Yes rows (historical exposure). historical_value_proxy_total = sum(tenure × current MonthlyCharges), not sum(TotalCharges). missing_total_charges = count of blank source TotalCharges entries.

`artifacts/dashboard.json` expresses the same descriptive aggregates; `evaluation.json` contains the distinct train/validation/test evidence. Do not confuse descriptive whole-sample churn rates with out-of-sample predictive performance.
