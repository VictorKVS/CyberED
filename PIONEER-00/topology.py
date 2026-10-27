"""PIONEER P02A: topology graph from a validated architecture."""
import json
from pathlib import Path
from pioneer import validate


def build_topology(model):
    errors = validate(model)
    if errors:
        raise ValueError("; ".join(errors))

    nodes = []
    edges = []
    for network in model["networks"]:
        nodes.append({
            "id": "network:" + network["id"],
            "type": "network",
            "label": network["id"],
            "cidr": network["cidr"],
        })
    for resource in model["resources"]:
        nodes.append({
            "id": "resource:" + resource["id"],
            "type": resource["kind"],
            "label": resource["id"],
        })
        edges.append({
            "source": "resource:" + resource["id"],
            "target": "network:" + resource["network"],
            "relation": "connected_to",
        })
    return {
        "project_id": model["project_id"],
        "schema_version": "0.1",
        "nodes": nodes,
        "edges": edges,
    }


if __name__ == "__main__":
    model = json.loads(Path("examples/architecture.json").read_text(encoding="utf-8"))
    topology = build_topology(model)
    Path("topology.json").write_text(
        json.dumps(topology, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"TOPOLOGY: nodes={len(topology['nodes'])}, edges={len(topology['edges'])}")
