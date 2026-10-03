"""Build CyberED weighted knowledge graph from document registry + knowledge core.

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
OUT = DATA / "knowledge_graph.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    docs = load(DOCS)
    core = load(CORE)

    confidence = core["weight_model"]["source_confidence"]
    nodes = list(core["nodes"])
    edges = list(core["edges"])

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

        targets: dict[str, float] = {}

        def link(target: str, weight: float):
            targets[target] = max(weight, targets.get(target, 0.0))

        kind = doc.get("kind", "")
        if kind == "gis":
            link("DOM-GIS", 0.92)
        if kind == "pdn":
            link("DOM-PDN", 0.94)
        if kind == "fstec":
            link("DOM-IB", 0.82)
        if kind == "fsb":
            link("DOM-SKZI", 0.86)
        if kind in {"rkn", "rospotreb"}:
            link("DOM-PDN", 0.82)
        if kind == "gost":
            link("DOM-STANDARDS", 0.88)

        hay = " ".join(
            [
                doc.get("scope", ""),
                doc.get("title", ""),
                *doc.get("tags", []),
            ]
        ).lower()

        if "пдн" in hay or "персональ" in hay:
            link("DOM-PDN", 0.90)
        if "гис" in hay or "госсектор" in hay:
            link("DOM-GIS", 0.88)
        if "кии" in hay:
            link("DOM-KII", 0.92)
        if "скзи" in hay or "крипт" in hay:
            link("DOM-SKZI", 0.90)

        for target, weight in targets.items():
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
        "schema": "cybered.knowledge_graph.v1",
        "generated_from": [
            str(DOCS.relative_to(ROOT)),
            str(CORE.relative_to(ROOT)),
        ],
        "weight_model": core["weight_model"],
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "documents": len(docs.get("documents", [])),
        },
        "nodes": nodes,
        "edges": edges,
    }

    OUT.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"CyberED Knowledge Graph: "
        f"{graph['stats']['nodes']} nodes / "
        f"{graph['stats']['edges']} edges / "
        f"{graph['stats']['documents']} documents"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
