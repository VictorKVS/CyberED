document.getElementById("year").textContent = new Date().getFullYear();

const DATA_URL = "data/alina_ib_index.json";

function text(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function renderQueries(items) {
    const root = document.getElementById("query-grid");
    root.innerHTML = "";

    for (const item of items) {
        const card = document.createElement("article");
        card.className = "query-card";
        card.innerHTML = `
            <strong>${item.label}</strong>
            <div class="count">${item.matches}</div>
            <small>совпадений</small>
        `;
        root.appendChild(card);
    }
}

function renderHits(items) {
    const root = document.getElementById("hits-list");
    root.innerHTML = "";

    if (!items.length) {
        root.innerHTML = '<div class="empty-card">Совпадений пока нет.</div>';
        return;
    }

    for (const item of items.slice(0, 60)) {
        const card = document.createElement("article");
        card.className = "hit-card";

        const excerpt = document.createElement("p");
        excerpt.textContent = item.excerpt || "";

        card.innerHTML = `
            <div class="hit-head">
                <strong>${item.filename || "Источник"}</strong>
                <span class="hit-tag">${item.query_label || "ИБ"}</span>
            </div>
        `;
        card.appendChild(excerpt);

        const meta = document.createElement("div");
        meta.className = "hit-meta";
        meta.innerHTML = `
            <span>SOURCE ${item.source_id || "—"}</span>
            <span>${item.locator || "без локатора"}</span>
            <span>CANDIDATE</span>
        `;
        card.appendChild(meta);

        root.appendChild(card);
    }
}

async function loadAlina() {
    try {
        const response = await fetch(DATA_URL, { cache: "no-store" });
        if (!response.ok) throw new Error("snapshot not found");

        const data = await response.json();
        const alina = data.alina || {};
        const track = (alina.security_tracks || [])[0] || {};
        const regulatory = data.regulatory_search || {};

        text("alina-online", alina.online ? "ONLINE" : "OFFLINE");
        text("alina-phase", alina.phase || "—");
        text("security-chunks", track.chunks ?? 0);
        text("security-books", (track.books ?? 0) + (track.references ?? 0));
        text("regulatory-hits", (regulatory.hits || []).length);
        text(
            "generated-at",
            data.generated_at
                ? "Снимок: " + new Date(data.generated_at).toLocaleString("ru-RU")
                : "Время снимка неизвестно."
        );

        renderQueries(regulatory.queries || []);
        renderHits(regulatory.hits || []);
    } catch (error) {
        text("alina-online", "NO SNAPSHOT");
        text("alina-phase", "Запусти automation/START_ALINA_IB_SYNC.ps1");
        document.getElementById("query-grid").innerHTML =
            '<div class="empty-card">Локальный снимок Алины ещё не создан.</div>';
    }
}

loadAlina();
setInterval(loadAlina, 60000);
