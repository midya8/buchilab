import copy,itertools,json,os,pathlib,random,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from buchilab.witness import lassos,verify_lassos
ROOT=pathlib.Path(__file__).resolve().parents[1]
CS=json.loads((ROOT/'docs/controls.json').read_text())

def arena(graph,owners,goals):
 return {'states':[{'name':'s'+str(i),'owner':'controller' if owners>>i&1 else 'environment','goal':bool(goals>>i&1),'moves':[{'action':'m'+str(j),'to':'s'+str(t)} for j,t in enumerate(ts)]} for i,ts in enumerate(graph)]}

class WitnessTests(unittest.TestCase):
 def test_exhaustive_three_state(self):
  count=0
  opts=[list(j for j in range(3) if mask>>j&1) for mask in range(1,8)]
  for graph in itertools.product(opts,repeat=3):
   for owners in range(8):
    for goals in range(8):
     self.assertTrue(verify_lassos(lassos(arena(graph,owners,goals))));count+=1
  self.assertEqual(count,21952)
 def test_seeded_and_duplicate_target_bound(self):
  rng=random.Random(98127)
  for _ in range(120):
   n=rng.randrange(1,7);graph=[[rng.randrange(n) for _ in range(rng.randrange(1,4))] for i in range(n)]
   self.assertTrue(verify_lassos(lassos(arena(graph,rng.randrange(1<<n),rng.randrange(1<<n)))))
  r=lassos(arena([[0,0,0]]*6,63,0));self.assertEqual(len(r['policies']),729);self.assertTrue(verify_lassos(r));self.assertLess(len(json.dumps(r).encode()),8*1024*1024)
 def test_empty_goal_prefix_and_policy_controls(self):
  rs=[lassos(c['input']) for c in CS]
  self.assertEqual(rs[0]['policies'][0]['roots'][0]['lasso'],{'anchor':'idle','prefix':[],'cycle':[{'from':'idle','action':'wait','to':'idle'}]})
  self.assertIsNone(rs[0]['policies'][1]['roots'][0]['lasso'])
  self.assertEqual([e['to'] for e in rs[1]['policies'][0]['roots'][0]['lasso']['prefix']],['goal','done'])
  self.assertEqual(rs[5]['policies'][0]['choices'],[])
  for r in rs:self.assertTrue(verify_lassos(r))
 def test_anchor_order_action_ties_and_multiedge_cycle(self):
  # s0 is a cyclic vertex only via a two-edge cycle. Root s3 has a shorter
  # self-loop, but input-order anchor is s0, so canonical lasso is not globally shortest.
  data=arena([[1,1],[0,2],[2],[3,0]],0,0);r=lassos(data);w=r['policies'][0]['roots'][3]['lasso']
  self.assertEqual(w['anchor'],'s0');self.assertEqual([e['action'] for e in w['prefix']],['m1']);self.assertEqual([e['action'] for e in w['cycle']],['m0','m0']);self.assertTrue(verify_lassos(r))
 def test_forgery_all_families_and_strict_types(self):
  r=lassos(CS[1]['input'])
  changes=[lambda x:x.update(schema='wrong'),lambda x:x['policies'][0].update(index=False),lambda x:x['policies'][0]['choices'][0].update(action='fake'),lambda x:x['policies'][0]['roots'][0].update(winning=True),lambda x:x['policies'][0]['roots'][0].update(state='goal'),lambda x:x['policies'][0]['roots'][0].update(lasso=None),lambda x:x['policies'][0]['roots'][0]['lasso'].update(anchor='goal'),lambda x:x['policies'][0]['roots'][0]['lasso'].update(prefix=[]),lambda x:x['policies'][0]['roots'][0]['lasso'].update(cycle=[]),lambda x:x['policies'][0]['roots'][0]['lasso']['cycle'][0].update(action='fake'),lambda x:x['policies'][0]['roots'][0]['lasso']['prefix'].reverse(),lambda x:x['policies'][0]['roots'][0]['lasso']['cycle'].append(x['policies'][0]['roots'][0]['lasso']['cycle'][0]),lambda x:x.update(extra=1)]
  for change in changes:
   x=copy.deepcopy(r);change(x);self.assertFalse(verify_lassos(x))
  win=lassos(CS[5]['input']);win['policies'][0]['roots'][0]['lasso']={'anchor':'a','prefix':[],'cycle':[]};self.assertFalse(verify_lassos(win))
  for bad in (None,{},[],True,{'input':None}):self.assertFalse(verify_lassos(bad))
 def test_checker_does_not_call_solver_and_immutable(self):
  data=copy.deepcopy(CS[0]['input']);before=copy.deepcopy(data);r=lassos(data);self.assertEqual(data,before);old=copy.deepcopy(r)
  with patch('buchilab.witness.analyze',side_effect=AssertionError),patch('buchilab.core.analyze',side_effect=AssertionError):self.assertTrue(verify_lassos(r))
  self.assertEqual(r,old)
 def test_strict_atomic_cli_and_old_v1_unchanged(self):
  with tempfile.TemporaryDirectory() as td:
   source=pathlib.Path(td)/'arena.json';out=pathlib.Path(td)/'out.json';source.write_text(json.dumps(CS[0]['input']))
   cmd=[sys.executable,'-m','buchilab.witness'];subprocess.run(cmd+[str(source),'--output',str(out)],check=True,capture_output=True);self.assertEqual(json.loads(out.read_text()),lassos(CS[0]['input']))
   p=subprocess.run(cmd+[str(out),'--verify'],capture_output=True,text=True);self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),{'valid':True,'schema':'buchilab-lassos-v1'})
   out.write_text('preserve');source.write_text('{"states":[],"states":[]}');p=subprocess.run(cmd+[str(source),'--output',str(out)],capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve')
   for raw in ('NaN','{}','x'*65537):
    p=subprocess.run(cmd+['-','--output',str(out)],input=raw,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve')
   from buchilab import analyze
   for c in CS:self.assertEqual(analyze(c['input'])['schema'],'buchilab-v1')
