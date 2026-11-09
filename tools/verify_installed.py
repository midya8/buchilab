"""Reproduce every browser control through installed import and both CLI entry points."""
import importlib
import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys
from buchilab import analyze, verify
controls=json.loads(Path(sys.argv[1]).read_text())
origins=[]
for name in ['buchilab','buchilab.core','buchilab.verify','buchilab.__main__','buchilab.witness']:
    origin=str(Path(importlib.import_module(name).__file__).resolve())
    assert 'site-packages' in origin,origin
    origins.append(origin)
outside=tempfile.TemporaryDirectory()
env=dict(os.environ);env.pop('PYTHONPATH',None)
for c in controls:
    expected=analyze(c['input']);assert verify(expected)
    for cmd in [[sys.executable,'-m','buchilab'],[str(Path(sys.executable).parent/'buchilab')]]:
        p=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
        actual=json.loads(p.stdout);assert actual==expected
        p=subprocess.run(cmd+['-','--verify'],input=json.dumps(actual),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
        assert json.loads(p.stdout)=={'valid':True,'schema':'buchilab-v1'}
from buchilab.witness import lassos,verify_lassos
lasso_controls=json.loads(Path(sys.argv[2]).read_text())
for c in lasso_controls:
    expected=lassos(c['input']);assert verify_lassos(expected)
    cmd=[sys.executable,'-m','buchilab.witness']
    p=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
    actual=json.loads(p.stdout);assert actual==expected
    p=subprocess.run(cmd+['-','--verify'],input=json.dumps(actual),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
    assert json.loads(p.stdout)=={'valid':True,'schema':'buchilab-lassos-v1'}
print(json.dumps({'reports':len(controls),'entry_points':2,'lasso_reports':len(lasso_controls),'lasso_entry_points':1,'installed_origins':origins}))

outside.cleanup()
