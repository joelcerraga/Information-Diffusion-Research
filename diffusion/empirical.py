"""Event-level research: all fits retain horizon and information-set labels."""
import json
import numpy as np
import pandas as pd
from scipy import stats
from .common import ROOT,design,sha256,utcnow,write_json,save_csv
from .statistics import ols_hc3,wild_band,pca_fit,pca_transform,adjustment_diagnostics,year_block_intervals,paired_mse_summary

H=np.arange(1,21)

def load_events():return pd.read_csv(ROOT/'data/processed/event-register.csv')

def build_surprise():
    ev=load_events();c=design()['surprise_inputs']
    d=ev[(ev.phase=='development')&(ev.event_type=='Statements')]
    model=pca_fit(d[c].to_numpy()*100)
    model.update(inputs=c,n=len(d),training_event_ids=d.event_id.tolist(),definition='One development-score standard deviation; rate increases oriented positive; not a structurally identified monetary-policy shock.')
    write_json(ROOT/'outputs/models/surprise-pca.json',model)
    ev['surprise']=pca_transform(ev[c].to_numpy()*100,model)
    save_csv(ev,ROOT/'data/processed/events-with-surprise.csv')
    return model

def data_for(phases):
    events=pd.read_csv(ROOT/'data/processed/events-with-surprise.csv').set_index('event_id')
    frames=[]
    for phase in phases:
        p=ROOT/f'data/processed/bars-{phase}.csv'
        if p.exists():frames.append(pd.read_csv(p))
    return pd.concat(frames,ignore_index=True),events

def panel(bars,events,asset,typ,kind='event',price='close',shift=0):
    b=bars[(bars.asset==asset)&(bars.kind==kind)]
    p=b.pivot(index='event_id',columns='offset',values=price).sort_index()
    ids=[i for i in p.index if events.loc[i,'event_type']==typ]
    p=p.loc[ids];m=events.loc[ids].copy()
    base=p[-1+shift].to_numpy()[:,None]
    y=10000*np.log(p[H-1+shift].to_numpy()/base)
    x=np.c_[np.ones(len(m)),m.surprise.to_numpy()]
    return x,y,m,p

def return_between(p,a,b):return 10000*np.log(p[b-1].to_numpy()/p[a-1].to_numpy())

def coefficient_row(x,y,name,asset,typ,phase):
    f=ols_hc3(x,y)
    return {'phase':phase,'event_type':typ,'asset':asset,'measure':name,'n':f['n'],'estimate':float(f['coef'][1,0]),'se':float(f['se'][1,0]),'ci_low':float(f['lo'][1,0]),'ci_high':float(f['hi'][1,0]),'units':'bp per development surprise SD'}

