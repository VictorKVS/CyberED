import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gate1 import canonical_digest, prepare_handoff, check_gate1


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


ARCH = load("examples/architecture_dependencies.json")
SEC = load("security/security-model-traceable.json")
CAT = load("security/source-catalog.json")


def approval_for(handoff):
    return {key: handoff[key] for key in (
        "project_id", "architecture_revision", "architecture_sha256",
        "security_sha256", "catalog_sha256"
    )} | {"decision": "APPROVED", "approved_by": "training-reviewer", "approved_at": "2026-10-27T00:00:00Z"}


class Gate1Tests(unittest.TestCase):
    def test_prepared_handoff_requires_review(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        self.assertEqual(handoff["approval_status"], "READY_FOR_REVIEW")
        self.assertEqual(len(handoff["architecture_sha256"]), 64)

    def test_no_approval_denied(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        self.assertFalse(check_gate1(handoff, {})[0])

    def test_matching_metadata_passes(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        self.assertTrue(check_gate1(handoff, approval_for(handoff))[0])

    def test_changed_architecture_denied(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        approval = approval_for(handoff)
        altered = copy.deepcopy(ARCH)
        altered["resources"][0]["memory_gb"] = 8
        changed = prepare_handoff(altered, SEC, CAT)
        self.assertFalse(check_gate1(changed, approval)[0])

    def test_changed_security_denied(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        approval = approval_for(handoff)
        changed_sec = copy.deepcopy(SEC)
        changed_sec["threats"][0]["name"] = "Changed"
        changed = prepare_handoff(ARCH, changed_sec, CAT)
        self.assertFalse(check_gate1(changed, approval)[0])

    def test_digest_order_independent(self):
        self.assertEqual(canonical_digest({"a": 1, "b": 2}),
                         canonical_digest({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
