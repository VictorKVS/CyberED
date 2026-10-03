const SVG_NS="http://www.w3.org/2000/svg";
const state={graph:null,domain:"PDN",query:"",nodes:[],edges:[]};
const DOMAIN_IDS={PDN:"DOM-PDN",GIS:"DOM-GIS",KII:"DOM-KII",SKZI:"DOM-SKZI",STANDARDS:"DOM-STANDARDS"};
const year=document.getElementById("year");if(year)year.textContent=new Date().getFullYear();

function el(name,attrs={}){const n=document.createElementNS(SVG_NS,name);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}

function subgraph(){
 const root=DOMAIN_IDS[state.domain];
 const adj=new Map();
 for(const e of state.graph.edges){
  if(!adj.has(e.from))adj.set(e.from,[]);
  if(!adj.has(e.to))adj.set(e.to,[]);
  adj.get(e.from).push(e.to);adj.get(e.to).push(e.from);
 }
 const keep=new Set([root]);let frontier=[root];
 for(let depth=0;depth<2;depth++){const next=[];for(const id of frontier){for(const n of adj.get(id)||[]){if(!keep.has(n)){keep.add(n);next.push(n);}}}frontier=next;}
 // Keep the deep PDN model even if an edge is 3 hops away.
 if(state.domain==="PDN") for(const n of state.graph.nodes) if(n.id.startsWith("PDN-")||n.id.startsWith("ROLE-")) keep.add(n.id);
 let nodes=state.graph.nodes.filter(n=>keep.has(n.id));
 const q=state.query.trim().toLowerCase();
 if(q) nodes=nodes.filter(n=>[n.label,n.title,n.scope,n.status,n.type].join(" ").toLowerCase().includes(q));
 const ids=new Set(nodes.map(n=>n.id));
 const edges=state.graph.edges.filter(e=>ids.has(e.from)&&ids.has(e.to));
 state.nodes=nodes;state.edges=edges;
}

function layout(nodes){
 const groups={document:[],domain:[],system:[],data:[],knowledge:[],control_family:[],process:[],artifact:[],role:[]};
 for(const n of nodes)(groups[n.type]||groups.knowledge).push(n);
 const columns=[
  ["document"],["domain"],["system","data","knowledge"],["control_family","process"],["role","artifact"]
 ];
 const pos=new Map();
 columns.forEach((types,ci)=>{
   const arr=types.flatMap(t=>groups[t]||[]);
   const x=90+ci*255;
   arr.forEach((n,i)=>{const y=55+(i+1)*(610/(arr.length+1));pos.set(n.id,{x,y});});
 });
 return pos;
}

function render(){
 subgraph();
 document.getElementById("kg-nodes").textContent=state.graph.stats.nodes;
 document.getElementById("kg-edges").textContent=state.graph.stats.edges;
 document.getElementById("kg-docs").textContent=state.graph.stats.documents;
 document.getElementById("kg-mode").textContent=state.domain==="PDN"?"ПДн":state.domain;
 renderList();renderSvg();
}

function renderList(){
 const root=document.getElementById("kg-node-list");root.innerHTML="";
 const sorted=[...state.nodes].sort((a,b)=>(b.weight||0)-(a.weight||0));
 for(const n of sorted.slice(0,120)){
   const row=document.createElement("div");row.className="kg-node-row";
   row.innerHTML=`<strong>${esc(n.label||n.id)}</strong><span>${esc(n.type)} · w=${Number(n.weight||0).toFixed(2)}</span>`;
   row.onclick=()=>showDetail(n.id);root.appendChild(row);
 }
}

function renderSvg(){
 const svg=document.getElementById("kg-canvas");svg.innerHTML="";svg.classList.add("kg-canvas");
 const pos=layout(state.nodes);const byId=new Map(state.nodes.map(n=>[n.id,n]));
 for(const e of state.edges){
  const a=pos.get(e.from),b=pos.get(e.to);if(!a||!b)continue;
  const line=el("line",{x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:"kg-edge","stroke-width":(0.6+(e.weight||.5)*3).toFixed(2),opacity:(0.22+(e.weight||.5)*.62).toFixed(2)});
  line.addEventListener("click",()=>showEdge(e));svg.appendChild(line);
 }
 for(const n of state.nodes){
  const p=pos.get(n.id);if(!p)continue;
  const g=el("g",{class:"kg-node "+n.type,transform:`translate(${p.x} ${p.y})`});
  const r=8+(n.weight||.5)*10;
  g.appendChild(el("circle",{cx:0,cy:0,r:r.toFixed(1)}));
  const t=el("text",{x:r+5,y:3});t.textContent=(n.label||n.id).slice(0,30);g.appendChild(t);
  const w=el("text",{x:r+5,y:14,class:"kg-weight"});w.textContent="w="+Number(n.weight||0).toFixed(2);g.appendChild(w);
  g.addEventListener("click",()=>showDetail(n.id));svg.appendChild(g);
 }
}

function showDetail(id){
 const n=state.graph.nodes.find(x=>x.id===id);if(!n)return;
 const links=state.graph.edges.filter(e=>e.from===id||e.to===id).sort((a,b)=>(b.weight||0)-(a.weight||0));
 const root=document.getElementById("kg-detail");
 root.innerHTML=`<div class="kg-pane-title">NODE DETAIL</div><h2>${esc(n.label||n.id)}</h2>
 <div class="kg-meta">
  <div><span>TYPE</span><strong>${esc(n.type)}</strong></div>
  <div><span>NODE WEIGHT</span><strong>${Number(n.weight||0).toFixed(2)}</strong></div>
  <div><span>ORIGIN</span><strong>${esc(n.origin||"—")}</strong></div>
  ${n.status?`<div><span>SOURCE STATUS</span><strong>${esc(n.status)}</strong></div>`:""}
 </div>
 <p>${esc(n.title||n.scope||"")}</p>
 <h3>Связи</h3><ul class="kg-links">${links.slice(0,24).map(e=>{const other=e.from===id?e.to:e.from;const on=state.graph.nodes.find(x=>x.id===other);return `<li>${esc(e.type)} → ${esc(on?.label||other)} <span class="kg-pill">w=${Number(e.weight||0).toFixed(2)}</span></li>`;}).join("")}</ul>`;
}

function showEdge(e){
 const a=state.graph.nodes.find(n=>n.id===e.from),b=state.graph.nodes.find(n=>n.id===e.to);
 const root=document.getElementById("kg-detail");
 root.innerHTML=`<div class="kg-pane-title">EDGE DETAIL</div><h2>${esc(e.type)}</h2><p>${esc(a?.label||e.from)} → ${esc(b?.label||e.to)}</p><div class="kg-meta"><div><span>EDGE WEIGHT</span><strong>${Number(e.weight||0).toFixed(2)}</strong></div><div><span>AUTO</span><strong>${e.auto?"YES":"NO"}</strong></div></div>`;
}

async function load(){
 const r=await fetch("data/knowledge_graph.json",{cache:"no-store"});state.graph=await r.json();render();
}
document.querySelectorAll(".kg-filter").forEach(b=>b.onclick=()=>{document.querySelectorAll(".kg-filter").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.domain=b.dataset.domain;state.query="";document.getElementById("kg-search").value="";render();});
document.getElementById("kg-search").addEventListener("input",e=>{state.query=e.target.value;render();});
load().catch(err=>{document.getElementById("kg-detail").innerHTML="<h2>Ошибка загрузки графа</h2>";console.error(err);});