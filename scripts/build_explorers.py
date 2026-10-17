import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.common import ROOT

def build():
    template=(ROOT/'explorers/template.html').read_text()
    data=(ROOT/'outputs/explorer-data.json').read_text().replace('</','<\\/')
    plotly=(ROOT/'vendor/plotly-3.1.0.min.js').read_text().replace('</script','<\\/script')
    html=template.replace('/* PLOTLY_BUNDLE */',plotly).replace('/* RESEARCH_DATA */',data)
    p=ROOT/'interactive-explorers.html';p.write_text(html);print(p,p.stat().st_size)
if __name__=='__main__':build()
