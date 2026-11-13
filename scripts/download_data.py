"""Explicit development-only downloader. Never called by app.py."""
from pathlib import Path
import hashlib
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
URL='https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/d5371f5/data/Telco-Customer-Churn.csv'
EXPECTED='16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91'
if __name__=='__main__':
    data=urllib.request.urlopen(URL,timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=EXPECTED:raise ValueError('Checksum mismatch')
    dest=ROOT/'data/private/telco.csv';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print('Verified source saved to ignored data/private/telco.csv. Do not commit source rows.')
