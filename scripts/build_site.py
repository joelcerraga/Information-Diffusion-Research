"""Build the static GitHub Pages presentation from published aggregate results."""
from pathlib import Path
import csv, json, html, math

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://joelcerraga.github.io/Information-Diffusion-Research/'
REPO = 'https://github.com/joelcerraga/Information-Diffusion-Research'
PAPER = 'paper/final/Information-Diffusion-Final-Paper.pdf'
GRAPHS = [
 ('response-surface','Response surface','01 / Empirical estimates','Explore fitted responses across horizons and rate surprises, with an uncertainty band for each selected slice.','Horizon · Surprise · Response'),
 ('lead-lag','Lead–lag relationships','02 / Exploratory diagnostics','Compare contemporaneous movement with lagged correlations across the provider quote series.','Lag · Asset pair · Correlation'),
 ('diffusion-laboratory','Diffusion laboratory','03 / Synthetic mechanisms','Change the adjustment rate and quote delay to see how measurement can resemble slow learning.','Time · Adjustment rate · Fraction')
]

def write(path, text):
 p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')

def head(title, description, path='', prefix='', graph=False):
 thumb='interactive-graphs.png' if graph else 'information-diffusion-research.png'
 image=ROOT/'assets/thumbnails'/thumb
 w,h=1774,887
 if image.exists():
  from PIL import Image
  with Image.open(image) as im:w,h=im.size
 e=html.escape; url=BASE+path
 return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | Joel Cerraga</title><meta name="description" content="{e(description)}"><meta name="author" content="Joel Cerraga"><meta name="theme-color" content="#102b3e">
<link rel="canonical" href="{url}"><meta property="og:type" content="website"><meta property="og:site_name" content="Information Diffusion Research"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}assets/thumbnails/{thumb}"><meta property="og:image:secure_url" content="{BASE}assets/thumbnails/{thumb}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}"><meta property="og:image:alt" content="{e(title)} by Joel Cerraga, with conceptual teal geometry on white">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(description)}"><meta name="twitter:image" content="{BASE}assets/thumbnails/{thumb}"><meta name="twitter:image:alt" content="{e(title)} by Joel Cerraga">
<link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg"><link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/research.css"><script src="{prefix}assets/site.js" defer></script></head>'''

def header(prefix='', current='overview', mode=''):
 return f'''<body{(' data-explorer="'+mode+'"') if mode else ''}><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="wrap nav-inner"><a class="brand" href="{prefix}index.html"><img class="brand-mark" src="{prefix}assets/favicon.svg" width="34" height="34" alt=""><span>Information Diffusion<small>Joel Cerraga</small></span></a><button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false">Menu</button><nav class="nav-links" id="site-nav" aria-label="Main navigation"><a href="{prefix}index.html" {'aria-current="page"' if current=='overview' else ''}>Overview</a><a href="{prefix}explorers/" {'aria-current="page"' if current=='graphs' else ''}>Interactive graphs</a><a href="{prefix}{PAPER}">Paper ↗</a><a href="{REPO}">GitHub ↗</a></nav></div></header>'''

def footer(prefix=''):
 return f'''<footer class="site-footer"><div class="wrap footer-inner"><p>Joel Cerraga · Quantitative research · Research release 2026</p><div class="footer-links"><a href="{prefix}explorers/">Interactive graphs</a><a href="{prefix}{PAPER}">Final paper</a><a href="{REPO}">Source &amp; reproduction</a></div></div></footer></body></html>'''

def cards(prefix=''):
 return '<div class="card-grid three">'+''.join(f'''<a class="graph-card" href="{prefix}explorers/{slug}/"><div class="card-image"><img src="{prefix}assets/previews/{slug}.svg" width="900" height="560" alt="{title}: static preview of the {'synthetic model' if slug=='diffusion-laboratory' else 'published aggregate results'}" loading="lazy"><span class="card-tag">{'Synthetic' if slug=='diffusion-laboratory' else 'Research results'}</span></div><div class="card-body"><p class="card-meta">{tag}</p><h3>{title}</h3><p>{desc}</p><div class="card-bottom"><span>Open explorer</span><span aria-hidden="true">↗</span></div></div></a>''' for slug,title,tag,desc,axes in GRAPHS)+'</div>'

