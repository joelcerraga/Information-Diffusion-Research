"""Public acquisition, binary decoding and strict event-time alignment."""
import io
import json
import lzma
import struct
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from .common import ROOT, design, sha256, utcnow, write_json, save_csv, phase

USMPD_URL='https://www.frbsf.org/wp-content/uploads/USMPD.xlsx'
FEED='https://www.dukascopy.com/datafeed'
AGENT='InformationDiffusionResearch/0.1 (academic historical analysis)'

def fetch(url, path, attempts=4):
    p=Path(path)
    if p.exists() and p.stat().st_size:
        return {'url':url,'path':str(p.relative_to(ROOT)),'status':'cached','sha256':sha256(p),'bytes':p.stat().st_size}
    p.parent.mkdir(parents=True,exist_ok=True)
    errors=[]
    for attempt in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':AGENT})
            with urllib.request.urlopen(req,timeout=30) as response:
                blob=response.read()
            if not blob:raise ValueError('empty response')
            if p.suffix=='.bi5':
                raw=lzma.decompress(blob)
                if len(raw)%24:raise ValueError('candle record length is not a multiple of 24')
            tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(blob);tmp.replace(p)
            return {'url':url,'path':str(p.relative_to(ROOT)),'status':'downloaded','sha256':sha256(p),'bytes':len(blob),'retrieved_utc':utcnow(),'previous_errors':errors}
        except Exception as exc:
            errors.append(f'{type(exc).__name__}: {exc}')
            if isinstance(exc,urllib.error.HTTPError) and exc.code in (403,404):break
            if attempt+1<attempts:
                wait=min(45,5*2**attempt)
                if isinstance(exc,urllib.error.HTTPError):
                    retry=exc.headers.get('Retry-After','')
                    if retry.isdigit(): wait=max(wait,int(retry))
                time.sleep(wait)
    return {'url':url,'path':str(p.relative_to(ROOT)),'status':'failed','errors':errors,'retrieved_utc':utcnow()}

def initialise():
    conf=design()
    path=ROOT/'protocol/design-v1.json'
    lock=ROOT/'protocol/design-v1-lock.json'
    if not lock.exists():write_json(lock,{'sha256':sha256(path),'recorded_utc':utcnow(),'scope':'Protocol locked before study-period intraday acquisition; source schema and 2017 availability probes preceded the lock.'})
    if json.loads(lock.read_text())['sha256']!=sha256(path):raise ValueError('Protocol changed after lock')
    raw=ROOT/'data/raw/USMPD.xlsx';record=fetch(USMPD_URL,raw)
    if record['status']=='failed':raise RuntimeError(record)
    write_json(ROOT/'data/usmpd-source.json',record)
    x=pd.ExcelFile(raw)
    all_dates=set()
    for sheet in ['Statements','Press Conferences','Minutes']:
        all_dates.update(pd.read_excel(x,sheet).Date.dt.strftime('%Y-%m-%d'))
    rows=[]; excluded=[]
    for typ in conf['event_types']:
        d=pd.read_excel(x,typ)
        d=d[(d.Date>=conf['sample']['start'])&(d.Date<=conf['sample']['end'])]
        for _,r in d.iterrows():
            date=r.Date.strftime('%Y-%m-%d'); t=pd.Timestamp(r.date_time)
            reason=''
            if r.get('Unscheduled',0)==1:reason='unscheduled communication'
            elif t.strftime('%H:%M')!='14:00':reason='outside declared 14:00 release profile'
            elif r[conf['surprise_inputs']].isna().any():reason='missing rate surprise component'
            if reason:excluded.append({'event_type':typ,'date':date,'reason':reason});continue
            row={'event_id':typ.lower()+'_'+date,'event_type':typ,'date':date,'phase':phase(date),'event_time_ny':t.tz_localize('America/New_York').isoformat(),'event_time_utc':t.tz_localize('America/New_York').tz_convert('UTC').isoformat(),'SEP':int(r.get('SEP',0))}
            for c in conf['surprise_inputs']+['SP500','SPFUT','UST2Y','UST10Y']:row[c]=r.get(c,np.nan)
            for j,days in enumerate([7,14,21,28]):
                candidate=(r.Date-pd.Timedelta(days=days)).strftime('%Y-%m-%d')
                row['control_'+str(j)]=candidate if candidate not in all_dates else ''
            rows.append(row)
    ev=pd.DataFrame(rows).sort_values(['date','event_type'])
    save_csv(ev,ROOT/'data/processed/event-register.csv')
    save_csv(pd.DataFrame(excluded),ROOT/'data/processed/event-exclusions.csv')
    save_csv(pd.read_excel(x,'README'),ROOT/'data/processed/usmpd-readme.csv')
    return ev

def bar_path(symbol,date,side):
    dt=pd.Timestamp(date)
    rel=f'{symbol}/{dt.year}/{dt.month-1:02d}/{dt.day:02d}/{side}_candles_min_1.bi5'
    return FEED+'/'+rel,ROOT/'data/raw/dukascopy'/rel

