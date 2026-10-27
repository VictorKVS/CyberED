import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from security_validator import validate_security

ARCH = json.loads((ROOT / "examples" / "architecture_dependencies.json").read_text(encoding="utf-8"))
SEC = json.loads((ROOT / "security" / "security-model.json").read_text(encoding="utf-8"))


class SecurityValidatorTests(unittest.TestCase):
    def test_valid_security_graph(self):
        self.assertEqual(validate_security(ARCH, SEC), [])

    def test_unknown_asset(self):
        sec = copy.deepcopy(SEC)
        sec["threats"][0]["affected_assets"] = ["ghost"]
        self.assertTrue(any("unknown affected asset" in x for x in validate_security(ARCH, sec)))

    def test_unknown_control(self):
        sec = copy.deepcopy(SEC)
        sec["requirements"][0]["controls"] = ["ghost"]
        self.assertTrue(any("unknown requirement control" in x for x in validate_security(ARCH, sec)))

    def test_duplicate_threat(self):
        sec = copy.deepcopy(SEC)
        sec["threats"].append(copy.deepcopy(sec["threats"][0]))
        self.assertTrue(any("duplicate" in x for x in validate_security(ARCH, sec)))

    def test_project_mismatch(self):
        sec = copy.deepcopy(SEC)
        sec["project_id"] = "wrong-project"
        self.assertIn("project_id mismatch", validate_security(ARCH, sec))


if __name__ == "__main__":
    unittest.main()