def landing():
 desc='Joel Cerraga’s research into price responses to Federal Reserve communication. Explore the final paper, eight notebooks and interactive 3D graphs.'
 s=head('Information Diffusion in Financial Markets',desc)+header()
 s+=f'''<main id="main"><section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><p class="eyebrow">Event studies · Price discovery · Lead–lag analysis</p><h1>Information<br><span>Diffusion</span></h1><p class="lede">How quickly does new information enter prices? A study of Federal Reserve communication, minute-by-minute responses and the limits of measuring market adjustment.</p><div class="button-row"><a class="button" href="explorers/">Explore the graphs ↗</a><a class="button secondary" href="{PAPER}">Read the paper</a></div><p class="hero-note">Research by Joel Cerraga · Free public data · 2018–2025 sample</p></div><figure class="hero-visual" style="margin:0"><img src="assets/previews/response-surface.svg" width="900" height="560" alt="Fitted SPX statement response over time and rate surprise"><figcaption class="visual-label"><span>FITTED RESPONSE / POOLED STATEMENTS</span><span>1–20 MIN</span></figcaption></figure></div></section>
<div class="wrap"><div class="stat-strip"><div class="stat"><strong>128</strong><span>scheduled communication events</span></div><div class="stat"><strong>336</strong><span>accepted event–asset pairs</span></div><div class="stat"><strong>8</strong><span>executed research notebooks</span></div><div class="stat"><strong>3</strong><span>interactive research explorers</span></div></div></div>
<section class="section"><div class="wrap question-grid"><div><p class="eyebrow">The research question</p><h2>Market adjustment begins with a measurement problem.</h2><p>A delayed price response can reflect gradual learning, a stale quote, an incorrectly aligned clock or the arrival of further news. The study asks which interpretations remain defensible after checking those possibilities.</p><p>As Hasbrouck (2007) explains in <em>Empirical market microstructure</em>, the observation process matters when interpreting prices. Here, a source-clock audit becomes a central part of the economic analysis.</p></div><div class="method-list"><div class="method-item"><span class="method-num">01</span><div><h3>Establish the information clock</h3><p>Align scheduled FOMC statements and minutes with provider quotes; audit missing observations and seasonal timestamp behaviour.</p></div></div><div class="method-item"><span class="method-num">02</span><div><h3>Estimate the response path</h3><p>Hold the development rate-surprise factor fixed and estimate each completed minute separately, with uncertainty across horizons.</p></div></div><div class="method-item"><span class="method-num">03</span><div><h3>Test what the model can support</h3><p>Use six simulated mechanisms, matched-day comparisons and chronological prediction checks before interpreting an adjustment speed.</p></div></div></div></div></section>
<section class="section tinted"><div class="wrap question-grid"><div><p class="eyebrow">Main findings / Accepted SPX statement windows</p><h2>An early response. An unresolved adjustment speed.</h2><p>The statement association appears early. Meeting minutes show a more delayed exploratory pattern. Neither communication type meets every criterion for a reliable single time-to-adjustment estimate.</p><p>Prediction checks show no convincing improvement over a development-mean baseline. The rate factor uses information through minute +20; earlier response estimates are retrospective associations.</p></div><div class="result-box"><h3>Estimated statement response</h3><p class="muted small">Basis points per development surprise standard deviation</p><div class="result-numbers"><div class="result-number"><strong>−29.46</strong><span>At minute 20<br>95% interval: −40.31 to −18.61</span></div><div class="result-number"><strong>+0.44</strong><span>Additional minutes 5–20<br>95% interval: −6.66 to +7.54</span></div></div><p class="result-note">49 accepted statements. The pooled sample fails the declared 80% coverage threshold. An interval containing zero does not establish complete information absorption.</p><a class="text-link" href="{PAPER}">Read the complete findings ↗</a></div></div></section>
<section class="section"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">Interactive research</p><h2>Three ways to examine the evidence.</h2></div><p>Rotate the graphs, inspect a slice and change a controlled mechanism. Each view explains its units and limits.</p></div>{cards()}<p class="graph-hint">Empirical views use published aggregate estimates. The diffusion laboratory uses simulated mechanisms.</p></div></section>
<section class="section tinted"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">Read. Inspect. Reproduce.</p><h2>The complete research record.</h2></div></div><div class="resource-grid"><article class="resource"><h3>The final paper</h3><p>46 A4 pages, including the front matter, numbered equations, results, research reflections and Harvard references.</p><a href="{PAPER}">Open the PDF ↗</a></article><article class="resource"><h3>Code and notebooks</h3><p>Eight executed notebooks, analytical modules, synthetic validation and retained protocols.</p><a href="{REPO}/tree/main/notebooks">Browse the notebooks ↗</a></article><article class="resource"><h3>Decisions and limitations</h3><p>The acquisition setbacks, clock repair, coverage failures and model diagnostics that shaped the study.</p><a href="{REPO}/blob/main/docs/reflection-log.md">Read the reflection log ↗</a></article></div><div class="callout" style="margin-top:35px"><p><strong>Scope of the evidence.</strong> SPX and NSX are provider index-linked quotes; EURUSD is a provider FX quote series. The analysis uses bid-only minute bars. Corrected 2024–2025 evaluation is post-audit chronological transfer: the original later-period results had already been examined. Exact empirical reruns require separately obtained input data; public checks and synthetic examples run from the repository.</p></div></div></section>
<div class="wrap section"><section class="references" aria-label="References"><h2>References</h2><p>Hasbrouck, J. (2007) <em>Empirical market microstructure: The institutions, economics, and econometrics of securities trading.</em> New York: Oxford University Press.</p><p>MacKinlay, A.C. (1997) ‘Event studies in economics and finance’, <em>Journal of Economic Literature</em>, 35(1), pp. 13–39.</p><p><a href="{REPO}/blob/main/references/harvard-references.txt">Complete Harvard bibliography ↗</a></p></section></div></main>'''
 write('index.html',s+footer())

