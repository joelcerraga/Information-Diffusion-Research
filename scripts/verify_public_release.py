"""Dependency-free checks for release links, social images, data and frozen code."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import csv, hashlib, json, struct

ROOT=Path(__file__).resolve().parents[1]
BASE='https://joelcerraga.github.io/Information-Diffusion-Research/'

class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.meta={};self.ids=[];self.canonical=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  for key in ['src','href']:
   if key in a:self.links.append(a[key])
  if tag=='meta':self.meta[a.get('property',a.get('name',''))]=a.get('content','')
  if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href')

def main():
 problems=[];pages=list((ROOT/'explorers').rglob('index.html'))+[ROOT/'index.html'];checked=0
 for f in pages:
  d=Page();d.feed(f.read_text())
  if len(d.ids)!=len(set(d.ids)):problems.append(f'Duplicate IDs: {f.relative_to(ROOT)}')
  for link in d.links:
   parsed=urlsplit(link)
   if parsed.scheme or parsed.netloc or not parsed.path:continue
   target=f.parent/unquote(parsed.path)
   if target.is_dir():target=target/'index.html'
   if not target.is_file():problems.append(f'Broken link: {f.relative_to(ROOT)} -> {link}')
   checked+=1
  expected=BASE+('' if f==ROOT/'index.html' else f.parent.relative_to(ROOT).as_posix()+'/')
  if d.canonical!=expected or d.meta.get('og:url')!=expected:problems.append(f'Canonical URL: {f}')
  for key in ['og:title','og:description','og:image','og:image:alt','twitter:image','twitter:card']:
   if not d.meta.get(key):problems.append(f'Missing {key}: {f}')
  image=d.meta.get('og:image','')
  if not image.startswith(BASE):problems.append(f'Unexpected thumbnail origin: {f}')
  else:
   p=ROOT/image[len(BASE):]
   if not p.is_file():problems.append(f'Missing thumbnail: {p}')
   else:
    blob=p.read_bytes();w,h=struct.unpack('>II',blob[16:24])
    if (str(w),str(h))!=(d.meta.get('og:image:width'),d.meta.get('og:image:height')):problems.append(f'Thumbnail dimensions: {f}')
  if image!=d.meta.get('twitter:image'):problems.append(f'Inconsistent social images: {f}')
 freeze=json.loads((ROOT/'protocol/corrected-model-freeze.json').read_text())
 for p,digest in freeze['files'].items():
  if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:problems.append('Frozen file changed: '+p)
 for name in ['data/raw','data/processed','archive','outputs/explorer-data.json','interactive-explorers.html','research-review.html']:
  if (ROOT/name).exists():problems.append('Private input present in release: '+name)
 if len(list((ROOT/'notebooks').glob('*.ipynb')))!=8:problems.append('Notebook count differs from eight')
 for p in (ROOT/'notebooks').glob('*.ipynb'):
  d=json.loads(p.read_text())
  for cell in d['cells']:
   if any(o.get('output_type')=='error' for o in cell.get('outputs',[])):problems.append('Notebook error: '+p.name)
 data=json.loads((ROOT/'assets/research-data.js').read_text().split('window.RESEARCH_DATA=')[1].rstrip(';\n'))
 if set(data)!={'curves','coverage','lags','ranges'}:problems.append('Unexpected explorer data fields')
 rows=[r for r in data['curves'] if r['asset']=='SPX' and r['phase']=='pooled' and r['event_type']=='Statements' and r['horizon']==20]
 if len(rows)!=1 or abs(rows[0]['beta']+29.46)>.005:problems.append('Headline estimate does not match source table')
 paper=ROOT/'paper/final/Information-Diffusion-Final-Paper.pdf'
 if hashlib.sha256(paper.read_bytes()).hexdigest()!='379d4064bc53f3ff0cb2a3b5197c1a8bfaa7555bc48b53fd368afb253d64fd74':problems.append('Final PDF bytes differ from the supplied final version')
 if problems:raise SystemExit('\n'.join(problems))
 print(f'PASS: {len(pages)} pages; {checked} local links; social metadata and thumbnail dimensions; eight notebooks; aggregate graph data; final PDF; {len(freeze["files"])} frozen analytical files.')

if __name__=='__main__':main()
