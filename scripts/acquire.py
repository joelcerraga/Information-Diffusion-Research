import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.data import initialise,acquire_phase,process_phase
from diffusion.common import ROOT
import argparse
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['development','validation','holdout']);p.add_argument('--initialise',action='store_true');p.add_argument('--workers',type=int,default=2);p.add_argument('--process-only',action='store_true');a=p.parse_args()
if a.initialise:
    e=initialise();print(e.groupby(['event_type','phase']).size().to_string(),flush=True)
if a.phase:
    if a.phase=='holdout' and not (ROOT/'protocol/holdout-release.json').exists():raise RuntimeError('Freeze the development model and analysis code before releasing holdout')
    if not a.process_only:acquire_phase(a.phase,a.workers)
    print(process_phase(a.phase).groupby(['event_type','asset']).event_accepted.agg(['sum','count']).to_string(),flush=True)