def gallery():
 desc='Interactive 3D response surfaces, lead–lag relationships and a synthetic diffusion laboratory from Joel Cerraga’s information-diffusion research.'
 s=head('Information Diffusion — Interactive Graphs',desc,'explorers/','../',True)+header('../','graphs')
 s+=f'''<main id="main"><section class="page-intro"><div class="wrap"><p class="breadcrumb"><a href="../index.html">Overview</a><span>/</span>Interactive graphs</p><div class="catalog-intro"><div><p class="eyebrow">Information Diffusion Research</p><h1>Explore how<br>markets respond.</h1><p class="lede">Move from empirical associations to a controlled experiment. Each explorer pairs a rotatable 3D view with a readable two-dimensional companion.</p><div class="tag-row"><span class="tag">Three interactive views</span><span class="tag">Free public data</span><span class="tag">Units &amp; interpretation</span></div></div><img src="../assets/thumbnails/interactive-graphs.png" width="1774" height="887" alt="Information Diffusion Interactive Graphs by Joel Cerraga; conceptual cover artwork"></div></div></section><section class="section"><div class="wrap">{cards('../')}<p class="graph-hint">Drag to rotate, scroll to zoom and use the controls to compare scenarios. CSV exports accompany the empirical graphs.</p><div class="callout" style="margin-top:32px"><p><strong>Reading the graphs.</strong> A smooth surface visualises an estimated relationship; it does not establish a causal mechanism or a trading opportunity. The laboratory’s adjustment times belong to its chosen synthetic mechanism. No empirical diffusion time passed every reporting criterion.</p></div><div class="button-row"><a class="button secondary" href="../{PAPER}">Read the methods and findings</a><a class="button secondary" href="{REPO}">Browse the research code ↗</a></div></div></section></main>'''
 write('explorers/index.html',s+footer('../'))

