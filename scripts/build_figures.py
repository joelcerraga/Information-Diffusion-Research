import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.reporting import audit_summaries,figures,explorer_data
print(audit_summaries());print('Figures',len(figures()));d=explorer_data();print('Explorer paths',len(d['paths']))
