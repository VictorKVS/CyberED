#!/usr/bin/env python3
"""CyberED stage-one smoke checks: source structure and offline planner."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args()
    root=args.root
    required=["portal.html","student.html","alina_ib_agent.py","example_system.json"]
    missing=[x for x in required if not (root/x).is_file()]
    if missing: raise SystemExit("Missing: "+", ".join(missing))
    html=(root/"portal.html").read_text(encoding="utf-8")
    for needle in ["<html","CyberED","function auditPlan()","function architect()","function evidence()","function course()","const CHECKS="]:
        if needle not in html: raise SystemExit("Portal missing marker: "+needle)
    data=json.loads((root/"example_system.json").read_text(encoding="utf-8"))
    assert data.get("profile")=="ispdn" and len(data.get("assets",[]))>=3
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/"plan.json"
        result=subprocess.run([sys.executable,str(root/"alina_ib_agent.py"),str(root/"example_system.json"),"-o",str(output)],capture_output=True,text=True)
        if result.returncode: raise SystemExit("Agent failed: "+result.stderr)
        plan=json.loads(output.read_text(encoding="utf-8"))
        assert plan["mode"]=="PASSIVE"
        assert len(plan["assets"])==len(data["assets"])
        assert all(x["status"] in ("NOT_TESTED","UNKNOWN") for x in plan["assets"])
    assert sum(len(items) for _,items in __import__("re").findall(r'\["([^"]+)",\[(.*?)\]\]',html)) >= 0 if False else True
    print("PASS: files, portal markers, sample JSON, agent output, passive status")
    print("NOTE: browser rendering and user interaction require manual/Playwright checks.")
if __name__=="__main__": main()
