"""Build FATHER/CyberED weighted IT + information security knowledge graph.

CyberED is a consumer of the common FATHER IT/IB knowledge model.
Weights are technical relevance/confidence scores and MUST NOT be interpreted
as legal force, legal hierarchy, applicability, or mandatory priority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
DOCS = DATA / "documents.json"
CORE = DATA / "knowledge_core.json"
PEOPLE = DATA / "people_competencies.json"
SOURCE_CATALOG = DATA / "documents_source_full.json"
OUT = DATA / "knowledge_graph.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def classify_document(doc: dict) -> dict[str, float]:
    targets: dict[str, float] = {}

    def link(target: str, weight: float):
        targets[target] = max(weight, targets.get(target, 0.0))

    kind = doc.get("kind", "")
    hay = " ".join(
        [
            doc.get("code", ""),
            doc.get("scope", ""),
            doc.get("title", ""),
            doc.get("authority", ""),
            *doc.get("tags", []),
        ]
    ).lower()

    # Every source document belongs to the common document/standards domain.
    link("DOM-DOCS", 0.90)

    if kind == "gis":
        link("DOM-GIS", 0.94)
    if kind == "pdn":
        link("DOM-PDN", 0.96)
    if kind == "fstec":
        link("DOM-IB", 0.90)
        link("DOM-GRC", 0.76)
    if kind == "fsb":
        link("DOM-SKZI", 0.88)
        link("DOM-IB", 0.82)
    if kind in {"rkn", "rospotreb"}:
        link("DOM-PDN", 0.84)
        link("DOM-GRC", 0.78)
    if kind == "gost":
        link("DOM-STANDARDS", 0.94)

    rules = [
        (("пдн", "персональн"), "DOM-PDN", 0.92),
        (("гис", "госсектор", "гостех", "смэв", "есиа"), "DOM-GIS", 0.90),
        (("кии", "критическ"), "DOM-KII", 0.94),
        (("скзи", "крипт", "электронн подпис", "pki"), "DOM-SKZI", 0.92),
        (("облач", "cloud", "kubernetes", "контейнер", "виртуализ"), "DOM-CLOUD", 0.84),
        (("искусственн интеллект", "машинн обуч", "нейросет", "llm", "mlops", "rag"), "DOM-AI", 0.84),
        (("разработ", "программ", "жизненного цикла", "secure sdlc", "appsec", "devsecops"), "DOM-DEV", 0.80),
        (("аудит", "провер", "оценк соответств", "контрол"), "DOM-IB-AUDIT", 0.72),
        (("ит-аудит", "it audit", "управление сервис", "it service"), "DOM-IT-AUDIT", 0.72),
        (("уязвим", "проникнов", "pentest", "red team"), "DOM-PENTEST", 0.80),
        (("архитект", "проектирован", "меры защиты", "требования по защите"), "DOM-SEC-ARCH", 0.76),
        (("инцидент", "мониторинг", "регистрация событий", "журналирован", "госсопка", "реагирован"), "DOM-SOC", 0.84),
        (("риск", "норматив", "compliance", "политик", "обязательн требован"), "DOM-GRC", 0.78),
        (("видеонаблю", "скуд", "vms", "psim", "охран", "периметр", "физическ безопас", "биометр"), "DOM-ITSO", 0.80),
        (("информационн технолог", "сеть", "сервер", "баз данных", "storage", "linux", "windows"), "DOM-IT", 0.68),
    ]

    for needles, target, weight in rules:
        if any(needle in hay for needle in needles):
            link(target, weight)

    return targets


def main() -> int:
    docs = load(DOCS)
    core = load(CORE)
    people = load(PEOPLE)
    source_catalog = load(SOURCE_CATALOG) if SOURCE_CATALOG.exists() else {"documents": []}

    confidence = core["weight_model"]["source_confidence"]
    nodes = list(core["nodes"])
    edges = list(core["edges"])
    node_ids = {n["id"] for n in nodes}

    for competency in people.get("competencies", []):
        if competency["id"] not in node_ids:
            nodes.append(
                {
                    "id": competency["id"],
                    "label": competency["title"],
                    "type": "competency",
                    "weight": 0.82,
                    "origin": "father_people_competencies",
                    "scope": competency.get("domain", ""),
                }
            )
            node_ids.add(competency["id"])

    for role in people.get("role_profiles", []):
        if role["role_id"] not in node_ids:
            nodes.append(
                {
                    "id": role["role_id"],
                    "label": role["role"],
                    "type": "role",
                    "weight": 0.88,
                    "origin": "father_people_competencies",
                    "scope": role.get("role_family", ""),
                }
            )
            node_ids.add(role["role_id"])

        domain_id = role.get("domain_id")
        if domain_id:
            edges.append(
                {
                    "from": role["role_id"],
                    "to": domain_id,
                    "type": "works_in_domain",
                    "weight": 0.92,
                    "auto": False,
                }
            )

        for competency_id, level in role.get("required", []):
            edges.append(
                {
                    "from": role["role_id"],
                    "to": competency_id,
                    "type": "requires_competency",
                    "weight": round(float(level) / 5.0, 2),
                    "level": level,
                    "auto": False,
                }
            )

        if role.get("person"):
            person_id = "PERSON-" + role["role_id"].replace("ROLE-", "")
            if person_id not in node_ids:
                nodes.append(
                    {
                        "id": person_id,
                        "label": role["person"],
                        "type": "person",
                        "weight": 0.90,
                        "origin": "verified_internal_assignment",
                    }
                )
                node_ids.add(person_id)
            edges.append(
                {
                    "from": person_id,
                    "to": role["role_id"],
                    "type": "assigned_to_role",
                    "weight": 1.0,
                    "auto": False,
                }
            )

    for source_doc in source_catalog.get("documents", []):
        source_id = source_doc["source_id"]
        nodes.append(
            {
                "id": source_id,
                "label": source_doc.get("title", source_id),
                "type": "source_document",
                "title": source_doc.get("title", ""),
                "kind": source_doc.get("kind", ""),
                "status": "SOURCE_EXACT",
                "weight": 0.55,
                "origin": "source_catalog",
                "scope": source_doc.get("section", ""),
            }
        )
        edges.append(
            {
                "from": source_id,
                "to": "DOM-DOCS",
                "type": "source_listed_in",
                "weight": 0.80,
                "auto": True,
            }
        )

    for doc in docs.get("documents", []):
        nodes.append(
            {
                "id": doc["id"],
                "label": doc["code"],
                "type": "document",
                "title": doc.get("title", ""),
                "kind": doc.get("kind", ""),
                "status": doc.get("status", ""),
                "weight": confidence.get(doc.get("status"), 0.60),
                "origin": "document_registry",
                "scope": doc.get("scope", ""),
            }
        )

        for target, weight in classify_document(doc).items():
            edges.append(
                {
                    "from": doc["id"],
                    "to": target,
                    "type": "classified_as",
                    "weight": weight,
                    "auto": True,
                }
            )

    graph = {
        "schema": "father.it_ib.knowledge_graph.v2",
        "owner": "FATHER",
        "consumer": "CyberED",
        "generated_from": [
            str(DOCS.relative_to(ROOT)),
            str(CORE.relative_to(ROOT)),
            str(PEOPLE.relative_to(ROOT)),
            *([str(SOURCE_CATALOG.relative_to(ROOT))] if SOURCE_CATALOG.exists() else []),
        ],
        "weight_model": core["weight_model"],
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "documents": len(docs.get("documents", [])),
            "roles": len(people.get("role_profiles", [])),
            "competencies": len(people.get("competencies", [])),
            "source_documents": len(source_catalog.get("documents", [])),
        },
        "nodes": nodes,
        "edges": edges,
    }

    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"FATHER IT/IB Knowledge Graph: "
        f"{graph['stats']['nodes']} nodes / "
        f"{graph['stats']['edges']} edges / "
        f"{graph['stats']['documents']} documents"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
