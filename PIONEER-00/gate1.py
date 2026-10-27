"""PIONEER P04: immutable handoff fingerprint and fail-closed GATE-1 check.

Approval file is a local training artifact, not cryptographic proof of identity.
No deployment is performed.
"""
import hashlib
import json
from pathlib import Path
from pioneer import validate, build_handoff
from dependency_graph import build_dependency_graph
from compliance_validator import validate_compliance


def canonical_digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare_handoff(architecture, security, catalog):
    errors = validate(architecture) + validate_compliance(architecture, security, catalog)
    if errors:
        raise ValueError("; ".join(errors))
    build_dependency_graph(architecture)
    handoff = build_handoff(architecture)
    handoff["architecture_sha256"] = canonical_digest(architecture)
    handoff["security_sha256"] = canonical_digest(security)
    handoff["catalog_sha256"] = canonical_digest(catalog)
    handoff["approval_status"] = "READY_FOR_REVIEW"
    return handoff


def check_gate1(handoff, approval):
    required = ("project_id", "architecture_revision", "architecture_sha256",
                "security_sha256", "catalog_sha256")
    if handoff.get("approval_status") != "READY_FOR_REVIEW":
        return False, "handoff must be READY_FOR_REVIEW"
    if approval.get("decision") != "APPROVED":
        return False, "GATE-1 approval missing"
    if not approval.get("approved_by") or not approval.get("approved_at"):
        return False, "approval identity or timestamp missing"
    for field in required:
        if not handoff.get(field) or handoff[field] != approval.get(field):
            return False, f"approval mismatch: {field}"
    return True, "GATE-1 metadata matched; identity not cryptographically verified"


def main():
    root = Path(__file__).resolve().parent
    def load(path):
        return json.loads((root / path).read_text(encoding="utf-8-sig"))
    handoff = prepare_handoff(
        load("examples/architecture_dependencies.json"),
        load("security/security-model-traceable.json"),
        load("security/source-catalog.json"),
    )
    output = root / "handoff-gate1.json"
    output.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"handoff": str(output), "approval_status": handoff["approval_status"],
                      "architecture_sha256": handoff["architecture_sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
