import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pioneer import build_handoff, validate

MODEL = json.loads((ROOT / "examples" / "architecture.json").read_text(encoding="utf-8"))


class PioneerTests(unittest.TestCase):
    def test_valid_example(self):
        self.assertEqual(validate(MODEL), [])

    def test_overlapping_networks(self):
        model = copy.deepcopy(MODEL)
        model["networks"].append({"id": "other", "cidr": "10.10.10.128/25"})
        self.assertTrue(any("overlapping" in e for e in validate(model)))

    def test_unknown_network(self):
        model = copy.deepcopy(MODEL)
        model["resources"][0]["network"] = "missing"
        self.assertTrue(any("unknown network" in e for e in validate(model)))

    def test_gate_not_approved(self):
        handoff = build_handoff(MODEL)
        self.assertEqual(handoff["approval_status"], "READY_FOR_REVIEW")
        self.assertEqual(handoff["target_agent"], "AG-003")


if __name__ == "__main__":
    unittest.main()
