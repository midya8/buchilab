"""Finite total turn-based goalty games, with synchronous fixed-point witnesses."""
import re


def validate(data):
    if not isinstance(data, dict) or set(data) != {'states'}:
        raise ValueError('input must contain exactly states')
    states = data['states']
    if not isinstance(states, list) or not 1 <= len(states) <= 6:
        raise ValueError('states must contain one to six records')
    names = []
    for s in states:
        if not isinstance(s, dict) or set(s) != {'name', 'owner', 'goal', 'moves'}:
            raise ValueError('state keys must be name, owner, goal, moves')
        name = s['name']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', name) or name in names:
            raise ValueError('state names must be unique ASCII identifiers, at most 16 characters')
        names.append(name)
        if s['owner'] not in ('controller', 'environment') or type(s['goal']) is not bool:
            raise ValueError('owner must be controller/environment and goal must be boolean')
        if not isinstance(s['moves'], list) or not 1 <= len(s['moves']) <= 3:
            raise ValueError('each state needs one to three moves; dead ends are rejected')
        actions = []
        for m in s['moves']:
            if not isinstance(m, dict) or set(m) != {'action', 'to'}:
                raise ValueError('move keys must be action and to')
            a = m['action']
            if not isinstance(a, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', a) or a in actions:
                raise ValueError('actions must be unique per state, at most 16 ASCII identifier characters')
            actions.append(a)
    if any(m['to'] not in names for s in states for m in s['moves']):
        raise ValueError('every move target must name a declared state')
    return {'states': [{'name': s['name'], 'owner': s['owner'], 'goal': s['goal'],
                        'moves': [dict(m) for m in s['moves']]} for s in states]}



def analyze(data):
    from itertools import product
    data = validate(data); ss = data['states']; ns = [s['name'] for s in ss]
    ids = {n:i for i,n in enumerate(ns)}; n = len(ss)
    ordered = lambda bits: [x for i,x in enumerate(ns) if bits & (1 << i)]
    z = (1 << n)-1; outer = []
    while True:
        y = 0; rounds = []; ranks = [None]*n
        while True:
            after = 0; checks = []
            for i,s in enumerate(ss):
                flags = [bool((z if s['goal'] else y) & (1 << ids[m['to']])) for m in s['moves']]
                q = any(flags) if s['owner']=='controller' else all(flags)
                if q: after |= 1 << i
                checks.append({'state':s['name'],'operator':'exists' if s['owner']=='controller' else 'all',
                               'scope':'outer' if s['goal'] else 'inner','target_membership':flags,'qualified':q})
            added = after & ~y
            rounds.append({'index':len(rounds),'before':ordered(y),'after':ordered(after),'added':ordered(added),'checks':checks})
            for i in range(n):
                if added & (1 << i): ranks[i] = len(rounds)
            if after == y: break
            y = after
        outer.append({'index':len(outer),'before':ordered(z),'rounds':rounds,'after':ordered(y),'removed':ordered(z & ~y)})
        if y == z: break
        z = y
    states = []
    for i,s in enumerate(ss):
        win = bool(z & (1 << i)); moves=[]
        for m in s['moves']:
            j=ids[m['to']]; tw=bool(z & (1 << j))
            progress=win and tw and (s['goal'] or ranks[j] < ranks[i])
            moves.append({**m,'target_winning':tw,'target_rank':ranks[j],'rank_permitted':progress})
        states.append({'name':s['name'],'owner':s['owner'],'goal':s['goal'],'winning':win,'rank':ranks[i],
                       'moves':moves,'controller_choice':next((m['action'] for m in moves if s['owner']=='controller' and m['rank_permitted']),None)})
    controlled=[i for i,s in enumerate(ss) if s['owner']=='controller']; policies=[]
    for choices in product(*(range(len(ss[i]['moves'])) for i in controlled)):
        choice=dict(zip(controlled,choices))
        adj=[[ids[m['to']] for j,m in enumerate(s['moves']) if i not in choice or j==choice[i]] for i,s in enumerate(ss)]
        # Tarjan on the non-goal induced graph, not only bottom SCCs of the full graph.
        counter=[0]; indices={}; low={}; stack=[]; active=set(); components=[]
        def visit(v):
            indices[v]=low[v]=counter[0];counter[0]+=1;stack.append(v);active.add(v)
            for w in adj[v]:
                if ss[w]['goal']:continue
                if w not in indices:visit(w);low[v]=min(low[v],low[w])
                elif w in active:low[v]=min(low[v],indices[w])
            if low[v]==indices[v]:
                comp=[]
                while True:
                    w=stack.pop();active.remove(w);comp.append(w)
                    if w==v:break
                comp.sort()
                if len(comp)>1 or v in adj[v]:components.append(comp)
        for i,s in enumerate(ss):
            if not s['goal'] and i not in indices:visit(i)
        components.sort(key=lambda c:c[0]); bad={v for c in components for v in c}; roots=[]
        for root in range(n):
            reached={root}; todo=[root]
            for v in todo:
                for w in adj[v]:
                    if w not in reached: reached.add(w);todo.append(w)
            roots.append({'state':ns[root],'reachable':[ns[i] for i in range(n) if i in reached],
                          'bad_reachable':[ns[i] for i in range(n) if i in bad & reached],'winning':not bool(bad & reached)})
        policies.append({'index':len(policies),'choices':[{'state':ns[i],'action':ss[i]['moves'][choice[i]]['action']} for i in controlled],
                         'edges':[{'from':ns[i],'action':m['action'],'to':m['to']} for i,s in enumerate(ss) for j,m in enumerate(s['moves']) if i not in choice or j==choice[i]],
                         'bad_components':[[ns[v] for v in c] for c in components], 'roots':roots,
                         'winning':[r['state'] for r in roots if r['winning']]})
    canonical=next(p['index'] for p in policies if all(not s['winning'] or s['controller_choice'] is None or any(c['state']==s['name'] and c['action']==s['controller_choice'] for c in p['choices']) for s in states))
    return {'schema':'buchilab-v1','input':data,'outer':outer,'winning':ordered(z),'losing':ordered(((1 << n)-1)^z),
            'states':states,'policies':policies,'canonical_policy':canonical}
