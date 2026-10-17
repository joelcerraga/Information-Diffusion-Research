"""Supplementary stress test prompted by realised sample sizes; not a retuning step."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from diffusion.synthetic import CASES,sample,truth
from diffusion.statistics import ols_hc3,wild_band
from diffusion.common import ROOT,save_csv
rows=[];raw=[];M=200
for n in [16,30]:
    for case in CASES:
        true=truth(case,np.arange(1,21));point=[];joint=[];reject=[];est=[]
        for rep in range(M):
            x,y=sample(case,n,20261016+n*10000+rep);f=ols_hc3(x,y);band=wild_band(f,reps=199,seed=rep+123);late=ols_hc3(x,y[:,-1]-y[:,4]);est.append(f['coef'][1,-1]);point.append(f['lo'][1,-1]<=true[-1]<=f['hi'][1,-1]);joint.append(np.all((band['lo']<=true)&(band['hi']>=true)));reject.append(late['lo'][1,0]*late['hi'][1,0]>0)
            raw.append({'case':case,'n':n,'replication':rep,'terminal_estimate':est[-1],'terminal_covered':point[-1],'path_covered':joint[-1],'late_reject_zero':reject[-1]})
        p=float(np.mean(point));s=float(np.mean(joint));r=float(np.mean(reject));rows.append({'case':case,'n':n,'replications':M,'true_terminal':true[-1],'bias':float(np.mean(est)-true[-1]),'rmse':float(np.sqrt(np.mean((np.array(est)-true[-1])**2))),'pointwise_coverage':p,'coverage_mcse':np.sqrt(p*(1-p)/M),'simultaneous_coverage':s,'simultaneous_mcse':np.sqrt(s*(1-s)/M),'true_late_slope':true[-1]-true[4],'late_rejection_rate':r,'late_rejection_mcse':np.sqrt(r*(1-r)/M),'stage':'supplementary sample-size stress after coverage audit'})
        print(n,case,p,s,r,flush=True)
save_csv(pd.DataFrame(rows),ROOT/'outputs/tables/synthetic-small-sample.csv');save_csv(pd.DataFrame(raw),ROOT/'outputs/tables/synthetic-small-sample-replications.csv')
