# Data provenance and redistribution boundary

Reviewed 13 November 2026.

## Exact data used

- Owner: IBM GitHub organization; repository `IBM/telco-customer-churn-on-icp4d`.
- File: `data/Telco-Customer-Churn.csv`.
- Pinned revision: `d5371f5` (repository overview reports latest commit dated 25 June 2020).
- Download URL: https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/d5371f5/data/Telco-Customer-Churn.csv
- SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`.
- Downloaded size: 970,457 bytes. 7,043 rows, 21 source columns; 1,869 Churn=Yes and 5,174 Churn=No. 11 blank TotalCharges values become missing numeric values.

The source repository is archived and read-only (22 July 2024). Its README describes a churn code pattern but does not establish collection dates, original sampling, consent, population representativeness, feature cutoff times or a distinct dataset license.

## Evidence read

1. https://github.com/IBM/telco-customer-churn-on-icp4d — README states: “This code pattern is licensed under the Apache Software License, Version 2.” Separate third-party objects have their respective licenses. This does not by itself prove a specific license for the underlying dataset.
2. https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE — Apache License 2.0, with redistribution/notice conditions and no dataset-specific statement.
3. https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/README.md — 404; no separate data README exists at this path. The file tree showed the CSV.
4. https://www.ibm.com/docs/en/cognos-analytics/12.0.x?topic=samples-telco-customer-churn — related IBM Cognos documentation describes a fictional telco company and churn as leaving in the last month. It lists five enhanced XLSX files and CLTV/Churn Score derived fields. Those fields are NOT in this original 21-column CSV. The related documentation does not prove identical schema, row provenance or a separate dataset license for the CSV used here.

## Distribution policy

Raw rows are kept only in ignored `data/private/`. No source IDs, raw customer records or uploaded data are in the public file manifest. Public assets contain fitted linear coefficients, holdout curve/metric aggregates and segment aggregates (minimum segment group size is 1,473 for Contract and 1,024 across the shipped segment dimensions). The deliberately synthetic scoring template is generated from hand-chosen values, not copied from a source row. A model artifact is not a formal anonymization or differential-privacy guarantee.

Repository-level Apache-2.0 code licensing is confirmed; a separate dataset-specific redistribution license remains unconfirmed. Do not describe this CSV as CC0, public-domain or definitively Apache-licensed data. Before redistributing raw data or using commercially, resolve the underlying data terms with the owner. The project’s MIT license covers newly written code, not source data or IBM trademarks.

## Interpretation constraints

The cross-sectional sample does not establish a prospective prediction window or observed outcomes after a feature cutoff. Churn labels are interpreted as sample labels, not guaranteed next-month events. No payment delays, intervention responses, real lifetime value, acquisition costs or business savings are observed. We keep these absent rather than invent them.
