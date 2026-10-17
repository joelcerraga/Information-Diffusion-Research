"""Maintain paper-preparation registers without typesetting the paper."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from diffusion.common import ROOT,save_csv,write_json
from diffusion.reporting import table

out=ROOT/'paper/tables';out.mkdir(exist_ok=True)
register=[]
def add(number,title,frame,notes):
    name=f'table-{number:02d}.csv';save_csv(frame,out/name)
    register.append({'number':number,'title':title,'caption':f'Table {number}. {title}.','source':'paper/tables/'+name,'notes':notes,'caption_placement':'centred below'})

ev=pd.read_csv(ROOT/'data/processed/event-register.csv')
add(1,'Scheduled event sample',ev.groupby(['phase','event_type']).size().reset_index(name='events'),'Before quote exclusions. Internal holdout denotes the later post-audit period.')
c=table('coverage.csv')
add(2,'Complete-window data coverage',c[['phase','event_type','asset','accepted','planned','coverage','sample_gate']],'Every minute from −61 to +25 is required; no imputation.')
add(3,'Source-clock comparison probes',table('clock-probe-summary.csv'),'Offsets are source-lookup shifts relative to the initial documented-clock interpretation. The applied correction is a calendar rule, not per-event selection.')
p=json.loads((ROOT/'outputs/models/surprise-pca.json').read_text())
add(4,'Development rate-factor construction',pd.DataFrame({'input':p['inputs'],'loading':p['loadings'],'centre_bp':p['centre_bps']}),'Covariance PCA, 39 development statements; explained variance 0.9149345 and score SD 8.009662 bp.')
s=pd.concat([table('synthetic-validation.csv'),table('synthetic-small-sample.csv')])
add(5,'Simulation interval coverage',s[['case','n','replications','pointwise_coverage','coverage_mcse','simultaneous_coverage','simultaneous_mcse']],'200 replications per case/size; paired noise across cases. N=16/30 supplementary after coverage audit.')
add(6,'Simulation late-response rejection',s[['case','n','true_late_slope','late_rejection_rate','late_rejection_mcse']],'Rejection is power when the true late slope is nonzero and false-positive frequency when it is zero.')
effects=pd.concat([table(f'effects-{p}.csv') for p in ['development','holdout','pooled']])
e=effects.query("asset=='SPX' and measure in ['cumulative_20','late_5_20']")
add(7,'Primary response and lag estimates',e[['phase','event_type','measure','n','estimate','ci_low','ci_high']],'bp per development surprise SD; pointwise 95% HC3 intervals. Later period is post-audit transfer.')
add(8,'Matched-day realised variance comparison',table('realised-variance-summary.csv')[['event_type','asset','n','median_rv_ratio','ci_low','ci_high']],'Median ratio of first-20-minute event variance to matched-day variance, with event-pair bootstrap intervals.')
ll=table('lead-lag-tests-pooled.csv')
add(9,'Exploratory cross-series lag diagnostics',ll[['event_type','source','target','events','incremental_R2','p_value_exploratory']],'Own three lags and event fixed effects. Short-panel bias, approximate clustered inference and unadjusted multiplicity preclude a confirmatory interpretation.')
tr=table('transfer-holdout.csv').query("asset=='SPX' and event_type=='Statements'")
add(10,'Post-audit chronological prediction losses',tr[['target','n','model_mse','baseline_mse','difference','difference_ci_low','difference_ci_high']],'Squared bp. Negative differences favour the model. Within-window targets are retrospective; +20-to-+25 availability is idealised.')
g=[]
for phase in ['development','holdout','pooled']:
    for typ,d in json.loads((ROOT/f'outputs/adjustment-{phase}.json').read_text()).items():
        g.append({'phase':phase,'event_type':typ,'bootstrap_valid_fraction':d['gates']['bootstrap_valid_fraction'],'sample_adequate':d['sample']['adequate'],'reportable_t90_minutes':d['reportable_t90_minutes'],'reportable':d['reportable'],'failed_rules':'; '.join([k for k in ['terminal_ci_excludes_zero','late_response_equivalence_heuristic','shape_fit','interior_parameters','bootstrap_gate'] if not d['gates'][k]]+([] if d['sample']['adequate'] else ['sample_coverage']))})
add(11,'Conditional speed reporting decisions',pd.DataFrame(g),'A missing reportable t90 is an identification result; raw optimiser candidates are diagnostics only. Split the failed-rule text into a note panel in A4 typesetting.')
r=table('robustness-pooled.csv').query("asset=='SPX' and event_type=='Statements' and measure!='leave_one_out'")
add(12,'Primary robustness and placebo checks',r[['measure','n','estimate','ci_low','ci_high']],'bp per development surprise SD. Year-block intervals are sensitivity checks with few year blocks, not assured nominal inference.')
write_json(ROOT/'paper/table-register.json',register)
save_csv(pd.DataFrame(register)[['number','title','source']],ROOT/'paper/list-of-tables.csv')
f=json.loads((ROOT/'outputs/figure-register.json').read_text())
save_csv(pd.DataFrame(f)[['number','title','png','svg']],ROOT/'paper/list-of-figures.csv')
listings=[
    (1,'Source-clock mapping and complete-window construction','diffusion/histdata.py'),
    (2,'HC3 and event-path wild-bootstrap inference','diffusion/statistics.py'),
    (3,'Synthetic known-mechanism validation','diffusion/synthetic.py'),
    (4,'Horizon, lag and chronological estimators','diffusion/empirical.py'),
    (5,'Executed notebook construction','scripts/build_notebooks.py'),
    (6,'Interactive response, path and diffusion views','explorers/template.html')]
save_csv(pd.DataFrame(listings,columns=['number','listing','source']),ROOT/'paper/list-of-code-listings.csv')
execution=json.loads((ROOT/'outputs/validation/notebook-execution.json').read_text())
names=['Research design','Public-data and clock audit','Synthetic validation','Event-response estimation','Lead–lag analysis','Chronological transfer','Robustness and reflections','Research handover']
milestones=[{'id':f'M{i+1}','title':names[i],'notebook':item['notebook'],'status':'complete','executed_code_cells':item['code_cells']} for i,item in enumerate(execution['notebooks'])]
write_json(ROOT/'research/milestones.json',milestones)
print('Tables',len(register),'figures',len(f),'code listings',len(listings),'milestones',len(milestones))
