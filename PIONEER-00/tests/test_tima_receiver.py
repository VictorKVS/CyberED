import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gate1 import prepare_handoff
from tima_receiver import receive


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


ARCH = load("examples/architecture_dependencies.json")
SEC = load("security/security-model-traceable.json")
CAT = load("security/source-catalog.json")


def training_approval(handoff):
    fields = ("project_id", "architecture_revision", "architecture_sha256",
              "security_sha256", "catalog_sha256")
    approval = {field: handoff[field] for field in fields}
    approval.update(decision="APPROVED", approved_by="test-fixture",
                    approved_at="2026-10-27T00:00:00Z")
    return approval


class TimaReceiverTests(unittest.TestCase):
    def test_without_approval_rejected(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        status, _ = receive(handoff, {}, ARCH, SEC, CAT)
        self.assertEqual(status, "REJECTED")

    def test_training_metadata_accepted_for_review_only(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        status, _ = receive(handoff, training_approval(handoff), ARCH, SEC, CAT)
        self.assertEqual(status, "ACCEPTED_FOR_REVIEW")

    def test_architecture_modified_after_approval_rejected(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        approval = training_approval(handoff)
        changed_arch = copy.deepcopy(ARCH)
        changed_arch["resources"][0]["memory_gb"] = 8
        status, _ = receive(handoff, approval, changed_arch, SEC, CAT)
        self.assertEqual(status, "REJECTED")

    def test_security_modified_after_approval_rejected(self):
        handoff = prepare_handoff(ARCH, SEC, CAT)
        approval = training_approval(handoff)
        changed_sec = copy.deepcopy(SEC)
        changed_sec["threats"][0]["name"] = "changed"
        status, _ = receive(handoff, approval, ARCH, changed_sec, CAT)
        self.assertEqual(status, "REJECTED")


if __name__ == "__main__":
    unittest.main()
