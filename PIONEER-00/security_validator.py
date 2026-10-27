"""PIONEER P03A: validate security knowledge graph references (offline)."""
import json
from pathlib import Path


def validate_security(architecture, security):
    errors = []
    if security.get("project_id") != architecture.get("project_id"):
        errors.append("project_id mismatch")
    assets = {r.get("id") for r in architecture.get("resources", [])}
    controls = {c.get("id") for c in architecture.get("security_controls", [])}
    threat_ids = set()
    requirement_ids = set()
    used_controls = set()

    for threat in security.get("threats", []):
        tid = threat.get("id")
        if not tid or tid in threat_ids:
            errors.append(f"duplicate or missing threat id: {tid}")
        threat_ids.add(tid)
        for asset in threat.get("affected_assets", []):
            if asset not in assets:
                errors.append(f"unknown affected asset: {tid} -> {asset}")
        for control in threat.get("controls", []):
            used_controls.add(control)
            if control not in controls:
                errors.append(f"unknown threat control: {tid} -> {control}")

    for req in security.get("requirements", []):
        rid = req.get("id")
        if not rid or rid in requirement_ids:
            errors.append(f"duplicate or missing requirement id: {rid}")
        requirement_ids.add(rid)
        for control in req.get("controls", []):
            used_controls.add(control)
            if control not in controls:
                errors.append(f"unknown requirement control: {rid} -> {control}")

    if not security.get("threats"):
        errors.append("threats must not be empty")
    if not security.get("requirements"):
        errors.append("requirements must not be empty")
    for control in controls - used_controls:
        errors.append(f"unreferenced architecture control: {control}")
    return errors


def main():
    root = Path(__file__).resolve().parent
    architecture = json.loads((root / "examples" / "architecture_dependencies.json").read_text(encoding="utf-8-sig"))
    security = json.loads((root / "security" / "security-model.json").read_text(encoding="utf-8-sig"))
    errors = validate_security(architecture, security)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
