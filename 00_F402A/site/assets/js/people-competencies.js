const state={data:null,selected:null};
const y=document.getElementById("year");if(y)y.textContent=new Date().getFullYear();
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function compMap(){return new Map(state.data.competencies.map(c=>[c.id,c]));}
function renderSummary(){
 const roles=state.data.role_profiles;
 document.getElementById("people-role-count").textContent=roles.length;
 document.getElementById("people-assigned-count").textContent=roles.filter(r=>r.person).length;
 document.getElementById("people-comp-count").textContent=state.data.competencies.length;
 document.getElementById("people-gap-count").textContent=roles.filter(r=>!r.person).length;
}
function renderRoles(){
 const root=document.getElementById("people-role-list");root.innerHTML="";
 state.data.role_profiles.forEach(r=>{
   const b=document.createElement("button");
   b.className="people-role-btn"+(state.selected===r.role_id?" active":"");
   b.innerHTML=`<span>${esc(r.role_id)}</span><strong>${esc(r.role)}</strong><small>${r.person?esc(r.person):"ЛИЦО НЕ НАЗНАЧЕНО"}</small>`;
   b.onclick=()=>{state.selected=r.role_id;renderRoles();renderProfile(r);};
   root.appendChild(b);
 });
}
function renderProfile(role){
 const comps=compMap();
 const root=document.getElementById("people-profile");
 const person=role.person||"Не назначено";
 const assignment=role.person?"VERIFIED / CHECK EVIDENCE":"NOT_ASSIGNED";
 root.innerHTML=`
   <div class="profile-head">
     <div><span class="role-code">${esc(role.role_id)}</span><h2>${esc(role.role)}</h2></div>
     <span class="assignment-state">${assignment}</span>
   </div>
   <div class="person-card">
     <span>КОНКРЕТНОЕ ЛИЦО</span>
     <strong>${esc(person)}</strong>
     <p>${role.evidence?.length?"Основание: "+role.evidence.map(esc).join(" · "):"Приказ / положение / должностная инструкция пока не связаны."}</p>
   </div>
   <h3 class="competency-title">Требуемые компетенции</h3>
   <div class="competency-list">
     ${role.required.map(([id,level])=>{
       const c=comps.get(id)||{title:id,domain:"",sources:[]};
       return `<article class="competency-card">
         <div class="competency-top"><div><span>${esc(c.domain)}</span><strong>${esc(c.title)}</strong></div><b>L${level}</b></div>
         <div class="competency-source-title">Где искать / изучать</div>
         <div class="competency-sources">${(c.sources||[]).map(s=>`<a href="${esc(s.href)}">${esc(s.label)} →</a>`).join("")}</div>
       </article>`;
     }).join("")}
   </div>
   <div class="competency-note">Уровни L1–L5 — внутренняя модель CyberED, а не нормативная квалификационная шкала. Нормативно обязательную квалификацию добавляем только после привязки конкретного источника.</div>
 `;
}
async function load(){
 const r=await fetch("data/people_competencies.json",{cache:"no-store"});state.data=await r.json();
 renderSummary();renderRoles();
 const first=state.data.role_profiles[0];if(first){state.selected=first.role_id;renderRoles();renderProfile(first);}
}
load().catch(e=>{document.getElementById("people-profile").innerHTML="<h2>Ошибка загрузки модели компетенций</h2>";console.error(e);});