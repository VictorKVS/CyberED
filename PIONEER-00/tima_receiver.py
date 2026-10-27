"""Read-only training TIMA receiver. Not the actual AG-003 agent."""
import json
from pathlib import Path
from gate1 import canonical_digest, check_gate1

ROOT = Path(__file__).resolve().parent


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def receive(handoff, approval, architecture, security, catalog):
    expected = {
        "architecture_sha256": canonical_digest(architecture),
        "security_sha256": canonical_digest(security),
        "catalog_sha256": canonical_digest(catalog),
    }
    for field, actual in expected.items():
        if handoff.get(field) != actual:
            return "REJECTED", f"source mismatch: {field}"
    allowed, reason = check_gate1(handoff, approval)
    if not allowed:
        return "REJECTED", reason
    return "ACCEPTED_FOR_REVIEW", reason


if __name__ == "__main__":
    handoff = load("handoff-gate1.json")
    architecture = load("examples/architecture_dependencies.json")
    security = load("security/security-model-traceable.json")
    catalog = load("security/source-catalog.json")
    status, reason = receive(handoff, {}, architecture, security, catalog)
    print(json.dumps({
        "agent": "TIMA-RECEIVER-PROTOTYPE",
        "project_id": handoff["project_id"],
        "status": status,
        "reason": reason,
        "deployment_permitted": False
    }, ensure_ascii=False, indent=2))
