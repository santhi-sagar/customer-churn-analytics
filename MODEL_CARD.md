# Model card

## Intended use

Portfolio education: explore associations in IBM’s Telco sample and demonstrate reproducible inference. A score may help form a question for investigation, not trigger an outreach campaign or consequential decision. Not validated for production, pricing, credit, employment, eligibility or vulnerable-customer targeting.

## Training design

Binary target: Churn=Yes (positive), Churn=No (negative). Fifteen numeric/categorical features include tenure, charges, service selections, contract and payment method. Excluded: customerID, gender, SeniorCitizen, Partner, Dependents. There is no feature selection based on test labels.

Stratified 60/20/20 split with seed 42. Training-only median imputation (TotalCharges has 11 missing source entries), scaling and full one-hot encoding. Prior-probability DummyClassifier baseline and L2 logistic regression C=0.1, 1, 10 candidates. Validation average precision selects the candidate; validation F1 selects threshold on a prespecified grid. Frozen artifact is not refitted afterward. Holdout metrics are a single final random-split estimate, not a confidence interval, time-series backtest or external validation.

The public JSON artifact contains numeric scaler parameters, encoder category order, coefficients and intercept. Runtime validation requires all fields; unlike training, missing inputs are rejected rather than silently imputed. Numeric accepted bounds: tenure 0–72 whole months, MonthlyCharges 0–120, TotalCharges 0–9000 sample monetary units. Unknown categories and inconsistent service states are rejected. These are sample-domain guardrails, not universal limits. All serving features are required; demographics and identifiers are rejected.

## Evidence

`artifacts/evaluation.json` contains candidate validation AP, final holdout ROC-AUC, average precision, F1, precision, recall, accuracy, Brier score, confusion matrix and curves. Curve arrays contain no source row identifiers or input features. `BUILD_REPORT.md` records executed test results. Portable inference is checked against sklearn probabilities to tolerance 1e-12. A deterministic rebuild compares serialized artifacts byte-for-byte in the same pinned environment.

Model scores have not been independently calibrated; Brier score is an evaluation statistic, not proof of calibration. The threshold optimizes F1, not costs, capacity, profit or intervention value. Accuracy alone is not an adequate measure for this imbalanced sample.

## Interpretation

Coefficients show conditional log-odds associations, not causal effects. Numeric inputs are standardized. Full one-hot categorical encoding with L2 regularization has no omitted reference category; individual category coefficients are not standalone category odds ratios versus a fixed omitted group. Correlated tenure, contract and charges can redistribute coefficients. Feature magnitudes cannot be treated as a fair ranking of recommended business actions. No per-customer causal explanation is supplied.

## Risks and limitations

- Data provenance and dataset-specific licensing are incomplete. Related IBM Cognos documentation describes fictional data but uses a different enhanced schema.
- No verified feature collection timestamps or prospective horizon. Contemporaneous features may encode status at/after churn; timing leakage cannot be ruled out.
- One historical sample with unknown sampling dates and representativeness; no external, geographic or temporal generalization established.
- Removing demographic columns does not establish fairness. Other features may be proxies. No subgroup audit has been performed.
- No treatment/control experiment, retention uplift estimate, realized savings, calibrated revenue forecast or lifetime profit estimate.
- No production authentication, long-term storage, audit trail, drift detection, reliability guarantee or privacy certification.

## Maintenance

Rebuild only after reviewing source checksum/provenance, feature definitions, time cutoff and rights. Validate schema, calibration, fairness and prospective performance on authorized new data before operational use. Do not upload real personal data to the demonstration. Dependency updates require rerunning training, portable-equivalence tests, reproducibility and AppTest.
