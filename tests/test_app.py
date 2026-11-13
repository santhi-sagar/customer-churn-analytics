import sys
from pathlib import Path
import json
import hashlib
import subprocess
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import FEATURES, validate_frame, predict, score, read_csv_bytes, synthetic_template, load_json


def test_synthetic_valid():
    x=synthetic_template()
    assert list(validate_frame(x).columns)==FEATURES
    p=predict(x)
    assert p.shape==(1,) and 0<p[0]<1
    output=score(x)
    assert output.input_row.tolist()==[1]
    assert output.monthly_charge_exposure_proxy.iloc[0]==pytest.approx(p[0]*65)
    assert output.historical_value_proxy.iloc[0]==780
    assert not set(FEATURES)&set(output.columns)

@pytest.mark.parametrize('column,value',[
    ('tenure',-1),('tenure',73),('tenure',1.5),('MonthlyCharges',float('inf')),
    ('MonthlyCharges',float('nan')),('TotalCharges','garbage'),('TotalCharges',9001),
    ('Contract','unknown'),('PhoneService','No'),('InternetService','No'),('TechSupport','No internet service')])
def test_bad_values(column,value):
    x=synthetic_template();x[column]=value
    with pytest.raises(ValueError):validate_frame(x)


def test_csv_and_headers():
    x=synthetic_template()
    assert len(read_csv_bytes(x.to_csv(index=False).encode()))==1
    with pytest.raises(ValueError):validate_frame(x.drop(columns='Contract'))
    with pytest.raises(ValueError):validate_frame(x.assign(customerID='private'))
    with pytest.raises(ValueError):validate_frame(x.iloc[:0])
    with pytest.raises(ValueError):validate_frame(pd.concat([x]*10001,ignore_index=True))
    with pytest.raises(ValueError):read_csv_bytes(b'a,a\n1,2')
    with pytest.raises(ValueError):read_csv_bytes(b'\xff\xfe')
    with pytest.raises(ValueError):read_csv_bytes(b'x'*(5*1024*1024+1))
    duplicate=x.copy();duplicate.columns=['tenure']*len(x.columns)
    with pytest.raises(ValueError):validate_frame(duplicate)


def test_reordered_columns_batch_consistency():
    x=synthetic_template(); y=x.iloc[:,::-1]
    np.testing.assert_allclose(predict(x),predict(y))
    batch=pd.concat([x,x],ignore_index=True)
    np.testing.assert_allclose(score(batch).churn_probability,[predict(x)[0]]*2)


def test_metrics_integrity():
    e=load_json('evaluation.json');d=load_json('dashboard.json')
    assert sum(e['split'].values())==d['customers']==7043
    assert np.array(e['confusion_matrix']).sum()==e['split']['test']
    assert e['portable_max_absolute_error']<1e-12
    assert e['holdout_selected']['roc_auc']>.75
    assert e['holdout_selected']['average_precision']>e['holdout_prevalence']
    for rows in d['segments'].values():
        assert sum(v['customers'] for v in rows)==7043
        assert sum(v['churned'] for v in rows)==d['churned']


def test_streamlit_app():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
    assert not at.exception
    assert len(at.tabs)==6
    assert any('Observed churn rate'==m.label for m in at.metric)
    at.button[0].click().run()
    assert not at.exception
    assert any(m.label=='Model churn probability' for m in at.metric)
    # A conflicting phone state is rejected by the same UI submit path.
    at.selectbox(key=None) if False else None
    next(w for w in at.selectbox if w.label=='PhoneService').set_value('No')
    at.button[0].click().run()
    assert not at.exception
    assert any('inconsistent' in err.value for err in at.error)


def test_headless_server_health():
    import socket
    import time
    import urllib.request
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','streamlit','run','app.py',
        '--server.headless=true',f'--server.port={port}', '--server.address=127.0.0.1'],
        cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.time()+40
        while time.time()<deadline:
            if process.poll() is not None:raise AssertionError('Streamlit exited before serving')
            try:
                response=urllib.request.urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1)
                assert response.read()==b'ok'
                return
            except (OSError,TimeoutError):time.sleep(.3)
        raise AssertionError('Streamlit did not become healthy')
    finally:
        process.terminate();process.wait(timeout=15)


def test_rebuild_identical():
    source=ROOT/'data/private/telco.csv'
    if not source.exists():pytest.skip('Private source excluded from public repository; download pinned source to reproduce.')
    files=['artifacts/model.json','artifacts/evaluation.json','artifacts/dashboard.json',
        'data/aggregates/segments.csv','data/aggregates/summary.csv','data/synthetic_scoring_template.csv']
    before={n:(ROOT/n).read_bytes() for n in files}
    subprocess.run([sys.executable,str(ROOT/'train.py'),'--data',str(source)],check=True,cwd=ROOT,capture_output=True)
    assert all((ROOT/n).read_bytes()==before[n] for n in files)
