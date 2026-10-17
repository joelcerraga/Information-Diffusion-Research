import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.synthetic import run_synthetic
print(run_synthetic().to_string(index=False))
