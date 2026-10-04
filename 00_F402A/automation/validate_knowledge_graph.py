from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    graph_name = "knowledge_graph.local.json" if (DATA / "knowledge_graph.local.json").exists() else "knowledge_graph.json"
    graph = load(graph_name)
    node_ids = [n["id"] for n in graph.get("nodes", [])]
    node_set = set(node_ids)
    errors: list[str] = []

    if len(node_ids) != len(node_set):
        errors.append("duplicate node IDs")

    for edge in graph.get("edges", []):
        if edge.get("from") not in node_set:
            errors.append(f"missing edge source: {edge.get('from')}")
        if edge.get("to") not in node_set:
            errors.append(f"missing edge target: {edge.get('to')}")
        weight = edge.get("weight")
        if not isinstance(weight, (int, float)) or not 0 <= weight <= 1:
            errors.append(f"invalid edge weight: {edge}")

    source_path = DATA / "documents_source_linked.local.json"
    if not source_path.exists():
        source_path = DATA / "documents_source_full.json"
    if source_path.exists():
        source = json.loads(source_path.read_text(encoding="utf-8"))
        normalized = load("documents.json")
        normalized_ids = {d["id"] for d in normalized.get("documents", [])}
        for item in source.get("documents", []):
            linked = item.get("normalized_id")
            if linked and linked not in normalized_ids:
                errors.append(
                    f"source {item.get('source_id')} links to missing normalized ID {linked}"
                )

    if errors:
        print("FATHER Knowledge validation: FAILED")
        for error in errors[:100]:
            print(" -", error)
        if len(errors) > 100:
            print(f" ... and {len(errors)-100} more")
        return 1

    print(
        "FATHER Knowledge validation: OK | "
        f"{len(node_ids)} nodes / {len(graph.get('edges', []))} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
