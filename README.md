# Signal — Customer Churn Analytics

A Streamlit portfolio app for exploring telecom churn patterns and checking a small, reproducible logistic model. The app runs without downloading a dataset or training at startup. It ships numeric model parameters and aggregate sample statistics, not customer records.

**Deployment status:** local build; no live URL verified in this build. Intended repository: https://github.com/santhi-sagar/customer-churn-analytics.

## Run locally

Python 3.12 is the tested version. From the repository directory:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` pins the four direct runtime dependencies only. `requirements-dev.txt` adds training/tests, and `requirements-lock.txt` records the exact full 46-package tested Windows environment (optional forensic reproduction, not the Linux deployment install). Runtime scoring uses a human-readable JSON logistic artifact, not a pickle. There is no runtime network call or external API key. A host may still need internet to install dependencies. Streamlit Community Cloud free hosting can sleep or restart; do not rely on session uploads or local files for durable storage.

## What is included

- Historical churn dashboard with contract, tenure, internet-service, payment-method and support segments, plus aggregate CSV downloads.
- A single-customer form and validated UTF-8 CSV scoring (10,000 rows / 5 MB maximum). Output contains only row numbers, scores, review flags and clearly named proxies.
- A synthetic input template. It is not a source customer.
- Holdout ROC and precision–recall curves, confusion matrix, prior baseline, model selection evidence and coefficient associations.
- Deterministic training script, strict schema validation, pytest checks, and Streamlit AppTest interaction coverage.
- Power BI-ready aggregate CSVs in `data/aggregates/`. `POWERBI_HANDOFF.md` defines safe use and double-counting constraints. The native Power BI report is handled separately; the presence of these assets does not mean a PBIX has been created or opened.

## Reproduce the study

The app does not need the private source CSV. To reproduce training, download the pinned IBM sample to the ignored `data/private/telco.csv` directory:

```bash
pip install -r requirements-dev.txt
python scripts/download_data.py
python train.py --data data/private/telco.csv
python -m pytest -q
```

The downloader and trainer verify SHA-256 `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91` against the pinned IBM commit. Read `DATA_PROVENANCE.md` before downloading or redistributing source material. The raw CSV contains customer IDs and must not be committed. `data/private/`, uploads, secrets and virtual environments are ignored.

Training uses a stratified random 60/20/20 split (4,225 / 1,409 / 1,409), seed 42. Preprocessing fits only training data. A prior baseline is compared with logistic regression C=0.1, 1, and 10. Candidate choice uses validation average precision; the threshold maximizes validation F1 over 0.05–0.95 in 0.01 steps, with the lowest threshold breaking ties. The selected model and threshold are frozen before test evaluation. There is no final refit on validation/test data.

The selected model is logistic regression C=1.0 at threshold 0.33. Final holdout results:

| Metric | Selected model | Prior baseline |
|---|---:|---:|
| ROC-AUC | 0.8417 | 0.5000 |
| Average precision | 0.6326 | 0.2654 |
| Precision | 0.5362 | 0.0000 |
| Recall | 0.7326 | 0.0000 |
| F1 | 0.6192 | 0.0000 |
| Accuracy | 0.7608 | 0.7346 |
| Brier score (lower is better) | 0.1382 | 0.1950 |

Baseline classification uses threshold 0.5 and predicts no churn. Confusion matrix for the selected model: TN=798, FP=237, FN=100, TP=274. See `artifacts/evaluation.json` and `BUILD_REPORT.md` for full evidence and exact dependency versions. Random splitting is not a substitute for temporal or external validation.

## Business definitions and limitations

**Observed churn rate** = source records with Churn=Yes / source records. **Historical churned-group monthly exposure** = sum of monthly charges among records already labeled churned. **Revenue at risk / weighted monthly exposure proxy** = sum(predicted churn probability × monthly charges) over the scored batch. It is not measured future loss, recoverable revenue, ARR, profit or demonstrated savings; probability calibration and a prospective time horizon have not been established.

**CLV proxy / historical value proxy** = tenure × current monthly charges. This is a constant-price approximation of historical gross value, not discounted lifetime value or future profit. `TotalCharges` is the source historical billing field, not the same calculation. No payment-delay field exists in this sample. PaymentMethod is not payment timeliness.

Customer ID, gender, senior-citizen status, partner and dependents are excluded from model inputs. Exclusion alone does not establish fairness because other inputs can be proxies. The dataset lacks collection timestamps and a verified feature cutoff; leakage from contemporaneous status cannot be ruled out. No retention treatment effect or causal business benefit is claimed. See `MODEL_CARD.md` and `DATA_DICTIONARY.md`.

Uploads are processed in the app session and are not intentionally written to disk. Do not upload real personal data. This sample application has no user authentication, formal privacy guarantee, audit trail, drift monitor or production SLA.

## Source and licensing

IBM’s archived [Telco code-pattern repository](https://github.com/IBM/telco-customer-churn-on-icp4d) supplies the CSV. The repository licenses its code pattern under Apache-2.0, but we found no separate dataset-specific license. This is documented uncertainty, not a claim that the dataset is public domain or CC0. No source rows are distributed here. See `DATA_PROVENANCE.md` and `THIRD_PARTY_NOTICES.md`. New project code is licensed under MIT; that license does not relicense IBM material.