def detail(g):
 slug,title,tag,desc,axes=g; p='../../'
 s=head(title+' — Information Diffusion',desc,'explorers/'+slug+'/',p,True)+header(p,'graphs',slug)
 s+=f'''<main id="main"><section class="page-intro"><div class="wrap"><p class="breadcrumb"><a href="../../index.html">Overview</a><span>/</span><a href="../">Interactive graphs</a><span>/</span>{title}</p><p class="eyebrow">{tag}</p><h1>{title}</h1><p class="lede">{desc}</p></div></section><section class="section explorer-section"><div class="wrap"><div class="callout" id="context"><p id="context-text"></p></div><div class="explorer-layout"><aside class="control-panel" aria-label="Graph controls"><h2>Explore the graph</h2><div id="empirical-controls"><label for="asset">Price series</label><select id="asset"><option>SPX</option><option>NSX</option><option>EURUSD</option></select><label for="communication">Communication</label><select id="communication"><option value="Statements">FOMC statements</option><option value="Minutes">Meeting minutes</option></select><label for="sample">Sample</label><select id="sample"><option value="pooled">Pooled 2018–2025</option><option value="development">Development 2018–2022</option><option value="validation">Validation 2023</option><option value="holdout">Later period 2024–2025</option></select></div><div id="response-controls"><label for="surprise">Surprise slice <output id="surprise-output" for="surprise">1.00 SD</output></label><input id="surprise" type="range" min="-2" max="2" step="0.01" value="1"></div><div id="lag-controls" hidden><label for="pair">Source → target</label><select id="pair"><option value="SPX|NSX">SPX → NSX</option><option value="NSX|SPX">NSX → SPX</option><option value="SPX|EURUSD">SPX → EURUSD</option><option value="EURUSD|SPX">EURUSD → SPX</option></select></div><div id="lab-controls" hidden><label for="fraction">First-minute fraction <output id="fraction-output">0.25</output></label><input id="fraction" type="range" min="0" max="1" step=".01" value=".25"><label for="rate">Adjustment rate <output id="rate-output">0.22 / min</output></label><input id="rate" type="range" min=".01" max="1" step=".01" value=".22"><label for="amplitude">Total response <output id="amplitude-output">−25 bp</output></label><input id="amplitude" type="range" min="-100" max="100" step="1" value="-25"><label for="delay">Quote delay <output id="delay-output">0 min</output></label><input id="delay" type="range" min="0" max="5" step="1" value="0"></div><div class="research-metric" id="metric" aria-live="polite"></div><p class="small muted" id="control-note"></p><button class="button secondary" id="reset" type="button">Reset camera</button><button class="button secondary" id="download" type="button">Download selected CSV</button></aside><div class="charts"><p class="small muted" id="status" role="status">Loading the research view…</p><figure class="research-chart"><div id="plot3d" aria-label="Rotatable three-dimensional research graph"></div><figcaption id="caption3d"></figcaption></figure><figure class="research-chart"><div id="plot2d" aria-label="Two-dimensional companion plot"></div><figcaption id="caption2d"></figcaption></figure><noscript><p>JavaScript is needed for the interactive graphs. A static preview and the paper remain available below.</p><img src="../../assets/previews/{slug}.svg" alt="Static preview of {title}"></noscript></div></div><div class="read-grid"><article><h2>How to read this view</h2><p id="reading"></p></article><article><h2>Interpretation and limits</h2><p id="limits"></p><a href="../../{PAPER}">Read the full methodology ↗</a></article></div><div class="next-explorer"><a href="../">← All interactive graphs</a><a href="{REPO}/tree/main/outputs/tables">Published estimates ↗</a></div></div></section></main><script src="../../vendor/plotly-3.1.0.min.js"></script><script src="../../assets/research-data.js"></script><script src="../../assets/explorer.js"></script>'''
 write(f'explorers/{slug}/index.html',s+footer(p))

