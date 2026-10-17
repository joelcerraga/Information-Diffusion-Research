"""Free web downloads and the independently audited calendar correction (A02)."""
import re
import json
import time
import zipfile
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from .common import ROOT, design, sha256, utcnow, write_json, save_csv

AGENT='InformationDiffusionResearch/0.1'

def source_page(symbol,year):
    return f'https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{symbol.lower()}/{year}'

def archive_path(symbol,year):return ROOT/f'data/raw/histdata/{symbol}/{year}.zip'

def download_year(symbol,year):
    path=archive_path(symbol,year);url=source_page(symbol,year)
    record={'symbol':symbol,'year':int(year),'url':url,'path':str(path.relative_to(ROOT))}
    if path.exists():
        record.update(status='cached',bytes=path.stat().st_size,sha256=sha256(path));return record
    errors=[]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':AGENT}),timeout=30) as r:html=r.read().decode()
            form=re.search(r'<form id="file_down".*?</form>',html,re.S)
            if form is None:raise ValueError('No free download form for this symbol/year')
            params=dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"',form.group()))
            if params.get('fxpair')!=symbol or params.get('date')!=str(year):raise ValueError('Download form instrument/year mismatch')
            req=urllib.request.Request('https://www.histdata.com/get.php',data=urllib.parse.urlencode(params).encode(),headers={'Referer':url,'User-Agent':AGENT})
            with urllib.request.urlopen(req,timeout=60) as r:blob=r.read()
            if blob[:2]!=b'PK':raise ValueError('Response is not a ZIP archive')
            path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_bytes(blob);tmp.replace(path)
            record.update(status='downloaded',bytes=len(blob),sha256=sha256(path),retrieved_utc=utcnow(),previous_errors=errors);return record
        except Exception as exc:
            errors.append(f'{type(exc).__name__}: {exc}')
            if isinstance(exc,urllib.error.HTTPError) and exc.code in (403,404,429):break
            if attempt<2:time.sleep(5*(attempt+1))
    record.update(status='failed',errors=errors,retrieved_utc=utcnow());return record

def acquire(which):
    years={'development':range(2017,2023),'validation':[2023],'holdout':[2024,2025]}[which]
    if which=='holdout' and not (ROOT/'protocol/holdout-release.json').exists():raise RuntimeError('Freeze model before holdout release')
    tasks=[(s,y) for s in design()['assets'].values() for y in years];records=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(download_year,*t) for t in tasks]
        for f in as_completed(futures):
            r=f.result();records.append(r)
            write_json(ROOT/f'data/histdata-acquisition-{which}.json',records)
            print(which,r['symbol'],r['year'],r['status'],flush=True)
    return records

def source_clock_to_utc(stamps,clock='audited'):
    naive=pd.to_datetime(stamps,format='%Y%m%d %H%M%S',errors='raise')
    if clock=='documented_est':return naive.dt.tz_localize('Etc/GMT+5').dt.tz_convert('UTC')
    if clock!='audited':raise ValueError('Unknown source clock rule')
    # Calendar rule from independent source comparisons, not from maximising model fit.
    # Source stamps are not London local times: the final five-hour displacement matters.
    return naive.dt.tz_localize('Europe/London',ambiguous='raise',nonexistent='raise').dt.tz_convert('UTC')+pd.Timedelta(hours=5)

def decode_year(path,clock='audited'):
    frames=[]
    with zipfile.ZipFile(path) as z:
        files=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if not files:raise ValueError('No CSV in archive')
        for name in files:
            with z.open(name) as f:
                d=pd.read_csv(f,sep=';',names=['stamp','open','high','low','close','volume_unused'],dtype={'stamp':str})
            d['time']=source_clock_to_utc(d.stamp,clock)
            frames.append(d.drop(columns=['stamp','volume_unused']))
    d=pd.concat(frames,ignore_index=True)
    d['duplicate']=d.time.duplicated(keep=False)
    d['valid']=(d[['open','high','low','close']]>0).all(axis=1)&(d.low<=d[['open','close']].min(axis=1))&(d.high>=d[['open','close']].max(axis=1))&~d.duplicate
    # A duplicate keeps an invalid marker; it is never silently made valid.
    d=d.drop_duplicates('time',keep='first').set_index('time').sort_index()
    if not ((d.index.second==0)&(d.index.microsecond==0)).all():raise ValueError('Non-minute time stamp')
    return d

