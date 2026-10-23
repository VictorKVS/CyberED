#!/usr/bin/env python3
"""FAS/1.0 baseline geometry and file validation (stdlib only)."""
import json,sys
from pathlib import Path
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
    cfg=json.loads((root/"avatar.json").read_text(encoding="utf-8"))
    assert cfg["standard"]=="FAS/1.0"
    assert cfg["canvas"]=={"width":1024,"height":1024}
    for name in ("left_eye","right_eye","mouth"):
        xy=cfg["anchors"][name]
        assert len(xy)==2 and all(isinstance(v,(int,float)) and 0<=v<=1 for v in xy),name
    for name,path in cfg["states"].items():
        p=(root/path).resolve()
        assert p.is_relative_to(root),f"unsafe path: {name}"
        assert p.is_file(),f"missing: {p}"
    print("FAS basic configuration checks: PASS")
    print("NOTE: image dimensions, alignment, blink and speech require additional visual QA.")
if __name__=="__main__":main()