def analyse(phases,label):
    bars,ev=data_for(phases);curve_rows=[];effects=[];checks=[];shapes={};rvrows=[]
    for typ in design()['event_types']:
        for asset in design()['assets']:
            x,y,m,p=panel(bars,ev,asset,typ)
            if len(m)<6:continue
            f=ols_hc3(x,y);band=wild_band(f,reps=1999)
            for j,h in enumerate(H):
                curve_rows.append({'phase':label,'event_type':typ,'asset':asset,'n':len(m),'horizon':int(h),'intercept':f['coef'][0,j],'beta':f['coef'][1,j],'se':f['se'][1,j],'point_low':f['lo'][1,j],'point_high':f['hi'][1,j],'sim_low':band['lo'][j],'sim_high':band['hi'][j],'sim_critical':band['critical']})
            for a,b,name in [(0,1,'first_minute'),(0,5,'cumulative_5'),(0,10,'cumulative_10'),(0,15,'cumulative_15'),(0,20,'cumulative_20'),(5,20,'late_5_20'),(20,25,'post_observation_20_25'),(-60,-10,'pre_placebo_60_10')]:
                effects.append(coefficient_row(x,return_between(p,a,b),name,asset,typ,label))
            if asset==design()['primary_asset']:
                shapes[typ]=adjustment_diagnostics(f,band,H)
                planned=int(((ev.event_type==typ)&ev.phase.isin(phases)).sum())
                minimum={'development':25,'validation':6,'holdout':10}.get(label,25)
                adequate=len(m)>=minimum and len(m)/planned>=.8
                shapes[typ]['sample']={'accepted':len(m),'planned':planned,'coverage':len(m)/planned,'minimum_events':minimum,'adequate':bool(adequate)}
                if not adequate:
                    shapes[typ].update(reportable=False,reportable_t50_minutes=None,reportable_t90_minutes=None,conditional_t90_interval=None,interpretation='Adjustment speed not reportable: sample coverage rule failed; numerical fit is diagnostic only.')
            # Unconditional event-versus-matched-day variation is distinct from a signed response.
            cx,cy,cm,cp=panel(bars,ev,asset,typ,'control')
            common=m.index.intersection(cm.index)
            for eid in common:
                er=10000*np.diff(np.log(p.loc[eid,np.arange(-1,20)].to_numpy(float)))
                cr=10000*np.diff(np.log(cp.loc[eid,np.arange(-1,20)].to_numpy(float)))
                rvrows.append({'phase':label,'event_id':eid,'event_type':typ,'asset':asset,'event_rv':float(er@er),'control_rv':float(cr@cr),'unit':'squared bp'})
            if len(cm)>=6:
                checks.append(coefficient_row(cx,cy[:,-1],'matched_day_placebo_20',asset,typ,label))
            # Timestamp and quote-field checks do not reselect the primary definition.
            for shift in [-1,1]:
                sx,sy,sm,sp=panel(bars,ev,asset,typ,shift=shift)
                checks.append(coefficient_row(sx,sy[:,-1],f'origin_shift_{shift:+d}',asset,typ,label))
            sx,sy,sm,sp=panel(bars,ev,asset,typ,price='open')
            checks.append(coefficient_row(sx,sy[:,-1],'open_price_same_bar_labels',asset,typ,label))
            # Open at h is an alternative exact-boundary endpoint; close at h-1 is primary.
            op=bars[(bars.asset==asset)&(bars.kind=='event')].pivot(index='event_id',columns='offset',values='open').loc[m.index]
            checks.append(coefficient_row(x,10000*np.log(op[20].to_numpy()/op[0].to_numpy()),'boundary_open_0_to_20',asset,typ,label))
            pre=return_between(p,-60,0)
            vol=np.sqrt(np.sum((10000*np.diff(np.log(p[np.arange(-61,0)].to_numpy()),axis=1))**2,axis=1))
            xx=np.c_[x,pre-pre.mean(),vol-vol.mean()]
            if len(m)>8:checks.append(coefficient_row(xx,y[:,-1],'pre_return_volatility_controls',asset,typ,label))
            post=p[np.arange(0,20)].to_numpy();flat=np.any(np.diff(post,axis=1)==0,axis=1)
            if (~flat).sum()>=6:checks.append(coefficient_row(x[~flat],y[~flat,-1],'exclude_any_flat_post_bar',asset,typ,label))
            # Influence: show the complete leave-one-event-out distribution.
            for i,eid in enumerate(m.index):
                keep=np.arange(len(m))!=i
                beta=float(np.linalg.lstsq(x[keep],y[keep,-1],rcond=None)[0][1])
                checks.append({'phase':label,'event_type':typ,'asset':asset,'measure':'leave_one_out','event_omitted':eid,'n':len(m)-1,'estimate':beta,'full_estimate':float(f['coef'][1,-1]),'units':'bp per development surprise SD'})
            if m.date.str[:4].nunique()>=3:
                intervals,valid=year_block_intervals(x,y,m.date.str[:4].to_numpy())
                checks.append({'phase':label,'event_type':typ,'asset':asset,'measure':'year_block_20_sensitivity','n':len(m),'estimate':float(f['coef'][1,-1]),'ci_low':float(intervals[0,-1]),'ci_high':float(intervals[1,-1]),'valid_bootstrap':valid,'year_blocks':m.date.str[:4].nunique(),'units':'bp per development surprise SD'})
    save_csv(pd.DataFrame(curve_rows),ROOT/f'outputs/tables/curves-{label}.csv')
    save_csv(pd.DataFrame(effects),ROOT/f'outputs/tables/effects-{label}.csv')
    save_csv(pd.DataFrame(checks),ROOT/f'outputs/tables/robustness-{label}.csv')
    save_csv(pd.DataFrame(rvrows),ROOT/f'outputs/tables/realised-variance-{label}.csv')
    write_json(ROOT/f'outputs/adjustment-{label}.json',shapes)
    return pd.DataFrame(effects)

