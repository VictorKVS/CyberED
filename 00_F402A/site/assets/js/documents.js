const state={filter:"all",status:"all",query:"",selected:null,data:null};
const year=document.getElementById("year"); if(year) year.textContent=new Date().getFullYear();

function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function visibleDocs(){
  const q=state.query.trim().toLowerCase();
  return state.data.documents.filter(d=>{
    const f=state.filter==="all"||d.kind===state.filter;
    const s=state.status==="all"||d.status===state.status;
    const hay=[d.code,d.title,d.authority,d.scope,...(d.tags||[])].join(" ").toLowerCase();
    return f&&s&&(!q||hay.includes(q));
  });
}
function statusClass(s){return "badge-"+String(s).toLowerCase();}
function renderList(){
  const list=document.getElementById("docs-list"); const docs=visibleDocs();
  document.getElementById("doc-count").textContent=docs.length;
  list.innerHTML="";
  if(!docs.length){list.innerHTML='<div class="doc-row"><p>Ничего не найдено.</p></div>';return;}
  docs.forEach(d=>{
    const row=document.createElement("article"); row.className="doc-row"+(state.selected===d.id?" active":"");
    row.innerHTML=`<div class="doc-row-top"><span class="doc-row-code">${esc(d.code)}</span><span class="doc-row-status ${statusClass(d.status)}">${esc(d.status)}</span></div><h3>${esc(d.title)}</h3><p>${esc(d.authority)} · ${esc(d.scope)}</p>`;
    row.onclick=()=>{state.selected=d.id;renderList();renderDetail(d);};
    list.appendChild(row);
  });
}
function renderDetail(d){
  const root=document.getElementById("doc-detail"); root.classList.remove("empty-detail");
  root.innerHTML=`
    <div class="detail-kicker">${esc(d.id)} · ${esc(d.code)}</div>
    <h2>${esc(d.title)}</h2>
    <p class="detail-summary">${esc(d.summary)}</p>
    <div class="detail-grid">
      <div class="detail-box"><span>Орган / источник</span><strong>${esc(d.authority)}</strong></div>
      <div class="detail-box"><span>Статус проверки</span><strong class="${statusClass(d.status)}">${esc(d.status)}</strong></div>
      <div class="detail-box"><span>Редакция</span><strong>${esc(d.edition)}</strong></div>
      <div class="detail-box"><span>Область</span><strong>${esc(d.scope)}</strong></div>
    </div>
    <div class="detail-section"><h3>Теги / применимость</h3><ul>${(d.tags||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>
    <div class="detail-section"><h3>Связанные требования</h3><p class="detail-summary">${d.requirements?.length?d.requirements.map(esc).join(", "):"Пока не атомизированы. Алина должна создать verified requirements из проверенного текста."}</p></div>
    <a class="requirement-link" href="requirements.html">Открыть контур требований →</a>`;
}
async function load(){
 const r=await fetch("data/documents.json",{cache:"no-store"}); state.data=await r.json(); renderList();
}
document.getElementById("doc-search").addEventListener("input",e=>{state.query=e.target.value;renderList();});
document.querySelectorAll(".filter-btn").forEach(b=>b.onclick=()=>{document.querySelectorAll(".filter-btn").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.filter=b.dataset.filter;renderList();});
document.querySelectorAll(".status-btn").forEach(b=>b.onclick=()=>{document.querySelectorAll(".status-btn").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.status=b.dataset.status;renderList();});
load().catch(err=>{document.getElementById("docs-list").innerHTML='<div class="doc-row"><p>Ошибка загрузки реестра документов.</p></div>';console.error(err);});