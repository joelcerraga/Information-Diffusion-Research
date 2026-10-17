"""Review tables, publication-sized scientific figures and explorer data."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import ROOT,design,sha256,write_json,save_csv
from .empirical import data_for,panel,return_between

PHASES=['development','validation','holdout']
COLORS={'SPX':'#164B65','NSX':'#14867B','EURUSD':'#C86542'}

def table(name):
    p=ROOT/'outputs/tables'/name
    # 'null' is a named simulation mechanism, not a missing category.
    try:return pd.read_csv(p,keep_default_na=False,na_values=['','NaN','nan'])
    except pd.errors.EmptyDataError:return pd.DataFrame()

def audit_summaries():
    ev=pd.read_csv(ROOT/'data/processed/events-with-surprise.csv');aud=pd.concat([pd.read_csv(ROOT/f'data/processed/audit-{p}.csv') for p in PHASES])
    rows=[];missing=[]
    for (phase,typ,asset),g in aud.groupby(['phase','event_type','asset']):
        n=int(g.event_accepted.sum());total=len(g);minimum={'development':25,'validation':6,'holdout':10}[phase]
        rows.append({'phase':phase,'event_type':typ,'asset':asset,'planned':total,'accepted':n,'excluded':total-n,'matched':int(g.control_accepted.sum()),'coverage':n/total,'minimum_n':minimum,'coverage_gate':n/total>=.8,'sample_gate':n>=minimum and n/total>=.8,'unique_control_days':g.control_date.nunique()})
        gg=g.merge(ev[['event_id','surprise']],on='event_id')
        for accepted in [True,False]:
            z=gg[gg.event_accepted==accepted]
            if len(z):missing.append({'phase':phase,'event_type':typ,'asset':asset,'accepted':accepted,'n':len(z),'mean_absolute_surprise':z.surprise.abs().mean()})
    save_csv(pd.DataFrame(rows),ROOT/'outputs/tables/coverage.csv');save_csv(pd.DataFrame(missing),ROOT/'outputs/tables/missingness-surprise.csv')
    save_csv(aud,ROOT/'outputs/tables/all-exclusions-and-controls.csv')
    cross=table('window-crosscheck-pooled.csv');cr=[]
    for (typ,field),g in cross.groupby(['event_type','source_field']):
        delta=g.histdata_log_return_bps-g.usmpd_return_bps
        cr.append({'event_type':typ,'source_field':field,'n':len(g),'correlation':g.histdata_log_return_bps.corr(g.usmpd_return_bps),'mean_difference_bps':delta.mean(),'median_absolute_difference_bps':delta.abs().median(),'rmse_difference_bps':np.sqrt(np.mean(delta**2))})
    save_csv(pd.DataFrame(cr),ROOT/'outputs/tables/window-crosscheck-summary.csv')
    rv=table('realised-variance-pooled.csv');rr=[]
    rng=np.random.default_rng(20261022)
    for (typ,asset),g in rv.groupby(['event_type','asset']):
        valid=g[(g.event_rv>0)&(g.control_rv>0)];lr=np.log(valid.event_rv.to_numpy()/valid.control_rv.to_numpy())
        ix=rng.integers(0,len(lr),size=(1999,len(lr)));ci=np.exp(np.quantile(np.median(lr[ix],axis=1),[.025,.975]))
        rr.append({'event_type':typ,'asset':asset,'n':len(lr),'median_rv_ratio':np.exp(np.median(lr)),'ci_low':ci[0],'ci_high':ci[1],'method':'event-pair percentile bootstrap of median log RV ratio; matched dates are observational controls'})
    save_csv(pd.DataFrame(rr),ROOT/'outputs/tables/realised-variance-summary.csv')
    freeze_path=ROOT/'protocol/corrected-model-freeze.json'
    if not freeze_path.exists():freeze_path=ROOT/'protocol/holdout-release.json'
    freeze=json.loads(freeze_path.read_text());changed=[p for p,h in freeze['files'].items() if sha256(ROOT/p)!=h]
    write_json(ROOT/'outputs/validation/freeze-check.json',{'all_frozen_files_unchanged':not changed,'changed_files':changed,'frozen_file_count':len(freeze['files'])})
    coverage=pd.DataFrame(rows)
    manifest_path=ROOT/'data/raw-manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else [{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size} for p in (ROOT/'data/raw').rglob('*') if p.is_file()]
    summary={'scheduled_statement_events':int((ev.event_type=='Statements').sum()),'minutes_events':int((ev.event_type=='Minutes').sum()),'accepted_event_asset_pairs':int(aud.event_accepted.sum()),'planned_event_asset_pairs':len(aud),'primary_pooled_statements':int(aud[(aud.asset=='SPX')&(aud.event_type=='Statements')].event_accepted.sum()),'source_archives':sum(x['path'].startswith('data/raw/histdata/') and x['path'].endswith('.zip') for x in manifest),'archived_source_bytes':sum(x['bytes'] for x in manifest),'primary_stage_gates':json.loads(coverage[(coverage.asset=='SPX')&(coverage.event_type=='Statements')].to_json(orient='records')),'frozen_model_unchanged':not changed}
    write_json(ROOT/'outputs/research-summary.json',summary)
    return summary

def figures():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#82919A','axes.labelcolor':'#263C49','xtick.color':'#415663','ytick.color':'#415663','grid.alpha':.2,'savefig.facecolor':'white','figure.facecolor':'white'})
    out=ROOT/'outputs/figures';out.mkdir(parents=True,exist_ok=True);register=[]
    def save(fig,num,title,caption):
        name=f'figure-{num:02d}';fig.savefig(out/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(out/(name+'.svg'),bbox_inches='tight');plt.close(fig)
        register.append({'number':num,'title':title,'caption':f'Figure {num}. {caption}','png':'outputs/figures/'+name+'.png','svg':'outputs/figures/'+name+'.svg'})
    d=table('synthetic-curves.csv');fig,axs=plt.subplots(3,2,figsize=(6.4,7.2),layout='constrained')
    for ax,(case,g) in zip(axs.flat,d.groupby('case',sort=False)):
        ax.fill_between(g.horizon,g.lo,g.hi,color='#D5E6EA');ax.plot(g.horizon,g.estimated,color=COLORS['SPX'],label='Estimated');ax.plot(g.horizon,g.truth,color=COLORS['EURUSD'],ls='--',label='Known truth');ax.axhline(0,color='#80909A',lw=.6);ax.set(title=case.replace('_',' ').capitalize(),xlabel='Minutes after release',ylabel='Response (bp / shock SD)');ax.grid()
    axs[0,0].legend(fontsize=8)
    save(fig,1,'Synthetic response paths','Six known mechanisms and their estimated responses. Shading is an event wild-bootstrap simultaneous band across 20 horizons; these are simulated data.')
    c=table('coverage.csv');fig,ax=plt.subplots(figsize=(6.4,4.3),layout='constrained');labels=[t+' / '+a for t in ['Statements','Minutes'] for a in ['SPX','NSX','EURUSD']];arr=np.zeros((6,3));texts={}
    for i,l in enumerate(labels):
        t,a=l.split(' / ')
        for j,p in enumerate(PHASES):
            r=c[(c.event_type==t)&(c.asset==a)&(c.phase==p)].iloc[0];arr[i,j]=r.coverage;texts[i,j]=f'{int(r.accepted)}/{int(r.planned)}'
    ax.imshow(arr,cmap='Blues',vmin=0,vmax=1,aspect='auto');ax.set_xticks(range(3),['2018–22\nDevelopment','2023\nValidation','2024–25\nLater period']);ax.set_yticks(range(6),labels)
    for (i,j),txt in texts.items():ax.text(j,i,txt,ha='center',va='center',color='white' if arr[i,j]>.7 else '#163B4D',fontsize=10)
    save(fig,2,'Coverage audit','Accepted event windows divided by planned events. Every required minute from −61 to +25 must be present and valid; missing bars are never filled.')
    fig,axs=plt.subplots(3,1,figsize=(6.4,7.2),sharex=True,layout='constrained')
    for ax,phase in zip(axs,['development','holdout','pooled']):
        g=table('curves-'+phase+'.csv').query("asset == 'SPX' and event_type == 'Statements'")
        ax.fill_between(g.horizon,g.sim_low,g.sim_high,color='#DCE8EF',label='95% simultaneous');ax.fill_between(g.horizon,g.point_low,g.point_high,color='#AECBD7',label='95% pointwise');ax.plot(g.horizon,g.beta,color=COLORS['SPX'],lw=1.8);ax.axhline(0,c='#81909A',lw=.7);ax.set(title=f"{('Later period — post-audit' if phase=='holdout' else phase.capitalize())} · n = {g.n.iloc[0]}",ylabel='Response (bp / surprise SD)');ax.grid()
    axs[0].legend(fontsize=8,ncol=2);axs[-1].set_xlabel('Minutes after statement')
    save(fig,3,'Primary response across samples','SPX provider-quote response to the frozen rate-surprise factor after clock correction. Pooled estimates are retrospective. Chronological transfer follows a documented source-clock repair after the original holdout had been examined; sample eligibility is reported separately.')
    d=table('curves-pooled.csv');fig,axs=plt.subplots(3,2,figsize=(6.4,7.2),sharex=True,layout='constrained')
    for i,asset in enumerate(['SPX','NSX','EURUSD']):
        for j,typ in enumerate(['Statements','Minutes']):
            ax=axs[i,j];g=d[(d.asset==asset)&(d.event_type==typ)];ax.fill_between(g.horizon,g.point_low,g.point_high,color=COLORS[asset],alpha=.18);ax.plot(g.horizon,g.beta,color=COLORS[asset]);ax.axhline(0,c='#81909A',lw=.7);ax.set(title=f'{asset} · {typ} · n={g.n.iloc[0]}',ylabel='bp / surprise SD');ax.grid()
    for ax in axs[-1]:ax.set_xlabel('Minutes after release')
    save(fig,4,'Assets and communication types','Pooled response curves with pointwise HC3 intervals. Panels have independent vertical scales. Asset and event-type comparisons are exploratory; the factor remains scaled to development statements.')
    d=table('effects-pooled.csv').query("measure == 'late_5_20'");fig,ax=plt.subplots(figsize=(6.4,4),layout='constrained')
    for i,(_,r) in enumerate(d.iterrows()):ax.errorbar(r.estimate,i,xerr=[[r.estimate-r.ci_low],[r.ci_high-r.estimate]],fmt='o',color=COLORS[r.asset],capsize=3)
    ax.set_yticks(range(len(d)),d.event_type+' / '+d.asset);ax.axvline(0,c='#81909A',lw=.8);ax.set_xlabel('Additional response from minute 5 to 20 (bp / surprise SD)');ax.grid(axis='x');ax.invert_yaxis()
    save(fig,5,'Lagged response estimates','The additional 5-to-20-minute response and its 95% HC3 interval. An interval containing zero does not establish that adjustment is complete.')
    d=table('window-crosscheck-pooled.csv').query("event_type == 'Statements'");fig,axs=plt.subplots(2,1,figsize=(6.4,6.8),layout='constrained')
    for ax,field in zip(axs,['SP500','SPFUT']):
        g=d[d.source_field==field];ax.scatter(g.usmpd_return_bps,g.histdata_log_return_bps,color=COLORS['SPX'],s=20,alpha=.75);lim=np.max(np.abs(g[['usmpd_return_bps','histdata_log_return_bps']].to_numpy()))*1.1;ax.plot([-lim,lim],[-lim,lim],ls='--',c='#B27758',lw=1);ax.set(title=f'{field} · correlation {g.usmpd_return_bps.corr(g.histdata_log_return_bps):.3f}',xlabel='Published USMPD window return (bp)',ylabel='HistData window log return (bp)');ax.grid()
    save(fig,6,'External window cross-check','The same nominal −10-to-+20-minute window compared with USMPD stock-index and futures returns. Agreement supports alignment; different instruments, quote conventions and boundary sampling prevent treating it as minute-level ground truth.')
    d=table('realised-variance-summary.csv');fig,ax=plt.subplots(figsize=(6.4,4),layout='constrained')
    for i,(_,r) in enumerate(d.iterrows()):ax.errorbar(r.median_rv_ratio,i,xerr=[[r.median_rv_ratio-r.ci_low],[r.ci_high-r.median_rv_ratio]],fmt='o',color=COLORS[r.asset],capsize=3)
    ax.set_xscale('log');ax.axvline(1,c='#81909A',lw=.7);ax.set_yticks(range(len(d)),d.event_type+' / '+d.asset);ax.invert_yaxis();ax.set_xlabel('Median event / matched-day realised variance ratio');ax.grid(axis='x')
    save(fig,7,'Event activity and matched days','First-20-minute realised variance relative to the matched weekday. Intervals are event-pair bootstrap intervals; a variance increase measures activity rather than the fraction of information absorbed.')
    d=table('transfer-holdout.csv').query("asset == 'SPX' and event_type == 'Statements'");fig,ax=plt.subplots(figsize=(6.4,3.2),layout='constrained')
    names={'cumulative_20':'0–20 min\nRetrospective','late_5_20':'5–20 min\nRetrospective','post_observation_20_25':'20–25 min\nIdealised available surprise'}
    for i,(_,r) in enumerate(d.iterrows()):ax.errorbar(r.difference,i,xerr=[[r.difference-r.difference_ci_low],[r.difference_ci_high-r.difference]],fmt='o',color=COLORS['SPX'],capsize=3)
    ax.set_yticks(range(len(d)),[names[t] for t in d.target]);ax.axvline(0,c='#81909A',lw=.8);ax.set_xlabel('Model MSE − baseline MSE (squared bp)');ax.invert_yaxis();ax.grid(axis='x')
    save(fig,8,'Chronological prediction check','Frozen corrected-development predictions on later statements. Negative differences favour the surprise model. This post-audit transfer follows the A02 clock repair, not an untouched holdout; within-window inputs are retrospective and +20-minute publication latency is not modelled.')
    d=table('lead-lag-correlations-pooled.csv');fig,axs=plt.subplots(2,1,figsize=(6.4,5.7),sharex=True,layout='constrained')
    for ax,typ in zip(axs,['Statements','Minutes']):
        for target in ['NSX','EURUSD']:
            g=d[(d.event_type==typ)&(d.source=='SPX')&(d.target==target)];ax.plot(g.lag_minutes,g.correlation,marker='o',markersize=3,color=COLORS[target],label=f'SPX → {target}')
        ax.axvline(0,c='#81909A',lw=.7);ax.axhline(0,c='#81909A',lw=.7);ax.set(title=typ,ylabel='Within-event correlation');ax.grid();ax.legend(fontsize=8)
    axs[-1].set_xlabel('Lag (minutes); positive means SPX precedes the other quote')
    save(fig,9,'Lead–lag diagnostics','Pooled within-event minute-return correlations. A peak at zero is common co-movement; a nonzero-lag peak can also reflect quote timing or shared news and does not establish causation.')
    d=table('robustness-pooled.csv').query("asset == 'SPX' and event_type == 'Statements' and measure == 'leave_one_out'").copy();d['date']=pd.to_datetime(d.event_omitted.str[-10:]);fig,ax=plt.subplots(figsize=(6.4,3.8),layout='constrained');ax.scatter(d.date,d.estimate,color=COLORS['SPX'],s=18);ax.axhline(d.full_estimate.iloc[0],ls='--',c=COLORS['EURUSD'],label='All accepted events');ax.set(xlabel='Omitted statement date',ylabel='20-minute slope (bp / surprise SD)');ax.grid();ax.legend(fontsize=8)
    save(fig,10,'Influence of individual events','The pooled SPX 20-minute slope after omitting each accepted statement in turn. This evaluates event influence without removing inconvenient observations from the main estimate.')
    bars,ev=data_for(PHASES);b=bars.query("asset == 'SPX' and kind == 'event' and event_id == 'statements_2024-01-31'").set_index('offset');x=np.arange(-30,120);y=10000*np.log(b.loc[x,'close']/b.loc[-1,'close']);fig,ax=plt.subplots(figsize=(6.4,3.8),layout='constrained');ax.plot(x+1,y,color=COLORS['SPX']);ax.axvspan(0,20,color='#D9E8ED',label='Primary response window');ax.axvline(0,c='#263C49',lw=1);ax.axvline(30,c=COLORS['EURUSD'],ls='--',label='Press conference begins');ax.axhline(0,c='#81909A',lw=.6);ax.set(title='31 January 2024 · first later-period statement',xlabel='Minutes after statement (bar-close boundary)',ylabel='Cumulative bid log return (bp)');ax.grid();ax.legend(fontsize=8)
    save(fig,11,'Sequential information releases','The first later-period statement, selected by date. The subsequent press conference introduces additional information; movements after that release cannot be attributed solely to delayed incorporation of the statement.')
    d=table('independent-clock-check.csv');t=pd.to_datetime(d.utc);reference=10000*np.diff(np.log(d.dukascopy_spy_bid));wrong=10000*np.diff(np.log(d.histdata_spx_bid_documented_time));corrected=10000*np.diff(np.log(d.histdata_spx_bid_shifted_60m));fig,axs=plt.subplots(2,1,figsize=(6.4,5.7),sharex=True,layout='constrained')
    for ax,values,title in [(axs[0],wrong,'Documented fixed-EST interpretation'),(axs[1],corrected,'Audited seasonal clock correction')]:
        ax.plot(np.arange(len(reference)),reference,c=COLORS['SPX'],lw=1,label='Independent SPY quote route');ax.plot(np.arange(len(values)),values,c=COLORS['EURUSD'],lw=.8,alpha=.8,label='HistData SPX quote');ax.set(title=title,ylabel='One-minute return (bp)');ax.grid()
    axs[0].legend(fontsize=7);axs[-1].set_xlabel('Minutes since 17:30 UTC, 21 September 2022')
    save(fig,12,'Clock-audit evidence','Independent download routes show that the documented clock misaligns the two series. Correcting the seasonal offset raises their minute-return correlation from −0.004 to 0.9995 on this probe. This checks timing rather than proving source independence or universal data quality.')
    write_json(ROOT/'outputs/figure-register.json',register)
    return register

def explorer_data():
    curves=pd.concat([table('curves-'+p+'.csv') for p in ['development','holdout','pooled']])
    bars,ev=data_for(PHASES);paths=[]
    for (eid,asset),g in bars[bars.kind=='event'].groupby(['event_id','asset']):
        g=g.set_index('offset');base=g.loc[-1,'close'];offsets=np.arange(-30,120);y=10000*np.log(g.reindex(offsets).close/base)
        paths.append({'id':eid,'asset':asset,'type':ev.loc[eid,'event_type'],'phase':ev.loc[eid,'phase'],'date':ev.loc[eid,'date'],'surprise':float(ev.loc[eid,'surprise']),'t':(offsets+1).tolist(),'returns':json.loads(y.to_json(orient='values'))})
    data={'curves':json.loads(curves.to_json(orient='records')),'paths':paths,'coverage':json.loads(table('coverage.csv').to_json(orient='records')),'figures':json.loads((ROOT/'outputs/figure-register.json').read_text()),'price_label':'HistData provider bid quotes; one-minute bars; no consolidated-exchange or executable-price claim','surprise_label':'Frozen development PCA, one development standard deviation; surprise uses the full −10 to +20 minute window','status':'Research review before final paper compilation'}
    write_json(ROOT/'outputs/explorer-data.json',data);return data
