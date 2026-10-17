import sys,unittest,json,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diffusion.common import ROOT,write_json,utcnow
stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py');result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
log=stream.getvalue();print(log)
(ROOT/'outputs/validation').mkdir(parents=True,exist_ok=True);(ROOT/'outputs/validation/checks.txt').write_text(log)
write_json(ROOT/'outputs/validation/checks.json',{'executed_utc':utcnow(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()})
sys.exit(0 if result.wasSuccessful() else 1)
