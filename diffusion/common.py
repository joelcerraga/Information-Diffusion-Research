from pathlib import Path
import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, p)

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def design():
    d=json.loads((ROOT/'protocol/design-v1.json').read_text())
    p=ROOT/'protocol/amendment-01.json'
    if p.exists():
        a=json.loads(p.read_text())
        for k in ['assets','primary_asset','bar_label']:d[k]=a[k]
        d['price_source']=a['source'];d['price_definition']=a['price_measure']
        d['missing_data']=a['missingness'];d['source_timezone']='Etc/GMT+5'
        d['primary_inference']=d['primary_inference'].replace('SPY','SPX')
        d['applied_amendments']=['A01']
    p=ROOT/'protocol/amendment-02.json'
    if p.exists():
        a=json.loads(p.read_text());d['source_timezone']=a['clock_rule'];d['applied_amendments'].append('A02')
        d['chronological_evaluation']+=' Corrected analysis follows A02; the original held-out outcomes had already been inspected. Treat as post-audit chronological transfer, not untouched validation.'
    return d

def phase(date):
    s = str(date)[:10]
    return 'development' if s <= '2022-12-31' else 'validation' if s <= '2023-12-31' else 'holdout'

def save_csv(df, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');df.to_csv(tmp,index=False,float_format='%.12g');os.replace(tmp,p)
