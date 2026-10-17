import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.empirical import *
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['development','validation','freeze','holdout','pooled'],required=True);a=p.parse_args()
if a.stage=='freeze':
    freeze_development();print('Chronological model and source freeze written.')
else:
    if a.stage=='development':build_surprise()
    phases=['development','validation','holdout'] if a.stage=='pooled' else [a.stage]
    print(analyse(phases,a.stage).to_string(index=False))
    independent_window_check(phases,a.stage)
    if a.stage in ['development','pooled']:print(lead_lag(phases,a.stage).to_string(index=False))
    if a.stage in ['validation','holdout'] and (ROOT/'outputs/models/development-predictions.json').exists():print(evaluate_transfer(a.stage).to_string(index=False))
