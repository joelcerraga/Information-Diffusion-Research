"""Reproduce the recorded research without resetting or replacing its freeze."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.common import ROOT,sha256

def command(*args):
    print('Running:', ' '.join(args),flush=True)
    subprocess.run([sys.executable,*args],cwd=ROOT,check=True)

def verify_freeze():
    d=json.loads((ROOT/'protocol/corrected-model-freeze.json').read_text())
    bad=[p for p,h in d['files'].items() if sha256(ROOT/p)!=h]
    if bad:raise RuntimeError('Frozen analytical files differ; preserve the recorded run and investigate: '+str(bad))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--full',action='store_true',help='Rerun simulations and all estimates from processed bars.')
    p.add_argument('--reprocess-raw',action='store_true',help='Verify the exact raw cache and rebuild corrected event panels.')
    a=p.parse_args();verify_freeze()
    if a.reprocess_raw:
        entries=json.loads((ROOT/'data/raw-manifest.json').read_text())
        bad=[r['path'] for r in entries if not (ROOT/r['path']).is_file() or sha256(ROOT/r['path'])!=r['sha256']]
        if bad:raise RuntimeError('Missing or altered raw files; extract the raw cache first: '+str(bad[:8]))
        for phase in ['development','validation','holdout']:
            command('scripts/acquire_histdata.py','--phase',phase,'--process-only')
    command('scripts/run_checks.py')
    if a.full:
        command('scripts/run_synthetic.py');command('scripts/run_small_sample.py')
        for phase in ['development','validation','holdout','pooled']:
            command('scripts/run_empirical.py','--stage',phase)
        verify_freeze()
        command('scripts/build_figures.py')
        command('scripts/build_explorers.py')
    command('scripts/build_notebooks.py')
    command('scripts/build_registers.py')
    verify_freeze()
    print('Research reproduction complete. Final paper and public publication remain separate stages.')

if __name__=='__main__':main()
