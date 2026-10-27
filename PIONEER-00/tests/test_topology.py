import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from topology import build_topology

MODEL = json.loads((ROOT / "examples" / "architecture.json").read_text(encoding="utf-8"))


class TopologyTests(unittest.TestCase):
    def test_expected_nodes_and_edges(self):
        graph = build_topology(MODEL)
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual(graph["edges"][0]["target"], "network:servers")

    def test_edge_endpoints_exist(self):
        graph = build_topology(MODEL)
        ids = {node["id"] for node in graph["nodes"]}
        for edge in graph["edges"]:
            self.assertIn(edge["source"], ids)
            self.assertIn(edge["target"], ids)

    def test_invalid_model_rejected(self):
        model = copy.deepcopy(MODEL)
        model["resources"][0]["network"] = "nonexistent"
        with self.assertRaises(ValueError):
            build_topology(model)


if __name__ == "__main__":
    unittest.main()
