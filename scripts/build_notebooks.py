"""Generate teaching notebooks and execute every code cell without hidden state.

The notebooks are ordinary nbformat-4 files. This dependency-light runner uses
Python exec, captures stdout and display MIME bundles, and fails on any cell
error. They can also be opened and rerun in Jupyter with the same source cells.
"""
import contextlib
import datetime
import hashlib
import io
import json
import platform
import sys
import time
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diffusion.common import ROOT, write_json
from diffusion import presentation

SETUP = '''from pathlib import Path
import sys, json
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'diffusion/common.py').exists())
if str(root) not in sys.path: sys.path.insert(0, str(root))
import numpy as np
import pandas as pd
from diffusion.common import ROOT, design, sha256
from diffusion.reporting import table
from diffusion.presentation import show_table, show_json, show_figure, show_plot, equation
pd.set_option('display.max_columns', 12)
print('Project:', ROOT.name)
print('Clock: A02 audited seasonal mapping. Later sample: post-audit chronological transfer.')
'''

def md(text): return ('markdown', text.strip())
def code(text): return ('code', text.strip())

BOOKS = [
('00_research_question_and_design', [
md('''# 00 · Research question and design

**Question:** how does the association between a scheduled information release and quoted prices evolve over the following minutes? The project separates an observable response curve, a conditional adjustment model and a predictive lead–lag diagnostic. None alone observes the instant when every investor has absorbed every part of a release.

This is an executed research record before paper assembly. The empirical study uses free public data, 2018–2025 FOMC statements as its primary setting, minutes as an extension, and SPX, NSX and EURUSD provider bid quotes. Earnings calls remain a future extension: a call contains multiple release times and needs reliable free historical timestamps, expectations and corporate-action-aware prices.

As Fama (1991) explains in *Efficient capital markets: II*, empirical efficiency tests depend on the return model used to evaluate prices. As MacKinlay (1997) explains in *Event studies in economics and finance*, a credible event study begins with a precise event and window definition. These points motivate narrow windows, explicit information sets and restrained interpretation.'''),
code(SETUP),
md('''## Design that survives the audit

The original design is immutable. Amendment A01 changed the data route after slow daily-file acquisition; A02 repaired a documented clock mismatch. The original held-out run had already been viewed. Corrected 2024–2025 results are therefore **post-audit chronological transfer**, never an untouched holdout. The internal filename `holdout` is retained for traceability.

The primary quote series remains SPX even though other series have better historical coverage. Missing windows are excluded as whole event–asset pairs; no missing return is imputed. The 2023 sample is retained in the audit but is too small for the declared response regressions.'''),
code('''d = design()
keys = ['primary_asset','primary_event_type','assets','surprise_inputs','sample_gates']
show_json({k:d[k] for k in keys})
events = pd.read_csv(ROOT/'data/processed/event-register.csv')
counts = events.groupby(['phase','event_type']).size().reset_index(name='planned_events')
show_table(counts, 'Table N00.1. Scheduled releases before quote-coverage exclusions.')
assert len(events) == 128
assert ((events.phase=='development') & (events.event_type=='Statements')).sum() == 39
print('Event register verified: 63 statements and 65 minutes releases.')'''),
md('''## Three clocks and three questions

Calendar time identifies the public release; event time counts completed minute bars; the information clock records when a regressor becomes observable. The USMPD rate surprise is measured from −10 to +20 minutes. It cannot be used as a release-time predictor. Within-window fits are retrospective associations. The separate +20-to-+25 exercise grants idealised immediate availability at +20, without a publication-latency model.

As Gürkaynak, Sack and Swanson (2005) demonstrate, policy actions and statements can contain distinct target and path information. A single principal component is a compact descriptor, not their two-factor structural decomposition. As Jarociński and Karadi (2020) explain, announcements may also reveal information about economic conditions; a rate-price covariance does not isolate a pure policy shock.'''),
code('''timeline = pd.DataFrame([
    ['−61 to −1','Required pre-event bars','Quality checks and pre-event controls'],
    ['0','Scheduled statement or minutes release','Event-time origin'],
    ['1 to 20','Completed minute horizons','Primary retrospective response curve'],
    ['−10 to +20','USMPD surprise measurement','Full factor unavailable at release'],
    ['20 to 25','Post-observation exercise','Idealised +20 availability only'],
    ['+30, where applicable','Press conference begins','New information; extended plots are descriptive']
], columns=['time / minutes','observation','interpretation'])
show_table(timeline, 'Table N00.2. Release time, price observation and factor availability.')
equation(2)
equation(5)
equation(7)'''),
md('''## What would count as a speed estimate?

A visible return and a statistically nonzero response are not enough. A conditional speed is reported only if the terminal response is distinguishable from zero, the curve plausibly reaches a plateau, the monotone fit is adequate and interior, bootstrap fits are stable, and sample coverage passes. The plateau margin is estimated from the data; it is a reporting heuristic rather than a calibrated equivalence test. Failure to reject a late response is not evidence of complete adjustment.

As Hong, Lim and Stein (2000) motivate in their study of slow news diffusion, information can propagate unevenly across investors. Their longer-horizon equity evidence motivates a question here; it does not establish a minute-scale FOMC mechanism.'''),
code('''equation(8)
equation(9)
equation(10)
equation(18)
refs = json.loads((ROOT/'references/references.json').read_text())
print('Verified bibliography entries:', len(refs))
print('Full Harvard bibliography: references/harvard-references.txt')
print('Source relevance and verification notes: references/source-register.csv')'''),
md('''## Milestone outcome

The design, estimands, information sets and reporting rules are explicit. The exercise can measure conditional price-response paths and test for lagged associations. It cannot establish universal market efficiency, a causal structural shock, executable profit, or the exact sub-minute time when all information is priced.''')]),

('01_public_data_and_clock_audit', [
md('''# 01 · Public data and the clock audit

This notebook follows the data from free sources to an auditable event panel. The USMPD workbook supplies event times, rate changes and independent published window returns. HistData annual ASCII M1 files supply bid OHLC quotes. As Acosta et al. (2026) describe in their event-study database paper, separating communication types and measurement windows matters for interpreting FOMC responses.

Provider SPX and NSX are index-linked quote series, not consolidated exchange prices or tradable ETF midpoint records. EURUSD is a provider FX quote. As Hasbrouck (2007) explains in *Empirical market microstructure*, observed quote and trade processes require careful distinction when measuring price discovery.'''),
code(SETUP),
code('''summary = json.loads((ROOT/'outputs/research-summary.json').read_text())
show_json({k:summary[k] for k in ['scheduled_statement_events','minutes_events','accepted_event_asset_pairs','planned_event_asset_pairs','source_archives','archived_source_bytes']})
coverage = table('coverage.csv')
show_table(coverage[['phase','event_type','asset','accepted','planned','coverage','sample_gate']], 'Table N01.1. Complete-window coverage and sample eligibility.')
assert coverage.accepted.sum() == 336
assert coverage.planned.sum() == 384
show_figure(2)'''),
md('''## Why the documented time zone failed

HistData's specification describes fixed Eastern Standard Time. The archived quotes did not follow that interpretation in summer. An external window comparison triggered a minute-by-minute audit against a separate Dukascopy route. In September 2022, SPX/SPY minute-return correlation rose from −0.0037 to 0.9995 after looking up source observations one hour later. March 2022, when the US and Europe were on different seasonal clocks, distinguished their daylight-saving calendars.

As Kebe and Uhl (2024) report in *High-frequency effects of novel news on the EURUSD exchange rate*, HistData daylight adjustments can contradict its documentation. Their observation corroborates the mismatch. The specific European calendar mapping used here is our inference from the probes, not a rule established by that article. Some routes may share underlying quotes; route agreement is not proof of independent price formation.'''),
code('''probes = table('clock-probe-summary.csv')
show_table(probes, 'Table N01.2. Independently downloaded minute-quote clock probes.', decimals=6)
equation(19)
from diffusion.histdata import source_clock_to_utc
source = pd.Series(pd.to_datetime(['2022-03-16 09:00','2022-09-21 10:00','2022-11-02 10:00']))
mapped = source_clock_to_utc(source)
show_table(pd.DataFrame({'source_stamp':source.astype(str),'audited_utc':mapped.astype(str)}), 'Table N01.3. Deterministic source-to-UTC conversion examples.')
show_figure(12)'''),
md('''## What was corrected, and what remains uncertain

A02 applies one calendar rule to all three series and to events and matched controls. No event-specific offset is selected to improve a return result. The entire earlier run is retained in `archive/documented-clock-run/`. Corrected development models were frozen before corrected later predictions were recalculated, but the earlier outcome inspection means the later sample is no longer untouched.

All required bars from −61 through +25 must exist and satisfy quote checks. Extended plots preserve gaps rather than filling them. The three accepted 2023 statement observations are insufficient for the declared regression threshold of six. Better timestamp alignment does not repair absent bars or make missingness random.'''),
code('''audit = table('all-exclusions-and-controls.csv')
excluded = audit[~audit.event_accepted]
show_table(excluded.head(12), 'Table N01.4. First 12 exclusions; the full exclusion register is retained.')
show_table(table('missingness-surprise.csv'), 'Table N01.5. Surprise magnitude by coverage status; descriptive, not a missing-at-random test.')
cross = table('window-crosscheck-summary.csv')
show_table(cross, 'Table N01.6. Published-window agreement after A02.')
assert cross.query("event_type=='Statements' and source_field=='SP500'").correlation.iloc[0] > .99
show_figure(6)'''),
md('''## Reproduction and outcome

`scripts/acquire_histdata.py` retrieves free annual files through the ordinary public download form, caches exact bytes and records hashes. There are no credentials or paid keys. `scripts/audit_clocks.py` reproduces the selected minute probes. Raw files are packaged separately so notebook review does not require a 100 MB download or a live source connection.

The corrected 30-minute SPX/USMPD statement-window correlation is 0.9949. This is useful alignment evidence, not proof of every minute's correctness: USMPD contains different instruments and simple percentage returns, whereas these bars produce log returns. The primary development and pooled SPX samples still fail the 80% coverage rule.''')]),

('02_synthetic_validation', [
md('''# 02 · Synthetic validation and failure cases

Simulation asks whether the estimator behaves sensibly when the mechanism is known. Six cases separate immediate adjustment, gradual adjustment, reversal, no response, continuing drift and stale quotes. Noise consists of heteroskedastic Student-t increments with serial dependence within events.

As Morris, White and Crowther (2019) explain in their simulation-study tutorial, performance estimates need a defined data-generating mechanism and Monte Carlo uncertainty. A nominal 95% interval is not established by one visually convincing curve. The initial design uses 200 replications at each of N=40 and N=80; N=16 and N=30 were added transparently after the coverage audit, without selecting a new empirical specification.'''),
code(SETUP),
code('''from diffusion.synthetic import sample, truth, CASES
from diffusion.statistics import ols_hc3, wild_band, fit_adjustment
h = np.arange(1,21)
x,y = sample('gradual',80,20261016)
fit = ols_hc3(x,y)
band = wild_band(fit,reps=1999)
saved = table('synthetic-curves.csv').query("case=='gradual'")
np.testing.assert_allclose(fit['coef'][1], saved.estimated, rtol=1e-9)
np.testing.assert_allclose(band['lo'], saved.lo, rtol=1e-9)
print('Fresh 80-event fit and 1,999-draw simultaneous band reproduce the saved example.')
show_figure(1)'''),
code('''recovered = fit_adjustment(h,truth('gradual',h))
np.testing.assert_allclose([recovered['amplitude_bps'],recovered['first_minute_fraction'],recovered['k_per_minute']],[-25,.25,.22],rtol=1e-5)
show_json({k:v for k,v in recovered.items() if k!='predicted'})
print('Noiseless parameter recovery is exact to numerical tolerance; this is not empirical speed identification.')
equation(17)'''),
code('''initial = table('synthetic-validation.csv').assign(stage='initial N=40/80')
extra = table('synthetic-small-sample.csv')
results = pd.concat([initial,extra],ignore_index=True)
show_table(results[['stage','case','n','pointwise_coverage','simultaneous_coverage','late_rejection_rate']], 'Table N02.1. Simulation coverage and late-response rejection rates.')
null = results.query("case=='null'")[['n','pointwise_coverage','coverage_mcse','simultaneous_coverage','simultaneous_mcse','late_rejection_rate','late_rejection_mcse']].sort_values('n')
assert len(null)==4 and set(results['case'])==set(CASES)
show_table(null, 'Table N02.2. Null-case performance with Monte Carlo standard errors.')
assert len(results)==24
assert results.replications.sum()==4800
raw = pd.concat([table('synthetic-replications.csv'),table('synthetic-small-sample-replications.csv')])
assert len(raw)==4800
for (case,n),g in raw.groupby(['case','n']):
    row=results[(results.case==case)&(results.n==n)].iloc[0]
    assert np.isclose(g.terminal_covered.mean(),row.pointwise_coverage)
    assert np.isclose(g.path_covered.mean(),row.simultaneous_coverage)
print('All 4,800 scenario fits reconcile with the saved replication-level records.')'''),
md('''## Reading the imperfections

Late-response false-positive rates in the null case are 6.0%, 6.5%, 4.5% and 8.5% at N=16, 30, 40 and 80. The N=80 rate is above nominal and is retained, with MCSE about 2.0 percentage points. The supplementary N=16 gradual-response rejection rate is only 41.5%, illustrating low power in a sample the size of the later statement period.

The six cases share random noise within each sample size and replication, deliberately making comparisons paired. Therefore 4,800 scenario fits involve 800 distinct noise draws, not 4,800 independent experiments. Coverage repeats across additive cases because the fixed signal changes while regression-error draws do not. Each case has 200 independent replications; uncertainty should not be computed by pooling paired cases as independent observations.

As MacKinnon and White (1985) motivate, leverage adjustment improves heteroskedastic covariance estimation; it does not eliminate every small-sample error. As Davidson and Flachaire (2008) explain, wild-bootstrap behaviour depends on the design and implementation. These tests are evidence about the stated simulations, not a guarantee for market data.'''),
code('''equation(11)
equation(12)
equation(13)
print('Heavy simulations can be rerun with:')
print('  python scripts/run_synthetic.py')
print('  python scripts/run_small_sample.py')
print('The executed notebook independently recomputes an example and audits every saved replication group.')'''),
md('''## Milestone outcome

The unrestricted curves can represent mechanisms that a monotone adjustment model cannot. Synthetic quote staleness can imitate delayed information incorporation. Reversals and continuing drift must not be forced into a single half-life. The empirical analysis therefore starts with unrestricted horizon regressions and makes speed reporting conditional on diagnostics.''')]),

('03_event_response_estimation', [
md('''# 03 · Event-time response estimation

The rate factor is the first covariance principal component of MP1, MP2, ED2, ED3 and ED4, fitted on 39 development statements before quote exclusions. Its centre, orientation and standard-deviation scale remain fixed across dates and communication types. The quarterly-rate inputs switch from Eurodollar to SOFR in 2022 according to the source construction.

As Acosta et al. (2026) describe, several rate maturities can summarise different aspects of FOMC news. Here the factor is scaled to one development standard deviation rather than a structural unit shock. As Jordà (2005) motivates in his local-projection paper, separate horizon regressions avoid imposing a complete dynamic curve in advance. This event-level adaptation estimates conditional associations, not structurally identified impulse responses.'''),
code(SETUP),
code('''from diffusion.statistics import pca_fit, pca_transform, ols_hc3, wild_band
from diffusion.empirical import data_for, panel, return_between
events = pd.read_csv(ROOT/'data/processed/event-register.csv')
dev = events.query("phase=='development' and event_type=='Statements'")
frozen = json.loads((ROOT/'outputs/models/surprise-pca.json').read_text())
fresh = pca_fit(dev[frozen['inputs']].to_numpy()*100)
for key in ['centre_bps','loadings','score_sd','explained_variance']:
    np.testing.assert_allclose(fresh[key],frozen[key],rtol=1e-12)
show_table(pd.DataFrame({'input':frozen['inputs'],'loading':frozen['loadings'],'development_centre_bp':frozen['centre_bps']}), 'Table N03.1. Frozen development PCA.')
print(f"Explained rate-input variance: {100*frozen['explained_variance']:.3f}%")
print(f"Unstandardised score SD: {frozen['score_sd']:.6f} bp")
equation(3)
equation(4)'''),
code('''bars, events = data_for(['development'])
x,y,meta,prices = panel(bars,events,'SPX','Statements')
fit = ols_hc3(x,y)
band = wild_band(fit,reps=1999)
saved = table('curves-development.csv').query("asset=='SPX' and event_type=='Statements'")
np.testing.assert_allclose(fit['coef'][1],saved.beta,rtol=1e-9)
np.testing.assert_allclose(band['hi'],saved.sim_high,rtol=1e-9)
late_y = return_between(prices,5,20)
np.testing.assert_allclose(late_y,y[:,-1]-y[:,4],atol=1e-10)
late = ols_hc3(x,late_y)
assert np.isclose(late['coef'][1,0],fit['coef'][1,-1]-fit['coef'][1,4])
print(f"Recomputed development curve from {len(meta)} events; late slope = {late['coef'][1,0]:.6f} bp/SD.")
show_figure(3)'''),
code('''effects = pd.concat([table(f'effects-{p}.csv') for p in ['development','holdout','pooled']],ignore_index=True)
selected = effects.query("asset=='SPX' and measure in ['cumulative_20','late_5_20']").copy()
selected['phase']=selected.phase.replace({'holdout':'later, post-audit'})
show_table(selected[['phase','event_type','measure','n','estimate','ci_low','ci_high']], 'Table N03.2. Primary response and additional 5-to-20-minute association.')
show_figure(4)
show_figure(5)'''),
md('''## What the response estimates say

The pooled statement slope reaches −29.46 bp per development surprise SD by minute 20; the additional 5-to-20-minute slope is +0.44 bp, with a 95% interval of −6.66 to +7.54. This supports an early response association without proving adjustment is complete. Pooled minutes releases show an additional −28.05 bp association over minutes 5–20, with interval −51.23 to −4.86. That extension is exploratory and is not evidence that the same structural mechanism governs statements and minutes.

The later-period statement slope is smaller in magnitude than the development slope, with broad intervals. These intervals are not a formal test of equality across periods. The primary development and pooled statement samples also fail the coverage gate, so their estimates describe accepted windows rather than a certified representative event population.

The simultaneous band covers 20 horizons within one asset/type/sample family. It does not correct the entire project for all assets, types, specifications and exploratory comparisons. The PCA is treated as a frozen regressor: reported intervals are conditional on its estimated training loadings and do not propagate first-stage factor-estimation uncertainty.'''),
code('''rv = table('realised-variance-summary.csv')
show_table(rv[['event_type','asset','n','median_rv_ratio','ci_low','ci_high']], 'Table N03.3. Event versus matched-day realised variance.')
equation(14)
show_figure(7)'''),
md('''## Milestone outcome

The price-response associations are reproducible from cached minute bars and a fixed surprise model. Larger event-window variance confirms unusual activity, not a measured proportion of information incorporated. Signed responses, lagged responses and variance are kept as separate quantities.''')]),

('04_learning_lead_lag_analysis', [
md('''# 04 · Learning lead–lag analysis

Three distinct ideas are often called a lag. **Event lag** asks how a response accumulates after a release. **Cross-series lag** asks whether one quoted return precedes another. **Information lag** asks whether new knowledge has already reached market participants. The first two are observable statistical descriptions; the third needs additional identification.

As Hou and Moskowitz (2005) explain in their study of price delay, lagged information in market returns can reveal price-adjustment frictions. Their principal weekly-return design differs from this minute-event exercise, so their delay measure is not relabelled as our estimate. As Hasbrouck (2007) explains, observed quote dynamics also contain market-microstructure effects.'''),
code(SETUP),
md('''## A known two-minute lead

The toy example creates a target that follows a source with a two-minute delay. We correlate source at time t with target at time t+lag. Under this convention, a positive lag means the source precedes the target. Each event is demeaned within its paired window before pooling, matching the empirical diagnostic.'''),
code('''rng = np.random.default_rng(62)
source = rng.normal(size=(80,40))
target = rng.normal(scale=.2,size=(80,40))
target[:,2:] += source[:,:-2]
lag_rows=[]
for lag in range(-5,6):
    a=source[:,:40-lag] if lag>=0 else source[:,-lag:]
    b=target[:,lag:] if lag>=0 else target[:,:40+lag]
    a=a-a.mean(axis=1,keepdims=True);b=b-b.mean(axis=1,keepdims=True)
    lag_rows.append({'lag_minutes':lag,'correlation':np.corrcoef(a.ravel(),b.ravel())[0,1]})
toy=pd.DataFrame(lag_rows)
assert toy.loc[toy.correlation.idxmax(),'lag_minutes']==2
show_table(toy, 'Table N04.1. Synthetic known-delay check: source leads target by two minutes.')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6.4,3.4))
ax.plot(toy.lag_minutes,toy.correlation,'o-',color='#164B65');ax.axvline(2,color='#C86542',ls='--')
ax.set(xlabel='Lag in minutes; positive means source leads',ylabel='Within-event correlation',title='Known two-minute delay');ax.grid(alpha=.2)
show_plot(fig,'Notebook figure N04.1. Recovery of the known synthetic lead; simulated data.')'''),
code('''corr=table('lead-lag-correlations-pooled.csv')
peaks=corr.loc[corr.groupby(['event_type','source','target']).correlation.apply(lambda s:s.abs().idxmax())]
show_table(peaks[['event_type','source','target','lag_minutes','correlation','events']], 'Table N04.2. Largest absolute sample correlation across the displayed lags; descriptive selection only.')
show_figure(9)
equation(16)'''),
md('''## Conditioning on the target's own history

A persistent target can create a misleading source-return association. The regression therefore includes its own three lagged returns before adding three source-return lags, plus event fixed effects. Event-cluster CR1 uncertainty allows dependence within an event, but the finite number of clusters makes its Wald reference distribution approximate.

As Nickell (1981) shows in *Biases in dynamic models with fixed effects*, including lagged outcomes with fixed effects in short panels can bias coefficient estimates. Each event here contributes only 17 usable minute rows. Clustered standard errors do not remove that coefficient bias. The p-values below are descriptive diagnostics, with no project-wide multiplicity correction, causal interpretation or tradable-lead claim.'''),
code('''tests=table('lead-lag-tests-pooled.csv')
show_table(tests[['event_type','source','target','events','cross_lag_1','cross_lag_2','cross_lag_3','p_value_exploratory','incremental_R2']], 'Table N04.3. Exploratory dynamic fixed-effects diagnostics.')
from diffusion.empirical import data_for,panel
bars,ev=data_for(['development','validation','holdout'])
_,_,m,p=panel(bars,ev,'SPX','Statements')
_,_,mm,pp=panel(bars,ev,'NSX','Statements')
ids=m.index.intersection(mm.index)
a=10000*np.diff(np.log(p.loc[ids,np.arange(-1,20)].to_numpy()),axis=1)
b=10000*np.diff(np.log(pp.loc[ids,np.arange(-1,20)].to_numpy()),axis=1)
a-=a.mean(axis=1,keepdims=True);b-=b.mean(axis=1,keepdims=True)
zero=float(np.corrcoef(a.ravel(),b.ravel())[0,1])
saved=corr.query("event_type=='Statements' and source=='SPX' and target=='NSX' and lag_minutes==0").correlation.iloc[0]
assert np.isclose(zero,saved)
print(f'Recomputed zero-lag SPX/NSX correlation: {zero:.6f} across {len(ids)} events.')'''),
md('''## Milestone outcome

The toy lead is recovered with an explicit sign convention, and the empirical lag diagnostics are reproducible. Shared news, asynchronous quote updates, stale prices, short-panel bias and exploratory selection prevent these diagnostics from proving information transmission or arbitrage. The main evidence remains the separately estimated event-response path.''')]),

('05_chronological_transfer_and_information_sets', [
md('''# 05 · Chronological transfer and information sets

Development covers 2018–2022, validation covers 2023, and the later period covers 2024–2025. A model fitted only on development events is compared with the development-mean return baseline. The time split prevents fitting coefficients on later outcomes, but cannot undo the earlier inspection of the incorrectly aligned run. All corrected later checks are **post-audit chronological transfer**.

The relevant question is whether a fixed conditional relationship travels across time. It is not whether a strategy earns trading profits. The surprise uses information through +20 minutes; a model of the first 20 minutes is retrospective even when its coefficients come from earlier calendar years.'''),
code(SETUP),
code('''freeze=json.loads((ROOT/'protocol/corrected-model-freeze.json').read_text())
changed=[p for p,digest in freeze['files'].items() if sha256(ROOT/p)!=digest]
assert not changed
print('Corrected freeze timestamp:',freeze['released_utc'])
print('Frozen analytical files verified:',len(freeze['files']))
print(freeze['notice'])
models=json.loads((ROOT/'outputs/models/development-predictions.json').read_text())
for model in models.values():
    assert all('2018'<=eid[-10:-6]<='2022' for eid in model['training_ids'])
print('Every stored prediction model uses development event IDs only.')'''),
code('''from diffusion.empirical import data_for,panel,return_between
from diffusion.statistics import paired_mse_summary
bars,events=data_for(['holdout'])
x,y,m,p=panel(bars,events,'SPX','Statements')
model=models['Statements|SPX|cumulative_20']
actual=return_between(p,0,20)
prediction=x@model['coef']
baseline=np.full(len(m),model['baseline'])
fresh=paired_mse_summary(actual,prediction,baseline)
stored=table('transfer-holdout.csv').query("asset=='SPX' and event_type=='Statements' and target=='cumulative_20'").iloc[0]
for field in ['model_mse','baseline_mse','difference','difference_ci_low','difference_ci_high']:
    assert np.isclose(fresh[field],stored[field])
show_json(fresh)
equation(15)'''),
code('''transfer=table('transfer-holdout.csv').query("asset=='SPX' and event_type=='Statements'")
show_table(transfer[['target','n','model_mse','baseline_mse','difference','difference_ci_low','difference_ci_high']], 'Table N05.1. Later-period paired prediction-loss comparison, after the clock audit.')
assert ((transfer.difference_ci_low<0)&(transfer.difference_ci_high>0)).all()
show_figure(8)
show_table(table('coverage.csv').query("phase=='validation'")[['event_type','asset','accepted','planned','sample_gate']], 'Table N05.2. Why the 2023 validation period cannot support the declared response estimation.')'''),
md('''## Interpretation

For later statements, 0–20-minute MSE is 949.17 bp² for the surprise model and 957.96 bp² for the baseline. The paired difference is −8.80 bp² with a very broad interval spanning zero. The 5–20 and 20–25 models have larger point-estimate losses than their baselines, and their difference intervals also include zero. The study therefore finds no convincing predictive improvement across these three targets.

The first two targets overlap the rate-surprise observation window. The final target is temporally separate but assumes the completed surprise is available instantly at +20. It omits publication delay, transaction costs, spreads, executable prices and trade sizing. Neither numerical error reductions nor nominal p-values would establish a viable trading rule.

The historical split is a useful stability check, not a substitute for a genuinely untouched future sample after the clock rule has been fixed. No failed period or inconvenient event is removed to strengthen the transfer result.'''),
code('''show_figure(11)
print('Sequential release warning: the press conference may add new information from +30 minutes.')
print('The primary +20-minute horizon avoids attributing that later release to statement diffusion.')'''),
md('''## Milestone outcome

Chronological predictions and their paired loss intervals are reproduced from frozen coefficients. The information timing and the compromised original holdout are explicit. Later-period performance remains inconclusive, rather than a claimed forecasting success.''')]),

('06_robustness_and_research_reflections', [
md('''# 06 · Robustness, reporting gates and research reflections

This notebook distinguishes completed checks from successful hypotheses. A method can be implemented correctly while the available data fail to identify its intended quantity. The resulting negative or inconclusive result remains part of the research.'''),
code(SETUP),
code('''rows=[]
for phase in ['development','holdout','pooled']:
    d=json.loads((ROOT/f'outputs/adjustment-{phase}.json').read_text())
    for typ,item in d.items():
        g=item['gates']
        rows.append({'sample':phase.replace('holdout','later, post-audit'),'type':typ,'terminal':g['terminal_ci_excludes_zero'],'plateau':g['late_response_equivalence_heuristic'],'shape':g['shape_fit'],'interior':g['interior_parameters'],'bootstrap_valid':g['bootstrap_valid_fraction'],'coverage':item['sample']['adequate'],'reportable_speed':item['reportable']})
gates=pd.DataFrame(rows)
show_table(gates, 'Table N06.1. Speed-reporting gates for the primary SPX series.')
assert not gates.reportable_speed.any()
print('No empirical SPX statement or minutes speed passes every reporting gate.')
equation(18)'''),
md('''## Why an optimiser output is insufficient

The pooled statement curve has a finite numerical adjustment fit, but only 83.4% of the bootstrap curve fits satisfy the validity rule and pooled coverage is below 80%. Pooled minutes fail the plateau and interior-parameter rules, with only 17.6% of bootstrap curve fits valid. A raw fitted t90 is retained in diagnostic JSON for reproducibility; it is deliberately excluded from empirical headline results.

The bootstrap diagnostic fits only the first 199 of the 1,999 event-path draws, as declared in the implementation. Its interval, if reportable, would be conditional on passing shape checks. It does not turn a failed identification test into a precise speed. The estimated plateau margin is a heuristic, not a formally calibrated equivalence test.'''),
code('''robust=table('robustness-pooled.csv').query("asset=='SPX' and event_type=='Statements'")
small=robust.query("measure!='leave_one_out'")
show_table(small[['measure','n','estimate','ci_low','ci_high']], 'Table N06.2. Pooled SPX statement robustness and placebo estimates.')
effects=table('effects-pooled.csv').query("asset=='SPX' and event_type=='Statements' and measure in ['cumulative_10','cumulative_15','cumulative_20','pre_placebo_60_10']")
show_table(effects[['measure','n','estimate','ci_low','ci_high']], 'Table N06.3. Alternative endpoints and the pre-event placebo.')
loo=robust.query("measure=='leave_one_out'")
show_table(pd.DataFrame([{'events':len(loo),'minimum_omission_slope':loo.estimate.min(),'maximum_omission_slope':loo.estimate.max(),'full_slope':loo.full_estimate.iloc[0]}]), 'Table N06.4. Complete leave-one-event-out range.')
assert len(loo)==49
show_figure(10)'''),
md('''## Observed failures and mitigations

1. **Daily acquisition was impractical.** The initial free Dukascopy daily-file route progressed too slowly for the planned panel. A01 moved to free annual HistData archives and changed the instrument interpretation to provider bid quotes. The original route and logs remain available.
2. **Documentation did not align the prices.** Published-window disagreement led to selected minute probes and the A02 seasonal clock rule. Both the original and corrected runs are retained. The clock mismatch is corrected globally, rather than by shifting individual events to their largest move.
3. **The original holdout was already seen.** The corrected development model was frozen before corrected later predictions. This preserves a chronological fit but does not restore untouched validation; the language and claims have been downgraded accordingly.
4. **Coverage remained inadequate.** The 2023 gaps and primary-series development exclusions were not repaired by the clock correction. Complete-window requirements and reporting gates were retained. NSX and EURUSD were not promoted after observing better coverage.
5. **A precise speed was unsupported.** Unstable bootstrap fits, absent plateaus, boundary estimates and coverage failures blocked empirical t50/t90 reporting. Unrestricted response curves remain the principal output.
6. **A plausible regressor could leak future information.** The −10-to-+20 factor is explicitly retrospective within that interval. The separate +20-to-+25 exercise is labelled idealised and is not a trading backtest.
7. **Simulation error was not uniformly nominal.** The 8.5% null rejection rate at N=80 was retained. Supplementary sample-size tests were added after the coverage audit and labelled accordingly.
8. **Bid-only data cannot validate execution.** No meaningful spread or volume analysis is possible. Open-price, endpoint and timestamp checks are retained, but they cannot replace missing ask quotes or execution records.

These are observed development events and limitations, not fabricated accounts of improvements that were never tested.'''),
code('''freeze=json.loads((ROOT/'protocol/corrected-model-freeze.json').read_text())
assert all(sha256(ROOT/p)==digest for p,digest in freeze['files'].items())
checks=json.loads((ROOT/'outputs/validation/checks.json').read_text())
show_json(checks)
assert checks['passed'] and checks['tests']==21
print('Analytical freeze unchanged after all notebook recomputations.')'''),
md('''## Remaining limitations

HC3 intervals are conditional on a frozen estimated factor and assume event-level independence; year-block resampling is only a sensitivity check with few blocks. Matched weekdays are observational controls, not randomised treatments. One-minute bid quotes cannot resolve second-level diffusion. A strict completeness rule protects alignment but can select a nonrepresentative sample. Dynamic fixed-effects lag tests have short-panel bias, while multiple exploratory comparisons have no global multiplicity adjustment.

## Milestone outcome

Every failed gate is visible. The analysis supports event-response measurement and a documented data-quality correction; it does not support a reliable single empirical diffusion speed.''')]),

('07_synthesis_and_publication_registers', [
md('''# 07 · Synthesis and publication preparation

The research milestones are complete with their limitations preserved. This notebook indexes the material for paper assembly; it does not compile the final paper or publish a repository.

**Main finding:** accepted scheduled-statement windows show an early negative SPX association with a rate-increasing surprise factor, while the additional 5–20-minute statement response is imprecise around zero. Minutes releases show a more delayed exploratory association. Neither event type supports a robust single speed estimate under the declared reporting gates. Later-period prediction checks do not show convincing improvement over the frozen mean baseline.'''),
code(SETUP),
code('''milestones=pd.DataFrame([
['M1','Design and sources','00','Definitions, information sets, scholarly foundations'],
['M2','Public-data audit','01','Source cache, exclusions, A01/A02 clock history'],
['M3','Synthetic validation','02','Six mechanisms, four sample sizes, Monte Carlo uncertainty'],
['M4','Event-response estimation','03','Frozen PCA, horizon slopes, event/control activity'],
['M5','Lag analysis','04','Known-delay example and exploratory cross-series tests'],
['M6','Chronological transfer','05','Frozen predictions, paired losses, honest audit chronology'],
['M7','Robustness and reflections','06','Placebos, influence, gates and failures'],
['M8','Research handover','07','Registers, source material and reproducibility record']
],columns=['milestone','workstream','notebook','evidence'])
show_table(milestones,'Table N07.1. Completed research milestones.')
summary=json.loads((ROOT/'outputs/research-summary.json').read_text())
show_json(summary)'''),
code('''figures=json.loads((ROOT/'outputs/figure-register.json').read_text())
eqs=json.loads((ROOT/'paper/equation-register.json').read_text())
show_table(pd.DataFrame(figures)[['number','title']], 'Table N07.2. Figure register for the later paper assembly.')
show_table(pd.DataFrame(eqs)[['number','title']], 'Table N07.3. Numbered equation register.')
show_table(pd.read_csv(ROOT/'paper/abbreviations.csv'), 'Table N07.4. Abbreviations.')
show_table(pd.read_csv(ROOT/'paper/mathematical-symbols.csv'), 'Table N07.5. Mathematical symbols and units.')
assert len(figures)==12 and len(eqs)==19'''),
md('''## Interactive companions

Open `interactive-explorers.html` from the project root. It contains three offline views: a response surface over horizon and surprise magnitude, discrete observed event paths, and a synthetic adjustment laboratory. The surface is the fitted association β(h)z, not a probability distribution or causal price forecast. The synthetic laboratory labels its mechanism explicitly and shows how quote delay can resemble slow diffusion.

All figures have static scientific counterparts or explanatory captions. Three-dimensional rendering supplements the two-dimensional slices; it does not replace uncertainty intervals or data tables.'''),
code('''print('Interactive companion bytes:',(ROOT/'interactive-explorers.html').stat().st_size)
print('Static figures:',len(list((ROOT/'outputs/figures').glob('*.png'))))
print('Paper source registers: equations, figures, tables, abbreviations, symbols and code listings.')
print('Final typesetting remains a separate stage: title page, abstract, contents and all lists.')
print('Layout convention: A4 portrait; captions centred below figures, tables and equations.')
print('Bibliography: Harvard author-date entries only; verification annotations remain separate.')'''),
md('''## Research conclusion and next tests

The useful outcome is an auditable measurement framework, a corrected public-data panel and a clear boundary around what the estimates identify. A fresh future sample with the clock rule fixed in advance would provide stronger validation. Better quote provenance, second-level timestamps and contemporaneously available surprise measures would address distinct remaining limitations. Earnings-call work would additionally need separate earnings-release and call-segment clocks, expectations and corporate-action adjustments; it should not inherit the FOMC identification assumptions unexamined.

The future GitHub landing page can present the research question, concise findings, paper download, notebook index and three interactive views. Raw provider archives require a separate redistribution review before public upload. No website, repository or thumbnail has been published during this research stage.'''),
code('''refs=json.loads((ROOT/'references/references.json').read_text())
for ref in refs:
    print(ref['harvard'])
    print()
print('Reference entries:',len(refs))''')])
]

