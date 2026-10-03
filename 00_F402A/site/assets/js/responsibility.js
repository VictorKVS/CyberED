document.getElementById("year").textContent = new Date().getFullYear();

const LABELS = {
  REQUIREMENT:"Требование",
  OBLIGATION:"Обязанность",
  ROLE:"Роль",
  INTERNAL_DOCUMENT:"ЛНА / приказ / ДИ",
  PERSON:"Лицо",
  ACTION:"Действие",
  EVIDENCE:"Evidence",
  COMPLIANCE_STATUS:"Статус"
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderHierarchy(items) {
  const root = document.getElementById("hierarchy-flow");
  items.forEach(item => {
    const card = el("article", "role-major");
    card.append(el("div", "role-code", item.id));
    card.append(el("h3", "", item.title));
    card.append(el("p", "", item.responsibility));
    card.append(el("span", "state", item.responsibility_status));
    root.append(card);
  });
}

function renderLegal(items) {
  const root = document.getElementById("legal-basis");
  items.forEach(item => {
    const card = el("article", "legal-card");
    card.append(el("strong", "", item.title));
    card.append(el("p", "", item.scope));
    const ul = el("ul");
    item.establishes.forEach(x => ul.append(el("li", "", x)));
    card.append(ul);
    root.append(card);
  });
}

function renderTeam(items) {
  const root = document.getElementById("team-grid");
  items.forEach(item => {
    const card = el("article", "team-card");
    card.append(el("div", "lane", item.lane.toUpperCase()));
    card.append(el("h3", "", item.title));
    const ul = el("ul");
    item.responsibilities.forEach(x => ul.append(el("li", "", x)));
    card.append(ul);
    card.append(el("div", "evidence", "Подтверждение: " + item.evidence.join(" · ") + " · " + item.status));
    root.append(card);
  });
}

function renderTrace(items) {
  const root = document.getElementById("traceability");
  items.forEach((item, index) => {
    const step = el("div", "trace-step");
    step.append(el("strong", "", item));
    step.append(el("small", "", LABELS[item] || item));
    root.append(step);
    if (index < items.length - 1) root.append(el("div", "trace-arrow", "→"));
  });
}

function renderRaci(raci) {
  document.getElementById("raci-note").textContent = raci.note;
  const table = document.getElementById("raci-table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  trh.append(el("th", "", "Процесс / работа"));
  raci.columns.forEach(c => trh.append(el("th", "", c.title)));
  thead.append(trh);
  table.append(thead);

  const tbody = document.createElement("tbody");
  raci.rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.append(el("td", "", row.activity));
    raci.columns.forEach(c => {
      const td = el("td", "", row[c.id] || "—");
      td.dataset.raci = row[c.id] || "";
      tr.append(td);
    });
    tbody.append(tr);
  });
  table.append(tbody);
}

async function load() {
  const response = await fetch("data/responsibility.json", {cache:"no-store"});
  const data = await response.json();

  document.getElementById("model-status").textContent = data.model_status;
  document.getElementById("normative-count").textContent = data.hierarchy.length;
  document.getElementById("team-count").textContent = data.team_roles.length;
  document.getElementById("verified-count").textContent =
    data.team_roles.filter(x => x.status === "VERIFIED").length;

  renderHierarchy(data.hierarchy);
  renderLegal(data.legal_context);
  renderTeam(data.team_roles);
  renderTrace(data.traceability);
  renderRaci(data.raci);
}

load().catch(err => {
  document.getElementById("model-status").textContent = "DATA ERROR";
  console.error(err);
});
