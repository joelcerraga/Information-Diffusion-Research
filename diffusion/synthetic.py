import numpy as np
import pandas as pd
from .statistics import ols_hc3,wild_band,fit_adjustment,response_function
from .common import ROOT,save_csv,write_json

CASES=['immediate','gradual','reversal','null','continuing','stale_quotes']

def truth(case,h):
    h=np.asarray(h,float)
    if case=='immediate':return np.full_like(h,-25.)
    if case=='gradual':return response_function(h,-25,.25,.22)
    if case=='reversal':return -10-30*np.exp(-(h-1)/4)
    if case=='null':return np.zeros_like(h)
    if case=='continuing':return -3-1.5*(h-1)
    if case=='stale_quotes':return np.where(h<=2,0.,-25.)
    raise ValueError(case)

def sample(case,n,seed):
    rng=np.random.default_rng(seed);h=np.arange(1,21);z=rng.normal(size=n)
    shocks=rng.standard_t(5,size=(n,20))*1.6*np.sqrt(3/5)*(1+.45*np.abs(z[:,None]))
    for j in range(1,20):shocks[:,j]+=.25*shocks[:,j-1]
    noise=np.cumsum(shocks,axis=1)
    y=z[:,None]*truth(case,h)[None,:]+noise
    return np.c_[np.ones(n),z],y

def run_synthetic(repetitions=200):
    rows=[];examples=[];coverage=[]
    for case in CASES:
        for n in [40,80]:
            estimates=[];errors=[];point=[];sim=[];reject=[]
            target=truth(case,np.arange(1,21));target_late=target[-1]-target[4]
            for rep in range(repetitions):
                x,y=sample(case,n,20261016+n*10000+rep)
                f=ols_hc3(x,y);b=wild_band(f,reps=199,seed=rep+123)
                estimates.append(f['coef'][1,-1]);errors.append((f['coef'][1,-1]-target[-1])**2)
                point.append(f['lo'][1,-1]<=target[-1]<=f['hi'][1,-1]);sim.append(np.all((b['lo']<=target)&(b['hi']>=target)))
                late=ols_hc3(x,y[:,-1]-y[:,4]);reject.append(late['lo'][1,0]*late['hi'][1,0]>0)
                coverage.append({'case':case,'n':n,'replication':rep,'terminal_estimate':estimates[-1],'terminal_covered':point[-1],'path_covered':sim[-1],'late_reject_zero':reject[-1]})
            p=float(np.mean(point));s=float(np.mean(sim));r=float(np.mean(reject))
            rows.append({'case':case,'n':n,'replications':repetitions,'true_terminal':target[-1],'bias':float(np.mean(estimates)-target[-1]),'rmse':float(np.sqrt(np.mean(errors))),'pointwise_coverage':p,'coverage_mcse':float(np.sqrt(p*(1-p)/repetitions)),'simultaneous_coverage':s,'simultaneous_mcse':float(np.sqrt(s*(1-s)/repetitions)),'true_late_slope':target_late,'late_rejection_rate':r,'late_rejection_mcse':float(np.sqrt(r*(1-r)/repetitions))})
        x,y=sample(case,80,20261016);f=ols_hc3(x,y);b=wild_band(f,reps=1999)
        for j,h in enumerate(range(1,21)):examples.append({'case':case,'horizon':h,'truth':truth(case,[h])[0],'estimated':f['coef'][1,j],'lo':b['lo'][j],'hi':b['hi'][j]})
        print('Synthetic complete:',case,flush=True)
    save_csv(pd.DataFrame(rows),ROOT/'outputs/tables/synthetic-validation.csv')
    save_csv(pd.DataFrame(coverage),ROOT/'outputs/tables/synthetic-replications.csv')
    save_csv(pd.DataFrame(examples),ROOT/'outputs/tables/synthetic-curves.csv')
    params=fit_adjustment(np.arange(1,21),truth('gradual',np.arange(1,21)))
    write_json(ROOT/'outputs/synthetic-recovery.json',params)
    return pd.DataFrame(rows)
