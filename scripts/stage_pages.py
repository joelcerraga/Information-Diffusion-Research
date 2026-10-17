"""Stage only the intended website files for GitHub Pages."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'_site'
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir()
for name in ['index.html','.nojekyll']:
 shutil.copy2(ROOT/name,DEST/name)
for name in ['assets','explorers']:
 shutil.copytree(ROOT/name,DEST/name)
(DEST/'vendor').mkdir()
for name in ['plotly-3.1.0.min.js','plotly-LICENSE.txt']:
 shutil.copy2(ROOT/'vendor'/name,DEST/'vendor'/name)
(DEST/'paper/final').mkdir(parents=True)
shutil.copy2(ROOT/'paper/final/Information-Diffusion-Final-Paper.pdf',DEST/'paper/final/Information-Diffusion-Final-Paper.pdf')
print('Staged static website in _site/.')
