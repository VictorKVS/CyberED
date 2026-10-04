const state={
  mode:"normalized",
  filter:"all",
  status:"all",
  query:"",
  selected:null,
  normalized:null,
  source:null
};

const year=document.getElementById("year");
if(year) year.textContent=new Date().getFullYear();

function esc(s){
  return String(s??"").replace(/[&<>"']/g,m=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m]));
}

function statusClass(s){
  return "badge-"+String(s||"").toLowerCase();
}

function activeDocuments(){
  if(state.mode==="source" && state.source) return state.source.documents||[];
  return state.normalized?.documents||[];
}

function visibleDocs(){
  const q=state.query.trim().toLowerCase();
  return activeDocuments().filter(d=>{
    const kind=d.kind||"other";
    const filterOk=state.filter==="all"||kind===state.filter;
    const statusOk=state.mode==="source"||state.status==="all"||d.status===state.status;
    const hay=state.mode==="source"
      ? [d.title,d.section,d.kind,d.source_id].join(" ").toLowerCase()
      : [d.code,d.title,d.authority,d.scope,...(d.tags||[])].join(" ").toLowerCase();
    return filterOk&&statusOk&&(!q||hay.includes(q));
  });
}

function setStat(id,value){
  const node=document.getElementById(id);
  if(node) node.textContent=value;
}

function renderStats(){
  const all=activeDocuments();
  setStat("registry-total",all.length);
  setStat("registry-gost",all.filter(x=>x.kind==="gost").length);

  if(state.mode==="source"){
    setStat("registry-verified","—");
    setStat("registry-listed",all.length);
  }else{
    setStat("registry-verified",all.filter(x=>x.status==="VERIFIED").length);
    setStat("registry-listed",all.filter(x=>x.status==="SOURCE_LISTED").length);
  }
}

function renderList(){
  const list=document.getElementById("docs-list");
  const docs=visibleDocs();
  renderStats();
  document.getElementById("doc-count").textContent=docs.length;
  list.innerHTML="";

  if(!docs.length){
    list.innerHTML='<div class="doc-row"><p>Ничего не найдено.</p></div>';
    return;
  }

  docs.forEach(d=>{
    const id=state.mode==="source"?d.source_id:d.id;
    const row=document.createElement("article");
    row.className="doc-row"+(state.selected===id?" active":"");

    if(state.mode==="source"){
      row.innerHTML=
        `<div class="doc-row-top">
          <span class="doc-row-code">${esc(d.source_id)} · строка ${esc(d.source_line)}</span>
          <span class="doc-row-status badge-source_exact">SOURCE_EXACT</span>
        </div>
        <h3>${esc(d.title)}</h3>
        <p>${esc(d.section)} · ${esc(d.kind)}</p>`;
    }else{
      row.innerHTML=
        `<div class="doc-row-top">
          <span class="doc-row-code">${esc(d.code)}</span>
          <span class="doc-row-status ${statusClass(d.status)}">${esc(d.status)}</span>
        </div>
        <h3>${esc(d.title)}</h3>
        <p>${esc(d.authority)} · ${esc(d.scope)}</p>`;
    }

    row.onclick=()=>{
      state.selected=id;
      renderList();
      renderDetail(d);
    };
    list.appendChild(row);
  });
}

function renderDetail(d){
  const root=document.getElementById("doc-detail");
  root.classList.remove("empty-detail");

  if(state.mode==="source"){
    root.innerHTML=`
      <div class="detail-kicker">${esc(d.source_id)} · SOURCE_EXACT</div>
      <h2>${esc(d.title)}</h2>
      <div class="detail-grid">
        <div class="detail-box"><span>Раздел исходного справочника</span><strong>${esc(d.section)}</strong></div>
        <div class="detail-box"><span>Строка источника</span><strong>${esc(d.source_line)}</strong></div>
        <div class="detail-box"><span>Технический класс</span><strong>${esc(d.kind)}</strong></div>
        <div class="detail-box"><span>Нормализованный ID</span><strong>${esc(d.normalized_id||"НЕ СВЯЗАН")}</strong></div>
      </div>
      <div class="detail-section">
        <h3>Статус обработки Алиной</h3>
        <p class="detail-summary">Исходная запись сохранена без вывода о действующей редакции, применимости или обязательности. Следующий этап: сопоставление с нормализованным документом → версия → пункт → requirement candidate → verification.</p>
      </div>
      <a class="requirement-link" href="knowledge.html">Открыть FATHER Knowledge Core →</a>`;
    return;
  }

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
    ${d.source_url?`<a class="requirement-link" href="${esc(d.source_url)}" target="_blank" rel="noopener">Официальный / проверочный источник ↗</a>`:""}
    <a class="requirement-link" href="requirements.html">Открыть контур требований →</a>`;
}

function resetDetail(){
  const root=document.getElementById("doc-detail");
  root.classList.add("empty-detail");
  root.innerHTML=`
    <div class="detail-placeholder">
      <span>FATHER DOCUMENT LIBRARY</span>
      <h2>Выберите документ</h2>
      <p>Откроется карточка текущего слоя: исходная запись либо нормализованный документ.</p>
    </div>`;
}

function setMode(mode){
  if(mode==="source"&&!state.source) return;

  state.mode=mode;
  state.selected=null;
  state.status="all";

  document.querySelectorAll(".catalog-mode-btn").forEach(btn=>{
    btn.classList.toggle("active",btn.dataset.mode===mode);
  });
  document.querySelectorAll(".status-btn").forEach(btn=>{
    btn.classList.toggle("active",btn.dataset.status==="all");
    btn.disabled=mode==="source";
  });

  resetDetail();
  renderList();
}

async function load(){
  const normalized=await fetch("data/documents.json",{cache:"no-store"});
  if(!normalized.ok) throw new Error("documents.json unavailable");
  state.normalized=await normalized.json();

  const sourceState=document.getElementById("source-catalog-state");
  try{
    const source=await fetch("data/documents_source_full.json",{cache:"no-store"});
    if(source.ok){
      state.source=await source.json();
      const count=state.source.stats?.documents??state.source.documents?.length??0;
      const sections=state.source.stats?.sections??state.source.sections?.length??0;
      sourceState.textContent=`SOURCE: ${count} документов · ${sections} разделов`;
      sourceState.classList.add("ready");
    }else{
      sourceState.textContent="SOURCE: запусти IMPORT_SOURCE_CATALOG.ps1";
    }
  }catch(_){
    sourceState.textContent="SOURCE: запусти IMPORT_SOURCE_CATALOG.ps1";
  }

  renderList();
}

document.getElementById("doc-search").addEventListener("input",e=>{
  state.query=e.target.value;
  renderList();
});

document.querySelectorAll(".filter-btn").forEach(btn=>btn.onclick=()=>{
  document.querySelectorAll(".filter-btn").forEach(x=>x.classList.remove("active"));
  btn.classList.add("active");
  state.filter=btn.dataset.filter;
  renderList();
});

document.querySelectorAll(".status-btn").forEach(btn=>btn.onclick=()=>{
  if(state.mode==="source") return;
  document.querySelectorAll(".status-btn").forEach(x=>x.classList.remove("active"));
  btn.classList.add("active");
  state.status=btn.dataset.status;
  renderList();
});

document.querySelectorAll(".catalog-mode-btn").forEach(btn=>btn.onclick=()=>{
  if(btn.dataset.mode==="source"&&!state.source){
    const node=document.getElementById("source-catalog-state");
    node.textContent="Сначала импортируй исходный TXT через automation/IMPORT_SOURCE_CATALOG.ps1";
    return;
  }
  setMode(btn.dataset.mode);
});

load().catch(err=>{
  document.getElementById("docs-list").innerHTML='<div class="doc-row"><p>Ошибка загрузки реестра документов.</p></div>';
  console.error(err);
});