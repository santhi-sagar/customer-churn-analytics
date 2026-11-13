"""Rebuild artifacts: python train.py --data data/private/telco.csv
No source rows, customer IDs or split indices are exported.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, roc_curve, precision_recall_curve, brier_score_loss)
from core import ROOT, FEATURES, NUMERIC, CATEGORIES, predict

SEED = 42
SOURCE = 'https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/d5371f5/data/Telco-Customer-Churn.csv'
EXPECTED_HASH = '16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91'


def dump(name, obj):
    (ROOT/'artifacts'/name).write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')


def metrics(y, p, threshold):
    flag = p >= threshold
    return {k: float(v) for k, v in {
        'accuracy': accuracy_score(y, flag), 'precision': precision_score(y, flag, zero_division=0),
        'recall': recall_score(y, flag, zero_division=0), 'f1': f1_score(y, flag),
        'roc_auc': roc_auc_score(y, p), 'average_precision': average_precision_score(y, p),
        'brier_score': brier_score_loss(y, p)}.items()}


def train(data):
    raw = Path(data).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_HASH:
        raise ValueError('Source checksum differs. Review provenance before changing the pinned source.')
    df = pd.read_csv(data)
    df.TotalCharges = pd.to_numeric(df.TotalCharges, errors='coerce')
    y = df.Churn.eq('Yes').astype(int)
    x = df[FEATURES]
    # Split first: transformations fit ONLY training data, never validation/test.
    xt, x_test, yt, y_test = train_test_split(x, y, test_size=.20, stratify=y, random_state=SEED)
    x_train, x_val, y_train, y_val = train_test_split(xt, yt, test_size=.25, stratify=yt, random_state=SEED)
    models, rows = {}, []
    baseline = DummyClassifier(strategy='prior').fit(x_train, y_train)
    rows.append({'model': 'Prior baseline', 'validation_average_precision': average_precision_score(y_val, baseline.predict_proba(x_val)[:,1])})
    for c in [.1, 1.0, 10.0]:
        pre = ColumnTransformer([
            ('num', Pipeline([('impute', SimpleImputer(strategy='median')), ('scale', StandardScaler())]), NUMERIC),
            ('cat', OneHotEncoder(handle_unknown='error', sparse_output=False), list(CATEGORIES))])
        pipe = Pipeline([('pre', pre), ('model', LogisticRegression(C=c, max_iter=2000, random_state=SEED))])
        pipe.fit(x_train, y_train)
        name = f'Logistic C={c}'
        models[name] = pipe
        rows.append({'model': name, 'validation_average_precision': average_precision_score(y_val, pipe.predict_proba(x_val)[:,1])})
    selected = max(models, key=lambda n: next(r['validation_average_precision'] for r in rows if r['model']==n))
    model = models[selected]
    pv = model.predict_proba(x_val)[:,1]
    thresholds = np.arange(.05, .951, .01)
    f1s = [f1_score(y_val, pv >= t) for t in thresholds]
    threshold = float(thresholds[int(np.argmax(f1s))])
    # Freeze trained model and threshold. No refit on validation, no test optimization.
    ptest = model.predict_proba(x_test)[:,1]
    baseline_p = baseline.predict_proba(x_test)[:,1]
    scaler = model['pre'].named_transformers_['num']['scale']
    encoder = model['pre'].named_transformers_['cat']
    artifact = {'format_version': 1, 'model': selected, 'threshold': threshold,
        'numeric': NUMERIC, 'categorical': list(CATEGORIES),
        'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist(),
        'training_median': model['pre'].named_transformers_['num']['impute'].statistics_.tolist(),
        'categories': [v.tolist() for v in encoder.categories_],
        'coef': model['model'].coef_[0].tolist(), 'intercept': float(model['model'].intercept_[0])}
    dump('model.json', artifact)
    # Validate portable inference against sklearn on complete holdout rows.
    complete = x_test.dropna()
    np.testing.assert_allclose(predict(complete, artifact), model.predict_proba(complete)[:,1], rtol=1e-12, atol=1e-12)
    fpr,tpr,_ = roc_curve(y_test, ptest)
    precision,recall,_ = precision_recall_curve(y_test, ptest)
    names = model['pre'].get_feature_names_out()
    coefs = sorted([{'feature': str(n).replace('num__','').replace('cat__',''), 'coefficient': float(c)} for n,c in zip(names,artifact['coef'])], key=lambda r: abs(r['coefficient']), reverse=True)
    evaluation = {'seed': SEED, 'source_sha256': sha, 'source_url': SOURCE,
        'sklearn_version': sklearn.__version__, 'split': {'train':len(x_train),'validation':len(x_val),'test':len(x_test)},
        'selected_model': selected, 'selection_metric': 'validation average precision',
        'threshold': threshold, 'threshold_objective': 'maximum validation F1 on 0.05–0.95 grid step 0.01; lowest threshold breaks ties',
        'candidates': rows, 'validation_selected': metrics(y_val,pv,threshold),
        'holdout_selected': metrics(y_test,ptest,threshold),
        'holdout_baseline_at_0_5': metrics(y_test,baseline_p,.5),
        'holdout_prevalence':float(y_test.mean()), 'confusion_matrix':confusion_matrix(y_test,ptest>=threshold).tolist(),
        'roc': {'fpr':fpr.tolist(),'tpr':tpr.tolist()}, 'pr':{'recall':recall.tolist(),'precision':precision.tolist()},
        'coefficients':coefs, 'portable_max_absolute_error':float(np.max(np.abs(predict(complete,artifact)-model.predict_proba(complete)[:,1])))}
    dump('evaluation.json', evaluation)
    # Historical descriptions use entire source sample, not holdout model evaluation.
    analysis = df.assign(churned=y, tenure_band=pd.cut(df.tenure,[-1,12,24,48,72],labels=['0–12','13–24','25–48','49–72']).astype(str))
    segments={}
    for col in ['Contract','tenure_band','InternetService','PaymentMethod','TechSupport']:
        grouped=analysis.groupby(col, observed=True).agg(customers=('churned','size'),churned=('churned','sum'),monthly_charges=('MonthlyCharges','sum')).reset_index()
        grouped['churn_rate']=grouped.churned/grouped.customers
        segments[col]=grouped.rename(columns={col:'segment'}).to_dict(orient='records')
    dash={'customers':len(df),'churned':int(y.sum()),'churn_rate':float(y.mean()),
        'monthly_charges':float(df.MonthlyCharges.sum()),
        'churned_monthly_charges':float(df.loc[y.eq(1),'MonthlyCharges'].sum()),
        'historical_value_proxy_total':float((df.MonthlyCharges*df.tenure).sum()),
        'missing_total_charges':int(df.TotalCharges.isna().sum()), 'segments':segments}
    dump('dashboard.json',dash)
    aggregate_dir = ROOT/'data/aggregates'
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    tables = []
    for dimension, records in segments.items():
        table = pd.DataFrame(records).rename(columns={'segment':'Segment', 'customers':'Customers', 'churned':'Churned', 'monthly_charges':'MonthlyCharges', 'churn_rate':'ChurnRate'})
        table.insert(0, 'Dimension', dimension)
        tables.append(table)
    pd.concat(tables, ignore_index=True).to_csv(aggregate_dir/'segments.csv', index=False)
    pd.DataFrame([{'Metric':k,'Value':v} for k,v in dash.items() if k!='segments']).to_csv(aggregate_dir/'summary.csv', index=False)
    from core import synthetic_template
    synthetic_template().to_csv(ROOT/'data/synthetic_scoring_template.csv', index=False)
    print(json.dumps({'selected':selected,'threshold':threshold,'holdout':evaluation['holdout_selected'],'splits':evaluation['split'],'portable_error':evaluation['portable_max_absolute_error']},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); args=ap.parse_args();train(args.data)
