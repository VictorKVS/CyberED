const year=document.getElementById("year");if(year)year.textContent=new Date().getFullYear();
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
async function load(){
 const r=await fetch("data/web_security_resources.json",{cache:"no-store"});
 if(!r.ok)throw new Error("web security resources unavailable");
 const data=await r.json();

 document.getElementById("ws-flow").innerHTML=
   '<div class="ws-flow-title">LEARNING FLOW</div>'+
   '<div class="ws-flow-grid">'+(data.learning_flow||[]).map((x,i)=>`<div><span>${String(i+1).padStart(2,"0")}</span><strong>${esc(x)}</strong></div>`).join("")+'</div>';

 const root=document.getElementById("ws-groups");
 root.innerHTML=(data.groups||[]).map(group=>`
   <section class="ws-group">
     <div class="ws-group-head"><div><span>${esc(group.id)}</span><h2>${esc(group.title)}</h2></div>${group.legal_note?`<p>${esc(group.legal_note)}</p>`:""}</div>
     <div class="ws-card-grid">
       ${(group.resources||[]).map(x=>`
         <article class="ws-card">
           <div class="ws-card-top"><span>${esc(x.kind)}</span><code>${esc(x.id)}</code></div>
           <h3>${esc(x.title)}</h3>
           ${x.purpose?`<p>${esc(x.purpose)}</p>`:""}
           ${x.categories?`<div class="ws-tags">${x.categories.map(t=>`<b>${esc(t)}</b>`).join("")}</div>`:""}
           ${x.scope_rule?`<div class="ws-scope">${esc(x.scope_rule)}</div>`:""}
           ${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">Открыть ресурс ↗</a>`:'<span class="ws-muted">URL не указан в исходном материале</span>'}
         </article>`).join("")}
     </div>
   </section>`).join("");
}
load().catch(err=>{document.getElementById("ws-groups").innerHTML='<section class="ws-group"><h2>Ошибка загрузки материалов</h2></section>';console.error(err);});