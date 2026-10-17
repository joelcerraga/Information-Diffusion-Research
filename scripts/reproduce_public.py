"""Run meaningful numerical checks and one fresh synthetic example without market inputs."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
 subprocess.run([sys.executable,'scripts/verify_public_release.py'],cwd=ROOT,check=True)
 subprocess.run([sys.executable,'scripts/run_checks.py'],cwd=ROOT,check=True)
 import numpy as np
 from diffusion.synthetic import sample,truth
 from diffusion.statistics import ols_hc3,wild_band,fit_adjustment
 x,y=sample('gradual',80,20261016)
 fit=ols_hc3(x,y);band=wild_band(fit,reps=1999)
 recovered=fit_adjustment(np.arange(1,21),truth('gradual',np.arange(1,21)))
 np.testing.assert_allclose([recovered['amplitude_bps'],recovered['first_minute_fraction'],recovered['k_per_minute']],[-25,.25,.22],atol=1e-5)
 out=ROOT/'outputs/public-reproduction';out.mkdir(exist_ok=True,parents=True)
 record={'example':'Synthetic gradual adjustment; not empirical identification','events':80,'bootstrap_draws':1999,'estimated_20_minute_slope':float(fit['coef'][1,-1]),'clean_parameter_recovery':recovered}
 (out/'synthetic-example.json').write_text(json.dumps(record,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v))+'\n')
 print('Public reproduction complete: checks and a fresh synthetic experiment. Full empirical reruns require separately retained data.')

if __name__=='__main__':main()
