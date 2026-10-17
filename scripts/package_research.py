"""Package a review handover and an optional exact-source cache separately."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def included(p):
    rel=p.relative_to(ROOT)
    if not p.is_file() or '__pycache__' in rel.parts or '.ipynb_checkpoints' in rel.parts:return False
    if 'node_modules' in rel.parts or p.suffix in {'.pyc','.pyo'}:return False
    if rel.parts[:2]==('data','raw'):return False
    if 'validation' in rel.parts and p.suffix=='.png':return False
    return rel.as_posix()!='DELIVERABLES.json'

def main():
    notebooks=json.loads((ROOT/'outputs/validation/notebook-execution.json').read_text())
    for n in notebooks['notebooks']:
        assert digest(ROOT/n['notebook'])==n['sha256'],n['notebook']
    freeze=json.loads((ROOT/'protocol/corrected-model-freeze.json').read_text())
    assert all(digest(ROOT/p)==h for p,h in freeze['files'].items())
    paths=sorted(p for p in ROOT.rglob('*') if included(p))
    manifest={'project':'Information Diffusion in Financial Markets','stage':'Executed research handover; final paper and public repository pending','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in paths],'raw_cache':'Separate information-diffusion-raw-cache.zip; extract inside the project directory.','exclusions':'Raw sources, Python caches and browser/visual-QA screenshots are outside the main archive.'}
    mp=ROOT/'DELIVERABLES.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
    main_zip=ROOT.parent/'information-diffusion-research.zip'
    with zipfile.ZipFile(main_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths+[mp]:z.write(p,ROOT.name+'/'+str(p.relative_to(ROOT)))
    raw_zip=ROOT.parent/'information-diffusion-raw-cache.zip'
    raw=json.loads((ROOT/'data/raw-manifest.json').read_text())
    with zipfile.ZipFile(raw_zip,'w',zipfile.ZIP_STORED) as z:
        for item in raw:
            p=ROOT/item['path'];assert digest(p)==item['sha256'];z.write(p,item['path'])
        z.write(ROOT/'data/raw-manifest.json','data/raw-manifest.json')
    for p in [main_zip,raw_zip]:
        with zipfile.ZipFile(p) as z:assert z.testzip() is None
        print(json.dumps({'file':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}),flush=True)

if __name__=='__main__':main()
