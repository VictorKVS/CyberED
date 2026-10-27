import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compliance_validator import validate_compliance


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


ARCH = read("examples/architecture_dependencies.json")
SEC = read("security/security-model-traceable.json")
CAT = read("security/source-catalog.json")


class ComplianceTests(unittest.TestCase):
    def test_valid_draft(self):
        self.assertEqual(validate_compliance(ARCH, SEC, CAT), [])

    def test_missing_source(self):
        sec = copy.deepcopy(SEC)
        sec["requirements"][0]["source_refs"][0]["source_id"] = "MISSING"
        self.assertTrue(any("unknown source" in x for x in validate_compliance(ARCH, sec, CAT)))

    def test_missing_clause(self):
        sec = copy.deepcopy(SEC)
        sec["requirements"][0]["source_refs"][0]["clause"] = ""
        self.assertTrue(any("missing clause" in x for x in validate_compliance(ARCH, sec, CAT)))

    def test_fake_verified_evidence(self):
        cat = copy.deepcopy(CAT)
        cat["evidence"][0]["status"] = "verified"
        self.assertTrue(any("without artifact_ref" in x for x in validate_compliance(ARCH, SEC, cat)))

    def test_duplicate_source(self):
        cat = copy.deepcopy(CAT)
        cat["sources"].append(copy.deepcopy(cat["sources"][0]))
        self.assertTrue(any("duplicate" in x for x in validate_compliance(ARCH, SEC, cat)))


if __name__ == "__main__":
    unittest.main()
