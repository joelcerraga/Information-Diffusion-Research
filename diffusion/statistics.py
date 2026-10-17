"""Transparent event-level regressions and uncertainty calculations."""
import numpy as np
from scipy import stats, optimize

def ols_hc3(x,y,alpha=.05):
    x=np.asarray(x,float); y=np.asarray(y,float)
    if y.ndim==1:y=y[:,None]
    if not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('nonfinite regression input')
    n,p=x.shape
    if n<=p or np.linalg.matrix_rank(x)<p:raise ValueError('insufficient observations or rank deficient design')
    a=np.linalg.pinv(x);coef=a@y;resid=y-x@coef
    leverage=np.einsum('ij,ji->i',x,a)
    if np.max(leverage)>=1-1e-10:raise ValueError('unit leverage prevents HC3 inference')
    adjusted=resid/(1-leverage[:,None])
    cov=np.einsum('pi,ih,qi->hpq',a,adjusted**2,a,optimize=True)
    se=np.sqrt(np.maximum(0,np.stack([np.diag(c) for c in cov],axis=1)))
    critical=stats.t.ppf(1-alpha/2,n-p)
    return {'coef':coef,'se':se,'lo':coef-critical*se,'hi':coef+critical*se,'cov':cov,'resid':resid,'hat':leverage,'a':a,'n':n,'p':p,'x':x,'y':y}

def wild_band(fit,coefficient=1,reps=1999,seed=20261016):
    """Shared event signs preserve the whole observed within-event path."""
    rng=np.random.default_rng(seed);x=fit['x'];a=fit['a']
    scaled=fit['resid']/(1-fit['hat'][:,None])
    weights=rng.choice([-1.,1.],size=(reps,fit['n']))
    delta=np.einsum('pi,bi,ih->bph',a,weights,scaled,optimize=True)
    e=weights[:,:,None]*scaled[None,:,:]-np.einsum('ip,bph->bih',x,delta,optimize=True)
    adj=e/(1-fit['hat'][None,:,None])
    se=np.sqrt(np.einsum('i,bih->bh',a[coefficient]**2,adj**2,optimize=True))
    t=np.divide(delta[:,coefficient,:],se,out=np.zeros_like(se),where=se>1e-12)
    c=float(np.quantile(np.max(np.abs(t),axis=1),.95))
    b=fit['coef'][coefficient];s=fit['se'][coefficient]
    return {'lo':b-c*s,'hi':b+c*s,'critical':c,'draws':b[None,:]+delta[:,coefficient,:]}

def pca_fit(rates):
    a=np.asarray(rates,float)
    if not np.isfinite(a).all():raise ValueError('missing rate changes')
    centre=a.mean(axis=0);_,s,vt=np.linalg.svd(a-centre,full_matrices=False)
    w=vt[0]
    if w.sum()<0:w=-w
    sd=float(np.std((a-centre)@w,ddof=1))
    if sd<=1e-10:raise ValueError('degenerate policy surprise')
    return {'centre_bps':centre.tolist(),'loadings':w.tolist(),'score_sd':sd,'explained_variance':float(s[0]**2/np.sum(s**2))}

def pca_transform(rates,model):
    return (np.asarray(rates,float)-model['centre_bps'])@np.asarray(model['loadings'])/model['score_sd']

def response_function(h,a,f,k):
    h=np.asarray(h,float)
    return a*(1-(1-f)*np.exp(-k*(h-1)))

