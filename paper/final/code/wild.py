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
