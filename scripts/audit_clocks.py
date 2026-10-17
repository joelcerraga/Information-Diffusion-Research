"""Reproduce clock probes from the cached independent download routes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from diffusion.histdata import decode_year,archive_path
from diffusion.data import decode_candles,bar_path,fetch
from diffusion.common import ROOT,save_csv,write_json
jobs=[('SPXUSD','SPYUSUSD','2022-09-21',1000),('SPXUSD','SPYUSUSD','2022-03-16',1000),('NSXUSD','QQQUSUSD','2022-09-21',1000),('EURUSD','EURUSD','2022-09-21',100000),('EURUSD','EURUSD','2022-03-16',100000)]
rows=[]
for hs,ds,date,scale in jobs:
    path=bar_path(ds,date,'BID')[1]
    if not path.exists():raise FileNotFoundError(f'{path}; obtain the five documented probe files with the data cache or the public acquisition helper')
    ref=decode_candles(path.read_bytes(),date,scale).close;source=decode_year(archive_path(hs,2022),clock='documented_est').close;ix=pd.date_range(date+' 17:30Z',date+' 19:30Z',freq='min')
    for shift in [0,60]:
        a=source.reindex(ix+pd.Timedelta(minutes=shift)).to_numpy();b=ref.reindex(ix).to_numpy();v=np.c_[np.diff(np.log(a)),np.diff(np.log(b))];v=v[np.isfinite(v).all(axis=1)]
        rows.append({'histdata':hs,'comparison':ds,'date':date,'shift_minutes':shift,'paired_returns':len(v),'return_correlation':np.corrcoef(v.T)[0,1]})
save_csv(pd.DataFrame(rows),ROOT/'outputs/tables/clock-probe-summary.csv');print(pd.DataFrame(rows).to_string(index=False))
