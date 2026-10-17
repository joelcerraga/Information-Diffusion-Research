import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.histdata import acquire,process
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['development','validation','holdout'],required=True);p.add_argument('--process-only',action='store_true');a=p.parse_args()
if not a.process_only:acquire(a.phase)
print(process(a.phase).groupby(['event_type','asset'])[['event_accepted','control_accepted']].sum().to_string())
