# Build and validation report

Build date: 13 November 2026. Scope: local Streamlit portfolio application, reproducible model pipeline and safe aggregate assets for a separately handled Power BI report. This build did not publish, deploy, edit LinkedIn or verify a native Power BI report.

## Delivered

`app.py`: five tabs (overview, single scoring, batch scoring, evidence, definitions). Contract/tenure/service/payment segments, historical KPIs, ROC/PR plots, confusion matrix, validation selection comparison, coefficient chart, download buttons and privacy/limitations notices.

`core.py`: exact field schema; finite numeric/range checks; required fields; category and service-consistency validation; 5 MB/10,000-row CSV guards; rejection of IDs/demographics/labels/duplicate headers; portable logistic inference; non-identifying score outputs; generated synthetic input template.

`train.py`: source-checksum guard; training-only preprocessing; stratified 60/20/20 split; prior baseline; three regularized logistic candidates; validation-only model/threshold choice; frozen test evaluation; JSON model/evidence/dashboard exports; Power BI aggregate CSVs and synthetic template. A separate notebook was not added because the small training script is the canonical reproducible pipeline.

`data/aggregates/segments.csv` contains 17 aggregated rows across five dimensions. Do not sum across dimensions: each dimension partitions the same 7,043 records. `summary.csv` has seven whole-sample metrics. `POWERBI_HANDOFF.md` and `DATA_DICTIONARY.md` define the exact measures. These assets are not proof that a Power BI report has been opened or validated.

## Tested environment

Windows, Python 3.12.7; NumPy 2.2.6, pandas 2.2.3, scikit-learn 1.6.1, SciPy 1.15.3, Streamlit 1.45.1, Plotly 6.1.2, pytest 8.3.5. The exact 46-package tested environment is saved in requirements-lock.txt. Minimal runtime requirements.txt pins only Streamlit, pandas, NumPy and Plotly. requirements-dev.txt adds sklearn 1.6.1, SciPy 1.15.3 and pytest 8.3.5. Linux deployment uses minimal runtime requirements, not the Windows forensic lock. Linux/cloud execution has not been verified in this build. Use Python 3.12 when deploying.

Commands executed from project directory using its isolated Python environment:

```text
python train.py --data data/private/telco.csv
python -m compileall -q app.py core.py train.py tests scripts
python -m pytest -q
uv pip check --python .venv/Scripts/python.exe
```

Final result: **18 passed in 14.19 seconds**, no test failures. Dependency check: **All installed packages are compatible** (46 packages). Compile/import check succeeded. Test suite includes:

- Valid synthetic single and repeated batch probabilities; input-column reordering; expected proxy arithmetic.
- Negative/out-of-range/fractional tenure, infinity/NaN/invalid charge inputs, unknown categories, inconsistent phone/internet service states.
- Missing/extra/duplicate headers, identifier rejection, empty/oversized tables, invalid encoding and oversized CSV bytes.
- Holdout split/confusion-matrix integrity; aggregate totals; model beats prevalence baseline on ranking metrics.
- Streamlit AppTest renders all five tabs without exceptions, submits the synthetic form, observes a probability, and rejects conflicting phone state without crashing.
- Actual headless Streamlit process starts with project config, returns `ok` from local `/_stcore/health`, and terminates cleanly.
- Rebuilding all three JSON artifacts, two aggregate CSVs and synthetic template is byte-for-byte identical in the pinned environment.

Portable coefficient-based inference matches sklearn on complete holdout records with maximum absolute difference **1.1102230246251565e-16**. Inference intentionally rejects missing inputs; sklearn training/evaluation median-imputes missing source TotalCharges using training-only statistics.

## Frozen evaluation

Source: 7,043 rows; observed Churn=Yes 1,869 (26.537%). Stratified split seed 42: train 4,225; validation 1,409; test 1,409.

Validation average precision: prior baseline 0.2654365; logistic C=0.1 0.6415359; C=1.0 0.6420254; C=10.0 0.6417507. Selected C=1.0. The small validation differences should not be interpreted as proof of universal superiority.

Threshold: **0.33**, maximizing validation F1 over 0.05–0.95 in 0.01 steps, lowest threshold breaking ties. No threshold was selected from the test set. Model not refit afterward.

| Holdout metric | Selected model | Prior baseline at threshold 0.5 |
|---|---:|---:|
| ROC-AUC | 0.8416518122 | 0.5 |
| Average precision | 0.6325857243 | 0.2654364798 |
| Precision | 0.5362035225 | 0 |
| Recall | 0.7326203209 | 0 |
| F1 | 0.6192090395 | 0 |
| Accuracy | 0.7608232789 | 0.7345635202 |
| Brier score | 0.1382465543 | 0.1949799673 |

Confusion matrix rows=true [No,Yes], columns=predicted [No,Yes]: `[[798,237],[100,274]]`. No external/temporal test, confidence interval, independent calibration assessment or fairness validation was performed.

## Attempts, adjustments and known boundaries

The host Python had pandas/NumPy but no sklearn. An isolated .venv was created. The first resolver installed SciPy 1.18.1, which emitted sklearn OptimizeWarning about unknown `iprint`; pinning SciPy 1.15.3 removed this warning, and the pipeline/tests were rerun. Installing packages fell back from hardlinks to copying across filesystems; this affected install speed, not test results. The final environment is compatible according to uv pip check.

A direct child-to-parent tool message using target `parent` was unsupported, so an early `POWERBI_HANDOFF.md` file and progress update were written instead. No task output depends on that failed message.

Source/license evidence: IBM archived repository and LICENSE were read; repository code pattern is Apache-2.0, with no separate dataset-specific license found. The requested data README URL returned 404. Related IBM Cognos documentation calls its sample fictional and describes churn in the last month, but its five enhanced XLSX files/CLTV fields are not the original CSV. See DATA_PROVENANCE.md for exact evidence URLs and caveats. No blanket claim of CC0/public-domain data is made.

The private raw CSV exists only in ignored `data/private/`, is excluded from sync by .strawberryignore, and must not be uploaded to a public repository. Public assets are derived aggregate statistics and numeric model parameters; no raw source customer IDs/rows, uploads or secrets are in the safe manifest. This is not a formal differential-privacy guarantee. Public-source derivative licensing uncertainty remains disclosed and should be resolved before commercial reuse or raw-data redistribution.

No payment delays, true CLV, realized savings, causal effects or production readiness were invented. Revenue-at-risk is explicitly a weighted monthly-charge exposure proxy, and the CLV proxy is explicitly constant-price historical value, not true lifetime profit. Feature timing leakage cannot be ruled out in the cross-sectional data. These limitations are visible in the app and model card.

## Runtime and publication handoff

From this project directory: `python -m streamlit run app.py` (or activate .venv then `streamlit run app.py`). Entry point `app.py`, Python 3.12. No API keys, secrets, runtime network dataset download or runtime training required. Use the files listed in PUBLIC_FILE_MANIFEST.json; never upload the project directory wholesale. Parent owns GitHub publication, Streamlit deployment and Power BI verification. No live URL is asserted here.
