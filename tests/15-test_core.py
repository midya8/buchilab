import unittest,json,itertools,random,copy,subprocess,sys,tempfile,pathlib
from unittest.mock import patch
from buchilab import analyze,verify,validate,policy_oracle
ROOT=pathlib.Path(__file__).resolve().parents[1]
def controls():return json.loads((ROOT/'docs/controls.json').read_text())
def state(i,owner,goal,targets):return {'name':'s'+str(i),'owner':owner,'goal':goal,'moves':[{'action':'m'+str(j),'to':'s'+str(t)} for j,t in enumerate(targets)]}
class Tests(unittest.TestCase):
 def test_controls_and_progress_failure(self):
  rs=[analyze(c['input']) for c in controls()]
  for r in rs:self.assertTrue(verify(r))
  a=rs[0];self.assertEqual(a['winning'],['idle','goal']);self.assertEqual(a['policies'][0]['winning'],[]);self.assertEqual(a['policies'][0]['bad_components'],[['idle']]);self.assertEqual(a['states'][0]['controller_choice'],'visit');self.assertFalse(a['states'][0]['moves'][0]['rank_permitted'])
  self.assertEqual(rs[1]['winning'],[]);self.assertGreater(len(rs[1]['outer']),1)
  self.assertEqual(rs[2]['winning'],[]);self.assertEqual(rs[3]['winning'],['pending','goal'])
  self.assertEqual([s['rank'] for s in rs[4]['states']],[6,5,4,3,2,1]);self.assertEqual(rs[5]['winning'],['a','b']);self.assertEqual(rs[6]['winning'],[])
 def test_all_three_state_arenas(self):
  subsets=[[i for i in range(3) if bits>>i&1] for bits in range(1,8)];count=0
  for graph in itertools.product(subsets,repeat=3):
   for owners in range(8):
    for goals in range(8):
     r=analyze({'states':[state(i,'controller' if owners>>i&1 else 'environment',bool(goals>>i&1),graph[i]) for i in range(3)]})
     self.assertTrue(verify(r),(graph,owners,goals));count+=1
  self.assertEqual(count,21952)
 def test_seeded_larger_and_policy_union(self):
  rng=random.Random(74301)
  for _ in range(140):
   n=rng.randint(1,6);r=analyze({'states':[state(i,rng.choice(['controller','environment']),bool(rng.getrandbits(1)),[rng.randrange(n) for _ in range(rng.randint(1,3))]) for i in range(n)]})
   self.assertTrue(verify(r));self.assertEqual(set(r['winning']),{x for p in r['policies'] for x in p['winning']});self.assertTrue(set(r['winning'])<=set(r['policies'][r['canonical_policy']]['winning']))
   for s in r['states']:
    if s['winning'] and s['owner']=='environment':self.assertTrue(all(m['rank_permitted'] for m in s['moves']))
 def test_forged_every_report_family(self):
  r=analyze(controls()[0]['input'])
  paths=[['schema'],['outer',0,'rounds',0,'checks',0,'qualified'],['outer',0,'rounds',0,'checks',0,'target_membership',0],['outer',0,'rounds',0,'before'],['outer',0,'after'],['outer',0,'removed'],['states',0,'rank'],['states',0,'controller_choice'],['states',0,'moves',0,'rank_permitted'],['policies',0,'bad_components'],['policies',0,'roots',0,'reachable'],['policies',0,'roots',0,'winning'],['policies',0,'edges'],['policies',0,'choices'],['canonical_policy'],['winning']]
  for path in paths:
   a=copy.deepcopy(r);v=a
   for k in path[:-1]:v=v[k]
   old=v[path[-1]];v[path[-1]]=not old if type(old)is bool else [] if type(old)is list and old else {'forged':True}
   self.assertFalse(verify(a),path)
  a=copy.deepcopy(r);a['canonical_policy']=True;self.assertFalse(verify(a));a=copy.deepcopy(r);a['extra']=0;self.assertFalse(verify(a))
 def test_checker_no_solver(self):
  r=analyze(controls()[4]['input'])
  with patch('buchilab.core.analyze',side_effect=RuntimeError('disabled')):self.assertTrue(verify(r))
 def test_schema_order_and_immutable(self):
  x=controls()[0]['input'];before=copy.deepcopy(x);r=analyze(x);self.assertEqual(x,before);self.assertEqual(analyze(x),r)
  bads=[{},[],{'states':[]},dict(x,extra=1),{'states':[dict(x['states'][0],moves=[])]},{'states':[dict(x['states'][0],goal=1)]},{'states':[dict(x['states'][0],name='Bad Name')]},{'states':[dict(x['states'][0],owner='random')]}]
  for b in bads:
   with self.assertRaises(ValueError):validate(b)
  y=copy.deepcopy(x);y['states'][0]['moves'][0]['to']='undeclared'
  with self.assertRaises(ValueError):validate(y)
  y=copy.deepcopy(x);y['states'][0]['moves'][1]['action']='wait'
  with self.assertRaises(ValueError):validate(y)
 def test_joint_policy_oracle_cycle_not_bottom_scc(self):
  x=controls()[2]['input'];r=analyze(x);self.assertEqual(r['policies'][0]['bad_components'],[['pending']]);self.assertEqual(policy_oracle(x),[[]])
  # The full graph's only SCC contains a goal. Its non-goal subgraph still has a losing self-cycle.
  self.assertEqual(r['policies'][0]['roots'][0]['reachable'],['pending','goal'])
 def test_maximum_policy_count_and_duplicate_targets(self):
  x={'states':[state(i,'controller',i==5,[(i+1)%6,i,i]) for i in range(6)]};r=analyze(x)
  self.assertEqual(len(r['policies']),729);self.assertTrue(verify(r));self.assertLess(len(json.dumps(r).encode()),8*1024*1024)
  self.assertEqual(r['policies'][0]['winning'],['s'+str(i) for i in range(6)])
 def test_strict_cli_atomic(self):
  with tempfile.TemporaryDirectory() as td:
   output=pathlib.Path(td)/'r.json';inp=pathlib.Path(td)/'a.json';inp.write_text(json.dumps(controls()[0]['input']))
   run=lambda *args:subprocess.run([sys.executable,'-m','buchilab',*map(str,args)],cwd=ROOT,capture_output=True,text=True)
   self.assertEqual(run(inp,'--output',output).returncode,0);self.assertEqual(run(output,'--verify').returncode,0);before=output.read_bytes()
   for text in ['{"states":[],"states":[]}','{"states":NaN}','['*1200, 'x'*65537]:
    inp.write_text(text);self.assertNotEqual(run(inp,'--output',output).returncode,0);self.assertEqual(output.read_bytes(),before)
   output.write_text('{"input":{}}');self.assertNotEqual(run(output,'--verify').returncode,0)
if __name__=='__main__':unittest.main()
