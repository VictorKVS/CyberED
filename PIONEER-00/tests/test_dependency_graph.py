import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dependency_graph import build_dependency_graph

MODEL = json.loads((ROOT / "examples" / "architecture_dependencies.json").read_text(encoding="utf-8"))


class DependencyGraphTests(unittest.TestCase):
    def test_graph_and_relations(self):
        graph = build_dependency_graph(MODEL)
        self.assertEqual(len(graph["nodes"]), 5)
        self.assertEqual(len(graph["edges"]), 4)
        relations = {edge["relation"] for edge in graph["edges"]}
        self.assertIn("depends_on", relations)
        self.assertIn("protects", relations)

    def test_missing_dependency(self):
        model = copy.deepcopy(MODEL)
        model["resources"][1]["depends_on"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            build_dependency_graph(model)

    def test_dependency_cycle(self):
        model = copy.deepcopy(MODEL)
        model["resources"][0]["depends_on"] = ["app01"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            build_dependency_graph(model)

    def test_unknown_protected_resource(self):
        model = copy.deepcopy(MODEL)
        model["security_controls"][0]["protects"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown protected resource"):
            build_dependency_graph(model)


if __name__ == "__main__":
    unittest.main()