def align_frame(d,event_time):
    offsets=np.arange(-61,120);start=pd.Timestamp(event_time).tz_convert('UTC')
    x=d.reindex(start+pd.to_timedelta(offsets,unit='m')).copy();x['offset']=offsets
    required=x[x.offset.between(-61,25)]
    missing=int(required.close.isna().sum());invalid=int((required.valid!=True).sum())
    if missing or invalid:raise ValueError(f'missing_required={missing};invalid_required={invalid}')
    return x.reset_index().rename(columns={'index':'time'})

def process(which):
    if which=='holdout' and not (ROOT/'protocol/holdout-release.json').exists():raise RuntimeError('Holdout has not been released')
    ev=pd.read_csv(ROOT/'data/processed/event-register.csv');ev=ev[ev.phase==which]
    bars=[];audit=[];year_audit=[]
    for asset,symbol in design()['assets'].items():
        needed=set(pd.to_datetime(ev.date).dt.year)
        for c in ['control_'+str(i) for i in range(4)]:needed.update(pd.to_datetime(ev[c].dropna()).dt.year)
        # Load only relevant years. Missing archives remain explicit exclusions.
        dates=set(ev.date)
        for c in ['control_'+str(i) for i in range(4)]:dates.update(ev[c].dropna())
        parts=[]
        for year in sorted(needed):
            path=archive_path(symbol,year)
            if not path.exists():continue
            d=decode_year(path)
            year_audit.append({'asset':asset,'year':int(year),'rows':len(d),'invalid_rows':int((~d.valid).sum()),'first_utc':str(d.index.min()),'last_utc':str(d.index.max()),'archive_sha256':sha256(path)})
            parts.append(d[np.isin(d.index.strftime('%Y-%m-%d'),list(dates))])
        d=pd.concat(parts).sort_index() if parts else pd.DataFrame(columns=['close','valid','open','high','low'],index=pd.DatetimeIndex([],tz='UTC',name='time'))
        for _,r in ev.iterrows():
            a={'event_id':r.event_id,'event_type':r.event_type,'date':r.date,'asset':asset,'phase':which,'event_accepted':False,'control_accepted':False,'control_reason':'event excluded'}
            try:
                x=align_frame(d,r.event_time_utc)
                a.update(event_accepted=True,event_reason='',flat_pre_fraction=float((x.loc[x.offset.between(-60,-1),'close'].diff()==0).mean()),flat_post_fraction=float((x.loc[x.offset.between(0,19),'close'].diff()==0).mean()))
                bars.append(x.assign(event_id=r.event_id,asset=asset,kind='event',source_date=r.date,phase=which))
            except Exception as exc:a['event_reason']=str(exc);audit.append(a);continue
            a['control_reason']='no candidate passed'
            for j in range(4):
                date=str(r.get('control_'+str(j),''))
                if not date or date=='nan':continue
                ct=pd.Timestamp(date+' 14:00').tz_localize('America/New_York').tz_convert('UTC')
                try:
                    x=align_frame(d,ct)
                    bars.append(x.assign(event_id=r.event_id,asset=asset,kind='control',source_date=date,phase=which))
                    a.update(control_accepted=True,control_reason='',control_date=date,control_candidate=j);break
                except Exception as exc:a['control_reason']=str(exc)
            audit.append(a)
        print('aligned',which,asset,'events',sum(a['event_accepted'] for a in audit if a['asset']==asset),flush=True)
    save_csv(pd.concat(bars,ignore_index=True) if bars else pd.DataFrame(),ROOT/f'data/processed/bars-{which}.csv')
    save_csv(pd.DataFrame(audit),ROOT/f'data/processed/audit-{which}.csv')
    save_csv(pd.DataFrame(year_audit),ROOT/f'data/processed/source-years-{which}.csv')
    return pd.DataFrame(audit)