def fit_adjustment(h,beta):
    h=np.asarray(h,float);b=np.asarray(beta,float)
    if np.max(np.abs(b))<1e-10:return {'success':False,'reason':'zero response'}
    best=None
    sign=1 if b[-1]>=0 else -1
    amplitude=max(abs(b[-1]),1.)*sign
    limit=max(10*np.max(np.abs(b)),100)
    for f in [.1,.5,.9]:
        fit=optimize.least_squares(lambda z:response_function(h,*z)-b,[amplitude,f,.2],bounds=([-limit,0,.01],[limit,1,5]),max_nfev=600)
        if best is None or np.sum(fit.fun**2)<np.sum(best.fun**2):best=fit
    a,f,k=map(float,best.x)
    pred=response_function(h,a,f,k);rmse=float(np.sqrt(np.mean((b-pred)**2)))
    def time_to(q):return 1. if f>=q else 1+float(np.log((1-f)/(1-q))/k)
    return {'success':bool(best.success),'amplitude_bps':a,'first_minute_fraction':f,'k_per_minute':k,'normalised_rmse':rmse/max(abs(b[-1]),1e-10),'t50_minutes':time_to(.5),'t90_minutes':time_to(.9),'remaining_half_life_minutes':float(np.log(2)/k),'boundary':bool(k<.011 or k>4.99 or f<.001 or f>.999),'predicted':pred.tolist()}

def adjustment_diagnostics(fit,band,h):
    b=fit['coef'][1];model=fit_adjustment(h,b)
    terminal=fit['lo'][1,-1]*fit['hi'][1,-1]>0
    late=ols_hc3(fit['x'],fit['y'][:,-1]-fit['y'][:,9],alpha=.1)
    margin=.25*abs(b[-1])
    plateau=bool(late['lo'][1,0]>-margin and late['hi'][1,0]<margin)
    draw_models=[fit_adjustment(h,draw) for draw in band['draws'][:199]]
    valid=[m for m in draw_models if m.get('success') and not m.get('boundary') and m.get('normalised_rmse',np.inf)<=.25]
    fraction=len(valid)/len(draw_models)
    gates={'terminal_ci_excludes_zero':bool(terminal),'late_response_equivalence_heuristic':plateau,'shape_fit':bool(model.get('normalised_rmse',np.inf)<=.25),'interior_parameters':bool(not model.get('boundary',True)),'bootstrap_valid_fraction':fraction,'bootstrap_gate':fraction>=.9}
    report=all([gates['terminal_ci_excludes_zero'],gates['late_response_equivalence_heuristic'],gates['shape_fit'],gates['interior_parameters'],gates['bootstrap_gate']])
    model['reportable']=bool(report);model['gates']=gates
    model['interpretation']='conditional model summary' if report else 'adjustment speed not identified under declared reporting rule'
    model['conditional_t90_interval']=np.quantile([m['t90_minutes'] for m in valid],[.025,.975]).tolist() if report else None
    model['reportable_t50_minutes']=model.get('t50_minutes') if report else None
    model['reportable_t90_minutes']=model.get('t90_minutes') if report else None
    return model

def year_block_intervals(x,y,years,reps=1999,seed=20261017):
    """Sensitivity only: few year blocks cannot establish nominal coverage."""
    rng=np.random.default_rng(seed);years=np.asarray(years);unique=np.unique(years);out=[]
    for _ in range(reps):
        chosen=rng.choice(unique,len(unique),replace=True)
        ix=np.concatenate([np.flatnonzero(years==v) for v in chosen])
        if np.linalg.matrix_rank(x[ix])<x.shape[1]:continue
        out.append(np.linalg.lstsq(x[ix],y[ix],rcond=None)[0][1])
    return np.quantile(out,[.025,.975],axis=0),len(out)

def paired_mse_summary(actual,predicted,baseline,reps=1999,seed=20261018):
    a=np.asarray(actual);p=np.asarray(predicted);b=np.asarray(baseline)
    diff=(a-p)**2-(a-b)**2
    rng=np.random.default_rng(seed);ix=rng.integers(0,len(a),size=(reps,len(a)))
    ci=np.quantile(diff[ix].mean(axis=1),[.025,.975])
    return {'n':len(a),'model_mse':float(np.mean((a-p)**2)),'baseline_mse':float(np.mean((a-b)**2)),'difference':float(diff.mean()),'difference_ci_low':float(ci[0]),'difference_ci_high':float(ci[1]),'units':'squared basis points; negative difference favours surprise model'}
