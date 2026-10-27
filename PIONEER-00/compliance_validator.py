"""PIONEER P03B: traceability validator; not a legal compliance certification."""
import json
from pathlib import Path
from security_validator import validate_security


def validate_compliance(architecture, security, catalog):
    errors = validate_security(architecture, security)
    sources = {}
    for item in catalog.get("sources", []):
        sid = item.get("id")
        if not sid or sid in sources:
            errors.append(f"duplicate or missing source id: {sid}")
        else:
            sources[sid] = item
        for key in ("title", "version", "verified_at", "url"):
            if not item.get(key):
                errors.append(f"source {sid} missing {key}")

    controls = {c.get("id") for c in architecture.get("security_controls", [])}
    req_ids = set()
    for req in security.get("requirements", []):
        rid = req.get("id")
        req_ids.add(rid)
        refs = req.get("source_refs", [])
        if not refs:
            errors.append(f"requirement {rid} has no source_refs")
        for ref in refs:
            source_id = ref.get("source_id")
            if source_id not in sources:
                errors.append(f"unknown source for {rid}: {source_id}")
            if not ref.get("clause"):
                errors.append(f"missing clause for {rid}")
            if not ref.get("verification_status"):
                errors.append(f"missing verification_status for {rid}")

    for item in catalog.get("evidence", []):
        eid = item.get("id")
        if item.get("requirement_id") not in req_ids:
            errors.append(f"evidence {eid} unknown requirement")
        if item.get("control_id") not in controls:
            errors.append(f"evidence {eid} unknown control")
        if item.get("status") == "verified" and not item.get("artifact_ref"):
            errors.append(f"evidence {eid} verified without artifact_ref")

    return errors


def main():
    root = Path(__file__).resolve().parent
    def read(path):
        return json.loads((root / path).read_text(encoding="utf-8-sig"))
    errors = validate_compliance(
        read("examples/architecture_dependencies.json"),
        read("security/security-model-traceable.json"),
        read("security/source-catalog.json"),
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