def freeze_development():
    corrected=(ROOT/'protocol/amendment-02.json').exists()
    freeze_path=ROOT/('protocol/corrected-model-freeze.json' if corrected else 'protocol/holdout-release.json')
    if freeze_path.exists():raise RuntimeError('Model already frozen; preserve this freeze')
    bars,ev=data_for(['development']);models={}
    for typ in design()['event_types']:
        for asset in design()['assets']:
            x,y,m,p=panel(bars,ev,asset,typ)
            if len(m)<6:continue
            for start,end,name in [(0,20,'cumulative_20'),(5,20,'late_5_20'),(20,25,'post_observation_20_25')]:
                target=return_between(p,start,end);coef=np.linalg.lstsq(x,target,rcond=None)[0]
                models['|'.join([typ,asset,name])]={'coef':coef.tolist(),'baseline':float(target.mean()),'n':len(m),'training_ids':m.index.tolist()}
    path=ROOT/'outputs/models/development-predictions.json';write_json(path,models)
    files=list((ROOT/'diffusion').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[path,ROOT/'outputs/models/surprise-pca.json',ROOT/'protocol/design-v1.json',ROOT/'protocol/amendment-01.json']
    if corrected:
        analytical={'__init__.py','common.py','data.py','histdata.py','statistics.py','empirical.py','synthetic.py','acquire.py','acquire_histdata.py','run_empirical.py','run_synthetic.py'}
        files=[p for p in files if p.suffix!='.py' or p.name in analytical]
    if corrected:files.append(ROOT/'protocol/amendment-02.json')
    notice='Post-audit chronological transfer. Original held-out outcomes were examined before discovering the clock problem. Corrected development model frozen before recalculating corrected held-out outcomes; no untouched holdout, prospective blinding or external preregistration claimed.' if corrected else 'Internal chronological freeze in retrospective historical research; no external preregistration or prospective blinding claimed. The source USMPD workbook includes later dates. A 2025 ZIP was downloaded for availability but not parsed before this freeze.'
    write_json(freeze_path,{'released_utc':utcnow(),'notice':notice,'files':{str(p.relative_to(ROOT)):sha256(p) for p in sorted(files)}})
    return models

def evaluate_transfer(phase):
    models=json.loads((ROOT/'outputs/models/development-predictions.json').read_text());bars,ev=data_for([phase]);rows=[];pred=[]
    for key,model in models.items():
        typ,asset,name=key.split('|');a,b={'cumulative_20':(0,20),'late_5_20':(5,20),'post_observation_20_25':(20,25)}[name]
        x,y,m,p=panel(bars,ev,asset,typ)
        if len(m)<3:continue
        target=return_between(p,a,b);prediction=x@model['coef'];baseline=np.full(len(m),model['baseline'])
        summary=paired_mse_summary(target,prediction,baseline)
        summary.update(phase=phase,event_type=typ,asset=asset,target=name,information_set='retrospective surprise completed at +20' if a<20 else 'idealised +20 information availability; publication latency not modelled')
        rows.append(summary)
        for i,eid in enumerate(m.index):pred.append({'phase':phase,'event_type':typ,'asset':asset,'target':name,'event_id':eid,'actual':target[i],'prediction':prediction[i],'baseline':baseline[i]})
    save_csv(pd.DataFrame(rows),ROOT/f'outputs/tables/transfer-{phase}.csv');save_csv(pd.DataFrame(pred),ROOT/f'outputs/tables/predictions-{phase}.csv')
    return pd.DataFrame(rows)

def independent_window_check(phases,label):
    bars,ev=data_for(phases);rows=[]
    for typ in design()['event_types']:
        x,y,m,p=panel(bars,ev,'SPX',typ)
        # Close of minute -11 approximates boundary -10; close of minute +19 boundary +20.
        observed=return_between(p,-10,20)
        for i,eid in enumerate(m.index):
            for field in ['SP500','SPFUT']:
                value=m.iloc[i][field]
                if pd.notna(value):rows.append({'phase':label,'event_id':eid,'event_type':typ,'source_field':field,'histdata_log_return_bps':observed[i],'usmpd_return_bps':100*value})
    out=pd.DataFrame(rows);save_csv(out,ROOT/f'outputs/tables/window-crosscheck-{label}.csv');return out

def lead_lag(phases,label):
    """Descriptive pooled lag correlation and event-FE predictive associations."""
    bars,ev=data_for(phases);rows=[];tests=[]
    for typ in design()['event_types']:
        for source,target in [('SPX','NSX'),('NSX','SPX'),('SPX','EURUSD'),('EURUSD','SPX')]:
            _,_,m,p=panel(bars,ev,source,typ);_,_,mm,pp=panel(bars,ev,target,typ)
            ids=m.index.intersection(mm.index)
            if len(ids)<8:continue
            src=10000*np.diff(np.log(p.loc[ids,np.arange(-1,20)].to_numpy()),axis=1)
            dst=10000*np.diff(np.log(pp.loc[ids,np.arange(-1,20)].to_numpy()),axis=1)
            for lag in range(-5,6):
                aa=src[:,:20-lag] if lag>=0 else src[:,-lag:]
                bb=dst[:,lag:] if lag>=0 else dst[:,:20+lag]
                aa=aa-aa.mean(axis=1,keepdims=True);bb=bb-bb.mean(axis=1,keepdims=True)
                corr=float(np.corrcoef(aa.ravel(),bb.ravel())[0,1])
                rows.append({'phase':label,'event_type':typ,'source':source,'target':target,'lag_minutes':lag,'correlation':corr,'events':len(ids),'meaning':'positive lag: source precedes target; descriptive, no causal or arbitrage interpretation'})
            xs=[];ys=[];groups=[]
            for g in range(len(ids)):
                xx=np.column_stack([dst[g,3-j:20-j] for j in [1,2,3]]+[src[g,3-j:20-j] for j in [1,2,3]])
                yy=dst[g,3:20];xs.append(xx-xx.mean(axis=0));ys.append(yy-yy.mean());groups.extend([g]*len(yy))
            xx=np.vstack(xs);yy=np.concatenate(ys);groups=np.array(groups)
            if np.linalg.matrix_rank(xx)<6:continue
            inv=np.linalg.inv(xx.T@xx);coef=inv@xx.T@yy;resid=yy-xx@coef
            meat=np.zeros((6,6))
            for g in np.unique(groups):
                score=xx[groups==g].T@resid[groups==g];meat+=np.outer(score,score)
            n=len(yy);G=len(ids);cov=inv@meat@inv*(G/(G-1))*((n-1)/(n-6-G))
            c=coef[3:];v=cov[3:,3:];wald=float(c@np.linalg.pinv(v)@c/3)
            own=np.linalg.lstsq(xx[:,:3],yy,rcond=None)[0];sse0=np.sum((yy-xx[:,:3]@own)**2);sse=np.sum(resid**2)
            tests.append({'phase':label,'event_type':typ,'source':source,'target':target,'events':G,'minute_rows':n,'cross_lag_1':coef[3],'cross_lag_2':coef[4],'cross_lag_3':coef[5],'cluster_wald_F':wald,'p_value_exploratory':float(stats.f.sf(wald,3,G-1)),'incremental_R2':float(1-sse/sse0),'interpretation':'Own lags and event fixed effects; event-cluster CR1 covariance, few-cluster approximation, multiple exploratory tests.'})
    save_csv(pd.DataFrame(rows),ROOT/f'outputs/tables/lead-lag-correlations-{label}.csv');save_csv(pd.DataFrame(tests),ROOT/f'outputs/tables/lead-lag-tests-{label}.csv')
    return pd.DataFrame(tests)