def decode_candles(blob,date,scale=1000):
    raw=lzma.decompress(blob)
    if len(raw)%24:raise ValueError('invalid binary length')
    data=list(struct.iter_unpack('>5If',raw))
    df=pd.DataFrame(data,columns=['seconds','open','close','low','high','quote_volume'])
    if df.empty:raise ValueError('empty decoded file')
    if (df.seconds%60!=0).any() or not df.seconds.between(0,86340).all():raise ValueError('invalid minute offsets')
    if df.seconds.duplicated().any() or not df.seconds.is_monotonic_increasing:raise ValueError('duplicate or unsorted minute offsets')
    for c in ['open','close','low','high']:df[c]=df[c]/scale
    df['valid']=(df[['open','close','low','high']]>0).all(axis=1)&(df.low<=df[['open','close']].min(axis=1))&(df.high>=df[['open','close']].max(axis=1))
    df['time']=pd.Timestamp(date,tz='UTC')+pd.to_timedelta(df.seconds,unit='s')
    return df.set_index('time')

def quote_day(symbol,date):
    sides=[]
    for side in ['BID','ASK']:
        _,p=bar_path(symbol,date,side)
        if not p.exists():raise FileNotFoundError(str(p))
        d=decode_candles(p.read_bytes(),date)
        sides.append(d[['close','valid','quote_volume']].rename(columns={c:side.lower()+'_'+c for c in ['close','valid','quote_volume']}))
    d=sides[0].join(sides[1],how='outer')
    d['mid']=(d.bid_close+d.ask_close)/2
    d['spread_bps']=10000*(d.ask_close-d.bid_close)/d.mid
    d['valid']=d.bid_valid.fillna(False)&d.ask_valid.fillna(False)&(d.ask_close>=d.bid_close)
    return d

def align_day(symbol,date,event_time):
    d=quote_day(symbol,date)
    start=pd.Timestamp(event_time).tz_convert('UTC')
    offsets=np.arange(-61,120)
    idx=start+pd.to_timedelta(offsets,unit='m')
    x=d.reindex(idx).copy();x['offset']=offsets
    primary=x[(x.offset>=-61)&(x.offset<=25)]
    missing=int(primary.mid.isna().sum()); invalid=int((~primary.valid.fillna(False)).sum())
    if missing or invalid:raise ValueError(f'missing_required={missing};invalid_required={invalid}')
    out=x.reset_index().rename(columns={'index':'time'})
    return out

def acquire_phase(which,workers=2):
    ev=pd.read_csv(ROOT/'data/processed/event-register.csv')
    ev=ev[ev.phase==which]
    conf=design(); tasks={}
    for _,r in ev.iterrows():
        for symbol in conf['assets'].values():
            for side in ['BID','ASK']:
                u,p=bar_path(symbol,r.date,side);tasks[str(p)]=(u,p)
                # First admissible matched date is attempted now. Remaining candidates
                # are downloaded only if coverage validation requires a fallback.
                candidates=[str(r.get('control_'+str(i),'')) for i in range(4)]
                candidates=[c for c in candidates if c and c!='nan']
                if candidates:
                    u,p=bar_path(symbol,candidates[0],side);tasks[str(p)]=(u,p)
    log=[]
    def task(item):
        r=fetch(*item);time.sleep(0.4);return r
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(task,v) for v in tasks.values()]
        for j,f in enumerate(as_completed(futures),1):
            log.append(f.result())
            if j%20==0:
                write_json(ROOT/f'data/acquisition-{which}.json',log)
                print(f'{which}: {j}/{len(tasks)} files; failures={sum(x["status"]=="failed" for x in log)}',flush=True)
    write_json(ROOT/f'data/acquisition-{which}.json',log)
    return log

def process_phase(which):
    ev=pd.read_csv(ROOT/'data/processed/event-register.csv');ev=ev[ev.phase==which]
    bars=[]; audits=[]
    for _,r in ev.iterrows():
        for asset,symbol in design()['assets'].items():
            audit={'event_id':r.event_id,'event_type':r.event_type,'date':r.date,'asset':asset,'phase':which}
            try:
                x=align_day(symbol,r.date,r.event_time_utc)
                audit.update(event_accepted=True,event_reason='',median_pre_spread_bps=float(x.loc[x.offset.between(-30,-1),'spread_bps'].median()),flat_pre_fraction=float((x.loc[x.offset.between(-60,-1),'mid'].diff()==0).mean()))
                x=x.assign(event_id=r.event_id,asset=asset,kind='event',source_date=r.date,phase=which)
                bars.append(x)
            except Exception as e:
                audit.update(event_accepted=False,event_reason=str(e));audits.append(audit);continue
            audit.update(control_accepted=False,control_reason='no candidate passed')
            for j in range(4):
                date=str(r.get('control_'+str(j),''))
                if not date or date=='nan':continue
                ct=pd.Timestamp(date+' 14:00').tz_localize('America/New_York').tz_convert('UTC')
                try:
                    if j>0:
                        for side in ['BID','ASK']:fetch(*bar_path(symbol,date,side))
                    z=align_day(symbol,date,ct)
                    z=z.assign(event_id=r.event_id,asset=asset,kind='control',source_date=date,phase=which);bars.append(z)
                    audit.update(control_accepted=True,control_reason='',control_date=date,control_candidate=j);break
                except Exception as e:audit['control_reason']=str(e)
            audits.append(audit)
    df=pd.concat(bars,ignore_index=True) if bars else pd.DataFrame()
    save_csv(df,ROOT/f'data/processed/bars-{which}.csv')
    save_csv(pd.DataFrame(audits),ROOT/f'data/processed/audit-{which}.csv')
    return pd.DataFrame(audits)
