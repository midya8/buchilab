/* Action-labelled simple-walk witnesses, separate from v1 report shape. */
import {analyze} from './engine.js';
export function lassos(data){
 const r=analyze(data),ss=r.input.states,ns=ss.map(s=>s.name),n=ns.length,ng=new Set(ss.filter(s=>!s.goal).map(s=>s.name));
 function walk(edges,start,end,cycle=false){if(start===end&&!cycle)return [];let frontier=[{vertices:[start],path:[]}];for(let depth=0;depth<(cycle?n:n-1);depth++){const next=[];for(const f of frontier)for(const e of edges){if(e.from!==f.vertices.at(-1))continue;if(e.to===end)return [...f.path,{...e}];if(!f.vertices.includes(e.to))next.push({vertices:[...f.vertices,e.to],path:[...f.path,{...e}]});}frontier=next;}return null;}
 const policies=r.policies.map(p=>{const non=p.edges.filter(e=>ng.has(e.from)&&ng.has(e.to));return {index:p.index,choices:p.choices,roots:p.roots.map(root=>{let lasso=null;if(!root.winning){for(const anchor of ns){if(!ng.has(anchor))continue;const cycle=walk(non,anchor,anchor,true);if(cycle===null)continue;const prefix=walk(p.edges,root.state,anchor);if(prefix!==null){lasso={anchor,prefix,cycle};break;}}if(lasso===null)throw Error('Missing witness');}return {state:root.state,winning:root.winning,lasso};})};});
 return {schema:'buchilab-lassos-v1',input:r.input,policies};
}
