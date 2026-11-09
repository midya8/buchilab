/* Independent explicit-set fixed points and DFS reachability; no model API. */
export function validate(data){
 const keys=(x,w)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join(',')===w.slice().sort().join(',');
 const id=x=>typeof x==='string'&&/^[A-Za-z][A-Za-z0-9_]{0,15}$/.test(x);
 if(!keys(data,['states'])||!Array.isArray(data.states)||data.states.length<1||data.states.length>6)throw Error('input needs exactly states, one to six records');
 const names=[];
 for(const s of data.states){if(!keys(s,['name','owner','goal','moves'])||!id(s.name)||names.includes(s.name))throw Error('unique ASCII state names, at most 16 characters');names.push(s.name);if(!['controller','environment'].includes(s.owner)||typeof s.goal!=='boolean')throw Error('controller/environment owner and boolean goal required');if(!Array.isArray(s.moves)||s.moves.length<1||s.moves.length>3)throw Error('one to three moves per state; dead ends rejected');const actions=[];for(const m of s.moves){if(!keys(m,['action','to'])||!id(m.action)||actions.includes(m.action))throw Error('unique action identifiers per state required');actions.push(m.action);}}
 if(data.states.some(s=>s.moves.some(m=>!names.includes(m.to))))throw Error('move targets must be declared');
 return {states:data.states.map(s=>({name:s.name,owner:s.owner,goal:s.goal,moves:s.moves.map(m=>({...m}))}))};
}
function products(sizes){let out=[[]];for(const size of sizes)out=out.flatMap(xs=>Array.from({length:size},(_,i)=>[...xs,i]));return out;}
export function analyze(raw){
 const data=validate(raw),ss=data.states,ns=ss.map(s=>s.name),ids=new Map(ns.map((n,i)=>[n,i])),order=set=>ns.filter(n=>set.has(n)),equal=(a,b)=>a.size===b.size&&[...a].every(x=>b.has(x));
 let z=new Set(ns),outer=[],rank;
 for(;;){let y=new Set(),rounds=[];rank=new Map(ns.map(n=>[n,null]));for(;;){const after=new Set(),checks=[];for(const s of ss){const target=s.goal?z:y,flags=s.moves.map(m=>target.has(m.to)),q=s.owner==='controller'?flags.some(Boolean):flags.every(Boolean);if(q)after.add(s.name);checks.push({state:s.name,operator:s.owner==='controller'?'exists':'all',scope:s.goal?'outer':'inner',target_membership:flags,qualified:q});}const added=order(after).filter(x=>!y.has(x));rounds.push({index:rounds.length,before:order(y),after:order(after),added,checks});for(const x of added)rank.set(x,rounds.length);if(equal(y,after))break;y=after;}outer.push({index:outer.length,before:order(z),rounds,after:order(y),removed:order(z).filter(x=>!y.has(x))});if(equal(z,y))break;z=y;}
 const states=ss.map(s=>{const moves=s.moves.map(m=>({ ...m,target_winning:z.has(m.to),target_rank:rank.get(m.to),rank_permitted:z.has(s.name)&&z.has(m.to)&&(s.goal||rank.get(m.to)<rank.get(s.name))}));return {name:s.name,owner:s.owner,goal:s.goal,winning:z.has(s.name),rank:rank.get(s.name),moves,controller_choice:s.owner==='controller'?(moves.find(m=>m.rank_permitted)?.action??null):null};});
 const cc=ss.map((s,i)=>s.owner==='controller'?i:-1).filter(i=>i>=0),policies=[];
 for(const cp of products(cc.map(i=>ss[i].moves.length))){const choice=new Map(cc.map((i,k)=>[i,cp[k]])),edges=ss.flatMap((s,i)=>s.moves.filter((m,j)=>!choice.has(i)||choice.get(i)===j).map(m=>({from:s.name,action:m.action,to:m.to}))),adj=ns.map(n=>edges.filter(e=>e.from===n).map(e=>ids.get(e.to)));
 const reachable=(root,nongoal=false)=>{const seen=new Set(nongoal?[]:[root]),todo=[root];for(let k=0;k<todo.length;k++)for(const w of adj[todo[k]])if((!nongoal||!ss[w].goal)&&!seen.has(w)){seen.add(w);todo.push(w);}return seen;};
 const reach=ns.map((_,i)=>reachable(i)),non=ns.map((_,i)=>ss[i].goal?new Set():reachable(i,true)),remaining=new Set(ns.map((_,i)=>i).filter(i=>non[i].has(i))),components=[];
 while(remaining.size){const first=Math.min(...remaining),comp=[...remaining].filter(j=>non[first].has(j)&&non[j].has(first)).sort((a,b)=>a-b);components.push(comp);for(const j of comp)remaining.delete(j);}
 const bad=new Set(components.flat()),roots=ns.map((name,i)=>{const br=ns.filter((_,j)=>bad.has(j)&&reach[i].has(j));return {state:name,reachable:ns.filter((_,j)=>reach[i].has(j)),bad_reachable:br,winning:br.length===0};});
 policies.push({index:policies.length,choices:cc.map(i=>({state:ns[i],action:ss[i].moves[choice.get(i)].action})),edges,bad_components:components.map(c=>c.map(i=>ns[i])),roots,winning:roots.filter(r=>r.winning).map(r=>r.state)});
 }
 const canonical_policy=policies.find(p=>states.every(s=>!s.winning||s.controller_choice===null||p.choices.some(c=>c.state===s.name&&c.action===s.controller_choice))).index;
 return {schema:'buchilab-v1',input:data,outer,winning:order(z),losing:ns.filter(x=>!z.has(x)),states,policies,canonical_policy};
}
