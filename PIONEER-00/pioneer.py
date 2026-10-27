"""PIONEER P01: offline architecture validator and TIMA handoff generator.

No infrastructure writes. Python 3.12 standard library only.
"""
import argparse
import ipaddress
import json
from pathlib import Path


def validate(model):
    errors = []
    required = ("project_id", "schema_version", "architecture_revision",
                "target_environment", "networks", "resources",
                "network_policy", "acceptance_tests")
    for key in required:
        if key not in model:
            errors.append(f"missing field: {key}")
    networks = {}
    for net in model.get("networks", []):
        nid = net.get("id")
        if not nid or nid in networks:
            errors.append(f"duplicate or missing network id: {nid}")
            continue
        try:
            cidr = ipaddress.ip_network(net["cidr"], strict=True)
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"invalid CIDR for {nid}: {exc}")
            continue
        for existing_id, existing_cidr in networks.items():
            if cidr.overlaps(existing_cidr):
                errors.append(f"overlapping networks: {nid} and {existing_id}")
        networks[nid] = cidr
    seen = set()
    for resource in model.get("resources", []):
        rid = resource.get("id")
        if not rid or rid in seen:
            errors.append(f"duplicate or missing resource id: {rid}")
        seen.add(rid)
        if resource.get("network") not in networks:
            errors.append(f"unknown network for {rid}: {resource.get('network')}")
        if not isinstance(resource.get("cpu"), int) or resource["cpu"] < 1:
            errors.append(f"invalid cpu for {rid}")
        if not isinstance(resource.get("memory_gb"), (int, float)) or resource["memory_gb"] <= 0:
            errors.append(f"invalid memory_gb for {rid}")
    if model.get("network_policy", {}).get("default_action") != "deny":
        errors.append("network_policy.default_action must be deny")
    if not model.get("acceptance_tests"):
        errors.append("acceptance_tests must not be empty")
    return errors


def build_handoff(model):
    return {
        "project_id": model["project_id"],
        "schema_version": model["schema_version"],
        "architecture_revision": model["architecture_revision"],
        "target_environment": model["target_environment"],
        "resources": model["resources"],
        "network_policy": model["network_policy"],
        "acceptance_tests": model["acceptance_tests"],
        "approval_status": "READY_FOR_REVIEW",
        "evidence_refs": [],
        "source_agent": "AG-005",
        "target_agent": "AG-003",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("handoff-to-tima.json"))
    args = parser.parse_args()
    model = json.loads(args.input.read_text(encoding="utf-8"))
    errors = validate(model)
    report = {"project_id": model.get("project_id"), "valid": not errors, "errors": errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        return 1
    args.output.write_text(json.dumps(build_handoff(model), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
