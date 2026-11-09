"""Independent explicit-set replay, Floyd SCCs and joint-policy lasso oracle."""
from itertools import product
from .core import validate


def _same(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(_same(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(_same(x,y) for x,y in zip(a,b))
    return a==b


def policy_oracle(data):
    data=validate(data);ss=data['states'];ns=[s['name'] for s in ss];ids={n:i for i,n in enumerate(ns)}
    cc=[i for i,s in enumerate(ss) if s['owner']=='controller'];ee=[i for i,s in enumerate(ss) if s['owner']=='environment'];out=[]
    for cp in product(*(range(len(ss[i]['moves'])) for i in cc)):
        good=set(ns)
        for ep in product(*(range(len(ss[i]['moves'])) for i in ee)):
            choices=dict(zip(cc,cp));choices.update(zip(ee,ep))
            for root in range(len(ss)):
                seen={};path=[];v=root
                while v not in seen:
                    seen[v]=len(path);path.append(v);v=ids[ss[v]['moves'][choices[v]]['to']]
                if not any(ss[w]['goal'] for w in path[seen[v]:]):good.discard(ns[root])
        out.append([x for x in ns if x in good])
    return out


def verify(report):
    try:
        data=validate(report['input']);ss=data['states'];ns=[s['name'] for s in ss];ids={x:i for i,x in enumerate(ns)};n=len(ns)
        order=lambda v:[x for x in ns if x in v]
        z=set(ns);outer=[]
        while True:
            y=set();rounds=[];ranks={x:None for x in ns}
            while True:
                after=set();checks=[]
                for s in ss:
                    target=z if s['goal'] else y;flags=[m['to'] in target for m in s['moves']]
                    qualified=any(flags) if s['owner']=='controller' else all(flags)
                    if qualified:after.add(s['name'])
                    checks.append({'state':s['name'],'operator':'exists' if s['owner']=='controller' else 'all',
                                   'scope':'outer' if s['goal'] else 'inner','target_membership':flags,'qualified':qualified})
                added=after-y
                rounds.append({'index':len(rounds),'before':order(y),'after':order(after),'added':order(added),'checks':checks})
                for x in added:ranks[x]=len(rounds)
                if after==y:break
                y=after
            outer.append({'index':len(outer),'before':order(z),'rounds':rounds,'after':order(y),'removed':order(z-y)})
            if z==y:break
            z=y
        records=[]
        for s in ss:
            name=s['name'];moves=[]
            for m in s['moves']:
                tw=m['to'] in z;rank=ranks[m['to']]
                permit=name in z and tw and (s['goal'] or rank<ranks[name])
                moves.append({**m,'target_winning':tw,'target_rank':rank,'rank_permitted':permit})
            records.append({'name':name,'owner':s['owner'],'goal':s['goal'],'winning':name in z,'rank':ranks[name],
                            'moves':moves,'controller_choice':next((m['action'] for m in moves if s['owner']=='controller' and m['rank_permitted']),None)})
        cc=[i for i,s in enumerate(ss) if s['owner']=='controller'];policies=[];oracle=policy_oracle(data)
        for cp in product(*(range(len(ss[i]['moves'])) for i in cc)):
            choices=dict(zip(cc,cp));edges=[{'from':s['name'],'action':m['action'],'to':m['to']} for i,s in enumerate(ss) for j,m in enumerate(s['moves']) if i not in choices or choices[i]==j]
            reach=[[i==j for j in range(n)] for i in range(n)];nong=[[False]*n for _ in range(n)]
            for e in edges:
                i=ids[e['from']];j=ids[e['to']];reach[i][j]=True
                if not ss[i]['goal'] and not ss[j]['goal']:nong[i][j]=True
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
                        nong[i][j]=nong[i][j] or (nong[i][k] and nong[k][j])
            remaining={i for i in range(n) if nong[i][i]};components=[]
            while remaining:
                i=min(remaining);c=sorted(j for j in remaining if nong[i][j] and nong[j][i]);remaining.difference_update(c);components.append(c)
            bad={i for c in components for i in c};roots=[]
            for i in range(n):
                br=[ns[j] for j in range(n) if j in bad and reach[i][j]]
                roots.append({'state':ns[i],'reachable':[ns[j] for j in range(n) if reach[i][j]],'bad_reachable':br,'winning':not bool(br)})
            win=[r['state'] for r in roots if r['winning']]
            if win!=oracle[len(policies)]:return False
            policies.append({'index':len(policies),'choices':[{'state':ns[i],'action':ss[i]['moves'][choices[i]]['action']} for i in cc],
                             'edges':edges,'bad_components':[[ns[i] for i in c] for c in components],'roots':roots,'winning':win})
        union={x for p in policies for x in p['winning']}
        if union!=z:return False
        canonical=next(p['index'] for p in policies if all(not s['winning'] or s['controller_choice'] is None or any(c['state']==s['name'] and c['action']==s['controller_choice'] for c in p['choices']) for s in records))
        if not z.issubset(set(policies[canonical]['winning'])):return False
        expected={'schema':'buchilab-v1','input':data,'outer':outer,'winning':order(z),'losing':order(set(ns)-z),
                  'states':records,'policies':policies,'canonical_policy':canonical}
        return _same(expected,report)
    except (ValueError,TypeError,KeyError,IndexError,StopIteration,RecursionError):return False
