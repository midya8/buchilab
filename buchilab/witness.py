"""Action-level counterexample lassos for individual positional policies."""
from .core import analyze


def lassos(data):
    report=analyze(data);ss=report['input']['states'];out=[]
    def shortest(edges,start,end,cycle=False):
        # BFS with predecessor edges: input edge order breaks shortest-path ties.
        if start==end and not cycle:return []
        queue=[start];seen={start};parent={}
        for v in queue:
            for e in edges:
                if e['from']!=v:continue
                w=e['to']
                if w==end and (cycle or start!=end):
                    path=[dict(e)];u=v
                    while u!=start:
                        edge=parent[u];path.append(dict(edge));u=edge['from']
                    return list(reversed(path))
                if w not in seen:seen.add(w);parent[w]=e;queue.append(w)
        if start==end and not cycle:return []
        raise ValueError('No path')
    for p in report['policies']:
        edges=p['edges'];ng={s['name'] for s in ss if not s['goal']};non=[e for e in edges if e['from'] in ng and e['to'] in ng];roots=[]
        for r in p['roots']:
            witness=None
            if not r['winning']:
                anchor=r['bad_reachable'][0]
                witness={'anchor':anchor,'prefix':shortest(edges,r['state'],anchor),'cycle':shortest(non,anchor,anchor,True)}
            roots.append({'state':r['state'],'winning':r['winning'],'lasso':witness})
        out.append({'index':p['index'],'choices':p['choices'],'roots':roots})
    return {'schema':'buchilab-lassos-v1','input':report['input'],'policies':out}


def main():
    # Reuse bounded strict parsing and atomic serialization, not the game solver.
    from .__main__ import main as cli
    return cli(generator=lassos,checker=verify_lassos,schema='buchilab-lassos-v1')


def verify_lassos(report):
    """Independent simple-walk enumeration plus joint-policy classification."""
    from itertools import product
    from .core import validate
    from .verify import _same,policy_oracle
    try:
        data=validate(report['input']);ss=data['states'];ns=[s['name'] for s in ss];n=len(ns)
        cc=[i for i,s in enumerate(ss) if s['owner']=='controller'];ng={s['name'] for s in ss if not s['goal']};expected=[];oracle=policy_oracle(data)
        def walk(edges,start,end,cycle=False):
            if start==end and not cycle:return []
            frontier=[([start],[])]
            for _ in range(n if cycle else n-1):
                following=[]
                for vertices,path in frontier:
                    for e in edges:
                        if e['from']!=vertices[-1]:continue
                        if e['to']==end:return path+[dict(e)]
                        if e['to'] not in vertices:following.append((vertices+[e['to']],path+[dict(e)]))
                frontier=following
            return None
        for cp in product(*(range(len(ss[i]['moves'])) for i in cc)):
            choice=dict(zip(cc,cp));edges=[{'from':s['name'],'action':m['action'],'to':m['to']} for i,s in enumerate(ss) for j,m in enumerate(s['moves']) if i not in choice or choice[i]==j];non=[e for e in edges if e['from'] in ng and e['to'] in ng];roots=[];win=oracle[len(expected)]
            for root in ns:
                witness=None
                if root not in win:
                    for anchor in ns:
                        if anchor not in ng:continue
                        cycle=walk(non,anchor,anchor,True)
                        if cycle is None:continue
                        prefix=walk(edges,root,anchor)
                        if prefix is not None:witness={'anchor':anchor,'prefix':prefix,'cycle':cycle};break
                    if witness is None:return False
                roots.append({'state':root,'winning':root in win,'lasso':witness})
            expected.append({'index':len(expected),'choices':[{'state':ns[i],'action':ss[i]['moves'][choice[i]]['action']} for i in cc],'roots':roots})
        return _same(report,{'schema':'buchilab-lassos-v1','input':data,'policies':expected})
    except (ValueError,TypeError,KeyError,IndexError,RecursionError):return False


if __name__=='__main__':raise SystemExit(main())