def build():
    out=ROOT/'notebooks';out.mkdir(exist_ok=True)
    manifest=[]
    import os
    old_cwd=Path.cwd();os.chdir(ROOT)
    try:
        for slug,items in BOOKS:
            started=time.perf_counter();namespace={'__name__':'__main__'};cells=[];count=0;cell_times=[]
            for index,(kind,source) in enumerate(items):
                cell={'cell_type':kind,'id':hashlib.sha256((slug+str(index)).encode()).hexdigest()[:12],'metadata':{},'source':source.splitlines(keepends=True)}
                if kind=='code':
                    count+=1;outputs=[];buf=io.StringIO();t=time.perf_counter()
                    presentation.set_sink(lambda data:outputs.append({'output_type':'display_data','data':data,'metadata':{}}))
                    try:
                        with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
                            exec(compile(source,f'{slug}:cell-{count}','exec'),namespace)
                    except Exception:
                        print(buf.getvalue());traceback.print_exc();raise
                    finally: presentation.set_sink(None)
                    if buf.getvalue():outputs.append({'output_type':'stream','name':'stdout','text':buf.getvalue().splitlines(keepends=True)})
                    elapsed=time.perf_counter()-t;cell_times.append(elapsed)
                    cell.update(execution_count=count,outputs=outputs)
                    cell['metadata']['execution']={'duration_seconds':round(elapsed,6)}
                cells.append(cell)
            nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':platform.python_version()},'research':{'status':'executed','runner':'scripts/build_notebooks.py; fresh Python namespace per notebook; actual cell execution','clock':'A02','later_sample':'post-audit chronological transfer'}},'nbformat':4,'nbformat_minor':5}
            path=out/(slug+'.ipynb');path.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
            record={'notebook':str(path.relative_to(ROOT)),'code_cells':count,'total_cells':len(cells),'duration_seconds':round(time.perf_counter()-started,3),'status':'passed','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cell_seconds':[round(x,3) for x in cell_times]}
            manifest.append(record);print(slug,count,'executed code cells',flush=True)
    finally:os.chdir(old_cwd)
    write_json(ROOT/'outputs/validation/notebook-execution.json',{'executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'notebooks':manifest,'passed':all(x['status']=='passed' for x in manifest)})
    return manifest

if __name__=='__main__':build()