def build_data():
 def csv_rows(name):
  with (ROOT/'outputs/tables'/name).open() as f:
   rows=list(csv.DictReader(f))
  for r in rows:
   for k,v in r.items():
    try:r[k]=float(v) if v not in ['True','False'] else v=='True'
    except (ValueError,TypeError):pass
  return rows
 data={'curves':sum((csv_rows('curves-'+p+'.csv') for p in ['development','validation','holdout','pooled']),[]),'coverage':csv_rows('coverage.csv'),'lags':sum((csv_rows('lead-lag-correlations-'+p+'.csv') for p in ['development','pooled']),[]),'ranges':json.loads((ROOT/'assets/surprise-ranges.json').read_text())}
 write('assets/research-data.js','"use strict";\nwindow.RESEARCH_DATA='+json.dumps(data,separators=(',',':'),allow_nan=False)+';\n')

def previews():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import numpy as np
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#102b3e','axes.labelcolor':'#566b78','xtick.color':'#566b78','ytick.color':'#566b78','svg.fonttype':'none'})
 data=json.loads((ROOT/'assets/research-data.js').read_text().split('window.RESEARCH_DATA=')[1].rstrip(';\n'))
 for slug,*_ in GRAPHS:
  fig=plt.figure(figsize=(9,5.6),facecolor='white');ax=fig.add_subplot(111,projection='3d');ax.view_init(25,-53)
  for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:
   axis.pane.fill=False;axis._axinfo['grid']['color']=(.82,.88,.89,.5)
  if slug=='response-surface':
   rows=[r for r in data['curves'] if r['phase']=='pooled' and r['asset']=='SPX' and r['event_type']=='Statements'];h=np.array([r['horizon'] for r in rows]);s=np.linspace(-2,2,25);X,Y=np.meshgrid(h,s);Z=Y*np.array([r['beta'] for r in rows]);ax.plot_surface(X,Y,Z,cmap='BrBG',alpha=.88,linewidth=.2,edgecolor='#ffffff55');ax.plot(h,np.ones(20),[r['beta'] for r in rows],color='#b68432',lw=3);ax.set(xlabel='Minutes after release',ylabel='Surprise (SD)',zlabel='Response (bp)')
  elif slug=='lead-lag':
   pairs=[('SPX','NSX'),('NSX','SPX'),('SPX','EURUSD'),('EURUSD','SPX')]
   for i,(a,b) in enumerate(pairs):
    r=[r for r in data['lags'] if r['phase']=='pooled' and r['event_type']=='Statements' and r['source']==a and r['target']==b];ax.plot([v['lag_minutes'] for v in r],[i]*len(r),[v['correlation'] for v in r],color=['#14756e','#102b3e','#b68432','#5998a2'][i],marker='o',ms=3,lw=2)
   ax.set(xlabel='Lag (minutes)',ylabel='Pair index',zlabel='Correlation',yticks=list(range(4)),zlim=(-.3,1));ax.set_yticklabels(['1','2','3','4'])
  else:
   h=np.arange(1,21);rates=np.linspace(.01,1,40);X,Y=np.meshgrid(h,rates);Z=100*(1-.75*np.exp(-Y*(X-1)));ax.plot_surface(X,Y,Z,cmap='GnBu',alpha=.9,linewidth=.2,edgecolor='#ffffff55');ax.plot(h,np.full(20,.22),100*(1-.75*np.exp(-.22*(h-1))),color='#b68432',lw=3);ax.set(xlabel='Minutes after release',ylabel='Rate (per minute)',zlabel='Adjustment (%)',zlim=(0,100))
  fig.subplots_adjust(left=.01,right=.92,bottom=.08,top=.98)
  path=ROOT/'assets/previews'/f'{slug}.svg';path.parent.mkdir(exist_ok=True,parents=True);fig.savefig(path);plt.close(fig)

def main():
 build_data();previews();landing();gallery()
 for g in GRAPHS:detail(g)
 print('Built landing page, graph gallery, three explorers and accurate static previews.')

if __name__=='__main__':main()
