# Aggregate data ready

Use data/aggregates/segments.csv and summary.csv. Also artifacts/dashboard.json. No source rows or IDs. Each dimension is an independently grouped view of the SAME 7043 source records; never sum Customers or charges across dimensions (double counting). Filter one Dimension first. ChurnRate = Churned/Customers. MonthlyCharges is whole-segment sum, not lost revenue. Summary churned_monthly_charges is historical churned-group monthly exposure; historical_value_proxy_total = sum(tenure * current MonthlyCharges), not true CLV. No payment-delay variable. Model-weighted revenue exposure applies only to scoring and is not in descriptive segment assets. These definitions must match Power BI.

Source raw CSV is ignored data/private/telco.csv and MUST NOT be published.
