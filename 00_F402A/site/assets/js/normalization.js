const state={data:null,candidates:null,candidateBySource:new Map(),status:"all",query:"",selected:null};
const year=document.getElementById("year");if(year)year.textContent=new Date().getFullYear();
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function visible(){
 const q=state.query.trim().toLowerCase();
 return (state.data?.items||[]).filter(x=>{
  const ok=state.status==="all"||x.queue_status===state.status;
  const hay=[x.source_id,x.section,x.kind,x.authority_family,x.act_date,x.act_number,x.short_title,x.raw_title].join(" ").toLowerCase();
  return ok&&(!q||hay.includes(q));
 });
}
function render(){
 const items=visible(),stats=state.data?.stats||{};
 document.getElementById("nq-total").textContent=stats.total||0;
 document.getElementById("nq-review").textContent=stats.review_required||0;
 document.getElementById("nq-normalize").textContent=stats.normalization_required||0;
 document.getElementById("nq-visible").textContent=items.length;
 document.getElementById("nq-candidates").textContent=state.candidates?.stats?.create_candidates||0;
 const root=document.getElementById("nq-list");root.innerHTML="";
 if(!items.length){root.innerHTML='<div class="nq-row"><p>Очередь пуста или ничего не найдено.</p></div>';return;}
 for(const x of items){
  const row=document.createElement("article");
  row.className="nq-row"+(state.selected===x.source_id?" active":"");
  row.innerHTML=`<div class="nq-row-top"><span>${esc(x.source_id)} · ${esc(x.section)}</span><b class="${x.queue_status==="REVIEW_REQUIRED"?"review":"normalize"}">${esc(x.queue_status)}</b></div>
  <h3>${esc(x.short_title||x.raw_title)}</h3>
  <p>${esc(x.authority_family||"other")} · № ${esc(x.act_number||"—")} · ${esc(x.act_date||"дата не распознана")}</p>`;
  row.onclick=()=>{state.selected=x.source_id;render();detail(x);};
  root.appendChild(row);
 }
}
function detail(x){
 const candidates=(x.candidates||[]).map(c=>`<li><strong>${esc(c.id)}</strong><span>score ${Number(c.score||0).toFixed(3)}</span></li>`).join("");
 const draft=state.candidateBySource.get(x.source_id);
 const draftHtml=draft?`<div class="nq-section"><h3>Черновая normalized-карточка</h3>
 <ul>
  <li><strong>CODE</strong><span>${esc(draft.proposed_document?.code||"—")}</span></li>
  <li><strong>TITLE</strong><span>${esc(draft.proposed_document?.title||"—")}</span></li>
  <li><strong>AUTHORITY</strong><span>${esc(draft.proposed_document?.authority||"—")}</span></li>
  <li><strong>EDITION</strong><span>${esc(draft.proposed_document?.edition||"—")}</span></li>
  <li><strong>STATE</strong><span>${esc(draft.state||"CANDIDATE")}</span></li>
 </ul>
 <p>Флаги: ${(draft.risk_flags||[]).length?(draft.risk_flags||[]).map(esc).join(", "):"нет критичных флагов"}</p>
 </div>`:"";
 document.getElementById("nq-detail").innerHTML=`<div class="nq-kicker">${esc(x.source_id)} · ${esc(x.queue_status)}</div>
 <h2>${esc(x.short_title||x.raw_title)}</h2>
 <div class="nq-grid">
  <div><span>Раздел</span><strong>${esc(x.section)}</strong></div>
  <div><span>Класс</span><strong>${esc(x.kind)}</strong></div>
  <div><span>Орган / family</span><strong>${esc(x.authority_family)}</strong></div>
  <div><span>Номер</span><strong>${esc(x.act_number||"—")}</strong></div>
  <div><span>Дата</span><strong>${esc(x.act_date||"—")}</strong></div>
  <div><span>Строка SOURCE</span><strong>${esc(x.source_line)}</strong></div>
 </div>
 <div class="nq-section"><h3>Исходная запись</h3><p>${esc(x.raw_title)}</p></div>
 <div class="nq-section"><h3>Кандидаты normalized</h3>${candidates?`<ul>${candidates}</ul>`:"<p>Кандидатов нет — требуется создание новой нормализованной карточки.</p>"}</div>
 ${draftHtml}
 <div class="nq-rule">SOURCE_FOUND ≠ REQUIREMENT_VERIFIED</div>`;
}
async function load(){
 try{
  const r=await fetch("data/source_normalization_queue.local.json",{cache:"no-store"});
  if(!r.ok)throw new Error("queue missing");
  state.data=await r.json();

  try{
   const cr=await fetch("data/normalization_candidates.local.json",{cache:"no-store"});
   if(cr.ok){
    state.candidates=await cr.json();
    state.candidateBySource=new Map(
      (state.candidates.create_candidates||[]).map(x=>[x.source_id,x])
    );
   }
  }catch(_){}

  render();
 }catch(err){
  document.getElementById("nq-list").innerHTML='<div class="nq-row"><h3>Локальная очередь ещё не создана</h3><p>Запусти automation/SYNC_FATHER_KNOWLEDGE.ps1.</p></div>';
  console.error(err);
 }
}
document.querySelectorAll(".nq-filter").forEach(b=>b.onclick=()=>{document.querySelectorAll(".nq-filter").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.status=b.dataset.status;render();});
document.getElementById("nq-search").addEventListener("input",e=>{state.query=e.target.value;render();});
load();