"""PIONEER P02B: dependency and security graph, read-only."""
from topology import build_topology


def build_dependency_graph(model):
    graph = build_topology(model)
    nodes = graph["nodes"]
    edges = graph["edges"]
    ids = {node["id"] for node in nodes}
    errors = []

    for resource in model.get("resources", []):
        source = "resource:" + resource["id"]
        for dep in resource.get("depends_on", []):
            target = "resource:" + dep
            if target not in ids:
                errors.append(f"unknown dependency: {source} -> {target}")
            elif target == source:
                errors.append(f"self dependency: {source}")
            else:
                edges.append({"source": source, "target": target, "relation": "depends_on"})

    for control in model.get("security_controls", []):
        cid = control.get("id")
        target = control.get("protects")
        if not isinstance(cid, str) or not cid:
            errors.append("security control missing id")
            continue
        node_id = "control:" + cid
        if node_id in ids:
            errors.append(f"duplicate control: {cid}")
            continue
        ids.add(node_id)
        nodes.append({"id": node_id, "type": "security_control", "label": cid})
        target_id = "resource:" + target if isinstance(target, str) else ""
        if target_id not in ids:
            errors.append(f"unknown protected resource: {target}")
        else:
            edges.append({"source": node_id, "target": target_id, "relation": "protects"})

    if errors:
        raise ValueError("; ".join(errors))

    dependencies = {}
    for edge in edges:
        if edge["relation"] == "depends_on":
            dependencies.setdefault(edge["source"], []).append(edge["target"])
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            raise ValueError(f"dependency cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for child in dependencies.get(node, []):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in dependencies:
        visit(node)

    graph["schema_version"] = "0.2"
    return graph
