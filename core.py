"""Shared schema, input validation and portable logistic inference. No network or pickle."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
NUMERIC = ['tenure', 'MonthlyCharges', 'TotalCharges']
CATEGORIES = {
    'PhoneService': ['Yes', 'No'],
    'MultipleLines': ['Yes', 'No', 'No phone service'],
    'InternetService': ['DSL', 'Fiber optic', 'No'],
    **{k: ['Yes', 'No', 'No internet service'] for k in
       ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies']},
    'Contract': ['Month-to-month', 'One year', 'Two year'],
    'PaperlessBilling': ['Yes', 'No'],
    'PaymentMethod': ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'],
}
FEATURES = NUMERIC + list(CATEGORIES)
EXCLUDED = ['customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'Churn']


def load_json(name):
    return json.loads((ROOT / 'artifacts' / name).read_text(encoding='utf-8'))


def validate_frame(frame, max_rows=10000):
    """Reject unknown/duplicate headers, missing values and inconsistent service states."""
    errors = []
    if not isinstance(frame, pd.DataFrame):
        raise ValueError('Expected a table.')
    if frame.empty or len(frame) > max_rows:
        errors.append(f'Provide 1–{max_rows:,} rows.')
    if frame.columns.duplicated().any():
        errors.append('Duplicate column names are not allowed.')
    missing = sorted(set(FEATURES) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(FEATURES))
    if missing:
        errors.append('Missing columns: ' + ', '.join(missing))
    if extra:
        errors.append('Unexpected columns (remove IDs, demographics and labels): ' + ', '.join(extra))
    if errors:
        raise ValueError(' '.join(errors))
    x = frame.loc[:, FEATURES].copy()
    for col in NUMERIC:
        x[col] = pd.to_numeric(x[col], errors='coerce')
        hi = {'tenure': 72, 'MonthlyCharges': 120, 'TotalCharges': 9000}[col]
        bad = (~np.isfinite(x[col])) | (x[col] < 0) | (x[col] > hi)
        if col == 'tenure':
            bad |= x[col] % 1 != 0
        if bad.any():
            errors.append(f'{col}: {int(bad.sum())} invalid values; expected finite numeric 0–{hi}' + (' whole months.' if col == 'tenure' else '.'))
    for col, options in CATEGORIES.items():
        if (~x[col].isin(options)).any():
            errors.append(f'{col}: use exactly {options}.')
    phone_bad = (x.PhoneService == 'No') != (x.MultipleLines == 'No phone service')
    if phone_bad.any():
        errors.append('PhoneService and MultipleLines are inconsistent.')
    for col in ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies']:
        if ((x.InternetService == 'No') != (x[col] == 'No internet service')).any():
            errors.append(f'InternetService and {col} are inconsistent.')
    if errors:
        raise ValueError(' '.join(errors))
    return x


def read_csv_bytes(data):
    import csv
    import io
    if len(data) > 5 * 1024 * 1024:
        raise ValueError('Maximum upload size is 5 MB.')
    try:
        text = data.decode('utf-8-sig')
        header = next(csv.reader(io.StringIO(text)))
        if len(header) != len(set(header)):
            raise ValueError('Duplicate column names are not allowed.')
        return validate_frame(pd.read_csv(io.StringIO(text)))
    except (UnicodeDecodeError, pd.errors.ParserError, StopIteration) as exc:
        raise ValueError('Use a UTF-8 CSV with one header row.') from exc


def predict(frame, artifact=None):
    x = validate_frame(frame)
    a = artifact if artifact is not None else load_json('model.json')
    numeric = (x[NUMERIC].to_numpy(float) - np.array(a['mean'])) / np.array(a['scale'])
    cats = [np.column_stack([(x[col] == v).astype(float) for v in values])
            for col, values in zip(CATEGORIES, a['categories'])]
    z = np.column_stack([numeric, *cats]) @ np.array(a['coef']) + a['intercept']
    return 1 / (1 + np.exp(-np.clip(z, -700, 700)))


def score(frame, artifact=None):
    a = artifact if artifact is not None else load_json('model.json')
    x = validate_frame(frame)
    p = predict(x, a)
    # Output is deliberately identifier-free; 1-based input row order is preserved.
    return pd.DataFrame({'input_row': np.arange(1, len(x) + 1),
        'churn_probability': p, 'review_flag': p >= a['threshold'],
        'monthly_charge_exposure_proxy': p * x.MonthlyCharges.to_numpy(),
        'historical_value_proxy': x.tenure.to_numpy() * x.MonthlyCharges.to_numpy()})


def synthetic_template():
    return pd.DataFrame([{**{'tenure': 12, 'MonthlyCharges': 65.0, 'TotalCharges': 780.0},
        **{k: v[0] for k, v in CATEGORIES.items()}}])[FEATURES]
