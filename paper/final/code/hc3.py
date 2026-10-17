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
